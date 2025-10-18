#!/usr/bin/env bash

# Source guard to prevent re-sourcing
[[ -n "${_UFW_SOURCED:-}" ]] && return 0
readonly _UFW_SOURCED=1

# Module documentation
# Purpose: Configure UFW (Uncomplicated Firewall) across distributions
# Dependencies: logging.sh
# Functions: switch_ufw_setup

# Function: switch_ufw_setup
# Purpose: Set up UFW firewall (disable firewalld if exists, then configure UFW)
# Returns: 0 on success, 1 on failure
#TESTING: Setup ufw is passed on Arch linux but needs
# more testing on other distros and edge cases.
switch_ufw_setup() {
  log_info "Setting up UFW firewall..."

  # Disable firewalld if it exists (Fedora/Debian may have it, Arch typically doesn't)
  if systemctl list-unit-files firewalld.service &>/dev/null; then
    log_info "Found firewalld, disabling it..."
    sudo systemctl disable --now firewalld 2>/dev/null || true
  fi

  # disable ufw first to avoid conflicts
  log_info "Disabling UFW if it's already enabled..."
  sudo ufw disable

  # Enable UFW service
  #TODO: are we need to enable systemctl or ufw enable is enough?
  # log_info "Enabling UFW service..."
  # if ! sudo systemctl enable --now ufw; then
  #   log_error "Failed to enable UFW service"
  #   return 1
  # fi

  # Set rate limit for SSH to prevent brute-force attacks
  sudo ufw limit 22/tcp

  # Configure default policies
  log_info "Configuring UFW policies and rules..."
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  # Allow internal SSH
  #
  #NOTE:  To lock this rule to SSH only, you’ll limit the 
  # proto (protocol) to tcp and then use the port parameter and set it to 22, SSH’s default port.
  # 
  # SSH itself does not natively support UDP for its core connection,
  # there are specific scenarios where UDP is involved; socat and netcat tunneling over UDP etc.--
  sudo ufw allow from 192.168.0.0/16 to any port 22 proto tcp

  # disable external SSH access
  sudo ufw deny ssh

  # Allow Syncthing ports
  #TODO: Research this, there was a package that handle this with group syncthing
  # we can allow syncthing if `sudo ufw app list` shows syncthing
  # otherwise, we can allow the ports manually. Decide which one is better.
  # sudo ufw allow "syncthing"
  sudo ufw allow 22000/tcp comment 'Syncthing'
  sudo ufw allow 21027/udp comment 'Syncthing'

  # Allow internal network
  #TESTING: testing is this internal only or 192.168.1.0/24?
  #TODO: what are the meaning for internal network allowance? (ollama access?)
  # better to be seperated?
  # TESTING: needs testing
  # sudo ufw allow from 192.168.0.0/16

  # Enable UFW
  sudo ufw enable

  log_info "UFW setup completed successfully"
  log_info "Check status with: sudo ufw status verbose"
  return 0
}

# Export function
export -f switch_ufw_setup
