#!/usr/bin/env bash

#TESTING:
virt_manager_setup() {
  log_info "Setting up virtualization..."

  # Check for UFW dependency
  if ! command -v ufw &>/dev/null; then
    log_info "UFW not installed but required for proper network configuration. Installing it first..."
    if ! sudo dnf install -y ufw; then
      log_error "Failed to install UFW, virtualization network rules won't be configured"
      # Continue with basic setup since libvirt can work without UFW rules
    fi
  fi

  # Install required packages
  log_info "Installing virtualization packages..."
  if ! sudo dnf install -y @virtualization; then
    log_error "Failed to install virtualization group"
    return 1
  fi

  if ! sudo dnf group install -y --with-optional virtualization; then
    log_warn "Failed to install optional virtualization packages"
    # Continue anyway with the base packages
  fi

  # Create the libvirt group if it doesn't exist
  if ! getent group libvirt >/dev/null; then
    sudo groupadd -r libvirt
  fi

  # Add user to libvirt group
  sudo usermod -aG libvirt "$USER"

  # Enable and start libvirt service
  if ! sudo systemctl enable --now libvirtd; then
    log_error "Failed to enable and start libvirt service"
    return 1
  fi

  # Libvirtd
  local libvirt_file="./configs/libvirt/network.conf"
  local dir_libvirt="/etc/libvirt/network.conf"

  # Fix network nat issue, switch iptables
  if ! sudo cp "$libvirt_file" "$dir_libvirt"; then
    log_error "Failed to copy libvirt network configuration"
  else
    log_info "Libvirt network configuration updated successfully"
  fi

  # enable network ufw
  if ! sudo ufw allow in on virbr0; then
    log_warn "Failed to allow incoming traffic on virbr0"
  fi
  if ! sudo ufw allow out on virbr0; then
    log_warn "Failed to allow outgoing traffic on virbr0"
  fi

  log_info "Virtualization setup completed. You may need to log out and log back in for group membership changes to take effect."
}