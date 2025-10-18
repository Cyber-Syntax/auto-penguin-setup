#!/usr/bin/env bash

# Source guard to prevent re-sourcing
[[ -n "${_ARCH_SOURCED:-}" ]] && return 0
readonly _ARCH_SOURCED=1

# AUR Helper Installation for Arch Linux
# Purpose: Ensure an AUR helper (paru/yay) is available
# Strategy: Use pre-compiled paru-bin to avoid memory issues during compilation

# Check if an AUR helper is installed, install paru-bin if missing
is_aur_helper_installed() {
  if command -v paru &>/dev/null || command -v yay &>/dev/null; then
    log_info "AUR helper (paru/yay) is already installed."
    return 0
  else
    log_warn "No AUR helper found. Installing 'paru-bin'..."
    if install_paru_helper; then
      log_success "paru installed successfully."
      return 0
    else
      log_error "Failed to install paru. Please install an AUR helper manually."
      return 1
    fi
  fi
}

# Install paru-bin AUR helper (pre-compiled binary)
# Uses /opt to avoid tmpfs memory limitations
install_paru_helper() {
  log_info "Installing paru AUR helper..."

  # Early exit if already installed
  if command -v paru &>/dev/null; then
    log_info "paru is already installed."
    return 0
  fi

  # Install build dependencies
  log_info "Installing build dependencies..."
  if ! sudo pacman -S --needed --noconfirm base-devel git; then
    log_error "Failed to install build dependencies"
    return 1
  fi

  # Use /opt directory to avoid /tmp tmpfs memory issues
  local build_dir="/opt/paru-bin"

  # Clean up any previous installation attempts
  if [[ -d "$build_dir" ]]; then
    log_info "Cleaning up previous build directory..."
    sudo rm -rf "$build_dir"
  fi

  # Clone paru-bin (pre-compiled) instead of paru (source build)
  log_info "Cloning paru-bin repository..."
  if ! sudo git clone https://aur.archlinux.org/paru-bin.git "$build_dir"; then
    log_error "Failed to clone paru-bin repository"
    return 1
  fi

  # Set ownership to current user for makepkg (cannot run as root)
  log_info "Setting directory permissions..."
  if ! sudo chown -R "$USER:$USER" "$build_dir"; then
    log_error "Failed to set directory ownership"
    sudo rm -rf "$build_dir"
    return 1
  fi

  # Build and install paru
  log_info "Building and installing paru..."
  if ! (cd "$build_dir" && makepkg -si --noconfirm); then
    log_error "Failed to build and install paru"
    sudo rm -rf "$build_dir"
    return 1
  fi

  # Clean up build directory
  log_info "Cleaning up build directory..."
  sudo rm -rf "$build_dir"

  # Verify installation
  if command -v paru &>/dev/null; then
    log_success "paru installed successfully"
    return 0
  else
    log_error "paru installation verification failed"
    return 1
  fi
}
