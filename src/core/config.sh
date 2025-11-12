#!/usr/bin/env bash
# config.sh - INI-based configuration management for auto-penguin-setup
# Handles loading/parsing of INI config files from XDG config dir

# Source guard to prevent re-sourcing
[[ -n "${_CONFIG_SOURCED:-}" ]] && return 0
readonly _CONFIG_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/distro_detection.sh
source src/core/package_manager.sh
source src/core/ini_parser.sh
source src/core/package_mapping.sh

# Constants (use uppercase) - only define if not already defined
if [[ -z "${SCRIPT_DIR+x}" ]]; then
  readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # PROJECT_ROOT is two levels up from src/core/
  readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  readonly CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/auto-penguin-setup"
  readonly EXAMPLES_DIR="$PROJECT_ROOT/config_examples"
fi

# Function: load_ini_config
# Purpose: Load INI configuration files (variables.ini, packages.ini, pkgmap.ini)
# Arguments: $1 - Configuration file name (e.g., "variables.ini")
# Returns: Path to the loaded configuration file or empty string on failure
load_ini_config() {
  local config_file="$1"
  local full_path="$CONFIG_DIR/$config_file"
  local example_path="$EXAMPLES_DIR/$config_file"

  # Primary location: XDG config directory
  if [[ -f "$full_path" ]]; then
    echo "$full_path"
    return 0
  fi

  # For testing environments, don't prompt and just return failure
  if [[ -n "${BATS_TEST_TMPDIR:-}" ]]; then
    return 1
  fi

  # Check for example configs that could be copied
  if [[ -f "$example_path" ]]; then
    echo -e "\nConfiguration file not found: $config_file"
    echo "An example configuration was found at: $example_path"
    echo "Would you like to use this example configuration?"
    read -p "[y/N] " answer
    echo

    if [[ "$answer" =~ ^[Yy]$ ]]; then
      # Create directory if it doesn't exist
      mkdir -p "$CONFIG_DIR" || {
        log_error "Failed to create configuration directory at $CONFIG_DIR"
        return 1
      }

      # Copy the example configuration
      if ! cp "$example_path" "$full_path"; then
        log_error "Failed to copy example configuration"
        return 1
      fi

      # If it's variables.ini, update the user
      if [[ "$config_file" == "variables.ini" ]]; then
        customize_variables_ini "$full_path"
      fi

      log_info "Copied example configuration to: $full_path"
      echo "$full_path"
      return 0
    fi
  fi

  log_error "Configuration file not found: $config_file"
  return 1
}

# Function: customize_variables_ini
# Purpose: Update variables.ini with current user and correct paths
# Arguments: $1 - Path to the variables.ini file to customize
# Returns: 0 on success, 1 on failure
customize_variables_ini() {
  local variables_file="$1"
  local current_user
  current_user=$(whoami)

  if [[ ! -f "$variables_file" ]]; then
    log_error "Cannot customize variables.ini: File not found at $variables_file"
    return 1
  fi

  # Use sed to update user and home paths
  sed -i "s|^user=.*|user=$current_user|" "$variables_file"
  sed -i "s|/home/developer|$HOME|g" "$variables_file"

  log_info "Successfully customized variables.ini for user $current_user"
  return 0
}

# Function: load_variables_ini
# Purpose: Load values from variables.ini into environment variables
# Arguments: $1 - Path to variables.ini file
# Returns: 0 on success, 1 on failure
load_variables_ini() {
  local variables_file="$1"

  if [[ ! -f "$variables_file" ]]; then
    log_error "Variables file not found: $variables_file"
    return 1
  fi

  log_info "Loading variables from INI configuration: $variables_file"

  # Parse the INI file
  parse_ini_file "$variables_file" || return 1

  # Load system variables
  user=$(get_ini_value "system" "user")
  [[ -z "$user" ]] && user=$(whoami)
  current_device=$(get_ini_value "system" "current_device")
  [[ -z "$current_device" ]] && current_device="desktop"

  # Load desktop variables
  hostname_desktop=$(get_ini_value "desktop" "hostname")
  [[ -z "$hostname_desktop" ]] && hostname_desktop="fedora"
  desktop_ip=$(get_ini_value "desktop" "ip")
  [[ -z "$desktop_ip" ]] && desktop_ip="192.168.1.100"
  desktop_session=$(get_ini_value "desktop" "session")
  [[ -z "$desktop_session" ]] && desktop_session="qtile"
  desktop_display_manager=$(get_ini_value "desktop" "display_manager")
  [[ -z "$desktop_display_manager" ]] && desktop_display_manager="sddm"

  # Load laptop variables
  hostname_laptop=$(get_ini_value "laptop" "hostname")
  [[ -z "$hostname_laptop" ]] && hostname_laptop="fedora-laptop"
  laptop_ip=$(get_ini_value "laptop" "ip")
  [[ -z "$laptop_ip" ]] && laptop_ip="192.168.1.101"
  laptop_session=$(get_ini_value "laptop" "session")
  [[ -z "$laptop_session" ]] && laptop_session="qtile"
  laptop_display_manager=$(get_ini_value "laptop" "display_manager")
  [[ -z "$laptop_display_manager" ]] && laptop_display_manager="sddm"

  # Load browser variables
  firefox_profile=$(get_ini_value "browser" "firefox_profile")
  firefox_profile_path=$(get_ini_value "browser" "firefox_profile_path")
  librewolf_dir=$(get_ini_value "browser" "librewolf_dir")
  librewolf_profile=$(get_ini_value "browser" "librewolf_profile")

  # Load SSH configuration
  ssh_port=$(get_ini_value "ssh" "port")
  [[ -z "$ssh_port" ]] && ssh_port="22"
  ssh_enable_service=$(get_ini_value "ssh" "enable_service")
  [[ -z "$ssh_enable_service" ]] && ssh_enable_service="true"
  ssh_password_auth=$(get_ini_value "ssh" "password_auth")
  [[ -z "$ssh_password_auth" ]] && ssh_password_auth="no"
  ssh_permit_root_login=$(get_ini_value "ssh" "permit_root_login")
  [[ -z "$ssh_permit_root_login" ]] && ssh_permit_root_login="no"
  ssh_key_auth=$(get_ini_value "ssh" "key_auth")
  [[ -z "$ssh_key_auth" ]] && ssh_key_auth="yes"

  # Export all variables
  export user current_device
  export hostname_desktop desktop_ip desktop_session desktop_display_manager
  export hostname_laptop laptop_ip laptop_session laptop_display_manager
  export firefox_profile firefox_profile_path librewolf_dir librewolf_profile
  export ssh_port ssh_enable_service ssh_password_auth ssh_permit_root_login ssh_key_auth

  log_info "Variables loaded successfully from INI"
  return 0
}

