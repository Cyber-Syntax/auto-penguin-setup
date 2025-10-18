#!/usr/bin/env bash

#TODO: maybe we add our dotfiles repo before enable syncthing?
# which syncthing is acces relay servers which not good for privacy
# maybe we can make a default config that disable relay servers or our dotfiles.
syncthing_setup() {
  log_info "Setting up Syncthing..."

  # For user-specific services, don't use sudo
  if ! systemctl --user enable --now syncthing; then
    log_error "Failed to enable Syncthing service"
    return 1
  fi

  log_info "Syncthing enabled successfully."
}