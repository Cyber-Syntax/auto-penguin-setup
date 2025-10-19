#!/usr/bin/env bats
# tests/test_package_mapping.sh - Tests for package mapping and COPR/AUR handling

load test_helper

setup() {
  # Get the absolute path to the repository root
  REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
  
  # Create temporary test directory
  export BATS_TEST_TMPDIR=$(mktemp -d -p "${BATS_TMPDIR:-/tmp}" "pkg_map_test.XXXXXX")
  
  # Source the modules in correct order
  source "$REPO_ROOT/src/core/logging.sh"
  source "$REPO_ROOT/src/core/distro_detection.sh"
  source "$REPO_ROOT/src/core/ini_parser.sh"
  source "$REPO_ROOT/src/core/package_mapping.sh"
  
  # Create test pkgmap.ini
  cat > "$BATS_TEST_TMPDIR/test_pkgmap.ini" << 'INIEOF'
[pkgmap.fedora]
qtile-extras=COPR:frostyx/qtile:python3-qtile-extras
lazygit=COPR:atim/lazygit
starship=COPR:atim/starship
regular-pkg=fedora-pkg

[pkgmap.arch]
qtile-extras=AUR:qtile-extras
lazygit=AUR:lazygit
regular-pkg=arch-pkg
INIEOF
}

teardown() {
  # Clean up temporary directory
  [[ -n "$BATS_TEST_TMPDIR" ]] && rm -rf "$BATS_TEST_TMPDIR"
}

@test "is_copr_package detects COPR packages" {
  run is_copr_package "COPR:user/repo"
  [ "$status" -eq 0 ]
  
  run is_copr_package "COPR:user/repo:pkgname"
  [ "$status" -eq 0 ]
  
  run is_copr_package "regular-package"
  [ "$status" -eq 1 ]
  
  run is_copr_package "AUR:package"
  [ "$status" -eq 1 ]
}

@test "is_aur_package detects AUR packages" {
  run is_aur_package "AUR:qtile-extras"
  [ "$status" -eq 0 ]
  
  run is_aur_package "regular-package"
  [ "$status" -eq 1 ]
  
  run is_aur_package "COPR:user/repo"
  [ "$status" -eq 1 ]
}

@test "extract_copr_repo extracts repository name" {
  run extract_copr_repo "COPR:frostyx/qtile"
  [ "$status" -eq 0 ]
  [ "$output" = "frostyx/qtile" ]
  
  run extract_copr_repo "COPR:atim/starship:starship"
  [ "$status" -eq 0 ]
  [ "$output" = "atim/starship" ]
  
  run extract_copr_repo "regular-package"
  [ "$status" -eq 0 ]
  [ "$output" = "" ]
}

@test "extract_copr_package extracts package name with explicit format" {
  run extract_copr_package "COPR:frostyx/qtile:python3-qtile-extras" ""
  [ "$status" -eq 0 ]
  [ "$output" = "python3-qtile-extras" ]
}

@test "extract_copr_package uses key as fallback" {
  run extract_copr_package "COPR:atim/starship" "starship"
  [ "$status" -eq 0 ]
  [ "$output" = "starship" ]
}

@test "extract_copr_package falls back to repo name" {
  run extract_copr_package "COPR:user/lazygit" ""
  [ "$status" -eq 0 ]
  [ "$output" = "lazygit" ]
}

@test "extract_aur_package extracts package name" {
  run extract_aur_package "AUR:qtile-extras"
  [ "$status" -eq 0 ]
  [ "$output" = "qtile-extras" ]
}

@test "map_package_name appends key to COPR packages" {
  # Mock detect_distro
  function detect_distro() { echo "fedora"; }
  export -f detect_distro
  
  # Load mappings
  load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  
  # Test COPR with explicit package name (should not modify)
  run map_package_name "qtile-extras" "fedora"
  [ "$status" -eq 0 ]
  [ "$output" = "COPR:frostyx/qtile:python3-qtile-extras" ]
  
  # Test COPR without explicit package name (should append key)
  run map_package_name "starship" "fedora"
  [ "$status" -eq 0 ]
  [ "$output" = "COPR:atim/starship:starship" ]
}

@test "map_package_name handles regular packages" {
  function detect_distro() { echo "fedora"; }
  export -f detect_distro
  
  load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  
  run map_package_name "regular-pkg" "fedora"
  [ "$status" -eq 0 ]
  [ "$output" = "fedora-pkg" ]
}

@test "map_package_name handles unmapped packages" {
  function detect_distro() { echo "fedora"; }
  export -f detect_distro
  
  load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  
  run map_package_name "unknown-pkg" "fedora"
  [ "$status" -eq 0 ]
  [ "$output" = "unknown-pkg" ]
}

@test "map_package_list processes multiple packages" {
  function detect_distro() { echo "fedora"; }
  export -f detect_distro
  
  load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  
  # Map multiple packages
  local packages=("qtile-extras" "lazygit" "regular-pkg" "unmapped")
  local mapped=()
  mapfile -t mapped < <(map_package_list "fedora" "${packages[@]}")
  
  [ "${#mapped[@]}" -eq 4 ]
  [ "${mapped[0]}" = "COPR:frostyx/qtile:python3-qtile-extras" ]
  [ "${mapped[1]}" = "COPR:atim/lazygit:lazygit" ]
  [ "${mapped[2]}" = "fedora-pkg" ]
  [ "${mapped[3]}" = "unmapped" ]
}

@test "load_package_mappings_ini loads fedora mappings" {
  function detect_distro() { echo "fedora"; }
  export -f detect_distro
  export DETECTED_DISTRO="fedora"
  
  run load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  [ "$status" -eq 0 ]
  
  # Verify mappings were loaded
  [ -n "${PACKAGE_MAPPINGS[qtile-extras]}" ]
  [ "${PACKAGE_MAPPINGS[qtile-extras]}" = "COPR:frostyx/qtile:python3-qtile-extras" ]
}

@test "load_package_mappings_ini loads arch mappings" {
  function detect_distro() { echo "arch"; }
  export -f detect_distro
  export DETECTED_DISTRO="arch"
  
  run load_package_mappings_ini "$BATS_TEST_TMPDIR/test_pkgmap.ini"
  [ "$status" -eq 0 ]
  
  # Verify mappings were loaded
  [ -n "${PACKAGE_MAPPINGS[qtile-extras]}" ]
  [ "${PACKAGE_MAPPINGS[qtile-extras]}" = "AUR:qtile-extras" ]
}
