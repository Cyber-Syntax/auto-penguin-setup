#!/usr/bin/env bash

touchpad_setup() {
  log_info "Setting up touchpad configuration..."

  local dir_touchpad="/etc/X11/xorg.conf.d/99-touchpad.conf"
  local touchpad_file="./configs/99-touchpad.conf"

  # make sure the destination directory exists
  if ! sudo mkdir -p "$(dirname "$dir_touchpad")"; then
    log_error "Failed to create directory for touchpad configuration"
    return 1
  fi

  if ! sudo cp "$touchpad_file" "$dir_touchpad"; then
    log_error "Failed to copy touchpad configuration file"
    return 1
  fi

  log_info "Touchpad configuration completed."
}