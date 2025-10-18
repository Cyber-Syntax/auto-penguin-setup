#!/usr/bin/env bash
# distro_detection.sh - Distribution detection and validation
# Purpose: Detect Linux distribution, version, and validate support

# Source guard to prevent re-sourcing
[[ -n "${_DISTRO_DETECTION_SOURCED:-}" ]] && return 0
readonly _DISTRO_DETECTION_SOURCED=1

# Source logging functions
source src/core/logging.sh

# Supported distributions
readonly SUPPORTED_DISTROS=("fedora" "arch" "debian")

# Function: detect_distro
# Purpose: Detect the Linux distribution
# Returns: Distribution name (fedora, arch, debian) to stdout
# Exit: 1 if detection fails
detect_distro() {
  local distro=""
  
  # Check if /etc/os-release exists
  if [[ ! -f /etc/os-release ]]; then
    log_error "Cannot detect distribution: /etc/os-release not found"
    return 1
  fi
  
  # Source os-release to get ID
  source /etc/os-release
  
  # Normalize distribution ID
  case "${ID,,}" in
    fedora)
      distro="fedora"
      ;;
    arch|archlinux)
      distro="arch"
      ;;
    debian|ubuntu|linuxmint|pop)
      distro="debian"
      ;;
    *)
      log_error "Unsupported distribution: $ID"
      log_error "Supported distributions: ${SUPPORTED_DISTROS[*]}"
      return 1
      ;;
  esac
  
  echo "$distro"
}

# Function: get_distro_version
# Purpose: Get the distribution version
# Returns: Version string to stdout
# Exit: 1 if detection fails
get_distro_version() {
  if [[ ! -f /etc/os-release ]]; then
    log_error "Cannot detect version: /etc/os-release not found"
    return 1
  fi
  
  source /etc/os-release
  echo "${VERSION_ID:-unknown}"
}

# Function: get_distro_pretty_name
# Purpose: Get the human-readable distribution name
# Returns: Pretty name to stdout
get_distro_pretty_name() {
  if [[ ! -f /etc/os-release ]]; then
    echo "Unknown Linux"
    return 1
  fi
  
  source /etc/os-release
  echo "${PRETTY_NAME:-Unknown Linux}"
}

# Function: validate_distro_support
# Purpose: Validate that the detected distribution is supported
# Parameters:
#   $1 - distro name (optional, will detect if not provided)
# Returns: 0 if supported, 1 if not
validate_distro_support() {
  local distro="${1:-}"
  
  # Detect if not provided
  if [[ -z "$distro" ]]; then
    distro=$(detect_distro) || return 1
  fi
  
  # Check if distro is in supported list
  for supported in "${SUPPORTED_DISTROS[@]}"; do
    if [[ "$distro" == "$supported" ]]; then
      log_debug "Distribution '$distro' is supported"
      return 0
    fi
  done
  
  log_error "Distribution '$distro' is not supported"
  log_error "Supported distributions: ${SUPPORTED_DISTROS[*]}"
  return 1
}

# Function: is_fedora
# Purpose: Check if running on Fedora
# Returns: 0 if Fedora, 1 if not
is_fedora() {
  local distro
  distro=$(detect_distro) || return 1
  [[ "$distro" == "fedora" ]]
}

# Function: is_arch
# Purpose: Check if running on Arch
# Returns: 0 if Arch, 1 if not
is_arch() {
  local distro
  distro=$(detect_distro) || return 1
  [[ "$distro" == "arch" ]]
}

# Function: is_debian
# Purpose: Check if running on Debian-based system
# Returns: 0 if Debian-based, 1 if not
is_debian() {
  local distro
  distro=$(detect_distro) || return 1
  [[ "$distro" == "debian" ]]
}
