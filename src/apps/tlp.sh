#!/usr/bin/env bash

#TODO: refactor function enable for better clearity
# one fuction is for installs and other is for enabling/configuring
# we might have subcommands in future for each app so better to keep them separate

#TODO: fallback for power-profile-daemon and tuned if tlp fails
tlp_setup() {
  log_info "Setting up TLP for power management..."

  local distro
  distro=$(detect_distro) || return 1

  # Get distribution version
  local distro_version
  distro_version=$(get_distro_version)
  log_debug "Detected $distro version: $distro_version"

  # Make sure tlp is installed, if not install it
  if ! pm_is_installed tlp; then
    log_info "TLP is not installed. Installing..."
    if ! pm_install tlp; then
      log_error "Failed to install TLP"
      return 1
    fi
  fi

  local tlp_file="./configs/01-mytlp.conf"
  local dir_tlp="/etc/tlp.d/01-mytlp.conf"

  # Create the tlp.d directory if it doesn't exist
  if [[ ! -d "/etc/tlp.d" ]]; then
    if ! sudo mkdir -p /etc/tlp.d; then
      log_error "Failed to create /etc/tlp.d directory"
      return 1
    fi
  fi

  # Backup if there is no backup
  if [[ ! -f "/etc/tlp.d/01-mytlp.conf.bak" ]]; then
    if ! sudo cp /etc/tlp.d/01-mytlp.conf /etc/tlp.d/01-mytlp.conf.bak; then
      log_warn "Failed to create backup of TLP configuration"
    fi
  fi

  # Copy the TLP configuration file
  if ! sudo cp "$tlp_file" "$dir_tlp"; then
    log_error "Failed to copy TLP configuration file"
    return 1
  fi

  # 2. Service management with existence checks
  handle_services() {
    local action="$1"
    shift
    for service in "$@"; do
      if systemctl list-unit-files | grep -q "^$service"; then
        if ! systemctl "$action" "$service"; then
          log_warn "Failed to $action $service"
        fi
      else
        log_debug "Service $service not found - skipping"
      fi
    done
  }

  # 3. TuneD handling (Fedora-specific)
  if [[ "$distro" == "fedora" ]] && [[ -n "$distro_version" ]] && ((distro_version > 40)); then
    log_info "Handling TuneD for Fedora $distro_version..."
    handle_services 'disable --now' tuned tuned-ppd

    if pm_is_installed tuned || pm_is_installed tuned-ppd; then
      if ! pm_remove tuned tuned-ppd; then
        log_error "Failed to remove TuneD packages"
        return 1
      fi
    fi
  fi

  # 4. power-profile-daemon handling (distro-specific)
  case "$distro" in
  fedora)
    if [[ -n "$distro_version" ]] && ((distro_version < 41)); then
      log_info "Handling power-profile-daemon for Fedora $distro_version..."
      handle_services 'disable --now' power-profile-daemon

      if pm_is_installed power-profile-daemon; then
        if ! pm_remove power-profile-daemon; then
          log_error "Failed to remove power-profile-daemon"
          return 1
        fi
      fi
    fi
    ;;
  arch | debian)
    # For Arch and Debian, disable power-profile-daemon if installed
    if pm_is_installed power-profiles-daemon 2>/dev/null; then
      log_info "Disabling power-profiles-daemon for $distro..."
      handle_services 'disable --now' power-profiles-daemon
    fi
    ;;
  esac

  # 5. Enable TLP services with verification
  log_info "Configuring TLP services..."
  for service in tlp tlp-sleep; do
    if [[ -f "/usr/lib/systemd/system/${service}.service" ]]; then
      if ! sudo systemctl enable --now "$service"; then
        log_error "Failed to enable $service"
        return 1
      fi
    else
      log_warn "$service service not found"
    fi
  done

  # mask rfkill to be able to handle radios with tlp
  if ! sudo systemctl mask systemd-rfkill.service; then
    log_warn "Failed to mask systemd-rfkill.service"
  fi

  if ! sudo systemctl mask systemd-rfkill.socket; then
    log_warn "Failed to mask systemd-rfkill.socket"
  fi

  # Check if tlp-rdw command exists and install if needed
  if ! command -v tlp-rdw &>/dev/null; then
    log_info "tlp-rdw command not found. Attempting to install..."
    if ! pm_install tlp-rdw; then
      log_warn "Failed to install tlp-rdw package. Skipping radio device handling."
    else
      log_info "tlp-rdw installed successfully"
    fi
  fi

  # Enable tlp radio device handling if command is available
  if command -v tlp-rdw &>/dev/null; then
    if ! sudo tlp-rdw enable; then
      log_warn "Failed to enable TLP radio device handling"
    fi
  else
    log_warn "tlp-rdw command not available. Skipping radio device handling."
  fi

  log_info "TLP setup completed successfully."
  return 0
}

