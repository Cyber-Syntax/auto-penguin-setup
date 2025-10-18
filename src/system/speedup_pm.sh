#!/usr/bin/env bash
# Optimize package manager configuration based on distribution

speed_up_package_manager() {
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Optimizing package manager configuration for $distro..."
  
  case "$distro" in
    fedora)
      speed_up_dnf
      ;;
    arch)
      speed_up_pacman
      ;;
    debian)
      speed_up_apt
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Package manager optimization completed"
}

# Tweaks DNF configuration to improve performance (Fedora-specific).
speed_up_dnf() {
  log_info "Configuring DNF for improved performance..."
  local _dnf_conf="/etc/dnf/dnf.conf"

  # Backup current dnf.conf if no backup exists
  if [[ ! -f "${_dnf_conf}.bak" ]]; then
    if ! sudo cp "$_dnf_conf" "${_dnf_conf}.bak"; then
      log_error "Failed to create backup of $_dnf_conf"
      return 1
    fi
  fi
  
  local settings=(
    "max_parallel_downloads=20"
    "pkg_gpgcheck=True"
    "skip_if_unavailable=True"
    "timeout=15"
    "retries=5"
  )

  for setting in "${settings[@]}"; do
    if ! grep -q "^$setting" "$_dnf_conf"; then
      log_debug "Adding setting: $setting"
      if ! echo "$setting" | sudo tee -a "$_dnf_conf" >/dev/null; then
        log_error "Failed to add setting: $setting"
        return 1
      fi
    fi
  done

  log_info "DNF configuration updated successfully."
}

# Optimize pacman configuration (Arch-specific)
#TODO: Verify that these settings do not cause issues
#NOTE: Configuration tested and working as intended
speed_up_pacman() {
  log_info "Configuring pacman for improved performance..."
  local _pacman_conf="/etc/pacman.conf"

  # Backup current pacman.conf if no backup exists
  if [[ ! -f "${_pacman_conf}.bak" ]]; then
    if ! sudo cp "$_pacman_conf" "${_pacman_conf}.bak"; then
      log_error "Failed to create backup of $_pacman_conf"
      return 1
    fi
    log_debug "Created backup: ${_pacman_conf}.bak"
  else
    log_debug "Backup already exists: ${_pacman_conf}.bak"
  fi

  # Settings that need to be added (pacman supports spaces around = sign)
  local settings=(
    "ParallelDownloads = 20"
  )

  for setting in "${settings[@]}"; do
    local key="${setting%% =*}"  # Extract key before ' ='
    local value="${setting##*= }"  # Extract value after '= '
    
    # Check if key exists (with flexible whitespace matching)
    if grep -qE "^${key}[[:space:]]*=" "$_pacman_conf"; then
      local current_value
      current_value=$(grep -E "^${key}[[:space:]]*=" "$_pacman_conf" | head -n1 | sed -E "s/^${key}[[:space:]]*=[[:space:]]*//" | xargs)
      
      if [[ "$current_value" == "$value" ]]; then
        log_debug "$key is already set to $value"
      else
        log_debug "$key is currently set to $current_value, updating to $value"
        if ! sudo sed -i -E "s/^${key}[[:space:]]*=.*/${setting}/" "$_pacman_conf"; then
          log_error "Failed to update setting: $setting"
          return 1
        fi
        log_info "Updated $key from $current_value to $value"
      fi
    else
      log_debug "Adding setting: $setting"
      if ! echo "$setting" | sudo tee -a "$_pacman_conf" >/dev/null; then
        log_error "Failed to add setting: $setting"
        return 1
      fi
      log_info "Added $key = $value"
    fi
  done

  # Enable Color output (uncomment if exists, add if doesn't)
  if grep -q "^#Color" "$_pacman_conf"; then
    log_debug "Uncommenting Color option in pacman"
    if ! sudo sed -i 's/^#Color/Color/' "$_pacman_conf"; then
      log_error "Failed to uncomment Color setting"
      return 1
    fi
    log_info "Enabled Color output"
  elif grep -q "^Color" "$_pacman_conf"; then
    log_debug "Color output already enabled"
  else
    log_debug "Adding Color option to pacman"
    if ! echo "Color" | sudo tee -a "$_pacman_conf" >/dev/null; then
      log_error "Failed to add Color setting"
      return 1
    fi
    log_info "Added Color output option"
  fi

  log_info "Pacman configuration updated successfully."
}

# Optimize APT configuration (Debian-specific)
#TESTING: This apt must be researched to ensure the config is optimal and doesn't cause issues
speed_up_apt() {
  log_info "Configuring APT for improved performance..."
  local _apt_conf="/etc/apt/apt.conf.d/99custom"

  # Create custom APT configuration
  cat <<EOF | sudo tee "$_apt_conf" >/dev/null
APT::Acquire::Queue-Mode "host";
APT::Acquire::Retries "3";
Acquire::http::Timeout "15";
Acquire::https::Timeout "15";
EOF

  if [[ $? -ne 0 ]]; then
    log_error "Failed to create APT configuration file"
    return 1
  fi

  log_info "APT configuration updated successfully."
}