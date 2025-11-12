#!/usr/bin/env bash
# ueberzugpp.sh
# Purpose: Install ueberzugpp for image preview in terminals

# Function: add_ueberzugpp_repo_fedora
# Purpose: Add OpenSUSE repository for ueberzugpp on Fedora
# Returns: 0 on success, 1 on failure
add_ueberzugpp_repo_fedora() {
  log_info "Adding ueberzugpp repository for Fedora..."

  local version
  version=$(get_distro_version)

  # Map version to repository name
  local repo_version
  case "$version" in
    40)
      repo_version="Fedora_40"
      ;;
    41)
      repo_version="Fedora_41"
      ;;
    42)
      repo_version="Fedora_42"
      ;;
    *)
      # Default to Rawhide for unknown versions
      log_warn "Unknown Fedora version '$version', using Rawhide repository"
      repo_version="Fedora_Rawhide"
      ;;
  esac

  local repo_url="https://download.opensuse.org/repositories/home:justkidding/${repo_version}/home:justkidding.repo"
  log_info "Adding repository from: $repo_url"

  if ! sudo dnf config-manager addrepo --from-repofile="$repo_url"; then
    log_error "Failed to add ueberzugpp repository"
    return 1
  fi

  log_success "Successfully added ueberzugpp repository"
  return 0
}

# Function: add_ueberzugpp_repo_debian
# Purpose: Add OpenSUSE repository for ueberzugpp on Debian/Ubuntu
# Returns: 0 on success, 1 on failure
add_ueberzugpp_repo_debian() {
  log_info "Adding ueberzugpp repository for Debian/Ubuntu..."

  # Detect if this is Ubuntu or Debian
  local os_id=""
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    os_id="${ID:-}"
  fi

  local repo_name
  local version
  version=$(get_distro_version)

  case "$os_id" in
    ubuntu|pop|linuxmint)
      # Map Ubuntu version to repository
      case "$version" in
        22.04)
          repo_name="xUbuntu_22.04"
          ;;
        23.04)
          repo_name="xUbuntu_23.04"
          ;;
        24.04)
          repo_name="xUbuntu_24.04"
          ;;
        24.10)
          repo_name="xUbuntu_24.10"
          ;;
        25.04)
          repo_name="xUbuntu_25.04"
          ;;
        *)
          # Default to latest LTS
          log_warn "Unknown Ubuntu version '$version', using 24.04 repository"
          repo_name="xUbuntu_24.04"
          ;;
      esac
      ;;
    debian)
      # Map Debian version to repository
      case "$version" in
        12)
          repo_name="Debian_12"
          ;;
        13)
          repo_name="Debian_13"
          ;;
        *)
          # Default to Testing for unknown versions
          log_warn "Unknown Debian version '$version', using Testing repository"
          repo_name="Debian_Testing"
          ;;
      esac
      ;;
    *)
      # Generic fallback for Debian-based systems
      log_warn "Unknown Debian-based system, using Debian Testing repository"
      repo_name="Debian_Testing"
      ;;
  esac

  local repo_url="http://download.opensuse.org/repositories/home:/justkidding/${repo_name}/"
  local key_url="https://download.opensuse.org/repositories/home:justkidding/${repo_name}/Release.key"

  log_info "Adding repository: $repo_url"

  # Add repository to sources list
  if ! echo "deb $repo_url /" | sudo tee /etc/apt/sources.list.d/home:justkidding.list >/dev/null; then
    log_error "Failed to add repository to sources list"
    return 1
  fi

  # Add GPG key
  log_info "Adding repository GPG key..."
  if ! curl -fsSL "$key_url" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_justkidding.gpg >/dev/null; then
    log_error "Failed to add repository GPG key"
    return 1
  fi

  # Update package lists
  log_info "Updating package lists..."
  if ! sudo apt-get update; then
    log_error "Failed to update package lists"
    return 1
  fi

  log_success "Successfully added ueberzugpp repository"
  return 0
}

# Function: install_ueberzugpp
# Purpose: Install ueberzugpp for image preview in terminals
# Returns: 0 on success, 1 on failure
install_ueberzugpp() {
  log_info "Installing ueberzugpp..."

  case "$CURRENT_DISTRO" in
    fedora)
      # Add OpenSUSE repository and install
      if ! add_ueberzugpp_repo_fedora; then
        log_error "Failed to add ueberzugpp repository"
        return 1
      fi
      if ! pm_install "ueberzugpp"; then
        log_error "Failed to install ueberzugpp"
        return 1
      fi
      ;;
    arch)
      # ueberzugpp is in official Arch repositories
      if ! pm_install "ueberzugpp"; then
        log_error "Failed to install ueberzugpp"
        return 1
      fi
      ;;
    debian)
      # Add OpenSUSE repository and install
      if ! add_ueberzugpp_repo_debian; then
        log_error "Failed to add ueberzugpp repository"
        return 1
      fi
      if ! pm_install "ueberzugpp"; then
        log_error "Failed to install ueberzugpp"
        return 1
      fi
      ;;
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac

  log_success "ueberzugpp installation completed"
  return 0
}