# Function: load_packages_ini
# Purpose: Load package arrays from packages.ini
# Arguments: $1 - Path to packages.ini file
# Returns: 0 on success, 1 on failure
load_packages_ini() {
  local packages_file="$1"

  if [[ ! -f "$packages_file" ]]; then
    log_error "Packages file not found: $packages_file"
    return 1
  fi

  log_info "Loading packages from INI configuration: $packages_file"

  # Parse the INI file
  parse_ini_file "$packages_file" || return 1

  # Load each package array from sections
  mapfile -t CORE_PACKAGES < <(get_ini_section "core")
  mapfile -t APPS_PACKAGES < <(get_ini_section "apps")
  mapfile -t DEV_PACKAGES < <(get_ini_section "dev")
  mapfile -t GAMES_PACKAGES < <(get_ini_section "games")
  mapfile -t DESKTOP_PACKAGES < <(get_ini_section "desktop")
  mapfile -t LAPTOP_PACKAGES < <(get_ini_section "laptop")
  mapfile -t HOMESERVER_PACKAGES < <(get_ini_section "homeserver")
  mapfile -t QTILE_PACKAGES < <(get_ini_section "qtile")
  mapfile -t I3_PACKAGES < <(get_ini_section "i3")
  mapfile -t WM_COMMON_PACKAGES < <(get_ini_section "wm-common")
  mapfile -t FLATPAK_PACKAGES < <(get_ini_section "flatpak")

  # Export all arrays
  export CORE_PACKAGES APPS_PACKAGES DEV_PACKAGES GAMES_PACKAGES
  export DESKTOP_PACKAGES LAPTOP_PACKAGES HOMESERVER_PACKAGES QTILE_PACKAGES I3_PACKAGES WM_COMMON_PACKAGES FLATPAK_PACKAGES

  log_info "Package arrays loaded successfully from INI"
  return 0
}

# Function: load_variables
# Purpose: Load values from variables.ini into environment variables
# Returns: 0 on success, 1 on failure
load_variables() {
  log_info "Loading variables from configuration..."

  local variables_file
  variables_file=$(load_ini_config "variables.ini")

  if [[ -z "$variables_file" || ! -f "$variables_file" ]]; then
    log_error "Failed to load variables configuration"
    return 1
  fi

  load_variables_ini "$variables_file"
  return $?
}

# Function: load_package_arrays
# Purpose: Load all package arrays from packages.ini
# Returns: 0 on success, 1 on failure
load_package_arrays() {
  log_info "Loading package arrays from configuration..."

  # Ensure distribution is detected before loading mappings
  if [[ -z "${DETECTED_DISTRO:-}" ]]; then
    DETECTED_DISTRO=$(detect_distro)
    export DETECTED_DISTRO
    log_debug "Detected distribution: $DETECTED_DISTRO"
  fi

  local packages_file
  packages_file=$(load_ini_config "packages.ini")

  if [[ -z "$packages_file" || ! -f "$packages_file" ]]; then
    log_error "Failed to load packages configuration"
    return 1
  fi

  load_packages_ini "$packages_file" || return 1

  # Load package mappings from pkgmap.ini (optional)
  local pkgmap_file="$CONFIG_DIR/pkgmap.ini"
  if [[ -f "$pkgmap_file" ]]; then
    log_debug "Loading package mappings from $pkgmap_file"
    load_package_mappings "$pkgmap_file" || {
      log_warn "Failed to load package mappings from pkgmap.ini, using default package names"
    }
  else
    log_debug "No pkgmap.ini found at $pkgmap_file, packages will use their original names"
  fi

  return 0
}

