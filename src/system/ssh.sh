#!/usr/bin/env bash
# Author: Serif Cyber-Syntax
# License: BSD 3-Clause
# SSH Automated Setup - Simplified implementation for power users
# Provides passwordless SSH authentication across multiple devices
# Uses Ed25519 keys (modern, secure default)
# Dependencies: logging.sh, config.sh, distro_detection.sh

#TODO: simplify and test

# Source guard to prevent re-sourcing
[[ -n "${_SSH_SOURCED:-}" ]] && return 0
readonly _SSH_SOURCED=1

# ====================
# Configuration Loading
# ====================

# Function: load_ssh_config
# Purpose: Load SSH configuration from variables.ini
# Sets: SSH_PORT, SSH_ENABLE_SERVICE, SSH_PASSWORD_AUTH, SSH_PERMIT_ROOT_LOGIN, SSH_KEY_AUTH
# Sets: SSH_CURRENT_DEVICE, SSH_DEVICES (associative array), SSH_TARGETS (array)
# Returns: 0 on success, 1 on failure
load_ssh_config() {
  log_debug "Loading SSH configuration from variables.ini"

  # Load basic SSH settings with defaults
  SSH_PORT="${ssh_port:-22}"
  SSH_ENABLE_SERVICE="${ssh_enable_service:-true}"
  SSH_PASSWORD_AUTH="${ssh_password_auth:-no}"
  SSH_PERMIT_ROOT_LOGIN="${ssh_permit_root_login:-no}"
  SSH_KEY_AUTH="${ssh_key_auth:-yes}"
  SSH_CURRENT_DEVICE="${current_device:-}"

  # Validate current_device is set
  if [[ -z "$SSH_CURRENT_DEVICE" ]]; then
    log_error "current_device not set in [system] section of variables.ini"
    return 1
  fi

  log_debug "SSH config loaded: port=$SSH_PORT, service=$SSH_ENABLE_SERVICE, current_device=$SSH_CURRENT_DEVICE"
  return 0
}

# Function: validate_ssh_config
# Purpose: Validate SSH configuration (check IPs, ports, current_device)
# Returns: 0 on success, 1 on failure
validate_ssh_config() {
  log_debug "Validating SSH configuration"

  # Check port is numeric and in valid range
  if ! [[ "$SSH_PORT" =~ ^[0-9]+$ ]] || [ "$SSH_PORT" -lt 1 ] || [ "$SSH_PORT" -gt 65535 ]; then
    log_error "Invalid SSH port: $SSH_PORT (must be 1-65535)"
    return 1
  fi

  # Check boolean values
  if [[ ! "$SSH_ENABLE_SERVICE" =~ ^(true|false|yes|no)$ ]]; then
    log_error "Invalid ssh.enable_service value: $SSH_ENABLE_SERVICE (must be true/false/yes/no)"
    return 1
  fi

  if [[ ! "$SSH_PASSWORD_AUTH" =~ ^(yes|no)$ ]]; then
    log_error "Invalid ssh.password_auth value: $SSH_PASSWORD_AUTH (must be yes/no)"
    return 1
  fi

  log_debug "SSH configuration validated successfully"
  return 0
}

# ====================
# SSH Service Management
# ====================

# Function: get_ssh_service_name
# Purpose: Cross-distro SSH service detection
# Returns: Prints "sshd" (Fedora/Arch) or "ssh" (Debian/Ubuntu)
# Exit code: 0 on success, 1 if service cannot be determined
get_ssh_service_name() {
  case "$CURRENT_DISTRO" in
    fedora | arch)
      echo "sshd"
      ;;
    debian)
      echo "ssh"
      ;;
    *)
      # Fallback detection
      if systemctl list-unit-files 2>/dev/null | grep -q "^sshd.service"; then
        echo "sshd"
      elif systemctl list-unit-files 2>/dev/null | grep -q "^ssh.service"; then
        echo "ssh"
      else
        log_error "Could not detect SSH service name for distribution: $CURRENT_DISTRO"
        return 1
      fi
      ;;
  esac
}

