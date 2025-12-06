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
source src/core/package_mapping.sh
source src/core/package_manager.sh
source src/core/repository_manager.sh
source src/core/config.sh
source src/core/install_packages.sh
source src/core/package_tracking.sh
source src/core/repo_migration.sh

# Initialize configuration and load variables
init_config

# Initialize package manager for detected distribution
init_package_manager || {
  log_error "Failed to initialize package manager"
  exit 1
}

# Initialize package tracking
init_package_tracking || {
  log_warn "Package tracking initialization failed, continuing without tracking"
}

# Validate install component names
validate_install_component() {
  local component=$1
  local valid_components=("core" "apps" "dev" "games" "flatpak" "laptop" "desktop" "homeserver")

  for valid in "${valid_components[@]}"; do
    if [[ "$component" == "$valid" ]]; then
      return 0
    fi
  done

  log_error "Invalid install component: '$component'"
  log_error "Valid components: ${valid_components[*]}"
  return 1
}

# Validate setup tool names
validate_setup_tool() {
  local tool=$1
  local valid_tools=(
    "brave" "vscode" "qtile" "i3" "lazygit" "ueberzugpp" "ollama" "protonvpn" "ohmyzsh"
    "tlp" "thinkfan" "auto-cpufreq" "trash-cli" "borgbackup" "syncthing"
    "ufw" "hyprland" "sddm" "sddm-autologin" "virt-manager"
    "nvidia-cuda" "nvidia-open" "vaapi" "intel-xorg" "nfancurve" "zenpower"
    "qtile-udev" "touchpad" "pm-speedup" "ffmpeg-swap" "remove-gnome"
    "update-system" "ssh"
  )

  for valid in "${valid_tools[@]}"; do
    if [[ "$tool" == "$valid" ]]; then
      return 0
    fi
  done

  log_error "Invalid setup tool: '$tool'"
  log_error "Valid tools: ${valid_tools[*]}"
  return 1
}

# Validate config types
validate_config_type() {
  local config=$1
  local valid_configs=("system" "default-apps")

  for valid in "${valid_configs[@]}"; do
    if [[ "$config" == "$valid" ]]; then
      return 0
    fi
  done

  log_error "Invalid config type: '$config'"
  log_error "Valid types: ${valid_configs[*]}"
  return 1
}

# Validate repository names
validate_repo() {
  local repo=$1
  local valid_repos=("rpm-fusion" "flathub")

  for valid in "${valid_repos[@]}"; do
    if [[ "$repo" == "$valid" ]]; then
      return 0
    fi
  done

  log_error "Invalid repository: '$repo'"
  log_error "Valid repositories: ${valid_repos[*]}"
  return 1
}

# Parse comma-separated values into array
parse_csv() {
  local input=$1
  local -n result_array=$2

  IFS=',' read -ra result_array <<<"$input"
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

CLI OPTIONS:
  --install GROUPS          Install package groups (comma-separated)
                            Available: core, apps, dev, games, flatpak
                            System-specific: laptop, desktop, homeserver

  --setup TOOLS             Setup specific tools (comma-separated)
                            Available: brave, vscode, qtile, i3, lazygit, ueberzugpp, ollama,
                            protonvpn, ohmyzsh, tlp, thinkfan, auto-cpufreq, trash-cli,
                            borgbackup, syncthing, ufw, hyprland, sddm, sddm-autologin,
                            virt-manager, nvidia-cuda, nvidia-open, vaapi, intel-xorg,
                            nfancurve, zenpower, qtile-udev, touchpad, pm-speedup,
                            ffmpeg-swap, remove-gnome, update-system, ssh

  --config TYPES            Apply system configurations (comma-separated)
                            Available: system, default-apps

  --enable-repo REPOS       Enable repositories (comma-separated)
                            Available: rpm-fusion, flathub

SYSTEM OPTIONS:
  --system-type TYPE        Override detection: laptop|desktop|server
  --dry-run                 Preview actions without executing
  --verbose                 Enable verbose logging (LOG_LEVEL_DEBUG)

PACKAGE TRACKING:
  --list-tracked            List all tracked packages
  --track-info PACKAGE      Show detailed info for a tracked package
  --sync-repos              Migrate packages with repository changes
  --check-repos             Check for repository changes without migrating
  --show-mappings           Show current package mappings from pkgmap.ini

UTILITY:
  -h, --help                Show this help message

EXAMPLES:
  # Combined installation and setup
  $0 --install core,apps,dev,laptop --setup tlp,thinkfan,touchpad

  # Preview before executing
  $0 --install core,apps,homeserver --dry-run

  # Developer setup with Oh My Zsh
  $0 --install core,apps,dev,desktop --setup ohmyzsh,lazygit,vscode

  # Package tracking examples
  $0 --list-tracked
  $0 --track-info lazygit
  $0 --check-repos
  $0 --sync-repos
  $0 --show-mappings

For more details, see docs/ and config_examples/.
EOF
  exit 0
}

