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
  local os_id=""
  local distro_from_os=""
  local distro_from_pkg=""

  # Read /etc/os-release if available to get a hint (but don't rely on it alone)
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    os_id="${ID:-}";
    case "${os_id,,}" in
      fedora|nobara)
        distro_from_os="fedora";
        ;;
      arch|archlinux|manjaro|garuda|cachyos|endeavouros)
        distro_from_os="arch";
        ;;
      debian|ubuntu|linuxmint|popos)
        distro_from_os="debian";
        ;;
      *)
        distro_from_os="";
        ;;
    esac
    log_debug "os-release ID='$os_id' -> distro_from_os='${distro_from_os:-unknown}'"
  else
    log_debug "/etc/os-release not found; will attempt package-manager-based detection"
  fi

  # Detect package managers present on the system
  local has_pacman=0 has_apt=0 has_dnf=0
  if command -v pacman >/dev/null 2>&1; then has_pacman=1; fi
  if command -v apt >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1; then has_apt=1; fi
  if command -v dnf >/dev/null 2>&1; then has_dnf=1; fi
  log_debug "pkgmgrs: pacman=$has_pacman apt=$has_apt dnf=$has_dnf"

  # Derive distro from package manager if clear
  if [[ $has_pacman -eq 1 && $has_apt -eq 0 && $has_dnf -eq 0 ]]; then
    distro_from_pkg="arch"
  elif [[ $has_apt -eq 1 && $has_pacman -eq 0 && $has_dnf -eq 0 ]]; then
    distro_from_pkg="debian"
  elif [[ $has_dnf -eq 1 && $has_pacman -eq 0 && $has_apt -eq 0 ]]; then
    distro_from_pkg="fedora"
  else
    distro_from_pkg=""
  fi
  log_debug "distro_from_pkg='${distro_from_pkg:-unknown}'"

  # Reconcile package-manager detection with os-release hint
  if [[ -n "$distro_from_pkg" ]]; then
    # If os-release exists and disagrees with pkg manager, prefer os-release when it maps
    if [[ -n "$distro_from_os" && "$distro_from_os" != "$distro_from_pkg" ]]; then
      log_debug "pkg manager suggests '$distro_from_pkg' but os-release suggests '$distro_from_os' -> using os-release"
      distro="$distro_from_os"
    else
      distro="$distro_from_pkg"
    fi
  else
    # No clear pkg-manager winner; fall back to os-release when present
    if [[ -n "$distro_from_os" ]]; then
      distro="$distro_from_os"
    else
      log_error "Cannot detect distribution: no known package manager (pacman/apt/dnf) found and /etc/os-release is unknown"
      log_error "Supported distributions: ${SUPPORTED_DISTROS[*]}"
      return 1
    fi
  fi

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