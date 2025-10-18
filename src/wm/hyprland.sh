#!/usr/bin/env bash

# Function: install_hyprland
# Purpose: Installs Hyprland Wayland compositor and its dependencies
install_hyprland() {
  log_info "Installing Hyprland and dependencies..."

  # # Add COPR repository for Hyprland
  #TODO: this is for faster updates and newer packages
  # but it is might be unstable, add here a approve from user
  # to choose if he wants to add the repo or not
  # log_info "Adding Hyprland COPR repository..."
  # if ! sudo dnf copr enable solopasha/hyprland -y; then
  #   log_error "Failed to add Hyprland COPR repository"
  #   return 1
  # fi

  # Core Hyprland packages
  local hypr_packages=(
    "hyprland"      # The Hyprland compositor
    "waybar"        # Status bar for Wayland
    "dunst"         # Notification daemon
    "gammastep"     # Color temperature adjustment
    "blueman"       # Bluetooth manager
    "swaybg"        # Setting up wallpaper
    "wl-clipboard"  # Wayland clipboard utilities
    "swaylock"      # Lockscreen
    "swayidle"      # Idle management daemon
    "wlr-randr"     # Xrandr clone for wlroots compositors
    "wev"           # Wayland event viewer
    "brightnessctl" # Brightness control
    "grim"          # Screenshots
    "slurp"         # Selection tool for screenshots
    "rofi"          # Application launcher
    "sddm"          # Display manager
  )

  # Install Hyprland and related packages
  log_info "Installing Hyprland and essential packages..."
  if ! sudo dnf install -y "${hypr_packages[@]}"; then
    log_error "Failed to install Hyprland packages"
    return 1
  fi

  # # Installing grimblast (screenshot utility)
  # log_info "Installing grimblast for screenshots..."
  # if ! sudo dnf copr enable agriffis/sway-extras -y; then
  #   log_warn "Failed to enable sway-extras COPR repository for grimblast"
  # else
  #   if ! sudo dnf install -y grimblast; then
  #     log_warn "Failed to install grimblast. You may need to install it manually."
  #   fi
  # fi

  # # Install cliphist (clipboard manager)
  # log_info "Installing cliphist (clipboard manager)..."
  # if ! command -v go &>/dev/null; then
  #   sudo dnf install -y golang
  # fi

  # # Using go install for cliphist
  # if ! go install github.com/sentriz/cliphist@latest; then
  #   log_warn "Failed to install cliphist. Make sure Go is properly configured."
  # fi

  log_info "Hyprland installation completed."
  log_warn "IMPORTANT: You should switch to SDDM and exit your current desktop environment to use Hyprland."
  log_info "Run the script with -S option to switch to SDDM after you've exited your desktop environment."

  return 0
}

