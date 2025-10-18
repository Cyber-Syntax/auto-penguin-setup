#!/usr/bin/env bash

xorg_setup_intel() {
  log_info "Setting up xorg configuration..."

  local intel_file="./configs/20-intel.conf"
  local dir_intel="/etc/X11/xorg.conf.d/20-intel.conf"

  # make sure the destination directory exists
  if ! sudo mkdir -p "$(dirname "$dir_intel")"; then
    log_error "Failed to create directory for Intel configuration"
    return 1
  fi

  # Execute commands directly instead of using log_cmd
  if ! sudo cp "$intel_file" "$dir_intel"; then
    log_error "Failed to copy Intel configuration file"
    return 1
  fi

  log_info "Xorg configuration completed."
}