#!/usr/bin/env bash

thinkfan_setup() {
  log_info "Setting up thinkfan for fan control..."

  local dir_thinkfan="/etc/thinkfan.conf"
  local thinkfan_file="./configs/thinkfan.conf"

  # Ensure package manager is initialized and try to install thinkfan when missing.
  # Uses the project's package manager abstraction which supports AUR and COPR via
  # pm_install, init_package_manager, pm_is_installed, and distro detection helpers.
  if source src/core/package_manager.sh >/dev/null 2>&1 && init_package_manager; then
    # pm_is_installed returns 0 when installed
    if ! pm_is_installed thinkfan; then
      log_info "thinkfan not installed — attempting to install for distro: ${CURRENT_DISTRO:-unknown}"
      if is_arch; then
        # On Arch, prefer installing from AUR (package manager abstraction understands AUR: prefix)
        if ! pm_install "AUR:thinkfan"; then
          log_error "Failed to install thinkfan from AUR"
          return 1
        fi
      else
        # Debian/Fedora should have thinkfan in official repos
        if ! pm_install thinkfan; then
          log_error "Failed to install thinkfan package from distro repositories"
          return 1
        fi
      fi
    else
      log_debug "thinkfan package already installed"
    fi
  else
    log_warn "Package manager initialization failed; skipping automatic installation. Ensure thinkfan is installed manually."
  fi

  # backup if there is no backup
  if [[ ! -f "/etc/thinkfan.conf.bak" ]]; then
    if ! sudo cp /etc/thinkfan.conf /etc/thinkfan.conf.bak; then
      log_warn "Failed to create backup of thinkfan configuration"
    fi
  fi

  # check thinkfan binary exists
  if ! command -v thinkfan >/dev/null 2>&1; then
    log_error "thinkfan binary not found after attempted installation. Please install thinkfan and try again."
    return 1
  fi

  if ! sudo cp "$thinkfan_file" "$dir_thinkfan"; then
    log_error "Failed to copy thinkfan configuration file"
    return 1
  fi

  # Modprobe thinkpad_acpi
  log_debug "Setting thinkpad_acpi module options..."
  if ! echo "options thinkpad_acpi fan_control=1 experimental=1" | sudo tee /etc/modprobe.d/thinkfan.conf >/dev/null; then
    log_error "Failed to create thinkpad_acpi options file"
    return 1
  fi

  if ! sudo modprobe -rv thinkpad_acpi; then
    log_warn "Failed to remove thinkpad_acpi module"
  fi

  if ! sudo modprobe -v thinkpad_acpi; then
    log_warn "Failed to load thinkpad_acpi module"
  fi

  log_info "Enabling and starting thinkfan services..."
  sudo systemctl enable --now thinkfan || log_warn "Failed to enable and start thinkfan service"
  sudo systemctl enable thinkfan-sleep || log_warn "Failed to enable thinkfan-sleep service"
  sudo systemctl enable thinkfan-wakeup || log_warn "Failed to enable thinkfan-wakeup service"

  # thinkfan sleep hack for 100% fan usage on suspend
  local thinkfan_sleep_hack="/etc/systemd/system/thinkfan-sleep-hack.service"
  log_debug "Creating thinkfan sleep hack service at $thinkfan_sleep_hack..."

  cat <<EOF | sudo tee "$thinkfan_sleep_hack" >/dev/null
[Unit]
Description=Set fan to auto so BIOS can shut off fan during S2 sleep
Before=sleep.target
After=thinkfan-sleep.service

[Service]
Type=oneshot
ExecStart=/usr/bin/logger -t '%N' "Setting /proc/acpi/ibm/fan to 'level auto'"
ExecStart=/usr/bin/bash -c '/usr/bin/echo "level auto" > /proc/acpi/ibm/fan'

[Install]
WantedBy=sleep.target
EOF

  local service_create_status=$?
  if [[ $service_create_status -ne 0 ]]; then
    log_error "Failed to create thinkfan-sleep-hack service file"
    return 1
  fi

  log_info "Enabling thinkfan-sleep-hack service..."
  if ! sudo systemctl enable thinkfan-sleep-hack; then
    log_warn "Failed to enable thinkfan-sleep-hack service"
  fi

  log_info "Thinkfan setup completed successfully."
}

