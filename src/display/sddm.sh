#!/usr/bin/env bash

# display_manager.sh - Display manager configuration abstraction
# Purpose: Abstract display manager configuration tasks (e.g., SDDM autologin)

# Function: switch_to_sddm
# Purpose: Switches the display manager to SDDM and optionally configures autologin
switch_to_sddm() {
  log_info "Switching to SDDM display manager..."

  # Check if SDDM is installed
  if ! rpm -q sddm &>/dev/null; then
    log_info "SDDM not found. Installing SDDM..."
    if ! sudo dnf install -y sddm; then
      log_error "Failed to install SDDM"
      return 1
    fi
  fi

  # Check if user is running in a graphical environment
  # Using ${VAR:-} syntax to handle unbound variables safely
  if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    log_warn "IMPORTANT: You appear to be running a graphical session."
    log_warn "It is STRONGLY RECOMMENDED to switch display managers from a TTY console."
    log_warn "Please follow these steps:"
    log_warn "1. Press Ctrl+Alt+F3 to switch to a TTY console"
    log_warn "2. Log in with your username and password"
    log_warn "3. Run this script with: sudo ./setup.sh -S"
    log_warn "4. After switching to SDDM, reboot with: sudo systemctl reboot"

    read -p "Continue anyway? This may cause your session to crash! [y/N] " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_info "Operation cancelled. Please run this from a TTY console."
      return 1
    fi
  fi

  # Find and disable the current display manager
  local current_dm
  current_dm=$(systemctl list-units --type=service --state=active | grep -E 'gdm|lightdm|lxdm|xdm' | awk '{print $1}')

  if [[ -n "$current_dm" ]]; then
    log_info "Disabling current display manager: $current_dm"
    if ! sudo systemctl disable --now "$current_dm"; then
      log_warn "Failed to disable current display manager: $current_dm"
    fi
  fi

  # Enable SDDM
  log_info "Enabling SDDM service..."
  if ! sudo systemctl enable --now sddm.service; then
    log_error "Failed to enable SDDM service"
    return 1
  fi

  # Ask user if they want to configure SDDM autologin
  read -p "Would you like to configure SDDM autologin? This will automatically log in after boot. [y/N] " -r
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Call the sddm_autologin function from apps.sh
    if ! sddm_autologin; then
      log_error "Failed to configure SDDM autologin"
      # Continue despite autologin failure
      log_info "Continuing with SDDM setup without autologin"
    fi
  else
    log_info "Skipping SDDM autologin configuration"
  fi

  log_success "SDDM is now set as the default display manager."
  log_info "To select your session, choose it from the SDDM session menu at login."
  log_info "You should reboot your system for the changes to take effect:"
  log_info "  sudo systemctl reboot"

  return 0
}