# Function: check_and_create_config
# Purpose: Check if configuration exists, create if missing
# Returns: 0 on success, 1 on failure
check_and_create_config() {
  log_info "Checking configuration..."

  # Check if config directory exists
  if [[ ! -d "$CONFIG_DIR" ]]; then
    log_info "Creating configuration directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR" || {
      log_error "Failed to create configuration directory"
      return 1
    }
  fi

  # Check for required configuration files
  local required_configs=("variables.ini" "packages.ini")
  local missing_configs=()

  for config in "${required_configs[@]}"; do
    if [[ ! -f "$CONFIG_DIR/$config" ]]; then
      missing_configs+=("$config")
    fi
  done

  if [[ ${#missing_configs[@]} -gt 0 ]]; then
    log_warn "Missing configuration files: ${missing_configs[*]}"

    # For testing environments, just return failure
    if [[ -n "${BATS_TEST_TMPDIR:-}" ]]; then
      return 1
    fi

    # Try to copy from examples or create defaults
    echo -e "\n===== Configuration Setup ====="
    echo "The following configuration files are missing:"
    for file in "${missing_configs[@]}"; do
      echo "  - $CONFIG_DIR/$file"
    done
    echo
    echo "Would you like to create them from examples?"
    read -r -p "[y/N] " answer
    echo

    if [[ "$answer" =~ ^[Yy]$ ]]; then
      for file in "${missing_configs[@]}"; do
        local target_file="$CONFIG_DIR/$file"
        local example_file="$EXAMPLES_DIR/$file"

        if [[ -f "$example_file" ]]; then
          log_info "Copying $file from examples..."
          cp "$example_file" "$target_file" || {
            log_error "Failed to copy $file"
            return 1
          }

          # Customize variables.ini with current user
          if [[ "$file" == "variables.ini" ]]; then
            customize_variables_ini "$target_file"
          fi

          echo "✓ Created $file"
        else
          # Example file not found - this should never happen as examples are in repo
          log_error "Example file not found: $example_file"
          log_error "Please ensure config_examples/ directory is present"
          return 1
        fi
      done

      # Also copy pkgmap.ini if it doesn't exist
      if [[ ! -f "$CONFIG_DIR/pkgmap.ini" ]]; then
        local pkgmap_example="$EXAMPLES_DIR/pkgmap.ini"
        if [[ -f "$pkgmap_example" ]]; then
          log_info "Copying pkgmap.ini from examples..."
          cp "$pkgmap_example" "$CONFIG_DIR/pkgmap.ini"
          echo "✓ Created pkgmap.ini"
        else
          log_error "Example file not found: $pkgmap_example"
          log_error "Please ensure config_examples/ directory is present"
          return 1
        fi
      fi

      echo -e "\n✓ Configuration files created successfully!"
      echo "Location: $CONFIG_DIR"
      echo
    else
      log_error "Cannot proceed without configuration files"
      return 1
    fi
  fi

  log_info "Configuration files found"
  return 0
}

# Function: init_config
# Purpose: Initialize all configuration
# Returns: 0 on success, exits on critical failure
init_config() {
  log_info "Initializing configuration..."

  # Check and create config if needed
  if ! check_and_create_config; then
    log_error "Failed to initialize configuration"
    exit 1
  fi

  # Load all configuration values
  if ! load_variables; then
    log_error "Failed to load variables"
    exit 1
  fi

  if ! load_package_arrays; then
    log_error "Failed to load package arrays"
    exit 1
  fi

  log_info "Configuration loaded successfully and ready to use"

  # Print a summary of the loaded configuration
  log_info "===== Configuration Summary ====="
  log_info "User: $user"
  log_info "Configuration format: INI"
  log_info "------------------------------"
  log_info "Core Packages: ${#CORE_PACKAGES[@]} packages"
  log_info "Apps Packages: ${#APPS_PACKAGES[@]} packages"
  log_info "Dev Packages: ${#DEV_PACKAGES[@]} packages"
  log_info "Qtile Packages: ${#QTILE_PACKAGES[@]} packages"
  log_info "Flatpak Packages: ${#FLATPAK_PACKAGES[@]} packages"
  log_info "Desktop Packages: ${#DESKTOP_PACKAGES[@]} packages"
  log_info "Laptop Packages: ${#LAPTOP_PACKAGES[@]} packages"
  log_info "Home Server Packages: ${#HOMESERVER_PACKAGES[@]} packages"
  log_info "Package Mappings: ${#PACKAGE_MAPPINGS[@]} mappings"
  log_info "===== End of Summary ====="

  return 0
}

# Initialize the environment when this script is sourced
# This allows the script to be used both as a library and as a standalone script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  init_config
fi
