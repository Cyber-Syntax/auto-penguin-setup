#!/usr/bin/env bash

# Autologin for gdm with machine-specific session
gdm_auto_login() {
  log_info "Setting up GDM autologin..."
  local gdm_custom="/etc/gdm/custom.conf"

  # Check if user is root or has sudo privileges
  if [[ $EUID -ne 0 ]]; then
    log_error "This function must be run as root or with sudo privileges"
    return 1
  fi

  # Verify username is set
  local config_user="${user:-$(whoami)}"
  if [[ -z "$config_user" ]]; then
    log_error "Unable to determine user for autologin"
    return 1
  fi

  # Determine system type from hostname
  local hostname
  hostname=$(hostname 2>/dev/null || echo "unknown")
  local session_value

  # Determine which session to use based on system type
  if [[ "$hostname" == "$hostname_desktop" ]]; then
    session_value="${desktop_session:-qtile}"
  elif [[ "$hostname" == "$hostname_laptop" ]]; then
    session_value="${laptop_session:-hyprland}"
  else
    session_value="qtile" # Default if hostname doesn't match known types
  fi

  log_info "Setting up GDM autologin for user $config_user with session $session_value..."

  log_debug "Creating GDM configuration at $gdm_custom..."
  cat <<EOF | sudo tee "$gdm_custom" >/dev/null
[daemon]
WaylandEnable=false
DefaultSession=${session_value}.desktop
AutomaticLoginEnable=True
AutomaticLogin=$config_user
EOF

  # Verify file was created and has correct content
  if [[ ! -f "$gdm_custom" ]]; then
    log_error "GDM configuration file was not created"
    return 1
  fi

  log_info "GDM autologin setup completed successfully"
  return 0
}