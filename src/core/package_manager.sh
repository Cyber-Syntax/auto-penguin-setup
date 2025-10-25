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

  # Ensure dnf-plugins-core is installed
  log_debug "Ensuring dnf-plugins-core is installed"
  sudo dnf install -y dnf-plugins-core &>/dev/null || true

  for repo in "${repos[@]}"; do
    log_info "Enabling COPR repository: $repo"
    if ! sudo dnf copr enable -y "$repo"; then
      log_warn "Failed to enable COPR repository: $repo (may already be enabled)"
      # Continue anyway, repo might already be enabled
    fi
  done

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

  # Categorize packages (ONLY check for COPR, not AUR)
  for pkg in "$@"; do
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
      log_debug "Categorized as COPR: $pkg -> repo: $copr_repo, pkg: $pkg_name"
    else
      # Regular package
      regular_pkgs+=("$pkg")
      log_debug "Categorized as regular: $pkg"
    fi
  done

  # Enable COPR repositories
  if [[ -v copr_repos_to_enable[@] ]] && [[ ${#copr_repos_to_enable[@]} -gt 0 ]]; then
    _enable_copr_repos "${!copr_repos_to_enable[@]}" || return 1
  fi

  # Install all packages together
  local all_pkgs=("${regular_pkgs[@]}" "${copr_pkgs[@]}")
  if [[ ${#all_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#all_pkgs[@]} packages: ${all_pkgs[*]}"
    if ! "${PM_INSTALL_CMD[@]}" "${all_pkgs[@]}"; then
      log_error "Failed to install packages"
      return 1
    fi
    log_success "Packages installed successfully"
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

  # Install regular packages
  if [[ ${#regular_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#regular_pkgs[@]} regular packages: ${regular_pkgs[*]}"
    if ! "${PM_INSTALL_CMD[@]}" "${regular_pkgs[@]}"; then
      log_error "Failed to install regular packages"
      install_failed=1
    else
      log_success "Regular packages installed successfully"
    fi
  fi

  # Install AUR packages
  if [[ ${#aur_pkgs[@]} -gt 0 ]]; then
    log_info "Installing ${#aur_pkgs[@]} AUR packages: ${aur_pkgs[*]}"
    if ! _install_aur_packages "${aur_pkgs[@]}"; then
      log_error "Failed to install AUR packages"
      install_failed=1
    else
      log_success "AUR packages installed successfully"
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

  # Execute remove command (sudo is already included in PM_REMOVE)
  # shellcheck disable=SC2086
  if ! $PM_REMOVE "$@"; then
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
