#!/usr/bin/env bash

# Install system-specific packages
install_system_specific_packages() {
  local system_type
  system_type=$(detect_system_type)
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
    *)
      log_warn "Unknown system type '$system_type'. Skipping system-specific packages."
      return 0
      ;;
  esac

  # Check if package list is empty
  if [[ ${#pkg_list[@]} -eq 0 ]]; then
    log_warn "No packages defined for $system_type installation"
    return 0
  fi

  log_debug "Package list: ${pkg_list[*]}"

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${pkg_list[@]}") || {
    log_error "Failed to map $system_type packages"
    return 1
  }

  # Install packages using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Error: Failed to install some $system_type packages."
    return 1
  fi

  log_info "${system_type^} packages installation completed."
}

install_core_packages() {
  log_info "Installing core packages..."
  
  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${CORE_PACKAGES[@]}") || {
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
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${APPS_PACKAGES[@]}") || {
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
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${DEV_PACKAGES[@]}") || {
    log_error "Failed to map development packages"
    return 1
  }
  
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
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${GAMES_PACKAGES[@]}") || {
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