#!/usr/bin/env bats
# test_flatpak_tracking.bats - Tests for flatpak tracking and install flow

# Setup test environment
setup() {
  # Load required modules
  export BATS_TEST_DIRNAME="${BATS_TEST_DIRNAME:-$(dirname "$BATS_TEST_FILENAME")}"
  export PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."

  # Create temporary test directory
  export TEST_TEMP_DIR="${BATS_TEST_TMPDIR}/flatpak_test_$$"
  mkdir -p "$TEST_TEMP_DIR"

  # Override XDG_DATA_HOME for testing
  export XDG_DATA_HOME="$TEST_TEMP_DIR/.local/share"

  # Prepare a fake bin directory and ensure it's first in PATH
  export PATH="$TEST_TEMP_DIR/bin:$PATH"
  mkdir -p "$TEST_TEMP_DIR/bin"

  # File to capture calls to the fake flatpak
  export FLATPAK_CALLS_FILE="$TEST_TEMP_DIR/flatpak_calls.log"

  # Create a fake flatpak binary that logs its args and succeeds
  cat >"$TEST_TEMP_DIR/bin/flatpak" <<'EOF'
#!/usr/bin/env bash
# Simple flatpak stub for tests. Logs args to FLATPAK_CALLS_FILE env var.
: "${FLATPAK_CALLS_FILE:=/tmp/flatpak_calls.log}"
echo "$(date -u +%s) $0 $*" >>"$FLATPAK_CALLS_FILE"

# Emulate basic behavior: accept remote-add and install
case "$1" in
  remote-add)
    # succeed
    exit 0
    ;;
  install)
    # succeed
    exit 0
    ;;
  *)
    # default success
    exit 0
    ;;
esac
EOF
  chmod +x "$TEST_TEMP_DIR/bin/flatpak"

  # Set test distribution envs if used by other modules
  export DETECTED_DISTRO="generic"
  export CURRENT_DISTRO="generic"

  # Load modules under test
  source "${PROJECT_ROOT}/src/core/logging.sh"
  source "${PROJECT_ROOT}/src/core/ini_parser.sh"
  source "${PROJECT_ROOT}/src/core/package_tracking.sh"
  source "${PROJECT_ROOT}/src/core/install_packages.sh"

  # Suppress log output during tests
  LOG_LEVEL="ERROR"
}

# Cleanup after each test
teardown() {
  if [[ -d "$TEST_TEMP_DIR" ]]; then
    rm -rf "$TEST_TEMP_DIR"
  fi
}

@test "track_flatpak_install adds flatpak entry with proper fields" {
  init_package_tracking

  run track_flatpak_install "org.signal.Signal" "flathub" "flatpak" "org.signal.Signal" "org.signal.Signal"
  [ "$status" -eq 0 ]

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  # Section exists
  grep -q "^\[package.org.signal.Signal\]$" "$db_file"
  # Source recorded as flatpak:flathub
  grep -q "^source=flatpak:flathub$" "$db_file"
  # Install method recorded as flatpak_install
  grep -q "^install_method=flatpak_install$" "$db_file"
  # Category recorded as flatpak
  grep -q "^category=flatpak$" "$db_file"
}

@test "install_flatpak_packages calls flatpak and records all apps" {
  # Ensure clean tracking DB
  init_package_tracking

  # Define some flatpak packages to install
  FLATPAK_PACKAGES=("org.signal.Signal" "io.github.martchus.syncthingtray")

  # Ensure the fake flatpak calls file is empty
  : >"$FLATPAK_CALLS_FILE"

  # Run the installer (should call our fake flatpak and then track entries)
  run install_flatpak_packages
  [ "$status" -eq 0 ]

  # Verify flatpak binary was called at least once (remote-add + install)
  grep -q "flatpak" "$FLATPAK_CALLS_FILE"

  # Verify both apps were recorded in the tracking DB
  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  grep -q "^\[package.org.signal.Signal\]$" "$db_file"
  grep -q "^\[package.io.github.martchus.syncthingtray\]$" "$db_file"

  # Verify their source/install_method/category
  grep -q "^source=flatpak:flathub$" "$db_file"
  grep -q "^install_method=flatpak_install$" "$db_file"
  grep -q "^category=flatpak$" "$db_file"

  # Check get_tracking_stats includes flatpak count equal to number of FLATPAK_PACKAGES
  run get_tracking_stats
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "^flatpak=${#FLATPAK_PACKAGES[@]}$"
}

@test "install_flatpak_packages skips when no FLATPAK_PACKAGES defined" {
  init_package_tracking

  # Unset or empty the array
  FLATPAK_PACKAGES=()

  run install_flatpak_packages
  [ "$status" -eq 0 ]

  # Ensure flatpak wasn't called
  [ ! -f "$FLATPAK_CALLS_FILE" ] || ! grep -q "install" "$FLATPAK_CALLS_FILE"
}
