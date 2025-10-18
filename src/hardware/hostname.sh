#!/usr/bin/env bash

laptop_hostname_change() {
  log_info "Changing hostname for laptop..."

  # Execute command directly instead of using log_cmd
  if ! hostnamectl set-hostname "$hostname_laptop"; then
    log_error "Failed to change hostname"
    return 1
  fi

  log_info "Hostname changed to $hostname_laptop."
}