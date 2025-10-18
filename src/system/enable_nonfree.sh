#!/usr/bin/env bash

# Function: enable_rpm_fusion
# Purpose: Enable additional repositories (distro-agnostic wrapper)
# Returns: 0 on success, 1 on failure
enable_rpm_fusion() {
  # Use the distro-agnostic repository manager function
  if ! enable_nonfree_repositories; then
    log_error "Failed to enable additional repositories"
    return 1
  fi
}

# Function: enable_nonfree_repositories
# Purpose: Enable non-free repositories for additional software
# Returns: 0 on success, 1 on failure
#TODO: rename this function to we add this because we need this on fedora and debian
#to be able to install non-free packages like nvidia drivers and ffmpeg etc.
enable_nonfree_repositories() {
  local distro
  distro=$(detect_distro) || return 1
  
  case "$distro" in
    fedora)
      log_info "Enabling RPM Fusion repositories for Fedora"
      if ! sudo dnf install -y \
        "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
        "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"; then
        log_error "Failed to enable RPM Fusion repositories"
        return 1
      fi
      log_success "RPM Fusion repositories enabled"
      ;;
    arch)
    #TODO: research needed for this, we might be need to enable extras or something...
      log_info "Arch Linux uses AUR for additional packages"
      log_info "No additional repositories needed (using AUR helper)"
      ;;
    debian)
    #TODO: need proper research for this
      log_info "Enabling contrib and non-free repositories for Debian"
      # Enable contrib and non-free components
      if ! sudo add-apt-repository -y contrib; then
        log_warn "Failed to add contrib repository"
      fi
      if ! sudo add-apt-repository -y non-free; then
        log_warn "Failed to add non-free repository"
      fi
      if ! sudo apt-get update; then
        log_error "Failed to update package lists"
        return 1
      fi
      log_success "Additional Debian repositories enabled"
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  return 0
}
