#!/usr/bin/env bash

tcp_bbr_setup() {
  # Copy TCP BBR configuration file
  echo "Setting up TCP BBR configuration..."

  local dir_tcp_bbr="/etc/sysctl.d/99-tcp-bbr.conf"
  local tcp_bbr_file="./configs/99-tcp-bbr.conf"

  if ! sudo cp "$tcp_bbr_file" "$dir_tcp_bbr"; then
    log_error "Failed to copy TCP BBR configuration file"
    return 1
  fi

  echo "Reloading sysctl settings..."
  sudo sysctl --system

}

