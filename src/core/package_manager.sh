#!/usr/bin/env bash
# package_manager.sh - Unified package manager abstraction
# Abstract package operations across dnf, pacman/paru, and apt

# Source guard to prevent re-sourcing
[[ -n "${_PACKAGE_MANAGER_SOURCED:-}" ]] && return 0
readonly _PACKAGE_MANAGER_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/distro_detection.sh
source src/distro/arch.sh
source src/core/package_mapping.sh

# Tracking will be sourced on-demand to avoid circular dependencies
declare -g TRACKING_AVAILABLE=0

# Package manager commands (initialized by init_package_manager)
# Using arrays to properly handle commands with multiple words
declare -a PM_INSTALL_CMD=()
declare -a PM_REMOVE_CMD=()
declare PM_UPDATE=""
declare PM_SEARCH=""
declare PM_IS_INSTALLED=""
declare CURRENT_DISTRO=""

# Initialize package manager commands based on detected distribution
init_package_manager() {
  CURRENT_DISTRO=$(detect_distro) || return 1

  log_info "Initializing package manager for $CURRENT_DISTRO"
  log_debug "Before initialization: PM_INSTALL_CMD has ${#PM_INSTALL_CMD[@]} elements"

  case "$CURRENT_DISTRO" in
    fedora)
      PM_INSTALL_CMD=(sudo dnf install -y)
      PM_REMOVE_CMD=(sudo dnf remove -y)
      PM_UPDATE="sudo dnf update -y"
      PM_SEARCH="dnf search"
      PM_IS_INSTALLED="rpm -q"
      ;;
    arch)
      # Prefer pacman than paru or yay.
      is_aur_helper_installed || return 1

      #TODO: Research about the commands and make sure they are optimal and doesn't cause issues
      if command -v pacman &>/dev/null; then
        PM_INSTALL_CMD=(sudo pacman -S --needed --noconfirm)
        PM_REMOVE_CMD=(sudo pacman -Rns --noconfirm)
        PM_UPDATE="sudo pacman -Syu --noconfirm"
        PM_SEARCH="pacman -Ss"
      elif command -v paru &>/dev/null; then
        PM_INSTALL_CMD=(paru -S --noconfirm)
        PM_REMOVE_CMD=(paru -Rns --noconfirm)
        PM_UPDATE="paru -Syu --noconfirm"
        PM_SEARCH="paru -Ss"
      elif command -v yay &>/dev/null; then
        PM_INSTALL_CMD=(yay -S --noconfirm)
        PM_REMOVE_CMD=(yay -Rns --noconfirm)
        PM_UPDATE="yay -Syu --noconfirm"
        PM_SEARCH="yay -Ss"
      else
        log_error "No supported package manager found (pacman, paru, or yay)"
        return 1
      fi
      PM_IS_INSTALLED="pacman -Q"
      ;;
    debian)
      PM_INSTALL_CMD=(sudo apt-get install -y)
      PM_REMOVE_CMD=(sudo apt-get remove -y)
      PM_UPDATE="sudo apt-get update && sudo apt-get upgrade -y"
      PM_SEARCH="apt-cache search"
      PM_IS_INSTALLED="dpkg -l"
      ;;
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac

  log_debug "After initialization: PM_INSTALL_CMD has ${#PM_INSTALL_CMD[@]} elements"
  log_debug "Package manager initialized: ${PM_INSTALL_CMD[*]}"
  log_debug "PM_INSTALL_CMD array contents:"
  for i in "${!PM_INSTALL_CMD[@]}"; do
    log_debug "  [$i]: '${PM_INSTALL_CMD[$i]}'"
  done

  # Try to load package tracking if available
  if [[ -f "src/core/package_tracking.sh" ]]; then
    source src/core/package_tracking.sh
    TRACKING_AVAILABLE=1
    log_debug "Package tracking module loaded"
  fi

  return 0
}