# Function: ensure_ssh_service_running
# Purpose: Start and enable SSH service if enable_service=true
# Returns: 0 on success, 1 on failure
ensure_ssh_service_running() {
  local ssh_service
  ssh_service=$(get_ssh_service_name) || return 1

  # Convert enable_service to boolean
  local enable_svc=false
  if [[ "$SSH_ENABLE_SERVICE" =~ ^(true|yes)$ ]]; then
    enable_svc=true
  fi

  if ! $enable_svc; then
    log_debug "SSH service not enabled (enable_service=$SSH_ENABLE_SERVICE), skipping"
    return 0
  fi

  log_info "Ensuring SSH service ($ssh_service) is running..."

  # Enable and start service
  if ! sudo systemctl enable --now "$ssh_service" 2>/dev/null; then
    log_error "Failed to enable and start SSH service: $ssh_service"
    return 1
  fi

  log_info "SSH service ($ssh_service) is running"
  return 0
}

# Function: configure_sshd_security
# Purpose: Configure SSH daemon security settings using drop-in config
# Creates: /etc/ssh/sshd_config.d/50-autopenguin.conf
# Returns: 0 on success, 1 on failure
configure_sshd_security() {
  log_info "Configuring SSH security settings..."

  local sshd_config_dir="/etc/ssh/sshd_config.d"
  local config_file="$sshd_config_dir/50-autopenguin.conf"

  # Create directory if it doesn't exist
  if [[ ! -d "$sshd_config_dir" ]]; then
    log_debug "Creating SSH drop-in config directory: $sshd_config_dir"
    sudo mkdir -p "$sshd_config_dir" || {
      log_error "Failed to create $sshd_config_dir"
      return 1
    }
  fi

  # Create drop-in configuration
  log_debug "Writing SSH configuration to $config_file"
  sudo tee "$config_file" >/dev/null <<EOF
# auto-penguin-setup SSH configuration
# Generated on $(date)

# Port configuration
Port $SSH_PORT

# Authentication
PasswordAuthentication $SSH_PASSWORD_AUTH
PubkeyAuthentication $SSH_KEY_AUTH
PermitRootLogin $SSH_PERMIT_ROOT_LOGIN
PermitEmptyPasswords no

# Security hardening
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

  if [[ $? -ne 0 ]]; then
    log_error "Failed to write SSH configuration file"
    return 1
  fi

  log_info "SSH security configuration written to $config_file"
  return 0
}

# Function: reload_sshd_config
# Purpose: Reload SSH daemon to apply configuration changes
# Returns: 0 on success, 1 on failure
reload_sshd_config() {
  local ssh_service
  ssh_service=$(get_ssh_service_name) || return 1

  log_info "Reloading SSH service to apply configuration..."

  if ! sudo systemctl reload "$ssh_service" 2>/dev/null; then
    log_warn "Reload failed, attempting restart..."
    if ! sudo systemctl restart "$ssh_service" 2>/dev/null; then
      log_error "Failed to reload/restart SSH service: $ssh_service"
      return 1
    fi
  fi

  log_info "SSH configuration reloaded successfully"
  return 0
}

# ====================
# SSH Key Management (Ed25519 only)
# ====================

# Function: create_ssh_keys
# Purpose: Create Ed25519 SSH keys if they don't exist
# Location: ~/.ssh/id_ed25519{,.pub}
# Returns: 0 on success, 1 on failure
create_ssh_keys() {
  local key_path="$HOME/.ssh/id_ed25519"
  local pub_key_path="$key_path.pub"

  if [[ -f "$key_path" ]] && [[ -f "$pub_key_path" ]]; then
    log_debug "Ed25519 SSH keys already exist at $key_path"
    return 0
  fi

  log_info "Generating Ed25519 SSH keys..."

  # Create .ssh directory if it doesn't exist
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"

  # Generate Ed25519 key with no passphrase (automated setup)
  if ! ssh-keygen -t ed25519 -f "$key_path" -N "" -C "auto-penguin-setup@$(hostname)" >/dev/null 2>&1; then
    log_error "Failed to generate Ed25519 SSH keys"
    return 1
  fi

  # Set proper permissions
  chmod 600 "$key_path"
  chmod 644 "$pub_key_path"

  log_info "Ed25519 SSH keys generated successfully at $key_path"
  return 0
}

