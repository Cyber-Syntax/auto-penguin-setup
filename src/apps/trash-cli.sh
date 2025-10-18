#!/usr/bin/env bash

#TEST: Both desktop and laptop
trash_cli_setup() {
  log_info "Setting up trash-cli service..."

  local dir_trash_cli_service="/etc/systemd/system/trash-cli.service"
  local dir_trash_cli_timer="/etc/systemd/system/trash-cli.timer"
  local trash_cli_service_file="./configs/trash-cli/trash-cli.service"
  local trash_cli_timer_file="./configs/trash-cli/trash-cli.timer"

  # Create service file
  if ! sudo cp "$trash_cli_service_file" "$dir_trash_cli_service"; then
    log_error "Failed to copy trash-cli service file"
    return 1
  fi

  # Create timer file
  if ! sudo cp "$trash_cli_timer_file" "$dir_trash_cli_timer"; then
    log_error "Failed to copy trash-cli timer file"
    return 1
  fi

  log_info "Enabling trash-cli timer..."
  sudo systemctl daemon-reload
  sudo systemctl enable --now trash-cli.timer

  log_info "trash-cli service setup completed."
}
