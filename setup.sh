#!/usr/bin/env bash
# Author: Serif Cyber-Syntax
# License: BSD 3-Clause
# Comprehensive installation and configuration script
#for sudo dnf-based systems.

# Prevents the script from continuing on errors, unset variables, and pipe failures.
set -euo pipefail
IFS=$'\n\t'

#!/usr/bin/env bash

# Setup XDG Base Directory paths if not already set
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"

# Source core modules in strict order (dependencies matter)
source src/core/logging.sh
source src/utils/string_utils.sh
source src/core/distro_detection.sh
source src/core/package_manager.sh
source src/core/package_mapping.sh
source src/core/repository_manager.sh
source src/core/config.sh
source src/core/install_packages.sh

# Initialize configuration and load variables
init_config

# Initialize package manager for detected distribution
init_package_manager || {
  log_error "Failed to initialize package manager"
  exit 1
}

# Auto-source all feature modules (order doesn't matter)
for module in src/apps/*.sh src/system/*.sh src/hardware/*.sh src/display/*.sh src/wm/*.sh; do
  [[ -f "$module" ]] && source "$module"
done

# Help message
usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

WARNING:
  I AM NOT RESPONSIBLE FOR ANY DAMAGE CAUSED BY THIS SCRIPT. USE AT YOUR OWN RISK.
  This script requires root privileges and may modify your system.

NOTE:
  Please edit your configuration files before running. See ~/.config/auto-penguin-setup/

This script automates installation and configuration for Fedora, Arch, and Debian/Ubuntu systems.

Options (A-Z):

  -h    Display this help message.

# Applications
  -A    Install application packages (apps/)
  -b    Install Brave Browser
  -B    Setup BorgBackup service
  -F    Install Flatpak packages
  -L    Install Lazygit
  -o    Install Ollama (AI runtime)
  -p    Install ProtonVPN and enable OpenVPN for SELinux
  -q    Install Qtile packages (window manager)
  -C    Install Visual Studio Code

# System
  -i    Install core packages
  -I    *WORK-IN-PROGRESS* Install system-specific packages (desktop/laptop)
  -D    Install development packages
  -G    Install games packages
  -f    Setup useful Linux configurations (boot timeout, TCP BBR, password timeout)
  -M    Set up default applications (mimeapps.list)
  -t    Setup trash-cli service
  -U    Switch UFW from firewalld and enable it
  -u    Run system updates (autoremove, fwupdmgr)
  -r    Enable RPM Fusion repositories
  -d    Speed up package manager (Parallel downloads etc.)
  -x    Swap ffmpeg-free with ffmpeg

# Hardware
  -E    Install auto-cpufreq (CPU frequency management)
  -T    Setup TLP for laptop power management
  -P    Setup thinkfan for laptop fan control
  -e    Setup Intel Xorg configuration (20-intel.conf)
  -z    Setup zenpower for Ryzen 5000 series
  -c    Setup touchpad (copy Xorg touchpad config)
  -n    Install NVIDIA CUDA
  -N    Switch to NVIDIA open drivers
  -j    Setup nfancurve for NVIDIA GPUs
  -v    Setup VA-API for NVIDIA RTX series

# Display & Window Manager
  -H    Install Hyprland Wayland compositor and dependencies
  -S    Switch to SDDM display manager (recommended for Hyprland)
  -X    Configure SDDM autologin (auto-login after boot)
  -Q    Install Qtile udev rule for xbacklight

# SSH Configuration
  -k    Setup SSH (automated from variables.ini)
  -K    Show SSH status

# Other / Experimental
  -a    Execute all functions (full setup)
  -g    Remove GNOME desktop environment (keep NetworkManager)
  -V    Setup virtualization (virt-manager, libvirt)
  -s    Enable Syncthing service
  -c    Enable tap-to-click for touchpad

Examples:
  Setup all:                 sudo $0 -a
  System-specific packages:   sudo $0 -I
  TLP for laptop:            sudo $0 -T
  Install Brave:             sudo $0 -b
  Install Qtile:             sudo $0 -q
  Setup SSH:                 sudo $0 -k
  Check SSH status:          sudo $0 -K

For more details, see docs/ and config_examples/.
EOF
  exit 1
}

# Check if any options that use DNF installation are enabled
#TODO: maybe we would simplify this, we can call speedup_pm.sh
# before anything else. So, we would handle it much more simple way
# because simple is better than complex.
needs_dnf_speedup() {
  # Return true if any of these options are enabled
  if $all_option ||
    $install_core_packages_option ||
    $install_system_specific_packages_option ||
    $install_app_packages_option ||
    $install_dev_packages_option ||
    $install_games_packages_option ||
    $qtile_option ||
    $brave_option ||
    $rpm_option ||
    $tlp_option ||
    $nvidia_cuda_option ||
    $switch_nvidia_open_option ||
    $virt_option ||
    $ufw_option ||
    $trash_cli_option ||
    $borgbackup_option ||
    $zenpower_option ||
    $vaapi_option ||
    $swap_ffmpeg_option ||
    $protonvpn_option ||
    $hyprland_option ||
    $sddm_option ||
    $sddm_autologin_option ||
    $ollama_option; then
    return 0 # true in bash
  fi
  return 1 # false in bash
}

#TODO: need cross-distro support
system_updates() {
  echo "Running system updates..."
  for attempt in {1..3}; do
    if sudo dnf autoremove -y; then
      break
    fi
    echo "Autoremove failed (attempt $attempt/3), retrying..."
    sleep $((attempt * 5))
  done || {
    echo "Failed to complete autoremove after 3 attempts"
    return 1
  }
  echo "System updates completed. (Review update logs for any errors.)"
}

setup_files() {
  #TODO: need to setup those function in options, temp for now
  grub_timeout
  # lightdm_autologin
  tcp_bbr_setup
  sudoers_setup
} 

#TODO: research and find a simple way to handle this options which it isn't look clean.
# Main function to parse arguments and execute tasks
main() {
  # Show help message if no arguments are provided or if -h is passed.
  if [[ "$#" -eq 1 && "$1" == "-h" ]]; then
    usage
  fi

  log_debug "Initializing script with args: $*"

  # Initialize option flags.
  all_option=false
  install_core_packages_option=false
  install_system_specific_packages_option=false
  install_app_packages_option=false
  install_dev_packages_option=false
  install_games_packages_option=false
  flatpak_option=false
  qtile_option=false
  brave_option=false
  rpm_option=false
  pm_speed_option=false
  swap_ffmpeg_option=false
  config_option=false
  lazygit_option=false
  ollama_option=false
  trash_cli_option=false
  borgbackup_option=false
  syncthing_option=false
  auto_cpufreq_option=false
  hyprland_option=false
  sddm_option=false
  ssh_setup_option=false
  ssh_status_option=false

  # New experimental option flags.
  ufw_option=false
  qtile_udev_option=false
  touchpad_option=false
  intel_option=false
  thinkfan_option=false
  tlp_option=false
  remove_gnome_option=false
  zenpower_option=false
  switch_nvidia_open_option=false
  nvidia_cuda_option=false
  vaapi_option=false
  protonvpn_option=false
  update_system_option=false
  virt_option=false
  install_vscode_option=false
  setup_default_applications_option=false
  sddm_autologin_option=false
  nfancurve_option=false

  # Process command-line options.
  while getopts "abBcdDEeFfGghHIiAalLjkKnNopPrstTuUvVzqQxCMSX" opt; do
    case $opt in
      a) all_option=true ;;
      A) install_app_packages_option=true ;;
      D) install_dev_packages_option=true ;;
      G) install_games_packages_option=true ;;
      b) brave_option=true ;;
      B) borgbackup_option=true ;;
      c) touchpad_option=true ;;
      e) intel_option=true ;;
      H) hyprland_option=true ;;
      i) install_core_packages_option=true ;;
      I) install_system_specific_packages_option=true ;;
      s) syncthing_option=true ;;
      S) sddm_option=true ;;
      X) sddm_autologin_option=true ;;
      d) pm_speed_option=true ;;
      V) virt_option=true ;;
      F) flatpak_option=true ;;
      f) config_option=true ;;
      L) lazygit_option=true ;;
      q) qtile_option=true ;;
      Q) qtile_udev_option=true ;;
      r) rpm_option=true ;;
      x) swap_ffmpeg_option=true ;;
      o) ollama_option=true ;;
      g) remove_gnome_option=true ;;
      n) nvidia_cuda_option=true ;;
      N) switch_nvidia_open_option=true ;;
      v) vaapi_option=true ;;
      p) protonvpn_option=true ;;
      P) thinkfan_option=true ;;
      t) trash_cli_option=true ;;
      T) tlp_option=true ;;
      u) update_system_option=true ;;
      U) ufw_option=true ;;
      z) zenpower_option=true ;;
      C) install_vscode_option=true ;;
      M) setup_default_applications_option=true ;;
      E) auto_cpufreq_option=true ;;
      j) nfancurve_option=true ;;
      k) ssh_setup_option=true ;;
      K) ssh_status_option=true ;;
      h) usage ;;
      *) usage ;;
    esac
  done

  # If no optional flags were provided, show usage and exit.
  if [[ "$all_option" == "false" ]] &&
    [[ "$install_core_packages_option" == "false" ]] &&
    [[ "$install_system_specific_packages_option" == "false" ]] &&
    [[ "$install_app_packages_option" == "false" ]] &&
    [[ "$install_dev_packages_option" == "false" ]] &&
    [[ "$install_games_packages_option" == "false" ]] &&
    [[ "$flatpak_option" == "false" ]] &&
    [[ "$borgbackup_option" == "false" ]] &&
    [[ "$touchpad_option" == "false" ]] &&
    [[ "$trash_cli_option" == "false" ]] &&
    [[ "$tlp_option" == "false" ]] &&
    [[ "$thinkfan_option" == "false" ]] &&
    [[ "$syncthing_option" == "false" ]] &&
    [[ "$qtile_option" == "false" ]] &&
    [[ "$intel_option" == "false" ]] &&
    [[ "$qtile_udev_option" == "false" ]] &&
    [[ "$brave_option" == "false" ]] &&
    [[ "$rpm_option" == "false" ]] &&
    [[ "$pm_speed_option" == "false" ]] &&
    [[ "$swap_ffmpeg_option" == "false" ]] &&
    [[ "$config_option" == "false" ]] &&
    [[ "$lazygit_option" == "false" ]] &&
    [[ "$ollama_option" == "false" ]] &&
    [[ "$remove_gnome_option" == "false" ]] &&
    [[ "$zenpower_option" == "false" ]] &&
    [[ "$nvidia_cuda_option" == "false" ]] &&
    [[ "$switch_nvidia_open_option" == "false" ]] &&
    [[ "$vaapi_option" == "false" ]] &&
    [[ "$protonvpn_option" == "false" ]] &&
    [[ "$ufw_option" == "false" ]] &&
    [[ "$update_system_option" == "false" ]] &&
    [[ "$virt_option" == "false" ]] &&
    [[ "$install_vscode_option" == "false" ]] &&
    [[ "$hyprland_option" == "false" ]] &&
    [[ "$sddm_option" == "false" ]] &&
    [[ "$sddm_autologin_option" == "false" ]] &&
    [[ "$auto_cpufreq_option" == "false" ]] &&
    [[ "$setup_default_applications_option" == "false" ]] &&
    [[ "$nfancurve_option" == "false" ]] &&
    [[ "$ssh_setup_option" == "false" ]] &&
    [[ "$ssh_status_option" == "false" ]]; then
    log_warn "No options specified"
    usage
  fi

  # Display detected distribution and system information
  local distro_name
  distro_name=$(get_distro_pretty_name)
  log_info "==========================================="
  log_info "Distribution: $distro_name"
  log_info "Distro Family: $CURRENT_DISTRO"
  
  #TODO: device detection desktop, laptop need better logic than hostname.
  # system_type=$(detect_system_type)
  # log_info "Device Type: $system_type"
  # log_info "==========================================="

  local need_core_packages=false
  #TESTING: new options lazygit,ufw and add more if needed
  if $all_option || $qtile_option || $trash_cli_option || $borgbackup_option || $syncthing_option || $ufw_option || $lazygit_option || $virt_option; then
    need_core_packages=true
    log_debug "Core packages are needed due to selected options"
  fi

  # Apply package manager speedup if any options requiring package installation are enabled
  #TODO: we don't need to speedup, for simplicity we let user to call it with command line argument.
  # if needs_dnf_speedup; then
  #   log_info "Optimizing package manager configuration for faster package operations..."
  #   speed_up_package_manager || log_warn "Failed to optimize package manager configuration"
  # fi

  # Install core packages.
  if $need_core_packages; then
    install_core_packages
  fi

  #TODO: currently we don't use this logic anymore
  # We need a better logic for this, we might be use functions to handle this or
  # completely new feature the handle device specific options.
  # # If laptop or desktop option is selected, install system-specific packages.
  # if $tlp_option || $thinkfan_option || $install_system_specific_packages_option; then
  #   install_system_specific_packages "$system_type"
  # fi

  # if $nvidia_cuda_option || $switch_nvidia_open_option || $vaapi_option || $borgbackup_option; then
  #   install_system_specific_packages "$system_type"
  # fi

  # Handle all_option logic
  if $all_option; then
    log_info "Executing all additional functions..."

    # Install all package types
    install_core_packages
    install_app_packages
    install_dev_packages
    install_games_packages
    install_system_specific_packages "$system_type"

    # System-specific additional functions.
    #NOTE: This starts first to make sure hostname is changed first
    if [[ "$system_type" == "laptop" ]]; then
      log_info "Executing laptop-specific functions..."
      #TODO: are we sure we want to call this every time?
      # laptop_hostname_change
      tlp_setup
      thinkfan_setup
      touchpad_setup
      xorg_setup_intel
    elif [[ "$system_type" == "desktop" ]]; then
      log_info "Executing desktop-specific functions..."
      # Desktop-specific functions could be added here.
      switch_nvidia_open
      nvidia_cuda_setup
      vaapi_setup
      borgbackup_setup
      nfancurve_setup
      # zenpower_setup #WARN: is it safe?
    fi

    enable_rpm_fusion
    install_qtile_packages
    setup_qtile_backlight_rules
    ffmpeg_swap
    setup_files
    switch_ufw_setup

    # nopasswdlogin_group
    # services
    syncthing_setup
    trash_cli_setup

    # app installations
    install_brave
    install_lazygit
    install_protonvpn
    install_flatpak_packages
    setup_default_applications

  else
    log_info "Executing selected additional functions..."
    if $ufw_option; then switch_ufw_setup; fi
    if $lazygit_option; then install_lazygit; fi
    if $install_core_packages_option; then install_core_packages; fi
    if $install_app_packages_option; then install_app_packages; fi
    if $install_dev_packages_option; then install_dev_packages; fi
    if $install_games_packages_option; then install_games_packages; fi
    if $install_system_specific_packages_option; then install_system_specific_packages "$system_type"; fi
    if $touchpad_option; then touchpad_setup; fi
    if $intel_option; then xorg_setup_intel; fi
    if $flatpak_option; then install_flatpak_packages; fi
    if $qtile_option; then install_qtile_packages; fi
    if $qtile_udev_option; then setup_qtile_backlight_rules; fi
    if $brave_option; then install_brave; fi
    if $rpm_option; then enable_rpm_fusion; fi
    if $trash_cli_option; then trash_cli_setup; fi
    if $tlp_option; then tlp_setup; fi
    if $thinkfan_option; then thinkfan_setup; fi
    if $syncthing_option; then syncthing_setup; fi
    if $borgbackup_option; then borgbackup_setup; fi
    if $pm_speed_option; then speed_up_package_manager; fi
    if $swap_ffmpeg_option; then ffmpeg_swap; fi
    if $ollama_option; then install_ollama; fi
    if $config_option; then setup_files; fi
    if $remove_gnome_option; then remove_gnome; fi
    if $zenpower_option; then zenpower_setup; fi
    if $nvidia_cuda_option; then nvidia_cuda_setup; fi
    if $switch_nvidia_open_option; then switch_nvidia_open; fi
    if $vaapi_option; then vaapi_setup; fi
    if $protonvpn_option; then install_protonvpn; fi
    if $update_system_option; then system_updates; fi
    if $virt_option; then virt_manager_setup; fi
    if $install_vscode_option; then install_vscode; fi
    if $setup_default_applications_option; then setup_default_applications; fi
    if $auto_cpufreq_option; then install_auto_cpufreq; fi
    if $hyprland_option; then install_hyprland; fi
    if $sddm_option; then switch_to_sddm; fi
    if $sddm_autologin_option; then sddm_autologin; fi
    if $nfancurve_option; then nfancurve_setup; fi
    if $ssh_setup_option; then ssh_setup; fi
    if $ssh_status_option; then ssh_status; fi
  fi

  log_info "Script execution completed."
}

# Execute main with provided command-line arguments.
main "$@"
