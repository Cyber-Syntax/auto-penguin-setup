#!/usr/bin/env bash

# Source guard to prevent re-sourcing
[[ -n "${_I3_SOURCED:-}" ]] && return 0
readonly _I3_SOURCED=1

# install_i3_packages - Install i3 window manager and shared WM packages
# Mirrors the installation approach used for Qtile: map package names per-distro
# and install via the package manager abstraction.
install_i3_packages() {
  log_info "Installing i3 and WM-common packages..."

  # Test mode: just show what would be installed
  if [[ -n "${BATS_TEST_TMPDIR:-}" ]]; then
    if [[ -v I3_PACKAGES[@] ]] && [[ ${#I3_PACKAGES[@]} -gt 0 ]]; then
      echo "sudo would run: dnf install -y ${I3_PACKAGES[*]}"
    fi
    if [[ -v WM_COMMON_PACKAGES[@] ]] && [[ ${#WM_COMMON_PACKAGES[@]} -gt 0 ]]; then
      echo "sudo would run: dnf install -y ${WM_COMMON_PACKAGES[*]}"
    fi
    return 0
  fi

  # If neither I3_PACKAGES nor WM_COMMON_PACKAGES are defined, nothing to do
  if { [[ ! -v I3_PACKAGES[@] ]] || [[ ${#I3_PACKAGES[@]} -eq 0 ]]; } &&
    { [[ ! -v WM_COMMON_PACKAGES[@] ]] || [[ ${#WM_COMMON_PACKAGES[@]} -eq 0 ]]; }; then
    log_warn "No i3 or WM-common packages defined in configuration"
    return 0
  fi

  # Install i3-specific packages if present
  if [[ -v I3_PACKAGES[@] ]] && [[ ${#I3_PACKAGES[@]} -gt 0 ]]; then
    log_debug "i3 package list (${#I3_PACKAGES[@]} packages): ${I3_PACKAGES[*]}"

    local i_mapped_array=()
    mapfile -t i_mapped_array < <(map_package_list "$CURRENT_DISTRO" "${I3_PACKAGES[@]}") || {
      log_error "Failed to map i3 packages"
      return 1
    }

    log_debug "Mapped ${#i_mapped_array[@]} i3 packages for $CURRENT_DISTRO:"
    for i in "${!i_mapped_array[@]}"; do
      log_debug "  [i3][$i]: '${i_mapped_array[$i]}'"
    done

    if ! pm_install_array "${i_mapped_array[@]}"; then
      log_error "Failed to install i3 packages"
      return 1
    fi
  fi

  # Install common WM packages (shared by X11-based window managers) if present
  if [[ -v WM_COMMON_PACKAGES[@] ]] && [[ ${#WM_COMMON_PACKAGES[@]} -gt 0 ]]; then
    log_debug "WM-common package list (${#WM_COMMON_PACKAGES[@]} packages): ${WM_COMMON_PACKAGES[*]}"

    local w_mapped_array=()
    mapfile -t w_mapped_array < <(map_package_list "$CURRENT_DISTRO" "${WM_COMMON_PACKAGES[@]}") || {
      log_error "Failed to map WM-common packages"
      return 1
    }

    log_debug "Mapped ${#w_mapped_array[@]} WM-common packages for $CURRENT_DISTRO:"
    for i in "${!w_mapped_array[@]}"; do
      log_debug "  [wm-common][$i]: '${w_mapped_array[$i]}'"
    done

    if ! pm_install_array "${w_mapped_array[@]}"; then
      log_error "Failed to install WM-common packages"
      return 1
    fi
  fi

  log_info "i3 and WM-common packages installation completed"
  return 0
}
