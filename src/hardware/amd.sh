#!/usr/bin/env bash

# Function: zenpower_setup
# Purpose: Setup zenpower for AMD Ryzen 5000 series (cross-distro)
# Returns: 0 on success, 1 on failure
zenpower_setup() {
  log_info "Setting up zenpower for Ryzen 5000 series..."

  local distro
  distro=$(detect_distro) || return 1

  # Check if running on AMD CPU
  if ! grep -q "AMD" /proc/cpuinfo; then
    log_error "This system does not appear to have an AMD CPU"
    return 1
  fi

  local blacklist_file="/etc/modprobe.d/zenpower.conf"
  #NOTE: k10temp conflict with zenpower3, so we blacklist it
  # check k10temp is loaded than unload it
  if lsmod | grep -q "^k10temp"; then
    log_info "k10temp module is currently loaded, unloading..." 
    if ! sudo modprobe -r k10temp; then
      log_error "Failed to unload k10temp module"
      return 1
    fi
  fi

  log_debug "Creating k10temp blacklist file at $blacklist_file..."
  if ! echo "blacklist k10temp" | sudo tee "$blacklist_file" >/dev/null; then
    log_error "Failed to create k10temp blacklist file"
    return 1
  fi

  case "$distro" in
    fedora)
      log_debug "Enabling zenpower3 COPR repository..."
      if ! sudo dnf copr enable shdwchn10/zenpower3 -y; then
        log_error "Failed to enable zenpower3 COPR repository"
        return 1
      fi
      log_debug "Installing zenpower3 and zenmonitor3..."
      if ! pm_install zenpower3 zenmonitor3; then
        log_error "Failed to install zenpower3 and zenmonitor3 packages"
        return 1
      fi
      ;;
    arch)
      log_debug "Installing zenpower3 and zenmonitor3 from AUR..."
      if ! repo_add zenpower3-dkms; then
        log_error "Failed to install zenpower3 from AUR"
        return 1
      fi
      if ! repo_add zenmonitor3; then
        log_warn "Failed to install zenmonitor3 from AUR (optional)"
      fi
      ;;
    debian)
    #TODO: search for a PPA or DEB package
      log_warn "Zenpower is not officially packaged for Debian/Ubuntu"
      log_info "Manual installation from source may be required"
      log_info "See: https://github.com/ocerman/zenpower3"
      return 1
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac

  # Load zenpower module
  log_debug "Loading zenpower module..."
  if ! sudo modprobe zenpower3; then
    log_error "Failed to load zenpower3 module"
    # Some users reported that a restart is needed after module installation
    log_info "A system restart may be required to load the zenpower3 module, please reboot and try again"
    return 1
  fi

  log_info "zenpower3 module loaded successfully"
  return 0
}

