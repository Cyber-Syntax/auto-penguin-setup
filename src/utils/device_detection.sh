#!/usr/bin/env bash

# Detect device type based on hostname like desktop, laptop, etc.
#TODO: need better logic than hostname for device detection.
detect_system_type() {
  local hostname detected_type
  #FIXME: hostname: command not found
# [ERROR] Unknown hostname 'unknown'
  hostname=$(hostname 2>/dev/null || echo "unknown")

  log_debug "Detected hostname: $hostname"

  # Ensure hostname variables are defined, use safe defaults if not
  local desktop_hostname="${hostname_desktop:-desktop}"
  local laptop_hostname="${hostname_laptop:-laptop}"

  if [[ "$hostname" == "$desktop_hostname" ]]; then
    detected_type="desktop"
  elif [[ "$hostname" == "$laptop_hostname" ]]; then
    detected_type="laptop"
  else
    log_error "Unknown hostname '$hostname'. Expected:"
    log_error "Desktop: $desktop_hostname"
    log_error "Laptop:  $laptop_hostname"
    exit 1
  fi

  # Output only the type to stdout
  echo "$detected_type"
}