# Function: get_ssh_key_path
# Purpose: Get the path to the Ed25519 public key
# Returns: Prints path to public key
get_ssh_key_path() {
  echo "$HOME/.ssh/id_ed25519.pub"
}

# Function: check_ssh_keys_exist
# Purpose: Check if Ed25519 SSH keys exist
# Returns: 0 if keys exist, 1 otherwise
check_ssh_keys_exist() {
  local key_path="$HOME/.ssh/id_ed25519"
  local pub_key_path="$key_path.pub"

  if [[ -f "$key_path" ]] && [[ -f "$pub_key_path" ]]; then
    return 0
  else
    return 1
  fi
}

# ====================
# SSH Key Exchange
# ====================

# Function: parse_remote_host
# Purpose: Parse user@ip:port format into components
# Arguments: $1 = user@ip:port string
# Exports: REMOTE_USER, REMOTE_IP, REMOTE_PORT
# Returns: 0 on success, 1 on parse failure
parse_remote_host() {
  local host_string="$1"

  # Parse user@ip:port
  if [[ "$host_string" =~ ^([^@]+)@([^:]+):([0-9]+)$ ]]; then
    REMOTE_USER="${BASH_REMATCH[1]}"
    REMOTE_IP="${BASH_REMATCH[2]}"
    REMOTE_PORT="${BASH_REMATCH[3]}"
  else
    log_error "Invalid host format: $host_string (expected user@ip:port)"
    return 1
  fi

  export REMOTE_USER REMOTE_IP REMOTE_PORT
  log_debug "Parsed remote host: user=$REMOTE_USER, ip=$REMOTE_IP, port=$REMOTE_PORT"
  return 0
}

# Function: check_host_reachable
# Purpose: Check if remote host is reachable on specified port
# Arguments: $1 = ip, $2 = port
# Returns: 0 if reachable, 1 otherwise
check_host_reachable() {
  local ip="$1"
  local port="$2"
  local timeout=3

  log_debug "Checking if $ip:$port is reachable..."

  # Use nc (netcat) for connectivity test with timeout
  if command -v nc >/dev/null 2>&1; then
    if nc -z -w "$timeout" "$ip" "$port" >/dev/null 2>&1; then
      log_debug "Host $ip:$port is reachable"
      return 0
    fi
  elif command -v timeout >/dev/null 2>&1; then
    # Fallback: use timeout with bash /dev/tcp
    if timeout "$timeout" bash -c "cat < /dev/null > /dev/tcp/$ip/$port" 2>/dev/null; then
      log_debug "Host $ip:$port is reachable"
      return 0
    fi
  else
    log_warn "Neither 'nc' nor 'timeout' available, skipping connectivity check"
    return 0 # Assume reachable if we can't test
  fi

  log_debug "Host $ip:$port is not reachable"
  return 1
}

