#!/usr/bin/env bash
#TEST: Currently only for desktop
borgbackup_setup() {
  # send sh script to /opt/borg/home-borgbackup.sh
  log_info "Moving borgbackup script to /opt/borg/home-borgbackup.sh..."

  local dir_borg_script="/opt/borg/home-borgbackup.sh"
  local dir_borg_timer="/etc/systemd/system/borgbackup-home.timer"
  local dir_borg_service="/etc/systemd/system/borgbackup-home.service"
  
  local borg_script_file="./configs/borg/home-borgbackup.sh"
  local borg_timer_file="./configs/borg/borgbackup-home.timer"
  local borg_service_file="./configs/borg/borgbackup-home.service"

  # check opt/borg directory
  if [ ! -d /opt/borg ]; then
    log_debug "Creating /opt/borg directory..."
    sudo mkdir -p /opt/borg
  fi
  
  # copy script to /opt/borg
  if [ ! -f /opt/borg/home-borgbackup.sh ]; then
    log_debug "Copying home-borgbackup.sh to /opt/borg..."
    if ! sudo cp "$borg_script_file" "$dir_borg_script"; then
      log_error "Failed to copy home-borgbackup.sh to /opt/borg"
      return 1
    fi
  else
    log_debug "home-borgbackup.sh already exists in /opt/borg"
  fi

  # check if borgbackup is installed
  if ! command -v borg &>/dev/null; then
    log_debug "Borgbackup is not installed, installing..."
    if ! sudo dnf install -y borgbackup; then
      log_error "Failed to install Borgbackup"
      return 1
    fi
  else
    log_debug "Borgbackup is already installed"
  fi

  # cp timer, service
  if ! sudo cp "$borg_service_file" "$dir_borg_service"; then
    log_error "Failed to copy borgbackup service file"
    return 1
  fi

  if ! sudo cp "$borg_timer_file" "$dir_borg_timer"; then
    log_error "Failed to copy borgbackup timer file"
    return 1
  fi

  # enable and start timer
  log_debug "Enabling and starting borgbackup timer..."
  if ! sudo systemctl enable --now borgbackup.timer; then
    log_error "Failed to enable and start borgbackup timer"
    return 1
  fi

  # end if everything is ok
  log_info "Borgbackup setup completed successfully"
  log_debug "Borgbackup timer is enabled and started"
}