# Check if any options that use package manager installation are enabled
#TODO: maybe we would simplify this, we can call speedup_pm.sh
# before anything else. So, we would handle it much more simple way
# because simple is better than complex.#TODO: need cross-distro support
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
  if [[ "$#" -eq 0 ]]; then
    usage
  fi

  # Handle help flags first
  for arg in "$@"; do
    case "$arg" in
    -h | --help)
      usage
      ;;
    esac
  done

  log_debug "Initializing script with args: $*"

  # CLI arrays
  local -a install_components=()
  local -a setup_tools=()
  local -a config_types=()
  local -a enable_repos=()
  local dry_run=false
  local system_type_override=""
  local tracking_action=""
  local tracking_package=""

  # Process CLI arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --install)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--install requires a comma-separated list of components"
        exit 1
      fi
      local -a components
      parse_csv "$2" components
      for component in "${components[@]}"; do
        if validate_install_component "$component"; then
          install_components+=("$component")
        else
          exit 1
        fi
      done
      shift 2
      ;;

    --setup)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--setup requires a comma-separated list of tools"
        exit 1
      fi
      local -a tools
      parse_csv "$2" tools
      for tool in "${tools[@]}"; do
        if validate_setup_tool "$tool"; then
          setup_tools+=("$tool")
        else
          exit 1
        fi
      done
      shift 2
      ;;

    --config)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--config requires a comma-separated list of configuration types"
        exit 1
      fi
      local -a configs
      parse_csv "$2" configs
      for config in "${configs[@]}"; do
        if validate_config_type "$config"; then
          config_types+=("$config")
        else
          exit 1
        fi
      done
      shift 2
      ;;

    --enable-repo)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--enable-repo requires a comma-separated list of repositories"
        exit 1
      fi
      local -a repos
      parse_csv "$2" repos
      for repo in "${repos[@]}"; do
        if validate_repo "$repo"; then
          enable_repos+=("$repo")
        else
          exit 1
        fi
      done
      shift 2
      ;;

    --system-type)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--system-type requires a value (laptop|desktop|server)"
        exit 1
      fi
      if [[ ! "$2" =~ ^(laptop|desktop|server)$ ]]; then
        log_error "Invalid system type: '$2'. Must be: laptop, desktop, or server"
        exit 1
      fi
      system_type_override="$2"
      shift 2
      ;;

    --dry-run)
      dry_run=true
      shift
      ;;

    --verbose)
      LOG_LEVEL="DEBUG"
      shift
      ;;

    --list-tracked)
      tracking_action="list"
      shift
      ;;

    --track-info)
      if [[ -z "$2" || "$2" == --* ]]; then
        log_error "--track-info requires a package name"
        exit 1
      fi
      tracking_action="info"
      tracking_package="$2"
      shift 2
      ;;

    --sync-repos)
      tracking_action="sync"
      shift
      ;;

    --check-repos)
      tracking_action="check"
      shift
      ;;

    --show-mappings)
      tracking_action="mappings"
      shift
      ;;

    *)
      log_error "Unknown option: $1"
      log_error "Run '$0 --help' for usage information"
      exit 1
      ;;
    esac
  done

  # Handle tracking actions first (they don't require other validations)
  if [[ -n "$tracking_action" ]]; then
    case "$tracking_action" in
    list)
      log_info "Listing tracked packages..."
      list_tracked_packages
      exit 0
      ;;
    info)
      log_info "Package information for: $tracking_package"
      if get_package_info "$tracking_package"; then
        exit 0
      else
        log_error "Package not tracked: $tracking_package"
        exit 1
      fi
      ;;
    sync)
      log_info "Synchronizing repository changes..."
      if migrate_all_changed_repos "interactive"; then
        log_success "Repository synchronization completed"
        exit 0
      else
        log_error "Repository synchronization failed or cancelled"
        exit 1
      fi
      ;;
    check)
      show_repo_changes
      exit 0
      ;;
    mappings)
      log_info "Loading package mappings..."
      local pkgmap_file="${CONFIG_DIR:-$HOME/.config/auto-penguin-setup}/pkgmap.ini"
      if [[ -f "$pkgmap_file" ]]; then
        load_package_mappings "$pkgmap_file" || {
          log_error "Failed to load package mappings"
          exit 1
        }
        echo ""
        echo "Package Mappings for $CURRENT_DISTRO:"
        echo "========================================"
        if [[ ${#PACKAGE_MAPPINGS[@]} -eq 0 ]]; then
          echo "No mappings found for this distribution."
        else
          for pkg in "${!PACKAGE_MAPPINGS[@]}"; do
            printf "%-30s -> %s\n" "$pkg" "${PACKAGE_MAPPINGS[$pkg]}"
          done | sort
        fi
        echo ""
      else
        log_error "No pkgmap.ini found at: $pkgmap_file"
        exit 1
      fi
      exit 0
      ;;
    esac
  fi

  # Validate that at least one action is specified
  if [[ ${#install_components[@]} -eq 0 ]] &&
    [[ ${#setup_tools[@]} -eq 0 ]] &&
    [[ ${#config_types[@]} -eq 0 ]] &&
    [[ ${#enable_repos[@]} -eq 0 ]]; then
    log_error "No actions specified. Use --install, --setup, --config, or --enable-repo"
    exit 1
  fi # Display detected distribution and system information
  local distro_name
  distro_name=$(get_distro_pretty_name)
  log_info "==========================================="
  log_info "Distribution: $distro_name"
  log_info "Distro Family: $CURRENT_DISTRO"

  # Set system type (override or detect)
  local system_type
  if [[ -n "$system_type_override" ]]; then
    system_type="$system_type_override"
    log_info "System Type: $system_type (overridden)"
  else
    # TODO: device detection desktop, laptop need better logic than hostname.
    system_type="desktop" # Default for now
    log_debug "System Type: $system_type (detected)"
  fi
  log_info "==========================================="

  # Dry-run preview
  if $dry_run; then
    log_info "🔍 DRY RUN MODE - Preview of actions (nothing will be executed)"
    echo ""

    if [[ ${#install_components[@]} -gt 0 ]]; then
      echo "📦 INSTALL COMPONENTS:"
      for component in "${install_components[@]}"; do
        echo "  - $component"
      done
      echo ""
    fi

    if [[ ${#setup_tools[@]} -gt 0 ]]; then
      echo "🔧 SETUP TOOLS:"
      for tool in "${setup_tools[@]}"; do
        echo "  - $tool"
      done
      echo ""
    fi

    if [[ ${#config_types[@]} -gt 0 ]]; then
      echo "⚙️  APPLY CONFIGURATIONS:"
      for config in "${config_types[@]}"; do
        echo "  - $config"
      done
      echo ""
    fi

    if [[ ${#enable_repos[@]} -gt 0 ]]; then
      echo "📚 ENABLE REPOSITORIES:"
      for repo in "${enable_repos[@]}"; do
        echo "  - $repo"
      done
      echo ""
    fi

    log_info "To execute these actions, run the same command without --dry-run"
    exit 0
  fi

  # Execute install components
  if [[ ${#install_components[@]} -gt 0 ]]; then
    log_info "Installing components: ${install_components[*]}"
    for component in "${install_components[@]}"; do
      case "$component" in
      core)
        install_core_packages
        ;;
      apps)
        install_app_packages
        ;;
      dev)
        install_dev_packages
        ;;
      games)
        install_games_packages
        ;;
      laptop)
        install_system_specific_packages "laptop"
        ;;
      desktop)
        install_system_specific_packages "desktop"
        ;;
      homeserver)
        install_system_specific_packages "homeserver"
        ;;
      flatpak)
        install_flatpak_packages
        ;;
      esac
    done
  fi

  # Execute setup tools
  if [[ ${#setup_tools[@]} -gt 0 ]]; then
    log_info "Setting up tools: ${setup_tools[*]}"
    for tool in "${setup_tools[@]}"; do
      case "$tool" in
      brave) install_brave ;;
      vscode) install_vscode ;;
      qtile) install_qtile_packages ;;
      i3) install_i3_packages ;;
      lazygit) install_lazygit ;;
      ueberzugpp) install_ueberzugpp ;;
      ollama) install_ollama ;;
      protonvpn) install_protonvpn ;;
      ohmyzsh) install_ohmyzsh ;;
      tlp) tlp_setup ;;
      thinkfan) thinkfan_setup ;;
      auto-cpufreq) install_auto_cpufreq ;;
      trash-cli) trash_cli_setup ;;
      borgbackup) borgbackup_setup ;;
      syncthing) syncthing_setup ;;
      ufw) switch_ufw_setup ;;
      hyprland) install_hyprland ;;
      sddm) switch_to_sddm ;;
      sddm-autologin) sddm_autologin ;;
      virt-manager) virt_manager_setup ;;
      nvidia-cuda) nvidia_cuda_setup ;;
      nvidia-open) switch_nvidia_open ;;
      vaapi) vaapi_setup ;;
      intel-xorg) xorg_setup_intel ;;
      nfancurve) nfancurve_setup ;;
      zenpower) zenpower_setup ;;
      qtile-udev) setup_qtile_backlight_rules ;;
      touchpad) touchpad_setup ;;
      pm-speedup) speed_up_package_manager ;;
      ffmpeg-swap) ffmpeg_swap ;;
      remove-gnome) remove_gnome ;;
      update-system) system_updates ;;
      ssh) ssh_setup ;;
      esac
    done
  fi

  # Execute configurations
  if [[ ${#config_types[@]} -gt 0 ]]; then
    log_info "Applying configurations: ${config_types[*]}"
    for config in "${config_types[@]}"; do
      case "$config" in
      system)
        setup_files
        ;;
      default-apps)
        setup_default_applications
        ;;
      esac
    done
  fi

  # Enable repositories
  if [[ ${#enable_repos[@]} -gt 0 ]]; then
    log_info "Enabling repositories: ${enable_repos[*]}"
    for repo in "${enable_repos[@]}"; do
      case "$repo" in
      rpm-fusion)
        enable_rpm_fusion
        ;;
      flathub)
        log_info "Flathub is enabled by default with Flatpak installation"
        ;;
      esac
    done
  fi

  log_info "✅ All tasks completed successfully!"
  exit 0
}

# Execute main with provided command-line arguments.
main "$@"
