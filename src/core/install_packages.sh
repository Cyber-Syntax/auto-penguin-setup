#!/usr/bin/env bash

# Install system-specific packages
# Usage: install_system_specific_packages <system_type>
#   system_type: laptop, desktop, or homeserver
install_system_specific_packages() {
  local system_type="$1"

  # Validate input
  if [[ -z "$system_type" ]]; then
    log_error "System type is required. Usage: install_system_specific_packages <laptop|desktop|homeserver>"
    return 1
  fi

  local pkg_list=()

  case "$system_type" in
  desktop)
    log_info "Installing desktop-specific packages..."
    pkg_list=("${DESKTOP_PACKAGES[@]}")
    ;;
  laptop)
    log_info "Installing laptop-specific packages..."
    pkg_list=("${LAPTOP_PACKAGES[@]}")
    ;;
  homeserver)
    log_info "Installing home server-specific packages..."
    pkg_list=("${HOMESERVER_PACKAGES[@]}")
    ;;
  *)
    log_error "Unknown system type '$system_type'. Valid types: laptop, desktop, homeserver"
    return 1
    ;;
  esac

  # Check if package list is empty
  if [[ ${#pkg_list[@]} -eq 0 ]]; then
    log_warn "No packages defined for $system_type installation"
    return 0
  fi

  log_debug "Package list for $system_type: ${pkg_list[*]}"

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "$system_type" "${pkg_list[@]}") || {
    log_error "Failed to map $system_type packages"
    return 1
  }

  # Install packages using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Failed to install some $system_type packages"
    return 1
  fi

  log_info "${system_type^} packages installation completed"
}

install_core_packages() {
  log_info "Installing core packages..."

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "core" "${CORE_PACKAGES[@]}") || {
    log_error "Failed to map core packages"
    return 1
  }

  log_debug "Mapped ${#mapped_array[@]} packages:"
  for i in "${!mapped_array[@]}"; do
    log_debug "  [$i]: '${mapped_array[$i]}'"
  done

  # Install using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Error: Failed to install core packages." >&2
    return 1
  fi

  log_info "Core packages installation completed."
}

install_app_packages() {
  log_info "Installing application packages..."

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "apps" "${APPS_PACKAGES[@]}") || {
    log_error "Failed to map application packages"
    return 1
  }

  # Install using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Error: Failed to install application packages." >&2
    return 1
  fi

  log_info "Application packages installation completed."
}

install_dev_packages() {
  log_info "Installing development packages..."

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "dev" "${DEV_PACKAGES[@]}") || {
    log_error "Failed to map development packages"
    return 1
  }

  log_debug "=== install_dev_packages: Mapped Array Debug ==="
  log_debug "Number of packages in mapped_array: ${#mapped_array[@]}"
  log_debug "Mapped packages:"
  for i in "${!mapped_array[@]}"; do
    log_debug "  [$i]: '${mapped_array[$i]}'"
  done
  log_debug "=== End Mapped Array Debug ==="

  # Install using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Error: Failed to install development packages." >&2
    return 1
  fi

  log_info "Development packages installation completed."
}

install_games_packages() {
  log_info "Installing games..."

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "games" "${GAMES_PACKAGES[@]}") || {
    log_error "Failed to map games packages"
    return 1
  }

  # Install using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Error: Failed to install games." >&2
    return 1
  fi

  log_info "Games installation completed."
}

install_flatpak_packages() {
  log_info "Installing Flatpak packages..."

  # Setup flathub if not already setup
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

  # Install flatpak packages as the regular user
  if ! flatpak install -y flathub "${FLATPAK_PACKAGES[@]}"; then
    log_error "Failed to install Flatpak packages."
    return 1
  fi

  log_info "Flatpak packages installation completed."
}