# Function: sddm_autologin
# Purpose: Configures SDDM for automatic login with the current user, using machine-specific settings
#TODO: need testing but also better to make a new display_manager variable which desktop-laptop device might use different display manager
# like desktop might use sddm which might gaming pc but laptop might use lightdm for better power management etc.
sddm_autologin() {
  log_info "Setting up SDDM autologin..."

  # Determine system type from hostname
  local hostname
  hostname=$(hostname 2>/dev/null || echo "unknown")
  local system_type="unknown"

  # Check hostname against our configured values from the nested structure
  if [[ "$hostname" == "$hostname_desktop" ]]; then
    system_type="desktop"
  elif [[ "$hostname" == "$hostname_laptop" ]]; then
    system_type="laptop"
  else
    log_warn "Unknown hostname '$hostname', will use default session"
  fi

  log_info "Detected system type: $system_type"

  # Get user from variables or fall back to current user
  local config_user="${user:-$(whoami)}"

  # Get session based on system type, using our loaded variables
  # These variables are loaded from the nested structure in load_variables
  local session_value
  if [[ "$system_type" == "desktop" ]]; then
    # Use desktop-specific session
    session_value="${desktop_session}"
  elif [[ "$system_type" == "laptop" ]]; then
    # Use laptop-specific session
    session_value="${laptop_session}"
  else
    # Use qtile as default when system type is unknown
    session_value="qtile"
  fi

  # If session is still empty, fall back to qtile
  session_value="${session_value:-qtile}"

  log_info "Using session: $session_value for user: $config_user"

  # Check if SDDM is installed
  if ! rpm -q sddm &>/dev/null; then
    log_error "SDDM is not installed. Please install it first."
    return 1
  fi

  # Determine which configuration file to use
  local conf_file
  if [[ -f "/etc/sddm.conf" ]]; then
    conf_file="/etc/sddm.conf"
    log_debug "Using existing SDDM config file at /etc/sddm.conf"
  else
    # Create SDDM configuration directory if it doesn't exist
    if [[ ! -d "/etc/sddm.conf.d/" ]]; then
      if ! sudo mkdir -p /etc/sddm.conf.d/; then
        log_error "Failed to create SDDM configuration directory"
        return 1
      fi
    fi
    conf_file="/etc/sddm.conf.d/autologin.conf"
    log_debug "Using SDDM config file at /etc/sddm.conf.d/autologin.conf"
  fi

  # Create backup of original file if it exists
  if [[ -f "$conf_file" && ! -f "${conf_file}.bak" ]]; then
    log_debug "Creating backup of SDDM configuration..."
    if ! sudo cp "$conf_file" "${conf_file}.bak"; then
      log_warn "Failed to create backup of SDDM configuration"
    else
      log_debug "SDDM configuration backup created at ${conf_file}.bak"
    fi
  fi

  # Parse existing content if file exists and extract sections
  local existing_content=""
  local general_section=""
  local other_sections=""

  if [[ -f "$conf_file" ]]; then
    existing_content=$(sudo cat "$conf_file" 2>/dev/null)

    # Extract the [General] section if it exists
    if echo "$existing_content" | grep -q '^\[General\]'; then
      general_section=$(echo "$existing_content" | awk '
        BEGIN {in_general = 0; content = ""}
        /^\[General\]/ {in_general = 1; content = content $0 "\n"; next}
        /^\[/ && in_general {in_general = 0; next}
        in_general {content = content $0 "\n"}
        END {print content}
      ')
    fi

    # Extract other sections except [Autologin] and [General]
    other_sections=$(echo "$existing_content" | awk '
      BEGIN {in_skip = 0; content = ""}
      /^\[(Autologin|General)\]/ {in_skip = 1; next}
      /^\[/ && in_skip {in_skip = 0; content = content $0 "\n"; next}
      /^\[/ && !in_skip {content = content $0 "\n"; next}
      !in_skip {content = content $0 "\n"}
      END {print content}
    ')
  fi

  # Create new autologin section with clean formatting
  local autologin_section="[Autologin]\n"
  autologin_section+="# Username for autologin session\n"
  autologin_section+="User=${config_user}\n"
  autologin_section+="# Name of session file for autologin session\n"
  autologin_section+="Session=${session_value}.desktop\n"
  autologin_section+="# Whether sddm should automatically log back into sessions when they exit\n"
  autologin_section+="Relogin=false\n"

  # Build the new configuration content with proper section ordering and spacing
  local new_content=""
  new_content+="${autologin_section}\n"

  # Add other sections if they exist (excluding [Autologin] and [General])
  if [[ -n "$other_sections" ]]; then
    new_content+="${other_sections}\n"
  fi

  # Add [General] section at the end if it exists
  if [[ -n "$general_section" ]]; then
    new_content+="${general_section}"
  fi

  # Trim trailing newlines and ensure file ends with exactly one newline
  new_content=$(echo -e "$new_content" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}')
  new_content="${new_content}\n"

  # Write the updated configuration
  log_debug "Writing new SDDM configuration..."
  if ! echo -e "$new_content" | sudo tee "$conf_file" >/dev/null; then
    log_error "Failed to write SDDM autologin configuration"
    return 1
  fi

  # Set proper file permissions
  if ! sudo chmod 644 "$conf_file"; then
    log_warn "Failed to set proper permissions on SDDM configuration file"
  fi

  log_success "SDDM autologin configuration completed successfully"
  log_info "The system will automatically log in as $config_user to $session_value after reboot"
  return 0
}