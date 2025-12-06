#!/usr/bin/env bats
# test_metadata_integration.bats - Integration tests for metadata-based tracking

# Setup test environment
setup() {
  # Load required modules
  export BATS_TEST_DIRNAME="${BATS_TEST_DIRNAME:-$(dirname "$BATS_TEST_FILENAME")}"
  export PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."

  # Create temporary test directory
  export TEST_TEMP_DIR="${BATS_TEST_TMPDIR}/metadata_test_$$"
  mkdir -p "$TEST_TEMP_DIR"

  # Override XDG_DATA_HOME for testing
  export XDG_DATA_HOME="$TEST_TEMP_DIR/.local/share"
  export CONFIG_DIR="$TEST_TEMP_DIR/config"
  mkdir -p "$CONFIG_DIR"

  # Set test distribution
  export DETECTED_DISTRO="fedora"
  export CURRENT_DISTRO="fedora"

  # Load modules
  source "${PROJECT_ROOT}/src/core/logging.sh"
  source "${PROJECT_ROOT}/src/core/ini_parser.sh"
  source "${PROJECT_ROOT}/src/core/distro_detection.sh"
  source "${PROJECT_ROOT}/src/core/package_mapping.sh"
  source "${PROJECT_ROOT}/src/core/package_tracking.sh"

  # Suppress log output during tests
  LOG_LEVEL="ERROR"

  # Create test pkgmap.ini
  cat >"$CONFIG_DIR/pkgmap.ini" <<'EOF'
[pkgmap.fedora]
lazygit=COPR:dejan/lazygit
starship=COPR:atim/starship
qtile-extras=COPR:frostyx/qtile
neovim=neovim

[pkgmap.arch]
lazygit=AUR:lazygit
thinkfan=AUR:thinkfan
neovim=neovim
EOF

  # Initialize tracking
  init_package_tracking
}

# Cleanup after each test
teardown() {
  if [[ -d "$TEST_TEMP_DIR" ]]; then
    rm -rf "$TEST_TEMP_DIR"
  fi
}

@test "metadata storage: COPR package with explicit name" {
  local pkg="lazygit"
  local mapped="COPR:dejan/lazygit:lazygit"
  local category="dev"

  _store_mapping_metadata "$pkg" "$mapped" "$category" "fedora"

  local metadata
  metadata=$(get_package_metadata "$pkg")

  [[ -n "$metadata" ]]
  [ "$metadata" = "COPR:dejan/lazygit|dev|lazygit" ]
}

@test "metadata storage: COPR package without explicit name" {
  local pkg="starship"
  local mapped="COPR:atim/starship"
  local category="dev"

  _store_mapping_metadata "$pkg" "$mapped" "$category" "fedora"

  local metadata
  metadata=$(get_package_metadata "$pkg")

  [ "$metadata" = "COPR:atim/starship|dev|starship" ]
}

@test "metadata storage: AUR package" {
  export DETECTED_DISTRO="arch"

  local pkg="lazygit"
  local mapped="AUR:lazygit"
  local category="dev"

  _store_mapping_metadata "$pkg" "$mapped" "$category" "arch"

  local metadata
  metadata=$(get_package_metadata "$pkg")

  [ "$metadata" = "AUR:lazygit|dev|lazygit" ]
}

@test "metadata storage: official package" {
  local pkg="neovim"
  local mapped="neovim"
  local category="apps"

  _store_mapping_metadata "$pkg" "$mapped" "$category" "fedora"

  local metadata
  metadata=$(get_package_metadata "$pkg")

  [ "$metadata" = "official|apps|neovim" ]
}

