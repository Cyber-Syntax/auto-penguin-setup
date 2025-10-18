#!/usr/bin/env bash

# Source guard to prevent re-sourcing
[[ -n "${_GRUB_SOURCED:-}" ]] && return 0
readonly _GRUB_SOURCED=1

# Backup GRUB configuration file
_backup_grub_config() {
  local grub_file="/etc/default/grub"
  local backup_file
  backup_file="${grub_file}.bak.$(date +%Y%m%d%H%M%S)"
  
  log_info "Creating backup of GRUB configuration..."
  
  if [[ ! -f "$grub_file" ]]; then
    log_error "GRUB configuration file not found: $grub_file"
    return 1
  fi
  
  if ! sudo cp -p "$grub_file" "$backup_file"; then
    log_error "Failed to create backup of GRUB configuration"
    return 1
  fi
  
  log_info "Backup created: $backup_file"
  return 0
}

# Regenerate GRUB configuration based on distribution
_regenerate_grub_config() {
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Regenerating GRUB configuration for $distro..."
  
  case "$distro" in
    fedora)
      # Fedora uses grub2-mkconfig and /boot/grub2/grub.cfg
      if ! command -v grub2-mkconfig >/dev/null 2>&1; then
        log_error "grub2-mkconfig command not found"
        return 1
      fi
      sudo grub2-mkconfig -o /boot/grub2/grub.cfg
      ;;
    arch)
      # Arch uses grub-mkconfig and /boot/grub/grub.cfg
      if ! command -v grub-mkconfig >/dev/null 2>&1; then
        log_error "grub-mkconfig command not found"
        return 1
      fi
      sudo grub-mkconfig -o /boot/grub/grub.cfg
      ;;
    debian)
      # Debian/Ubuntu uses update-grub (wrapper for grub-mkconfig)
      if command -v update-grub >/dev/null 2>&1; then
        sudo update-grub
      elif command -v grub-mkconfig >/dev/null 2>&1; then
        sudo grub-mkconfig -o /boot/grub/grub.cfg
      else
        log_error "Neither update-grub nor grub-mkconfig found"
        return 1
      fi
      ;;
    *)
      log_error "Unsupported distribution for GRUB configuration: $distro"
      return 1
      ;;
  esac
  
  log_info "GRUB configuration regenerated successfully"
  return 0
}

# Configure GRUB timeout setting
grub_timeout() {
  local grub_file="/etc/default/grub"
  local timeout_value="${1:-0}"
  
  log_info "Configuring GRUB timeout to ${timeout_value} seconds..."
  
  # Check if GRUB is installed
  if [[ ! -f "$grub_file" ]]; then
    log_warn "GRUB configuration not found, skipping GRUB timeout setup"
    return 0
  fi
  
  # Create backup before modifying
  if ! _backup_grub_config; then
    log_error "Backup failed, aborting GRUB timeout setup"
    return 1
  fi
  
  # Update existing GRUB_TIMEOUT or add new entry
  if grep -q '^GRUB_TIMEOUT=' "$grub_file"; then
    log_debug "Updating existing GRUB_TIMEOUT setting..."
    sudo sed -i "s/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=${timeout_value}/" "$grub_file"
  else
    log_debug "Adding new GRUB_TIMEOUT setting..."
    # Add new timeout setting after GRUB_CMDLINE_LINUX or at end of file
    if grep -q '^GRUB_CMDLINE_LINUX=' "$grub_file"; then
      sudo sed -i "/^GRUB_CMDLINE_LINUX=/a GRUB_TIMEOUT=${timeout_value}" "$grub_file"
    else
      echo "GRUB_TIMEOUT=${timeout_value}" | sudo tee -a "$grub_file" >/dev/null
    fi
  fi
  
  # Verify the change
  if ! grep -q "^GRUB_TIMEOUT=${timeout_value}" "$grub_file"; then
    log_error "Failed to set GRUB_TIMEOUT to ${timeout_value}"
    return 1
  fi
  
  log_info "GRUB_TIMEOUT set to ${timeout_value} successfully"
  
  # Regenerate GRUB configuration
  if ! _regenerate_grub_config; then
    log_error "Failed to regenerate GRUB configuration"
    log_warn "You may need to manually run the appropriate command for your distribution:"
    log_warn "  Fedora: sudo grub2-mkconfig -o /boot/grub2/grub.cfg"
    log_warn "  Arch:   sudo grub-mkconfig -o /boot/grub/grub.cfg"
    log_warn "  Debian: sudo update-grub"
    return 1
  fi
  
  log_info "GRUB timeout configuration completed successfully"
  return 0
}

#TODO: Research and add it when device detection feature implemented
# NOTE: Current nvidia-open driver needs 'pcie_port_pm=off' on GRUB_CMDLINE_LINUX
# to properly load the nvidia module. Add this manually if using nvidia-open.