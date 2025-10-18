#!/usr/bin/env bash
# Function: install_lazygit
# Purpose: Installs Lazygit terminal UI for git with distro-specific methods
# Returns: 0 on success, 1 on failure
install_lazygit() {
  log_info "Installing Lazygit..."

  case "$CURRENT_DISTRO" in
    fedora)
      # Use COPR repository on Fedora
      if ! repo_add_copr "atim/lazygit"; then
        log_error "Failed to add Lazygit COPR repository"
        return 1
      fi
      if ! pm_install "lazygit"; then
        log_error "Failed to install Lazygit"
        return 1
      fi
      ;;
    arch)
      # Lazygit is in community repository on Arch
      if ! pm_install "lazygit"; then
        log_error "Failed to install Lazygit"
        return 1
      fi
      ;;
    debian)
      # On Debian, try from official repos first, fallback to GitHub release
      log_info "Attempting to install from Debian repositories..."
      if ! pm_install "lazygit"; then
        log_warn "Lazygit not available in repositories, installing from GitHub..."
        if ! install_lazygit_from_github; then
          log_error "Failed to install Lazygit from GitHub"
          return 1
        fi
      fi
      ;;
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac

  log_info "Lazygit installation completed."
  return 0
}

# Function: install_lazygit_from_github
# Purpose: Install Lazygit from GitHub releases (fallback for Debian)
# Returns: 0 on success, 1 on failure
install_lazygit_from_github() {
  log_info "Installing Lazygit from GitHub releases..."
  
  local temp_dir
  temp_dir=$(mktemp -d)
  
  # Get latest release URL
  local release_url
  release_url=$(curl -s https://api.github.com/repos/jesseduffield/lazygit/releases/latest | \
    grep "browser_download_url.*Linux_x86_64.tar.gz" | \
    cut -d '"' -f 4)
  
  if [[ -z "$release_url" ]]; then
    log_error "Could not determine Lazygit release URL"
    rm -rf "$temp_dir"
    return 1
  fi
  
  log_info "Downloading Lazygit from: $release_url"
  if ! wget -P "$temp_dir" "$release_url"; then
    log_error "Failed to download Lazygit"
    rm -rf "$temp_dir"
    return 1
  fi
  
  # Extract and install
  if ! tar -xzf "$temp_dir"/*.tar.gz -C "$temp_dir"; then
    log_error "Failed to extract Lazygit"
    rm -rf "$temp_dir"
    return 1
  fi
  
  if ! sudo install "$temp_dir/lazygit" /usr/local/bin/lazygit; then
    log_error "Failed to install Lazygit binary"
    rm -rf "$temp_dir"
    return 1
  fi
  
  rm -rf "$temp_dir"
  log_info "Lazygit installed successfully from GitHub"
  return 0
}


