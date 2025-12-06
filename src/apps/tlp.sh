#!/usr/bin/env bash

#TODO: refactor function enable for better clearity
# one fuction is for installs and other is for enabling/configuring
# we might have subcommands in future for each app so better to keep them separate

# Disable services that conflict with TLP
# This includes tuned, tuned-ppd, and power-profiles-daemon
# Services are disabled but not removed to allow fallback if TLP setup fails
disable_conflicting_power_services() {
  log_info "Disabling services that conflict with TLP..."

  # List of services to check and disable
  local services_to_check=("tuned" "tuned-ppd" "power-profiles-daemon" "power-profile-daemon")
  local services_to_disable=()

  # Check which services exist
  for service in "${services_to_check[@]}"; do
    if systemctl list-unit-files | grep -q "^${service}"; then
      services_to_disable+=("$service")
    fi
  done

  # Disable found services
  if [[ ${#services_to_disable[@]} -gt 0 ]]; then
    log_info "Disabling conflicting services: ${services_to_disable[*]}"
    for service in "${services_to_disable[@]}"; do
      if ! sudo systemctl disable --now "$service" 2>/dev/null; then
        log_warn "Failed to disable $service"
      fi
    done
  else
    log_debug "No conflicting services found to disable"
  fi

  return 0
}

# Remove packages that conflict with TLP
# This should only be called after TLP is successfully set up
# to avoid leaving the system without any power management
remove_conflicting_power_packages() {
  log_info "Removing packages that conflict with TLP..."

  # List of packages to check and remove
  local packages_to_check=("tuned" "tuned-ppd" "power-profiles-daemon" "power-profile-daemon")
  local packages_to_remove=()

  # Check which packages are installed
  for pkg in "${packages_to_check[@]}"; do
    if pm_is_installed "$pkg"; then
      packages_to_remove+=("$pkg")
    fi
  done

  # Remove found packages
  if [[ ${#packages_to_remove[@]} -gt 0 ]]; then
    log_info "Removing conflicting packages: ${packages_to_remove[*]}"
    if ! pm_remove "${packages_to_remove[@]}"; then
      log_error "Failed to remove conflicting packages"
      return 1
    fi
    log_info "Successfully removed conflicting packages"
  else
    log_debug "No conflicting packages found to remove"
  fi

  return 0
}

tlp_setup() {
  log_info "Setting up TLP for power management..."

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

  # Disable conflicting power management services (but don't remove yet)
  # This allows fallback if TLP setup fails
  if ! disable_conflicting_power_services; then
    log_error "Failed to disable conflicting power services"
    return 1
  fi

  # Enable TLP services with verification
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

  # TLP setup successful - now safe to remove conflicting packages
  if ! remove_conflicting_power_packages; then
    log_warn "TLP is working, but failed to remove conflicting packages. You may want to remove them manually."
  fi

  log_info "TLP setup completed successfully."
  return 0
}
