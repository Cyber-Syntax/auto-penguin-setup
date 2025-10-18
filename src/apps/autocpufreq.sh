#!/usr/bin/env bash

# Purpose: Installs auto-cpufreq from GitHub repository for automatic CPU speed and power optimization
#NOTE: available in AUR, snap, auto-cpufreq-installer from github.
# it is better to use github installer on most distros which seems like others cause issues.
# we can use aur for arch based distros but still better to use github installer for consistency
# So, we can use this function for all distros
install_auto_cpufreq() {
  log_info "Installing auto-cpufreq..."

  local temp_dir
  temp_dir=$(mktemp -d)

  log_info "Cloning auto-cpufreq repository..."
  if ! git clone https://github.com/AdnanHodzic/auto-cpufreq.git "$temp_dir"; then
    log_error "Failed to clone auto-cpufreq repository"
    return 1
  fi

  log_info "Running auto-cpufreq installer..."
  log_info "NOTE: The installer will ask for confirmation during installation."
  log_info "Please respond to the prompts as needed (typically 'y' to proceed)."

  cd "$temp_dir" || {
    log_error "Failed to navigate to auto-cpufreq directory"
    return 1
  }

  # Pipe "I" into the installer to automatically select the Install option,
  # allowing the installer to proceed without manual intervention.
  if ! echo "I" | sudo ./auto-cpufreq-installer; then
    log_error "auto-cpufreq installation failed"
    cd - > /dev/null || true
    return 1
  fi

  cd - > /dev/null || true
  rm -rf "$temp_dir"

  log_info "auto-cpufreq installation completed"
  return 0
}