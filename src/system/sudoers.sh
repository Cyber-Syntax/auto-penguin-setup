#!/usr/bin/env bash

# TODO: Refactor to use /etc/sudoers.d/ directory structure for better modularity
# Currently using direct /etc/sudoers modification as sudoers.d wasn't working as expected

# Backup the sudoers file before making changes
_backup_sudoers() {
  local sudoers_file="/etc/sudoers"
  local backup_file
  backup_file="${sudoers_file}.bak.$(date +%Y%m%d%H%M%S)"

  log_info "Creating backup of sudoers file..."
  
  if ! sudo cp -p "$sudoers_file" "$backup_file"; then
    log_error "Failed to create backup of sudoers file"
    return 1
  fi
  
  log_info "Backup created: $backup_file"
  return 0
}

# Configure borgbackup to run without password prompt
sudoers_setup_borgbackup() {
  local sudoers_file="/etc/sudoers"
  local marker_start="# BEGIN auto-penguin-setup: borgbackup"
  local marker_end="# END auto-penguin-setup: borgbackup"
  
  log_info "Configuring sudoers for borgbackup passwordless execution..."
  
  # Create backup before modifying
  if ! _backup_sudoers; then
    log_error "Backup failed, aborting borgbackup sudoers setup"
    return 1
  fi
  
  # Remove old configuration if exists
  if sudo grep -q "$marker_start" "$sudoers_file"; then
    log_info "Removing existing borgbackup configuration..."
    sudo sed -i "/$marker_start/,/$marker_end/d" "$sudoers_file"
  fi
  
  # Add new configuration
  local config
  config=$(cat <<EOF
$marker_start
## Allow borgbackup script to run without password
$USER ALL=(ALL) NOPASSWD: /opt/borg/home-borgbackup.sh
$marker_end
EOF
)
  
  if ! echo "$config" | sudo tee -a "$sudoers_file" >/dev/null; then
    log_error "Failed to update sudoers file for borgbackup"
    return 1
  fi
  
  # Validate sudoers file syntax
  if ! sudo visudo -c -f "$sudoers_file" >/dev/null 2>&1; then
    log_error "Sudoers file syntax validation failed, restoring from backup"
    local latest_backup
    latest_backup=$(sudo ls -t "${sudoers_file}.bak."* 2>/dev/null | head -n1)
    if [[ -n "$latest_backup" ]]; then
      sudo cp "$latest_backup" "$sudoers_file"
    fi
    return 1
  fi
  
  log_info "Borgbackup sudoers configuration updated successfully"
  return 0
}

# Configure terminal password prompt timeout
sudoers_setup_terminal_timeout() {
  local sudoers_file="/etc/sudoers"
  local marker_start="# BEGIN auto-penguin-setup: terminal-timeout"
  local marker_end="# END auto-penguin-setup: terminal-timeout"
  
  log_info "Configuring sudoers for extended terminal password timeout..."
  
  # Create backup before modifying
  if ! _backup_sudoers; then
    log_error "Backup failed, aborting terminal timeout sudoers setup"
    return 1
  fi
  
  # Remove old configuration if exists
  if sudo grep -q "$marker_start" "$sudoers_file"; then
    log_info "Removing existing terminal timeout configuration..."
    sudo sed -i "/$marker_start/,/$marker_end/d" "$sudoers_file"
  fi
  
  # Add new configuration
  local config
  config=$(cat <<EOF
$marker_start
## Increase timeout on terminal password prompt
Defaults timestamp_type=global
Defaults env_reset,timestamp_timeout=20
$marker_end
EOF
)
  
  if ! echo "$config" | sudo tee -a "$sudoers_file" >/dev/null; then
    log_error "Failed to update sudoers file for terminal timeout"
    return 1
  fi
  
  # Validate sudoers file syntax
  if ! sudo visudo -c -f "$sudoers_file" >/dev/null 2>&1; then
    log_error "Sudoers file syntax validation failed, restoring from backup"
    local latest_backup
    latest_backup=$(sudo ls -t "${sudoers_file}.bak."* 2>/dev/null | head -n1)
    if [[ -n "$latest_backup" ]]; then
      sudo cp "$latest_backup" "$sudoers_file"
    fi
    return 1
  fi
  
  log_info "Terminal timeout sudoers configuration updated successfully"
  return 0
}

# Main sudoers setup function - orchestrates all sudoers configurations
sudoers_setup() {
  log_info "Starting sudoers configuration..."
  
  local errors=0
  
  # Setup borgbackup configuration
  if ! sudoers_setup_borgbackup; then
    log_warn "Borgbackup sudoers setup failed"
    ((errors++))
  fi
  
  # Setup terminal timeout configuration
  if ! sudoers_setup_terminal_timeout; then
    log_warn "Terminal timeout sudoers setup failed"
    ((errors++))
  fi
  
  if [[ $errors -eq 0 ]]; then
    log_info "All sudoers configurations completed successfully"
    return 0
  else
    log_warn "Sudoers setup completed with $errors error(s)"
    return 1
  fi
}

