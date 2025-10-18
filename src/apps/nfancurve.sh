#!/usr/bin/env bash
#TEST: Needed
nfancurve_setup() {
  # send sh script to /opt/nfancurve/temp.sh
  log_info "Sending nfancurve setup script to /opt/nfancurve/temp.sh..."

  # dirs to sends
  local dir_script="/opt/nfancurve/temp.sh"
  local dir_service="/etc/systemd/system/nfancurve.service"
  local dir_config="/opt/nfancurve/config"

  # files on the repo going to copied
  local nfancurve_config_file="./configs/nfancurve/config"
  local nfancurve_script_file="./configs/nfancurve/temp.sh"
  local nfancurve_service="./configs/nfancurve/nfancurve.service"

  # check opt/nfancurve directory
  if [ ! -d /opt/nfancurve ]; then
    log_debug "Creating /opt/nfancurve directory..."
    sudo mkdir -p /opt/nfancurve
  fi

  # copy script to /opt/nfancurve
  if [ ! -f /opt/nfancurve/temp.sh ]; then
    log_debug "Copying temp.sh to /opt/nfancurve..."
    if ! sudo cp "$nfancurve_script_file" "$dir_script"; then
      log_error "Failed to copy temp.sh to /opt/nfancurve"
      return 1
    fi
  else
    log_debug "temp.sh already exists in /opt/nfancurve"
  fi
  
  # copy config to /opt/nfancurve/config
  if [ ! -f /opt/nfancurve/config ]; then
    log_debug "Copying config to /opt/nfancurve/config..."
    if ! sudo cp "$nfancurve_config_file" "$dir_config"; then
      log_error "Failed to copy config to /opt/nfancurve/config"
      return 1
    fi
  else
    log_debug "temp.sh already exists in /opt/nfancurve"
  fi

  # cp service
  if ! sudo cp "$nfancurve_service" "$dir_service"; then
    log_error "Failed to copy nfancurve service file"
    return 1
  fi

  # enable service
  log_debug "Enabling nfancurve service..."
  if ! sudo systemctl enable --now nfancurve.service; then
    log_error "Failed to enable nfancurve service"
    return 1
  fi

  # end if everything is ok
  log_info "nfancurve setup completed successfully"
}

