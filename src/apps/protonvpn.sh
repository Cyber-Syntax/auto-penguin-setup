#!/usr/bin/env bash
# Function: install_protonvpn
# Purpose: Installs ProtonVPN with distro-specific repository setup
# Returns: 0 on success, 1 on failure
install_protonvpn() {
  log_info "Installing ProtonVPN..."

  case "$CURRENT_DISTRO" in
    fedora)
      # Fedora installation
      log_info "Installing ProtonVPN for Fedora..."
      
      local fedora_version
      fedora_version=$(awk '{print $3}' /etc/fedora-release)
      local repo_url="https://repo.protonvpn.com/fedora-${fedora_version}-stable"
      local key_url="${repo_url}/public_key.asc"
      local rpm_url="${repo_url}/protonvpn-stable-release/protonvpn-stable-release-1.0.2-1.noarch.rpm"

      # Import the GPG key
      log_info "Importing ProtonVPN GPG key..."
      if ! sudo rpm --import "${key_url}"; then
        log_error "Failed to import ProtonVPN GPG key"
        return 1
      fi

      # Download and install the repository package
      if [[ ! -f "/etc/yum.repos.d/protonvpn-stable.repo" ]]; then
        log_info "Downloading and installing ProtonVPN repository..."
        local tmp_rpm
        tmp_rpm=$(mktemp)

        if ! wget -O "${tmp_rpm}" "${rpm_url}"; then
          log_error "Failed to download ProtonVPN repository package"
          rm -f "${tmp_rpm}"
          return 1
        fi

        if ! sudo dnf install --setopt=assumeyes=1 "${tmp_rpm}"; then
          log_error "Failed to install ProtonVPN repository"
          rm -f "${tmp_rpm}"
          return 1
        fi

        rm -f "${tmp_rpm}"
      else
        log_info "ProtonVPN repository already installed"
      fi

      # Refresh repositories
      log_info "Refreshing package repositories..."
      sudo dnf check-update --refresh --setopt=assumeyes=1 || true

      # Install ProtonVPN
      if ! pm_install "proton-vpn-gnome-desktop"; then
        log_error "Failed to install ProtonVPN GNOME desktop integration"
        return 1
      fi
      ;;

    arch)
      # Arch Linux - ProtonVPN is in official repos
      log_info "Installing ProtonVPN from Arch repositories..."
      if ! pm_install "proton-vpn-gtk-app"; then
        log_error "Failed to install ProtonVPN"
        return 1
      fi
      ;;

    debian)
      # Debian/Ubuntu installation
      log_info "Installing ProtonVPN for Debian..."
      
      # Install prerequisites
      if ! pm_install "wget"; then
        log_error "Failed to install prerequisites"
        return 1
      fi
      
      local repo_package="protonvpn-stable-release_1.0.8_all.deb"
      local repo_url="https://repo.protonvpn.com/debian/dists/stable/main/binary-all/${repo_package}"
      local expected_checksum="0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180"
      
      local tmp_dir
      tmp_dir=$(mktemp -d)
      
      # Download the repository package
      log_info "Downloading ProtonVPN repository package..."
      if ! wget -O "${tmp_dir}/${repo_package}" "${repo_url}"; then
        log_error "Failed to download ProtonVPN repository package"
        rm -rf "${tmp_dir}"
        return 1
      fi
      
      # Verify checksum
      log_info "Verifying package checksum..."
      if ! echo "${expected_checksum} ${tmp_dir}/${repo_package}" | sha256sum --check -; then
        log_error "Checksum verification failed for ProtonVPN repository package"
        rm -rf "${tmp_dir}"
        return 1
      fi
      
      # Install the repository package
      log_info "Installing ProtonVPN repository..."
      if ! sudo dpkg -i "${tmp_dir}/${repo_package}"; then
        log_error "Failed to install ProtonVPN repository package"
        rm -rf "${tmp_dir}"
        return 1
      fi
      
      rm -rf "${tmp_dir}"
      
      # Update package lists
      if ! pm_update; then
        log_error "Failed to update package lists"
        return 1
      fi
      
      # Install ProtonVPN
      if ! pm_install "proton-vpn-gnome-desktop"; then
        log_error "Failed to install ProtonVPN GNOME desktop integration"
        return 1
      fi
      ;;

    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac

  log_info "ProtonVPN installation completed successfully"
  return 0
}