# Function: copy_key_to_remote
# Purpose: Copy Ed25519 public key to remote host using ssh-copy-id
# Arguments: $1 = device_name (from ssh_devices section)
# Returns: 0 on success, 1 on failure
copy_key_to_remote() {
  local device_name="$1"
  local device_config
  local ssh_key_path

  # Get device configuration from INI
  device_config=$(get_ini_value "ssh_devices" "$device_name")
  if [[ -z "$device_config" ]]; then
    log_error "Device '$device_name' not found in [ssh_devices] section"
    return 1
  fi

  # Parse remote host details
  parse_remote_host "$device_config" || return 1

  # Check if host is reachable
  if ! check_host_reachable "$REMOTE_IP" "$REMOTE_PORT"; then
    log_warn "Host $device_name ($REMOTE_IP:$REMOTE_PORT) is not reachable, skipping"
    return 1
  fi

  # Get SSH key path
  ssh_key_path=$(get_ssh_key_path)

  log_info "Copying SSH key to $device_name ($REMOTE_USER@$REMOTE_IP:$REMOTE_PORT)..."
  log_info "You may be prompted for password on the remote host"

  # Copy key using ssh-copy-id with custom port
  if ssh-copy-id -i "$ssh_key_path" -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_IP" 2>/dev/null; then
    log_info "SSH key copied successfully to $device_name"
    return 0
  else
    log_error "Failed to copy SSH key to $device_name"
    return 1
  fi
}

# Function: test_ssh_connection
# Purpose: Test passwordless SSH connection to remote host
# Arguments: $1 = device_name
# Returns: 0 on success (passwordless connection works), 1 on failure
test_ssh_connection() {
  local device_name="$1"
  local device_config

  # Get device configuration from INI
  device_config=$(get_ini_value "ssh_devices" "$device_name")
  if [[ -z "$device_config" ]]; then
    log_error "Device '$device_name' not found in [ssh_devices] section"
    return 1
  fi

  # Parse remote host details
  parse_remote_host "$device_config" || return 1

  log_debug "Testing SSH connection to $device_name..."

  # Test connection with passwordless authentication
  # Use -o BatchMode=yes to prevent password prompts
  # Use -o ConnectTimeout=5 for quick timeout
  if ssh -o BatchMode=yes -o ConnectTimeout=5 -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_IP" "exit" 2>/dev/null; then
    log_debug "SSH connection to $device_name successful (passwordless)"
    return 0
  else
    log_debug "SSH connection to $device_name failed (password required or unreachable)"
    return 1
  fi
}

# ====================
# Multi-Device Setup
# ====================

# Function: setup_ssh_for_all_targets
# Purpose: Read ssh_targets for current_device and copy keys to all targets
# Returns: 0 on success, 1 if no targets configured
setup_ssh_for_all_targets() {
  local targets_list
  local target_device
  local success_count=0
  local fail_count=0

  log_info "Setting up SSH keys for all target devices..."

  # Get targets for current device
  targets_list=$(get_ini_value "ssh_targets" "$SSH_CURRENT_DEVICE")

  if [[ -z "$targets_list" ]]; then
    log_warn "No SSH targets configured for device '$SSH_CURRENT_DEVICE' in [ssh_targets] section"
    return 1
  fi

  log_info "Targets for $SSH_CURRENT_DEVICE: $targets_list"

  # Split comma-separated list and process each target
  IFS=',' read -ra TARGETS <<<"$targets_list"
  for target_device in "${TARGETS[@]}"; do
    # Trim whitespace
    target_device=$(echo "$target_device" | xargs)

    log_info "Processing target: $target_device"

    if copy_key_to_remote "$target_device"; then
      ((success_count++))
    else
      ((fail_count++))
      log_warn "Skipping $target_device due to errors"
    fi
  done

  log_info "SSH key distribution complete: $success_count successful, $fail_count failed"

  if [[ $success_count -eq 0 ]]; then
    log_error "Failed to copy keys to any target device"
    return 1
  fi

  return 0
}