@test "map_package_list stores metadata with category" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  local packages=("lazygit" "starship" "neovim")
  local mapped_output
  mapfile -t mapped_output < <(map_package_list "fedora" "dev" "${packages[@]}")

  # Check mappings were returned
  [[ ${#mapped_output[@]} -eq 3 ]]

  # Check metadata was stored
  local lazygit_meta
  lazygit_meta=$(get_package_metadata "lazygit")
  [ "$lazygit_meta" = "COPR:dejan/lazygit|dev|lazygit" ]

  local starship_meta
  starship_meta=$(get_package_metadata "starship")
  [ "$starship_meta" = "COPR:atim/starship|dev|starship" ]

  local neovim_meta
  neovim_meta=$(get_package_metadata "neovim")
  [ "$neovim_meta" = "official|dev|neovim" ]
}

@test "metadata persists across multiple map_package_list calls" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  # First call - dev category
  map_package_list "fedora" "dev" "lazygit" >/dev/null

  # Second call - apps category
  map_package_list "fedora" "apps" "neovim" >/dev/null

  # Both should be stored
  local lazygit_meta
  lazygit_meta=$(get_package_metadata "lazygit")
  [ "$lazygit_meta" = "COPR:dejan/lazygit|dev|lazygit" ]

  local neovim_meta
  neovim_meta=$(get_package_metadata "neovim")
  [ "$neovim_meta" = "official|apps|neovim" ]
}

@test "tracking integration: track with metadata includes original name" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"
  map_package_list "fedora" "dev" "lazygit" >/dev/null

  # Simulate tracking after installation
  local metadata
  metadata=$(get_package_metadata "lazygit")
  IFS='|' read -r source category final_name <<<"$metadata"

  track_package_install "$final_name" "$source" "$category" "$final_name" "lazygit"

  # Verify tracking
  run is_package_tracked "lazygit"
  [ "$status" -eq 0 ]

  # Check stored values
  local stored_original
  stored_original=$(get_ini_value "package.lazygit" "original_name")
  [[ "$stored_original" == "lazygit" ]]

  local stored_source
  stored_source=$(get_ini_value "package.lazygit" "source")
  [[ "$stored_source" == "COPR:dejan/lazygit" ]]

  local stored_category
  stored_category=$(get_ini_value "package.lazygit" "category")
  [[ "$stored_category" == "dev" ]]
}

@test "PACKAGE_MAPPINGS lookup simulates repository source detection" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  # Check that mapping was loaded
  [[ -n "${PACKAGE_MAPPINGS[lazygit]:-}" ]]
  [[ "${PACKAGE_MAPPINGS[lazygit]}" == "COPR:dejan/lazygit" ]]
}

@test "mapped value parsing extracts COPR source correctly" {
  local mapped="COPR:dejan/lazygit"

  if [[ "$mapped" =~ ^COPR:([^:]+) ]]; then
    local source="COPR:${BASH_REMATCH[1]}"
    [[ "$source" == "COPR:dejan/lazygit" ]]
  else
    # Should not reach here
    false
  fi
}

@test "multiple packages from same category track correctly" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  local dev_packages=("lazygit" "starship" "neovim")
  map_package_list "fedora" "dev" "${dev_packages[@]}" >/dev/null

  # All should have dev category
  for pkg in "${dev_packages[@]}"; do
    local metadata
    metadata=$(get_package_metadata "$pkg")
    echo "$metadata" | grep -F "|dev|"
  done
}

@test "unmapped package defaults to official" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  # Package not in pkgmap.ini
  map_package_list "fedora" "apps" "curl" >/dev/null

  local metadata
  metadata=$(get_package_metadata "curl")
  [ "$metadata" = "official|apps|curl" ]
}

@test "metadata handles package name mapping differences" {
  # Create a pkgmap with name that differs from original
  cat >"$CONFIG_DIR/pkgmap2.ini" <<'EOF'
[pkgmap.arch]
gh=github-cli
fd-find=fd
EOF

  load_package_mappings "$CONFIG_DIR/pkgmap2.ini"
  export DETECTED_DISTRO="arch"

  map_package_list "arch" "dev" "gh" >/dev/null

  local metadata
  metadata=$(get_package_metadata "gh")
  # Original name is gh, but final installed name is github-cli
  [ "$metadata" = "official|dev|github-cli" ]
}

@test "list_tracked_packages shows original and installed names" {
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"
  map_package_list "fedora" "dev" "lazygit" >/dev/null

  # Track with both names
  track_package_install "lazygit" "COPR:dejan/lazygit" "dev" "lazygit" "lazygit"

  run list_tracked_packages
  [ "$status" -eq 0 ]

  # Output should contain both original and installed name columns
  echo "$output" | grep -q "ORIGINAL NAME"
  echo "$output" | grep -q "INSTALLED NAME"
  echo "$output" | grep -q "lazygit"
}

@test "package without mapping is treated as official" {
  # Load mappings but check unmapped package
  load_package_mappings "$CONFIG_DIR/pkgmap.ini"

  # Package not in pkgmap.ini should have no mapping entry
  [[ -z "${PACKAGE_MAPPINGS[unmapped - pkg]:-}" ]]
}

@test "metadata storage handles PPA packages" {
  local pkg="pkg1"
  local mapped="PPA:user/repo:pkg1"
  local category="apps"

  _store_mapping_metadata "$pkg" "$mapped" "$category" "debian"

  local metadata
  metadata=$(get_package_metadata "$pkg")
  [ "$metadata" = "PPA:user/repo|apps|pkg1" ]
}