# Purpose: Enable COPR repositories (Fedora only)
# Parameters:
#   $@ - COPR repository names (format: user/repo)
# Returns: 0 on success, 1 on failure
_enable_copr_repos() {
  local repos=("$@")

  if [[ ${#repos[@]} -eq 0 ]]; then
    log_debug "No COPR repositories to enable"
    return 0
  fi

  log_info "Enabling ${#repos[@]} COPR repositories..."
  log_debug "=== _enable_copr_repos called with ==="
  log_debug "Number of arguments: $#"
  log_debug "All arguments: $*"
  log_debug "Repos array size: ${#repos[@]}"
  for i in "${!repos[@]}"; do
    log_debug "  repos[$i] = '${repos[$i]}'"
  done
  log_debug "==================================="

  # Ensure dnf-plugins-core is installed - REQUIRED for COPR
  if ! rpm -q dnf-plugins-core &>/dev/null; then
    log_info "Installing dnf-plugins-core (required for COPR)..."
    if ! sudo dnf install -y dnf-plugins-core; then
      log_error "Failed to install dnf-plugins-core - COPR will not work!"
      return 1
    fi
  else
    log_debug "dnf-plugins-core is already installed"
  fi

  for repo in "${repos[@]}"; do
    log_info "Enabling COPR repository: $repo"

    # Capture output to see actual errors
    local copr_output
    if ! copr_output=$(sudo dnf copr enable -y "$repo" 2>&1); then
      log_error "Failed to enable COPR repository: $repo"
      log_error "DNF COPR output: $copr_output"
      return 1
    fi

    log_success "✓ Enabled COPR repository: $repo"
  done

  # Refresh metadata after enabling repos - CRITICAL for DNF to see new packages
  log_info "Refreshing package metadata after enabling COPR repositories..."
  if ! sudo dnf makecache --refresh; then
    log_error "Failed to refresh package metadata"
    return 1
  fi

  log_success "COPR repositories enabled and metadata refreshed"
  log_debug "DNF will verify package availability during installation"
  return 0
}

# Purpose: Install packages on Fedora (handles COPR repositories)
# Parameters:
#   $@ - Package names (may include COPR: prefix)
# Returns: 0 on success, 1 on failure
_pm_install_fedora() {
  local regular_pkgs=()
  local copr_pkgs=()
  local -A copr_repos_to_enable

  log_debug "=== _pm_install_fedora: Received ${#@} packages ==="
  log_debug "Raw package list: $*"

  # Categorize packages (ONLY check for COPR, not AUR)
  for pkg in "$@"; do
    log_debug "Processing package: '$pkg'"
    if is_copr_package "$pkg"; then
      # Extract COPR repository and package name
      local copr_repo
      copr_repo=$(extract_copr_repo "$pkg")

      local pkg_name
      pkg_name=$(extract_copr_package "$pkg" "")

      if [[ -z "$pkg_name" ]]; then
        log_error "Failed to extract package name from COPR mapping: $pkg"
        continue
      fi

      # Add package to COPR list and track repo
      copr_pkgs+=("$pkg_name")
      copr_repos_to_enable["$copr_repo"]=1
      log_debug "  ✓ Categorized as COPR package"
      log_debug "    Input: $pkg"
      log_debug "    Repo: $copr_repo"
      log_debug "    Package name: $pkg_name"
    else
      # Regular package
      regular_pkgs+=("$pkg")
      log_debug "  ✓ Categorized as regular package: $pkg"
    fi
  done

  log_debug "=== Categorization Complete ==="
  log_debug "Regular packages (${#regular_pkgs[@]}): ${regular_pkgs[*]:-}"
  log_debug "COPR packages (${#copr_pkgs[@]}): ${copr_pkgs[*]:-}"

  # Check if copr_repos_to_enable has any elements (safe with set -u)
  # Use -v test for associative arrays to avoid unbound variable errors
  if [[ -v copr_repos_to_enable[@] ]] && [[ ${#copr_repos_to_enable[@]} -gt 0 ]]; then
    log_debug "COPR repos to enable (${#copr_repos_to_enable[@]}): ${!copr_repos_to_enable[*]}"
  else
    log_debug "COPR repos to enable (0): none"
  fi

  # Enable COPR repositories
  if [[ -v copr_repos_to_enable[@] ]] && [[ ${#copr_repos_to_enable[@]} -gt 0 ]]; then
    log_debug "=== About to call _enable_copr_repos ==="
    log_debug "copr_repos_to_enable keys: ${!copr_repos_to_enable[*]}"
    log_debug "Number of repos: ${#copr_repos_to_enable[@]}"
    log_debug "========================================"

    log_info "Enabling COPR repositories: ${!copr_repos_to_enable[*]}"
    _enable_copr_repos "${!copr_repos_to_enable[@]}" || return 1
  else
    log_debug "No COPR repositories to enable"
  fi

  local install_failed=0

  # Install regular packages
  if [[ ${#regular_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#regular_pkgs[@]} regular packages: ${regular_pkgs[*]}"
    log_debug "Command: ${PM_INSTALL_CMD[*]} ${regular_pkgs[*]}"
    if ! "${PM_INSTALL_CMD[@]}" "${regular_pkgs[@]}"; then
      log_error "Failed to install regular packages"
      install_failed=1
    else
      log_success "Regular packages installed successfully"
      # Track regular packages using metadata
      for pkg in "${regular_pkgs[@]}"; do
        _track_installed_package_with_metadata "$pkg"
      done
    fi
  fi

  # Install COPR packages
  if [[ ${#copr_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#copr_pkgs[@]} COPR packages: ${copr_pkgs[*]}"
    log_debug "Command: ${PM_INSTALL_CMD[*]} ${copr_pkgs[*]}"

    if ! "${PM_INSTALL_CMD[@]}" "${copr_pkgs[@]}"; then
      log_error "Failed to install COPR packages"
      install_failed=1
    else
      log_success "COPR packages installed successfully"
      # Track COPR packages using metadata
      for pkg in "$@"; do
        _track_installed_package_with_metadata "$pkg"
      done
    fi
  fi

  if [[ $install_failed -eq 1 ]]; then
    log_error "Some packages failed to install"
    return 1
  fi

  return 0
}

# Purpose: Install packages on Arch (handles AUR packages)
# Parameters:
#   $@ - Package names (may include AUR: prefix)
# Returns: 0 on success, 1 on failure
_pm_install_arch() {
  local regular_pkgs=()
  local aur_pkgs=()
  local install_failed=0

  # Categorize packages (ONLY check for AUR, not COPR)
  for pkg in "$@"; do
    if is_aur_package "$pkg"; then
      local aur_name
      aur_name=$(extract_aur_package "$pkg")
      aur_pkgs+=("$aur_name")
      log_debug "Categorized as AUR: $pkg -> $aur_name"
    else
      # Regular package
      regular_pkgs+=("$pkg")
      log_debug "Categorized as regular: $pkg"
    fi
  done

  local install_failed=0

  # Install regular packages
  if [[ ${#regular_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#regular_pkgs[@]} regular packages: ${regular_pkgs[*]}"
    if ! "${PM_INSTALL_CMD[@]}" "${regular_pkgs[@]}"; then
      log_error "Failed to install regular packages"
      install_failed=1
    else
      log_success "Regular packages installed successfully"
      # Track installed packages using metadata
      for mapped_pkg in "${regular_pkgs[@]}"; do
        _track_installed_package_with_metadata "$mapped_pkg"
      done
    fi
  fi

  # Install AUR packages
  if [[ ${#aur_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#aur_pkgs[@]} AUR packages: ${aur_pkgs[*]}"

    # Extract package names (remove AUR: prefix)
    local aur_names=()
    for pkg in "${aur_pkgs[@]}"; do
      local pkg_name="${pkg#AUR:}"
      aur_names+=("$pkg_name")
    done

    if ! _install_aur_packages "${aur_names[@]}"; then
      log_error "Failed to install AUR packages"
      install_failed=1
    else
      log_success "AUR packages installed successfully"
      # Track AUR packages using metadata
      for mapped_pkg in "${aur_pkgs[@]}"; do
        _track_installed_package_with_metadata "$mapped_pkg"
      done
    fi
  fi

  if [[ $install_failed -eq 1 ]]; then
    log_error "Some packages failed to install"
    return 1
  fi

  return 0
}

# Purpose: Install packages on Debian (no special repository handling)
# Parameters:
#   $@ - Package names
# Returns: 0 on success, 1 on failure
_pm_install_debian() {
  # No categorization needed - all packages are regular
  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified for installation"
    return 0
  fi

  log_info "Installing ${#@} packages: $*"
  if ! "${PM_INSTALL_CMD[@]}" "$@"; then
    log_error "Failed to install packages"
    return 1
  fi

  log_success "Packages installed successfully"
  # Track installed packages using metadata
  for pkg in "$@"; do
    _track_installed_package_with_metadata "$pkg"
  done
  return 0
}

# COPR and AUR package handling:
# - COPR repositories are automatically enabled when packages are mapped with COPR: prefix
# - AUR packages are handled automatically when mapped with AUR: prefix
# See docs/COPR_AUR_HANDLING.md for details
#
# Purpose: Install packages using distribution-specific logic
# Automatically routes to appropriate handler based on CURRENT_DISTRO
# Parameters:
#   $@ - Package names (may include AUR: or COPR: prefixes for Arch/Fedora)
# Returns: 0 on success, 1 on failure
pm_install() {
  # Check if array is set and has elements (safe with set -u)
  if [[ ! -v PM_INSTALL_CMD[@] ]] || [[ ${#PM_INSTALL_CMD[@]} -eq 0 ]]; then
    log_error "Package manager not initialized. Call init_package_manager first."
    return 1
  fi

  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified for installation"
    return 0
  fi

  log_info "Processing ${#@} packages for installation"

  # Route to distribution-specific function
  case "$CURRENT_DISTRO" in
    fedora)
      _pm_install_fedora "$@"
      ;;
    arch)
      _pm_install_arch "$@"
      ;;
    debian)
      _pm_install_debian "$@"
      ;;
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac
}

# Purpose: Install AUR packages using paru or yay
# Parameters:
#   $@ - AUR package names (without AUR: prefix)
# Returns: 0 on success, 1 on failure
_install_aur_packages() {
  local aur_helper=""

  # Detect available AUR helper
  if command -v paru &>/dev/null; then
    aur_helper="paru"
  elif command -v yay &>/dev/null; then
    aur_helper="yay"
  else
    log_error "No AUR helper (paru/yay) found. Install one to enable AUR support."
    return 1
  fi

  log_debug "Using AUR helper: $aur_helper"
  log_debug "Installing AUR packages: $*"

  # Install using AUR helper
  if ! $aur_helper -S --needed --noconfirm "$@"; then
    log_error "Failed to install AUR packages: $*"
    return 1
  fi

  return 0
}

# Purpose: Remove packages using the detected package manager
# Parameters:
#   $@ - Package names to remove
pm_remove() {
  # Check if array is set and has elements (safe with set -u)
  if [[ ! -v PM_REMOVE_CMD[@] ]] || [[ ${#PM_REMOVE_CMD[@]} -eq 0 ]]; then
    log_error "Package manager not initialized. Call init_package_manager first."
    return 1
  fi

  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified for removal"
    return 0
  fi

  log_info "Removing packages: $*"

  # Execute remove command (sudo is already included in PM_REMOVE_CMD)
  # shellcheck disable=SC2086
  if ! "${PM_REMOVE_CMD[@]}" "$@"; then
    log_error "Failed to remove packages: $*"
    return 1
  fi

  log_success "Successfully removed packages"
  return 0
}

# Purpose: Update system packages
pm_update() {
  if [[ -z "$PM_UPDATE" ]]; then
    log_error "Package manager not initialized. Call init_package_manager first."
    return 1
  fi

  log_info "Updating system packages..."

  # Execute update command (sudo is already included in PM_UPDATE)
  if ! bash -c "$PM_UPDATE"; then
    log_error "Failed to update system packages"
    return 1
  fi

  log_success "Successfully updated system packages"
  return 0
}

# Purpose: Search for packages
# Parameters:
#   $1 - Search query
pm_search() {
  if [[ -z "$PM_SEARCH" ]]; then
    log_error "Package manager not initialized. Call init_package_manager first."
    return 1
  fi

  if [[ $# -eq 0 ]]; then
    log_error "No search query specified"
    return 1
  fi

  log_debug "Searching for packages: $1"

  # Execute search command
  $PM_SEARCH "$1"
}

# Purpose: Check if a package is installed
# Parameters:
#   $1 - Package name
# Returns: 0 if installed, 1 if not
pm_is_installed() {
  if [[ -z "$PM_IS_INSTALLED" ]]; then
    log_error "Package manager not initialized. Call init_package_manager first."
    return 1
  fi

  if [[ $# -eq 0 ]]; then
    log_error "No package name specified"
    return 1
  fi

  log_debug "Checking if package is installed: $1"

  # Execute check command (suppress output)
  $PM_IS_INSTALLED "$1" &>/dev/null
}

# Purpose: Install packages from an array
# Parameters:
#   $@ - Array of package names (pass as "${array[@]}")
# Returns: 0 on success, 1 on partial/full failure
pm_install_array() {
  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified in array"
    return 0
  fi

  local packages=("$@")
  log_info "Installing ${#packages[@]} packages..."

  if pm_install "${packages[@]}"; then
    return 0
  fi

  log_success "All packages installed successfully"
  return 0
}

# Function: _track_installed_package_with_metadata
# Purpose: Track package using stored mapping metadata
# Arguments:
#   $1 - Mapped package value (e.g., "COPR:user/repo:pkgname" or "pkgname")
#   $2 - Original package name (optional, for lookup)
_track_installed_package_with_metadata() {
  local mapped_pkg="$1"
  local original_pkg="${2:-}"

  # Only track if tracking is available
  if [[ "$TRACKING_AVAILABLE" -ne 1 ]]; then
    return 0
  fi

  # Extract the final package name and initial source from mapped value
  local source="official"
  local final_name=""

  # Parse mapped package to determine source and final name
  if [[ "$mapped_pkg" =~ ^COPR:([^:]+):(.+)$ ]]; then
    source="COPR:${BASH_REMATCH[1]}"
    final_name="${BASH_REMATCH[2]}"
  elif [[ "$mapped_pkg" =~ ^COPR:([^:]+)$ ]]; then
    source="COPR:${BASH_REMATCH[1]}"
    final_name="$original_pkg"
  elif [[ "$mapped_pkg" =~ ^AUR:(.+)$ ]]; then
    final_name="${BASH_REMATCH[1]}"
    source="AUR:$final_name"
  elif [[ "$mapped_pkg" =~ ^PPA:([^:]+):(.+)$ ]]; then
    source="PPA:${BASH_REMATCH[1]}"
    final_name="${BASH_REMATCH[2]}"
  elif [[ "$mapped_pkg" =~ ^PPA:([^:]+)$ ]]; then
    source="PPA:${BASH_REMATCH[1]}"
    final_name="$original_pkg"
  else
    final_name="$mapped_pkg"
  fi

  # Try to find metadata by searching for matching final name or original name
  local found_metadata=""
  local category="uncategorized"

  # First try: search by final name
  for pkg_key in "${!PACKAGE_MAPPING_METADATA[@]}"; do
    local metadata="${PACKAGE_MAPPING_METADATA[$pkg_key]}"
    IFS='|' read -r meta_source meta_category meta_final <<<"$metadata"

    if [[ "$meta_final" == "$final_name" ]] || [[ "$pkg_key" == "$final_name" ]]; then
      found_metadata="$metadata"
      original_pkg="$pkg_key"
      source="$meta_source"
      category="$meta_category"
      break
    fi
  done

  # Second try: if original_pkg provided, look it up directly
  if [[ -z "$found_metadata" ]] && [[ -n "$original_pkg" ]]; then
    if [[ -n "${PACKAGE_MAPPING_METADATA[$original_pkg]:-}" ]]; then
      found_metadata="${PACKAGE_MAPPING_METADATA[$original_pkg]}"
      IFS='|' read -r source category final_name <<<"$found_metadata"
    fi
  fi

  # Track the package with metadata including original name
  _track_package "$final_name" "$source" "$category" "${original_pkg:-$final_name}"

  log_debug "Tracked from metadata: $final_name (original: ${original_pkg:-unknown}, source: $source, category: $category)"
}

# Function: _track_package
# Purpose: Track a single installed package (internal helper)
# Arguments:
#   $1 - Package name
#   $2 - Source (e.g., "COPR:user/repo", "AUR:package", "official")
#   $3 - Category (optional, defaults to "uncategorized")
#   $4 - Original name (optional, name from packages.ini)
# Returns: 0 on success, 1 on failure
_track_package() {
  local package_name="$1"
  local source="$2"
  local category="${3:-uncategorized}"
  local original_name="${4:-$package_name}"

  # Only track if tracking is available
  if [[ "$TRACKING_AVAILABLE" -ne 1 ]]; then
    return 0
  fi

  # Initialize tracking if not already done
  if [[ "${TRACKING_INITIALIZED:-0}" -ne 1 ]]; then
    init_package_tracking 2>/dev/null || return 0
  fi

  # Track the package with original name
  track_package_install "$package_name" "$source" "$category" "$package_name" "$original_name" 2>/dev/null || {
    log_debug "Failed to track package: $package_name"
    return 0
  }

  log_debug "Tracked package: $package_name (original: $original_name, source: $source)"
  return 0
}

# Function: _track_installed_packages
# Purpose: Track multiple installed packages (internal helper)
# Arguments:
#   $1 - Source (e.g., "official")
#   $2 - Category
#   $@ - Package names
# Returns: 0 always
_track_installed_packages() {
  local source="$1"
  local category="$2"
  shift 2

  # Only track if tracking is available
  if [[ "$TRACKING_AVAILABLE" -ne 1 ]]; then
    return 0
  fi

  # Track each package
  for pkg in "$@"; do
    _track_package "$pkg" "$source" "$category"
  done

  return 0
}

# Function: extract_package_name
# Purpose: Extract clean package name from various formats
# Arguments:
#   $1 - Package string (may include COPR:, AUR: prefixes)
# Returns: Clean package name
extract_package_name() {
  local pkg="$1"

  # Remove COPR: prefix and extract package name
  if [[ "$pkg" =~ ^COPR:([^=]+)=(.+)$ ]]; then
    echo "${BASH_REMATCH[2]}"
    return 0
  fi

  # Remove AUR: prefix
  if [[ "$pkg" =~ ^AUR:(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  # Remove PPA: prefix (if present)
  if [[ "$pkg" =~ ^PPA:([^=]+)=(.+)$ ]]; then
    echo "${BASH_REMATCH[2]}"
    return 0
  fi

  # Return as-is if no prefix
  echo "$pkg"
  return 0
}
