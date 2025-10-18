#!/usr/bin/env bash
# repository_manager.sh - Repository management abstraction
# Purpose: Abstract repository operations across COPR, AUR, and PPAs

# Source guard to prevent re-sourcing
[[ -n "${_REPOSITORY_MANAGER_SOURCED:-}" ]] && return 0
readonly _REPOSITORY_MANAGER_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/distro_detection.sh

# Purpose: Add a repository based on distribution
# Parameters:
#   $1 - Repository identifier (COPR name, AUR package, or PPA)
#TODO: Improve function, maybe split into repo_add_copr, repo_add_aur, repo_add_ppa would be cleaner
repo_add() {
  local repo="${1:-}"
  
  if [[ -z "$repo" ]]; then
    log_error "No repository specified"
    return 1
  fi
  
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Adding repository '$repo' for $distro"
  
  case "$distro" in
    fedora)
      # COPR repository format: user/repo
      if [[ "$repo" =~ ^[^/]+/[^/]+$ ]]; then
        if ! sudo dnf copr enable -y "$repo"; then
          log_error "Failed to add COPR repository: $repo"
          return 1
        fi
      else
        log_error "Invalid COPR repository format: $repo (expected: user/repo)"
        return 1
      fi
      ;;
    arch)
      # For Arch, repositories are typically added via AUR helpers
      # or by editing /etc/pacman.conf
      log_warn "AUR package installation should be handled by AUR helper (paru/yay)"

      # Install package from AUR
      log_info "Installing AUR package: $repo"
      if command -v paru &>/dev/null; then
        if ! paru -S --noconfirm "$repo"; then
          log_error "Failed to install AUR package: $repo"
          return 1
        fi
      elif command -v yay &>/dev/null; then
        if ! yay -S --noconfirm "$repo"; then
          log_error "Failed to install AUR package: $repo"
          return 1
        fi
      else
        log_error "No AUR helper found. Install paru or yay first."
        return 1
      fi
      ;;
    debian)
      # PPA format: ppa:user/repo
      if [[ "$repo" =~ ^ppa: ]]; then
        if ! sudo add-apt-repository -y "$repo"; then
          log_error "Failed to add PPA: $repo"
          return 1
        fi
        # Update package lists after adding PPA
        if ! sudo apt-get update; then
          log_error "Failed to update package lists after adding PPA"
          return 1
        fi
      else
        log_error "Invalid PPA format: $repo (expected: ppa:user/repo)"
        return 1
      fi
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Successfully added repository: $repo"
  return 0
}

# Function: repo_enable
# Purpose: Enable a repository
# Parameters:
#   $1 - Repository name
# Returns: 0 on success, 1 on failure
repo_enable() {
  local repo="${1:-}"
  
  if [[ -z "$repo" ]]; then
    log_error "No repository specified"
    return 1
  fi
  
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Enabling repository '$repo' for $distro"
  
  case "$distro" in
    fedora)
      if ! sudo dnf config-manager --set-enabled "$repo"; then
        log_error "Failed to enable repository: $repo"
        return 1
      fi
      ;;
    arch)
      # Arch repositories are enabled by uncommenting in /etc/pacman.conf
      log_warn "Manual repository enabling in /etc/pacman.conf may be required"
      log_info "Please uncomment [$repo] section in /etc/pacman.conf if needed"
      ;;
    debian)
      # Debian repositories are enabled by uncommenting in sources.list
      log_warn "Manual repository enabling in /etc/apt/sources.list.d may be required"
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Repository enabled: $repo"
  return 0
}

# Function: repo_disable
# Purpose: Disable a repository
# Parameters:
#   $1 - Repository name
# Returns: 0 on success, 1 on failure
repo_disable() {
  local repo="${1:-}"
  
  if [[ -z "$repo" ]]; then
    log_error "No repository specified"
    return 1
  fi
  
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Disabling repository '$repo' for $distro"
  
  case "$distro" in
    fedora)
      if ! sudo dnf config-manager --set-disabled "$repo"; then
        log_error "Failed to disable repository: $repo"
        return 1
      fi
      ;;
    arch)
      log_warn "Manual repository disabling in /etc/pacman.conf may be required"
      log_info "Please comment out [$repo] section in /etc/pacman.conf if needed"
      ;;
    debian)
      log_warn "Manual repository disabling in /etc/apt/sources.list.d may be required"
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Repository disabled: $repo"
  return 0
}

# Function: repo_update
# Purpose: Update repository metadata/cache
# Returns: 0 on success, 1 on failure
repo_update() {
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Updating repository metadata for $distro"
  
  case "$distro" in
    fedora)
      if ! sudo dnf makecache --refresh; then
        log_error "Failed to update repository metadata"
        return 1
      fi
      ;;
    arch)
      if ! sudo pacman -Sy; then
        log_error "Failed to update repository metadata"
        return 1
      fi
      ;;
    debian)
      if ! sudo apt-get update; then
        log_error "Failed to update repository metadata"
        return 1
      fi
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Repository metadata updated successfully"
  return 0
}

