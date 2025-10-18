#!/usr/bin/env bash

# Source guard to prevent re-sourcing
[[ -n "${_QTILE_SOURCED:-}" ]] && return 0
readonly _QTILE_SOURCED=1

# install_qtile_packages - Install Qtile window manager and dependencies
# Follows the standard pattern from install_packages.sh
install_qtile_packages() {
  log_info "Installing Qtile packages..."

  # If in test mode, just print what would be run
  if [[ -n "${BATS_TEST_TMPDIR:-}" ]]; then
    echo "sudo would run: dnf install -y ${QTILE_PACKAGES[*]}"
    return 0
  fi

  # Verify QTILE_PACKAGES array exists and is not empty
  if [[ ! -v QTILE_PACKAGES[@] ]] || [[ ${#QTILE_PACKAGES[@]} -eq 0 ]]; then
    log_warn "No Qtile packages defined in configuration"
    return 0
  fi

  log_debug "Qtile package list (${#QTILE_PACKAGES[@]} packages): ${QTILE_PACKAGES[*]}"

  # Map packages for current distro (outputs newline-separated list)
  local mapped_array=()
  mapfile -t mapped_array < <(map_package_list "$CURRENT_DISTRO" "${QTILE_PACKAGES[@]}") || {
    log_error "Failed to map Qtile packages"
    return 1
  }

  log_debug "Mapped ${#mapped_array[@]} packages for $CURRENT_DISTRO:"
  for i in "${!mapped_array[@]}"; do
    log_debug "  [$i]: '${mapped_array[$i]}'"
  done

  # Install using package manager abstraction
  if ! pm_install_array "${mapped_array[@]}"; then
    log_error "Failed to install Qtile packages"
    return 1
  fi

  log_info "Qtile packages installation completed"
  return 0
}

# Udev rules for brightness control on qtile
#TODO: rename more better name
setup_qtile_backlight_rules() {
  log_info "Setting up udev rule for qtile..."

  local dir_qtile_rules="/etc/udev/rules.d/99-qtile.rules"
  local qtile_rules_file="./configs/99-qtile.rules"
  local dir_backlight="/etc/X11/xorg.conf.d/99-backlight.conf"
  local backlight_file="./configs/99-backlight.conf"

  # Check destination directories exist, create if missing
  if [[ ! -d "/etc/udev/rules.d" ]]; then
    log_info "/etc/udev/rules.d does not exist, creating..."
    if ! sudo mkdir -p "/etc/udev/rules.d"; then
      log_error "Failed to create /etc/udev/rules.d"
      return 1
    fi
  fi
  if [[ ! -d "/etc/X11/xorg.conf.d" ]]; then
    log_info "/etc/X11/xorg.conf.d does not exist, creating..."
    if ! sudo mkdir -p "/etc/X11/xorg.conf.d"; then
      log_error "Failed to create /etc/X11/xorg.conf.d"
      return 1
    fi
  fi

  # Execute commands directly instead of using log_cmd
  if ! sudo cp "$qtile_rules_file" "$dir_qtile_rules"; then
    log_error "Failed to copy udev rule for qtile"
    return 1
  fi

  log_info "Udev rule for qtile setup completed."

  # copy intel_backlight to xorg.conf.d
  if ! sudo cp "$backlight_file" "$dir_backlight"; then
    log_error "Failed to copy backlight configuration"
    return 1
  fi

  log_info "Backlight configuration completed."

  # reload udev rules
  if ! sudo udevadm control --reload-rules && sudo udevadm trigger; then
    log_error "Failed to reload udev rules"
    return 1
  fi

  log_info "Udev rules reloaded."
}

