#!/usr/bin/env bats
# test_package_tracking.bats - Tests for package tracking functionality

# Setup test environment
setup() {
  # Load required modules
  export BATS_TEST_DIRNAME="${BATS_TEST_DIRNAME:-$(dirname "$BATS_TEST_FILENAME")}"
  export PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."

  # Create temporary test directory
  export TEST_TEMP_DIR="${BATS_TEST_TMPDIR}/tracking_test_$$"
  mkdir -p "$TEST_TEMP_DIR"

  # Override XDG_DATA_HOME for testing
  export XDG_DATA_HOME="$TEST_TEMP_DIR/.local/share"

  # Load modules
  source "${PROJECT_ROOT}/src/core/logging.sh"
  source "${PROJECT_ROOT}/src/core/ini_parser.sh"
  source "${PROJECT_ROOT}/src/core/package_tracking.sh"

  # Suppress log output during tests
  LOG_LEVEL="ERROR"
}

# Cleanup after each test
teardown() {
  if [[ -d "$TEST_TEMP_DIR" ]]; then
    rm -rf "$TEST_TEMP_DIR"
  fi
}

@test "init_package_tracking creates database directory" {
  run init_package_tracking
  [ "$status" -eq 0 ]
  [ -d "${XDG_DATA_HOME}/auto-penguin-setup" ]
}

@test "init_package_tracking creates database file" {
  run init_package_tracking
  [ "$status" -eq 0 ]
  [ -f "${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini" ]
}

@test "init_package_tracking creates valid INI structure" {
  init_package_tracking

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  grep -q "^\[metadata\]$" "$db_file"
  grep -q "^version=" "$db_file"
  grep -q "^created_at=" "$db_file"
}

@test "track_package_install adds new package" {
  init_package_tracking

  run track_package_install "testpkg" "official" "test"
  [ "$status" -eq 0 ]

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  grep -q "^\[package.testpkg\]$" "$db_file"
}

@test "track_package_install stores correct metadata" {
  init_package_tracking
  track_package_install "testpkg" "COPR:user/repo" "apps"

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  grep -q "^name=testpkg$" "$db_file"
  grep -q "^source=COPR:user/repo$" "$db_file"
  grep -q "^category=apps$" "$db_file"
}

@test "track_package_install updates existing package" {
  init_package_tracking
  track_package_install "testpkg" "official" "apps"
  track_package_install "testpkg" "COPR:user/repo" "dev"

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"

  # Should have only one entry for testpkg
  local count=$(grep -c "^\[package.testpkg\]$" "$db_file")
  [ "$count" -eq 1 ]

  # Should have updated source
  grep -q "^source=COPR:user/repo$" "$db_file"
  grep -q "^category=dev$" "$db_file"
}

@test "get_tracked_packages lists all packages" {
  init_package_tracking
  track_package_install "pkg1" "official" "apps"
  track_package_install "pkg2" "AUR:pkg2" "dev"

  run get_tracked_packages
  [ "$status" -eq 0 ]

  echo "$output" | grep -q "pkg1"
  echo "$output" | grep -q "pkg2"
}

@test "get_package_source returns correct source" {
  init_package_tracking
  track_package_install "testpkg" "COPR:user/repo" "apps"

  run get_package_source "testpkg"
  [ "$status" -eq 0 ]
  [ "$output" = "COPR:user/repo" ]
}

@test "get_packages_from_repo filters by repository" {
  init_package_tracking
  track_package_install "pkg1" "COPR:user/repo1" "apps"
  track_package_install "pkg2" "COPR:user/repo1" "dev"
  track_package_install "pkg3" "COPR:user/repo2" "apps"
  track_package_install "pkg4" "official" "system"

  run get_packages_from_repo "COPR:user/repo1"
  [ "$status" -eq 0 ]

  echo "$output" | grep -q "pkg1"
  echo "$output" | grep -q "pkg2"
  echo "$output" | grep -qv "pkg3"
  echo "$output" | grep -qv "pkg4"
}

@test "is_package_tracked returns 0 for tracked package" {
  init_package_tracking
  track_package_install "testpkg" "official" "apps"

  run is_package_tracked "testpkg"
  [ "$status" -eq 0 ]
}

@test "is_package_tracked returns 1 for untracked package" {
  init_package_tracking

  run is_package_tracked "nonexistent"
  [ "$status" -eq 1 ]
}

@test "untrack_package removes package from database" {
  init_package_tracking
  track_package_install "testpkg" "official" "apps"

  run untrack_package "testpkg"
  [ "$status" -eq 0 ]

  run is_package_tracked "testpkg"
  [ "$status" -eq 1 ]
}

@test "get_package_info returns all package fields" {
  init_package_tracking
  track_package_install "testpkg" "COPR:user/repo" "apps"

  run get_package_info "testpkg"
  [ "$status" -eq 0 ]

  echo "$output" | grep -q "^name=testpkg$"
  echo "$output" | grep -q "^source=COPR:user/repo$"
  echo "$output" | grep -q "^category=apps$"
  echo "$output" | grep -q "^install_method=pm_install$"
}

@test "get_tracking_stats counts packages correctly" {
  init_package_tracking
  track_package_install "pkg1" "official" "apps"
  track_package_install "pkg2" "COPR:user/repo" "dev"
  track_package_install "pkg3" "COPR:user/repo2" "apps"
  track_package_install "pkg4" "AUR:pkg4" "system"

  run get_tracking_stats
  [ "$status" -eq 0 ]

  echo "$output" | grep -q "^total=4$"
  echo "$output" | grep -q "^copr=2$"
  echo "$output" | grep -q "^aur=1$"
  echo "$output" | grep -q "^official=1$"
}

@test "tracking database has correct permissions" {
  init_package_tracking

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  local perms=$(stat -c '%a' "$db_file")
  [ "$perms" = "600" ]
}

@test "track_package_install handles empty category" {
  init_package_tracking

  run track_package_install "testpkg" "official" ""
  [ "$status" -eq 0 ]

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"
  grep -q "^category=uncategorized$" "$db_file"
}

@test "track_package_install requires package name" {
  init_package_tracking

  run track_package_install "" "official" "apps"
  [ "$status" -eq 1 ]
}

@test "multiple packages in same category" {
  init_package_tracking
  track_package_install "pkg1" "official" "apps"
  track_package_install "pkg2" "official" "apps"
  track_package_install "pkg3" "COPR:user/repo" "apps"

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"

  # All three packages should be tracked
  grep -q "^\[package.pkg1\]$" "$db_file"
  grep -q "^\[package.pkg2\]$" "$db_file"
  grep -q "^\[package.pkg3\]$" "$db_file"
}

@test "timestamp format is ISO 8601" {
  init_package_tracking
  track_package_install "testpkg" "official" "apps"

  local db_file="${XDG_DATA_HOME}/auto-penguin-setup/package_tracking.ini"

  # Check timestamp matches ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
  grep -E "^installed_at=[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$" "$db_file"
}

@test "list_tracked_packages shows human-readable output" {
  init_package_tracking
  track_package_install "testpkg" "COPR:user/repo" "apps"

  run list_tracked_packages
  [ "$status" -eq 0 ]

  echo "$output" | grep -q "testpkg"
  echo "$output" | grep -q "COPR:user/repo"
}
