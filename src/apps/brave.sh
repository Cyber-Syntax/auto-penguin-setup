#!/usr/bin/env bash

# Purpose: Modifies Brave Browser desktop file to use basic password store (cross-distro)
disable_keyring_for_brave() {
  # Use XDG-compliant user desktop directory
  local user_desktop_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  local user_desktop_file="$user_desktop_dir/brave-browser.desktop"

  # Determine system desktop file location based on distro
  local system_desktop_file=""
  case "$CURRENT_DISTRO" in
    fedora | debian)
      system_desktop_file="/usr/share/applications/brave-browser.desktop"
      ;;
    arch)
      # On Arch with brave-bin, might be in different location
      if [[ -f "/usr/share/applications/brave-browser.desktop" ]]; then
        system_desktop_file="/usr/share/applications/brave-browser.desktop"
      elif [[ -f "/opt/brave-bin/brave-browser.desktop" ]]; then
        system_desktop_file="/opt/brave-bin/brave-browser.desktop"
      else
        # Fallback if neither location exists
        system_desktop_file="/usr/share/applications/brave-browser.desktop"
      fi
      ;;
    *)
      system_desktop_file="/usr/share/applications/brave-browser.desktop"
      ;;
  esac

  # Create the user desktop applications directory if it does not exist
  if [[ ! -d "$user_desktop_dir" ]]; then
    if ! mkdir -p "$user_desktop_dir"; then
      log_error "Failed to create user applications directory: $user_desktop_dir"
      return 1
    fi
    log_debug "Created user desktop directory: $user_desktop_dir"
  fi

  # If the user desktop file does not exist, copy from system
  if [[ ! -f "$user_desktop_file" ]]; then
    if [[ -f "$system_desktop_file" ]]; then
      log_info "Copying system desktop file to user directory..."
      if ! cp "$system_desktop_file" "$user_desktop_file"; then
        log_error "Failed to copy desktop file"
        return 1
      fi
    else
      log_error "Brave desktop file not found at: $system_desktop_file"
      return 1
    fi
  fi

  # If already modified, skip further changes
  if grep -q -- "--password-store=basic" "$user_desktop_file"; then
    log_info "Desktop file already modified - no changes needed"
    return 0
  fi

  # Create backup of the original file
  local backup_file="${user_desktop_file}.bak"
  log_debug "Creating backup at $backup_file"
  if ! cp "$user_desktop_file" "$backup_file"; then
    log_warn "Failed to create backup file, but proceeding anyway"
  fi

  # Modify all Exec lines to add --password-store=basic
  log_debug "Modifying desktop file to use basic password store"

  # Track if any modification was made
  local modified=false

  # Handle different Exec line formats:
  # 1. Exec=/usr/bin/brave-browser-stable [args...]
  # 2. Exec=brave [args...]
  # We need to insert --password-store=basic after the command but before other args

  # First pattern: /usr/bin/brave-browser-stable
  if grep -q "^Exec=/usr/bin/brave-browser-stable" "$user_desktop_file"; then
    log_debug "Modifying Exec lines with /usr/bin/brave-browser-stable"
    if sed -i 's|^Exec=/usr/bin/brave-browser-stable\(.*\)|Exec=/usr/bin/brave-browser-stable --password-store=basic\1|' "$user_desktop_file"; then
      modified=true
    fi
  fi

  # Second pattern: Exec=brave (for Arch brave-bin and similar)
  # Need to be careful not to match brave-browser-stable
  if grep -q "^Exec=brave " "$user_desktop_file" || grep -q "^Exec=brave$" "$user_desktop_file"; then
    log_debug "Modifying Exec lines with bare 'brave' command"
    if sed -i 's|^Exec=brave\([ ].*\)$|Exec=brave --password-store=basic\1|' "$user_desktop_file" \
      && sed -i 's|^Exec=brave$|Exec=brave --password-store=basic|' "$user_desktop_file"; then
      modified=true
    fi
  fi

  # Verify modification was successful
  if [[ "$modified" == false ]]; then
    log_error "Failed to modify desktop file - no matching Exec lines found"
    log_debug "Desktop file Exec lines:"
    grep "^Exec=" "$user_desktop_file" | while IFS= read -r line; do
      log_debug "  $line"
    done
    # Restore from backup
    if [[ -f "$backup_file" ]]; then
      log_debug "Restoring from backup"
      cp "$backup_file" "$user_desktop_file"
    fi
    return 1
  fi

  log_info "Successfully modified Brave desktop file"
  return 0
}

install_brave() {
  log_info "Installing Brave Browser..."

  # Check if Brave is already installed
  if command -v brave &>/dev/null || command -v brave-browser &>/dev/null; then
    log_info "Brave Browser is already installed"
  else
    log_info "Installing Brave Browser for $CURRENT_DISTRO..."

    # Use official Brave install script (requires sudo)
    if ! command -v curl &>/dev/null; then
      log_error "curl is required for Brave installation"
      return 1
    fi

    # Brave install script handle AUR/fedora/debian...
    if ! curl -fsS https://dl.brave.com/install.sh | bash; then
      log_error "Failed to install Brave Browser"
      return 1
    fi

    log_success "Brave Browser installed successfully"
  fi

  # Modify desktop file to use basic password store
  if ! disable_keyring_for_brave; then
    log_warn "Failed to modify Brave desktop file, but continuing"
  fi

  return 0
}
