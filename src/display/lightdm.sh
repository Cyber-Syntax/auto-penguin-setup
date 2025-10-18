#!/usr/bin/env bash

# Switch display manager to lightdm
switch_lightdm() {
  log_info "Switching display manager to LightDM..."

  # Execute commands directly instead of using log_cmd
  if ! sudo dnf install -y lightdm; then
    log_error "Failed to install LightDM"
    return 1
  fi

  if ! sudo systemctl disable gdm; then
    log_warn "Failed to disable GDM, it might not be installed"
  fi

  if ! sudo systemctl enable lightdm; then
    log_error "Failed to enable LightDM"
    return 1
  fi

  log_info "Display manager switched to LightDM."
}

# Configuration file modification function for lightdm autologin
# This function modifies the lightdm configuration file to enable autologin
lightdm_autologin() {
  local conf_file="/etc/lightdm/lightdm.conf"
  local user_name="${user:-$(whoami)}"
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

  log_info "Setting up LightDM autologin for user $user_name with session $session_value"

  # Check if lightdm.conf exists
  if [[ ! -f "$conf_file" ]]; then
    log_error "LightDM configuration file not found: $conf_file"
    return 1
  fi

  # Create a backup of the original config
  if [[ ! -f "${conf_file}.bak" ]]; then
    sudo cp "$conf_file" "${conf_file}.bak"
  fi

  # Read the content of the file
  local content
  content=$(sudo cat "$conf_file")

  # Check if the file contains the [Seat:*] section
  if echo "$content" | grep -q '\[Seat:\*\]'; then
    # Modify the existing configuration
    log_info "Modifying existing LightDM configuration..."
    local new_content
    new_content=$(echo "$content" | awk -v user="$user_name" -v session="$session_value" '
      BEGIN { in_seat = 0; autologin_user_modified = 0; autologin_session_modified = 0; }
      /^\[Seat:\*\]/ { in_seat = 1; print; next; }
      /^\[/ { in_seat = 0; print; next; }
      in_seat && /^#?autologin-user=/ {
        print "autologin-user=" user;
        autologin_user_modified = 1;
        next;
      }
      in_seat && /^#?autologin-session=/ {
        print "autologin-session='" session "'";
        autologin_session_modified = 1;
        next;
      }
      { print }
      END {
        if (in_seat) {
          if (!autologin_user_modified) print "autologin-user=" user;
          if (!autologin_session_modified) print "autologin-session='" session "'";
        }
      }
    ')

    # Write the new content to the file
    echo "$new_content" | sudo tee "$conf_file" >/dev/null
  else
    # Add the [Seat:*] section with autologin enabled
    log_info "Adding new LightDM autologin configuration..."
    local new_content="${content}\n\n[Seat:*]\n"
    new_content="${new_content}autologin-user=$user_name\n"
    new_content="${new_content}autologin-session=$session_value\n"

    # Write the new content to the file
    echo -e "$new_content" | sudo tee "$conf_file" >/dev/null
  fi
  # pam setup for auto unlock gnome keyring
  #TODO: handle this later
  #NOTE: this isn't work with autologin because its need password on from display manager
  #   # Gnome keyring auto unlock
  # auth       optional     pam_gnome_keyring.so
  # session    optional     pam_gnome_keyring.so auto_start
  #

  log_success "LightDM autologin configuration completed"
  return 0
}

#TEST: Group for passwordless login
#Seems like this isn't called or work?
#TODO: need to test this on lightdm, is it work?
nopasswdlogin_group() {
  echo "Creating group for passwordless login..."
  sudo groupadd -r autologin 2>/dev/null || echo "Group 'autologin' already exists."
  sudo gpasswd -a "$USER" nopasswdlogin
  sudo gpasswd -a "$USER" autologin
  echo "Group created for passwordless login."
  sudo usermod -aG autologin "$USER"
}