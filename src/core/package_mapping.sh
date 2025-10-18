#!/usr/bin/env bash
# package_mapping.sh - Package name mapping across distributions
# Purpose: Map package names that differ across distros using INI configuration

# Source guard to prevent re-sourcing
[[ -n "${_PACKAGE_MAPPING_SOURCED:-}" ]] && return 0
readonly _PACKAGE_MAPPING_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/distro_detection.sh
source src/core/ini_parser.sh

# Declare associative array for mappings (loaded from INI)
declare -A PACKAGE_MAPPINGS

# Function: load_package_mappings_ini
# Purpose: Load package name mappings from pkgmap.ini
# Parameters:
#   $1 - Path to pkgmap.ini file
# Returns: 0 on success, 1 on failure
load_package_mappings_ini() {
  local config_file="${1:-}"
  
  if [[ -z "$config_file" ]]; then
    log_error "No configuration file specified for loading mappings"
    return 1
  fi
  
  if [[ ! -f "$config_file" ]]; then
    log_debug "Package mapping file not found: $config_file"
    return 0
  fi
  
  log_debug "Loading package mappings from $config_file"
  
  # Parse the INI file
  parse_ini_file "$config_file" || return 1
  
  # Determine target section based on detected distro
  local target_section="pkgmap.${DETECTED_DISTRO}"
  
  if ! ini_section_exists "$target_section"; then
    log_debug "No mappings found for distribution: $DETECTED_DISTRO"
    return 0
  fi
  
  # Load mappings for current distro
  local keys
  mapfile -t keys < <(get_ini_section_keys "$target_section")
  
  for key in "${keys[@]}"; do
    # Skip numeric keys (from package lists)
    [[ "$key" =~ ^[0-9]+$ ]] && continue
    
    local mapped_value
    mapped_value=$(get_ini_value "$target_section" "$key")
    
    PACKAGE_MAPPINGS["$key"]="$mapped_value"
    log_debug "Mapped: $key -> $mapped_value"
  done
  
  log_info "Loaded ${#PACKAGE_MAPPINGS[@]} package mappings for $DETECTED_DISTRO"
  return 0
}

# Function: load_package_mappings
# Purpose: Load package name mappings from pkgmap.ini
# Parameters:
#   $1 - Path to pkgmap.ini file
# Returns: 0 on success, 1 on failure
load_package_mappings() {
  load_package_mappings_ini "$1"
}

# Function: map_package_name
# Purpose: Map a package name to the appropriate name for the target distro
# Parameters:
#   $1 - Package name
#   $2 - Target distro (optional, uses detected distro if not specified)
# Returns: Mapped package name to stdout
map_package_name() {
  local package="${1:-}"
  local distro="${2:-}"
  
  if [[ -z "$package" ]]; then
    log_error "No package name specified for mapping"
    return 1
  fi
  
  # Use detected distro if not specified
  if [[ -z "$distro" ]]; then
    distro=$(detect_distro) || return 1
  fi
  
  # Check if mapping exists
  if [[ -n "${PACKAGE_MAPPINGS[$package]:-}" ]]; then
    local mapped_name="${PACKAGE_MAPPINGS[$package]}"
    log_debug "Mapped '$package' to '$mapped_name' for $distro"
    echo "$mapped_name"
    return 0
  fi
  
  # No mapping found, return original name
  log_debug "No mapping for '$package' on $distro, using original name"
  echo "$package"
}

# Purpose: Map an entire array of package names to the target distro
# Parameters:
#   $1 - Target distro (optional, uses detected distro if not specified)
#   $@ - Array of package names (pass as "${array[@]}" starting from $2)
# Returns: Mapped package names to stdout (newline-separated)
map_package_list() {
  local distro="${1:-}"
  shift
  
  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified for mapping"
    return 0
  fi
  
  # Use detected distro if not specified
  if [[ -z "$distro" ]]; then
    distro=$(detect_distro) || return 1
  fi
  
  local packages=("$@")
  
  log_debug "Mapping ${#packages[@]} packages for $distro"
  
  for pkg in "${packages[@]}"; do
    map_package_name "$pkg" "$distro"
  done
}

# Function: is_aur_package
# Purpose: Check if a mapped package is from AUR
# Parameters:
#   $1 - Mapped package value (e.g., "AUR:qtile-extras" or "regular-package")
# Returns: 0 if AUR package, 1 otherwise
is_aur_package() {
  local mapped="${1:-}"
  [[ "$mapped" =~ ^AUR: ]] && return 0
  return 1
}

# Function: is_copr_package
# Purpose: Check if a mapped package is from COPR
# Parameters:
#   $1 - Mapped package value (e.g., "COPR:user/repo" or "regular-package")
# Returns: 0 if COPR package, 1 otherwise
is_copr_package() {
  local mapped="${1:-}"
  [[ "$mapped" =~ ^COPR: ]] && return 0
  return 1
}

# Function: extract_aur_package
# Purpose: Extract package name from AUR mapping
# Parameters:
#   $1 - Mapped value (e.g., "AUR:qtile-extras")
# Returns: Package name (e.g., "qtile-extras")
extract_aur_package() {
  local mapped="${1:-}"
  if [[ "$mapped" =~ ^AUR:(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo "$mapped"
  fi
}

# Function: extract_copr_repo
# Purpose: Extract COPR repository from mapping
# Parameters:
#   $1 - Mapped value (e.g., "COPR:user/repo")
# Returns: Repository (e.g., "user/repo")
extract_copr_repo() {
  local mapped="${1:-}"
  if [[ "$mapped" =~ ^COPR:(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo ""
  fi
}

export -f load_package_mappings
export -f load_package_mappings_ini
export -f map_package_name
export -f map_package_list
export -f is_aur_package
export -f is_copr_package
export -f extract_aur_package
export -f extract_copr_repo