# Function: generate_ssh_config
# Purpose: Generate ~/.ssh/config from ssh_devices section
# Creates Host entries for easy connection (ssh <device_name>)
# Returns: 0 on success, 1 on failure
generate_ssh_config() {
  local ssh_config_file="$HOME/.ssh/config"
  local temp_config_file
  local device_name
  local device_config
  local backup_suffix

  log_info "Generating SSH client configuration..."

  # Create .ssh directory if it doesn't exist
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"

  # Backup existing config if it exists
  if [[ -f "$ssh_config_file" ]]; then
    backup_suffix=".bak.$(date +%Y%m%d%H%M%S)"
    log_debug "Backing up existing SSH config to $ssh_config_file$backup_suffix"
    cp "$ssh_config_file" "$ssh_config_file$backup_suffix"
  fi

  # Create temporary config file
  temp_config_file=$(mktemp) || {
    log_error "Failed to create temporary file for SSH config"
    return 1
  }

  # Write header
  cat >"$temp_config_file" <<EOF
# SSH Client Configuration
# Generated by auto-penguin-setup on $(date)
# Device: $SSH_CURRENT_DEVICE

# Default settings for all hosts
Host *
  ServerAliveInterval 60
  ServerAliveCountMax 3
  ControlMaster auto
  ControlPath ~/.ssh/control-%r@%h:%p
  ControlPersist 10m

# Auto-generated host entries from [ssh_devices]
EOF

  # Read all devices from ssh_devices section and generate Host entries
  # Get section content using get_ini_section (if available) or parse manually
  local variables_file="$XDG_CONFIG_HOME/auto-penguin-setup/variables.ini"

  if [[ ! -f "$variables_file" ]]; then
    log_error "Variables file not found: $variables_file"
    rm -f "$temp_config_file"
    return 1
  fi

  # Parse ssh_devices section manually
  local in_section=false
  while IFS='=' read -r key value; do
    # Remove leading/trailing whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)

    # Check for section header
    if [[ "$key" =~ ^\[([^\]]+)\]$ ]]; then
      local section_name="${BASH_REMATCH[1]}"
      if [[ "$section_name" == "ssh_devices" ]]; then
        in_section=true
      else
        in_section=false
      fi
      continue
    fi

    # Skip if not in ssh_devices section or empty line
    if ! $in_section || [[ -z "$key" ]] || [[ "$key" =~ ^# ]]; then
      continue
    fi

    # Parse device: key=device_name, value=user@ip:port
    device_name="$key"
    device_config="$value"

    # Parse user@ip:port
    if parse_remote_host "$device_config"; then
      cat >>"$temp_config_file" <<EOF

Host $device_name
  HostName $REMOTE_IP
  User $REMOTE_USER
  Port $REMOTE_PORT
  IdentityFile ~/.ssh/id_ed25519
EOF
      log_debug "Added SSH config entry for $device_name"
    else
      log_warn "Skipping invalid device config: $device_name=$device_config"
    fi
  done <"$variables_file"

  # Move temp file to final location
  mv "$temp_config_file" "$ssh_config_file" || {
    log_error "Failed to write SSH config file"
    rm -f "$temp_config_file"
    return 1
  }

  # Set proper permissions
  chmod 600 "$ssh_config_file"

  log_info "SSH config generated successfully at $ssh_config_file"
  return 0
}

# ====================
# Main Setup Functions
# ====================

# Function: ssh_setup
# Purpose: Main entry point - fully automated SSH setup
# Steps:
#   1. Load and validate config
#   2. Create keys if needed
#   3. Configure sshd security
#   4. Enable SSH service (if configured)
#   5. Copy keys to all targets
#   6. Generate ~/.ssh/config
#   7. Test all connections
# Returns: 0 on success, 1 on failure
ssh_setup() {
  log_info "=========================================="
  log_info "Starting SSH Automated Setup"
  log_info "=========================================="

  # 1. Load and validate configuration
  load_ssh_config || {
    log_error "Failed to load SSH configuration"
    return 1
  }

  validate_ssh_config || {
    log_error "SSH configuration validation failed"
    return 1
  }

  # 2. Create SSH keys if they don't exist
  if ! check_ssh_keys_exist; then
    create_ssh_keys || {
      log_error "Failed to create SSH keys"
      return 1
    }
  else
    log_info "Ed25519 SSH keys already exist, reusing them"
  fi

  # 3. Configure sshd security settings
  configure_sshd_security || {
    log_error "Failed to configure SSH security"
    return 1
  }

  # 4. Enable and start SSH service (if configured)
  ensure_ssh_service_running || {
    log_warn "SSH service not running (check configuration)"
  }

  # 5. Reload SSH configuration
  reload_sshd_config || {
    log_warn "Failed to reload SSH configuration"
  }

  # 6. Copy keys to all target devices
  setup_ssh_for_all_targets || {
    log_warn "Some targets failed (see above)"
  }

  # 7. Generate ~/.ssh/config
  generate_ssh_config || {
    log_error "Failed to generate SSH client configuration"
    return 1
  }

  # 8. Test all connections
  log_info "Testing SSH connections to all targets..."
  local targets_list
  targets_list=$(get_ini_value "ssh_targets" "$SSH_CURRENT_DEVICE")

  if [[ -n "$targets_list" ]]; then
    IFS=',' read -ra TARGETS <<<"$targets_list"
    for target_device in "${TARGETS[@]}"; do
      target_device=$(echo "$target_device" | xargs)
      if test_ssh_connection "$target_device"; then
        log_info "✓ $target_device - Connection OK"
      else
        log_warn "✗ $target_device - Connection failed (password may be required)"
      fi
    done
  fi

  log_info "=========================================="
  log_info "SSH Setup Complete"
  log_info "=========================================="
  return 0
}

# Function: ssh_status
# Purpose: Display SSH status and configuration
# Shows:
#   - Service status
#   - Key existence
#   - Configured targets
#   - Connection tests
# Returns: 0 always (informational only)
ssh_status() {
  log_info "=========================================="
  log_info "SSH Status"
  log_info "=========================================="

  # Load configuration
  load_ssh_config 2>/dev/null || {
    log_error "Failed to load SSH configuration"
    return 1
  }

  # 1. Service status
  local ssh_service
  ssh_service=$(get_ssh_service_name 2>/dev/null)
  if [[ -n "$ssh_service" ]]; then
    local service_status
    service_status=$(systemctl is-active "$ssh_service" 2>/dev/null || echo "inactive")
    log_info "SSH Service: $ssh_service ($service_status)"
  else
    log_warn "SSH Service: Not detected"
  fi

  # 2. SSH Port
  log_info "SSH Port: $SSH_PORT"

  # 3. Key existence
  if check_ssh_keys_exist; then
    local key_path="$HOME/.ssh/id_ed25519"
    log_info "SSH Keys: Ed25519 ($key_path)"
  else
    log_warn "SSH Keys: Not found (run 'setup.sh -s' to generate)"
  fi

  # 4. Current device
  log_info "Current Device: $SSH_CURRENT_DEVICE"

  # 5. Configured targets
  log_info ""
  log_info "Configured Targets:"
  local targets_list
  targets_list=$(get_ini_value "ssh_targets" "$SSH_CURRENT_DEVICE")

  if [[ -z "$targets_list" ]]; then
    log_warn "  No targets configured for $SSH_CURRENT_DEVICE"
  else
    IFS=',' read -ra TARGETS <<<"$targets_list"
    for target_device in "${TARGETS[@]}"; do
      target_device=$(echo "$target_device" | xargs)
      local device_config
      device_config=$(get_ini_value "ssh_devices" "$target_device")

      if [[ -n "$device_config" ]]; then
        if parse_remote_host "$device_config" 2>/dev/null; then
          # Test connection
          if test_ssh_connection "$target_device" 2>/dev/null; then
            log_info "  ✓ $target_device ($REMOTE_IP:$REMOTE_PORT) - Connection OK"
          else
            log_warn "  ✗ $target_device ($REMOTE_IP:$REMOTE_PORT) - Connection Failed"
          fi
        else
          log_warn "  ✗ $target_device - Invalid configuration"
        fi
      else
        log_warn "  ✗ $target_device - Not found in [ssh_devices]"
      fi
    done
  fi

  log_info "=========================================="
  return 0
}
