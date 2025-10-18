#!/usr/bin/env bash
# Function: install_vscode
# Purpose: Installs Visual Studio Code with distro-specific repository setup
# Returns: 0 on success, 1 on failure
install_vscode() {
  log_info "Installing Visual Studio Code..."

  case "$CURRENT_DISTRO" in
    fedora)
      # Fedora/RPM-based installation
      log_info "Adding Visual Studio Code repository for Fedora..."
      
      # Import Microsoft GPG key
      if ! sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc; then
        log_error "Failed to import Microsoft GPG key"
        return 1
      fi
      
      # Create repository file
      local repo_file="/etc/yum.repos.d/vscode.repo"
      if [[ ! -f "$repo_file" ]]; then
        local repo_content="[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc"
        
        if ! echo "$repo_content" | sudo tee "$repo_file" >/dev/null; then
          log_error "Failed to create VS Code repository file"
          return 1
        fi
      fi
      
      # Update and install
      if ! pm_update; then
        log_warn "Repository update had warnings, continuing..."
      fi
      
      if ! pm_install "code"; then
        log_error "Failed to install Visual Studio Code"
        return 1
      fi
      ;;
      
    arch)
      # Arch Linux - VS Code is in AUR repo
      log_info "Installing Visual Studio Code from AUR..."
      if ! repo_add "visual-studio-code-bin"; then
        log_error "Failed to install Visual Studio Code"
        return 1
      fi
      ;;
      
    debian)
    # https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64
  # The easiest way to install Visual Studio Code for Debian/Ubuntu based distributions is to download and install the .deb package (64-bit), 
  #either through the graphical software center if it's available, or through the command line with:
  #     sudo apt install ./<file>.deb

  # # If you're on an older Linux distribution, you will need to run this instead:
  # # sudo dpkg -i <file>.deb
  # # sudo apt-get install -f # Install dependencies
  # To automatically install the apt repository and signing key, such as on a non-interactive terminal, run the following command first:
  #echo "code code/add-microsoft-repo boolean true" | sudo debconf-set-selections
  # To manually install the apt repository:
#   sudo apt-get install wget gpg
# wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
# sudo install -D -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/microsoft.gpg
# rm -f microsoft.gpg
# Create a /etc/apt/sources.list.d/vscode.sources file with the following contents to add a reference to the upstream package repository:
# Types: deb
# URIs: https://packages.microsoft.com/repos/code
# Suites: stable
# Components: main
# Architectures: amd64,arm64,armhf
# Signed-By: /usr/share/keyrings/microsoft.gpg
# lastly update the package cache and install the package:
# sudo apt update
# sudo apt install code # or code-insiders



      # Debian/Ubuntu installation
      log_info "Adding Visual Studio Code repository for Debian..."
      
      # Install prerequisites
      if ! pm_install "wget" "gpg"; then
        log_error "Failed to install prerequisites"
        return 1
      fi
      
      # Import Microsoft GPG key
      if ! wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | \
        sudo tee /usr/share/keyrings/packages.microsoft.gpg >/dev/null; then
        log_error "Failed to import Microsoft GPG key"
        return 1
      fi

      # Install microsoft.gpg
      if ! sudo install -D -o root -g root -m 644 /usr/share/keyrings/packages.microsoft.gpg /usr/share/keyrings/packages.microsoft.gpg; then
        log_error "Failed to install Microsoft GPG key"
        return 1
      fi

      #TESTING: Remove if below add repos works
#       # Create a /etc/apt/sources.list.d/vscode.sources file
#       if [[ ! -f /etc/apt/sources.list.d/vscode.sources ]]; then
#         local sources_content="[Source]
# Types: deb
# URIs: https://packages.microsoft.com/repos/code
# Suites: stable
# Components: main
# Architectures: amd64,arm64,armhf
# Signed-By: /usr/share/keyrings/packages.microsoft.gpg"
#         if ! echo "$sources_content" | sudo tee /etc/apt/sources.list.d/vscode.sources >/dev/null; then
#           log_error "Failed to create VS Code sources file"
#           return 1
#         fi
#       fi
      
      #TESTING: This below much better than above sources file creation but need to test is it works
      # Add repository (redundant if sources file created)
      if ! echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | \
        sudo tee /etc/apt/sources.list.d/vscode.list >/dev/null; then
        log_error "Failed to add VS Code repository"
        return 1
      fi
      
      # Update and install
      if ! pm_update; then
        log_error "Failed to update package lists"
        return 1
      fi
      
      if ! pm_install "code"; then
        log_error "Failed to install Visual Studio Code"
        return 1
      fi
      ;;
      
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac

  log_info "Visual Studio Code installation completed."
  return 0
}


