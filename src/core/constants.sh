#!/usr/bin/env bash
# Description: Constants for auto-penguin-setup cli script

#TODO: currently not used, we might migrate constants here in future

# # Default directories (can be overridden by the test harness)
# # REPO_DIR is set dynamically based on detected distribution
# USER_HOME="${USER_HOME:-$HOME}"
# USER_DESKTOP_DIR="${USER_DESKTOP_DIR:-$USER_HOME/.local/share/applications}"
# # Parameterize the location of the system desktop file
# DESKTOP_SYSTEM_FILE="${DESKTOP_SYSTEM_FILE:-/usr/share/applications/brave-browser.desktop}"

# # Directly load variables from variables.json in XDG config directory
# # Using apps_* prefix to avoid conflicts with readonly variables from config.sh
# apps_xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
# apps_config_dir="$apps_xdg_config/auto-penguin-setup"
# apps_variables_file="$apps_config_dir/variables.json"

# # Function to get distro-specific repo directory
# get_repo_dir() {
#   local distro
#   distro=$(detect_distro 2>/dev/null) || distro="unknown"
  
#   case "$distro" in
#     fedora)
#       echo "/etc/yum.repos.d"
#       ;;
#     arch)
#       echo "/etc/pacman.d"
#       ;;
#     debian)
#       echo "/etc/apt/sources.list.d"
#       ;;
#     *)
#       echo "/etc/yum.repos.d"  # Fallback default
#       ;;
#   esac
# }

# # Set REPO_DIR if not already set (for test harness compatibility)
# REPO_DIR="${REPO_DIR:-$(get_repo_dir)}"