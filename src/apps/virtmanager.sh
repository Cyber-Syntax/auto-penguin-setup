#!/usr/bin/env bash

#TESTING:
virt_manager_setup() {
  log_info "Setting up virtualization..."

  # Try to initialize package manager abstraction when available. If it fails
  # we'll still attempt distro-specific fallbacks below.
  if ! init_package_manager &>/dev/null; then
    log_debug "init_package_manager not available or failed; continuing with distro detection fallback"
  fi

  # Detect distribution (uses src/core/distro_detection.sh)
  local distro
  if ! distro=$(detect_distro 2>/dev/null); then
    log_error "Failed to detect distribution; cannot continue with virtualization setup"
    return 1
  fi

  log_info "Detected distribution: $distro"

  # Install packages per-distro. Prefer pm_install when available.
  case "$distro" in
    fedora)
      log_info "Installing virtualization packages for Fedora"

      # Fedora uses a dnf group for virtualization; prefer using dnf directly
      if command -v dnf &>/dev/null; then
        if ! sudo dnf install -y @virtualization; then
          log_error "Failed to install virtualization group with dnf"
          return 1
        fi

        if ! sudo dnf group install -y --with-optional virtualization; then
          log_warn "Failed to install optional virtualization packages (continuing)"
        fi
      else
        # Fallback to package manager abstraction if dnf not available
        if ! pm_install "@virtualization"; then
          log_warn "pm_install failed for @virtualization; continuing"
        fi
      fi
      ;;

    arch)
      log_info "Installing virtualization packages for Arch"
      # WARN: Currently, iptables and iptables-nft conflict.
      # There is a option talked about "Remove conflicts when --noconfirm is set" in here:
      # https://gitlab.archlinux.org/pacman/pacman/-/issues/60
      # 
      # HACK: workaround for this to work without asking user to resolve conflict manually
      # --ask=4 parameter to pacman/paru install command
      
      # Common packages for Arch; keep list conservative and let pacman/paru handle missing ones
      local -a arch_pkgs=(libvirt qemu virt-manager virt-install dnsmasq ebtables bridge-utils)
      if ! pm_install --ask=4 "${arch_pkgs[@]}"; then
        log_error "Failed to install virtualization packages on Arch"
        return 1
      fi
      ;;

    debian)
      log_info "Installing virtualization packages for Debian/Ubuntu"
      # Debian splits libvirt into daemon/system and clients
      local -a deb_pkgs=(libvirt-daemon-system libvirt-clients qemu-kvm virt-manager bridge-utils)
      if ! pm_install "${deb_pkgs[@]}"; then
        log_error "Failed to install virtualization packages on Debian-based system"
        return 1
      fi
      ;;

    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac

  # Ensure libvirt group exists and add the user to it
  if ! getent group libvirt >/dev/null; then
    log_info "Creating libvirt group"
    sudo groupadd -r libvirt || log_warn "groupadd libvirt failed (it may already exist)"
  fi
  log_info "Adding user '$USER' to libvirt group"
  sudo usermod -aG libvirt "$USER" || log_warn "usermod failed; you may need to add the user to 'libvirt' manually"

  # Enable and start libvirt service. Try common service names as a fallback.
  if sudo systemctl enable --now libvirtd 2>/dev/null; then
    log_info "Enabled and started 'libvirtd' service"
  elif sudo systemctl enable --now libvirt 2>/dev/null; then
    log_info "Enabled and started 'libvirt' service"
  else
    log_warn "Failed to enable/start libvirt service automatically; please enable 'libvirtd' or 'libvirt' service manually"
  fi

  # Copy project-provided libvirt network configuration if available
  local script_root
  script_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
  local libvirt_file="${script_root}/configs/libvirt/network.conf"
  local dir_libvirt="/etc/libvirt/network.conf"
  if [[ -f "$libvirt_file" ]]; then
    if sudo cp "$libvirt_file" "$dir_libvirt"; then
      log_info "Libvirt network configuration updated successfully"
    else
      log_warn "Failed to copy libvirt network configuration from '$libvirt_file' to '$dir_libvirt'"
    fi
  else
    log_debug "No project libvirt network configuration found at '$libvirt_file' (skipping)"
  fi

  # If ufw is present, open virbr0 so VMs can use NAT as expected. Only apply if ufw exists.
  #TODO: research ufw rules for better security
  if command -v ufw &>/dev/null; then
    if ! sudo ufw allow in on virbr0; then
      log_warn "Failed to allow incoming traffic on virbr0 via ufw"
    fi
    if ! sudo ufw allow out on virbr0; then
      log_warn "Failed to allow outgoing traffic on virbr0 via ufw"
    fi
  else
    log_debug "ufw not installed; skipping firewall rules for virbr0"
  fi

  log_info "Virtualization setup completed. You may need to log out and log back in for group membership changes to take effect."
}