#!/usr/bin/env bash

# Function: nvidia_cuda_setup
# Purpose: Install NVIDIA CUDA toolkit (cross-distro)
# Returns: 0 on success, 1 on failure
nvidia_cuda_setup() {
  log_info "Setting up NVIDIA CUDA..."

  local distro
  distro=$(detect_distro) || return 1

  # Check if system has NVIDIA GPU
  if ! lspci | grep -i nvidia &>/dev/null; then
    log_error "No NVIDIA GPU detected in this system"
    return 1
  fi

  local arch
  arch=$(uname -m)

  case "$distro" in
    fedora)
      local distro_version
      distro_version=$(get_distro_version)
      local cuda_repo
      cuda_repo="https://developer.download.nvidia.com/compute/cuda/repos/fedora${distro_version}/${arch}/cuda-fedora${distro_version}.repo"

      log_debug "Adding CUDA repository for Fedora $distro_version..."
      if ! sudo dnf config-manager addrepo --from-repofile="$cuda_repo"; then
        log_error "Failed to add CUDA repository"
        return 1
      fi

      log_debug "Cleaning DNF cache..."
      if ! sudo dnf clean all; then
        log_error "Failed to clean DNF cache"
        return 1
      fi

      log_debug "Disabling nvidia-driver module..."
      if ! sudo dnf module disable -y nvidia-driver; then
        log_warn "Failed to disable nvidia-driver module - this might be normal"
      fi

      log_debug "Setting package exclusions..."
      local exclude_pkgs="nvidia-driver,nvidia-modprobe,nvidia-persistenced,nvidia-settings,nvidia-libXNVCtrl,nvidia-xconfig"
      if ! sudo dnf config-manager setopt "cuda-fedora${distro_version}-${arch}.exclude=${exclude_pkgs}"; then
        log_error "Failed to set package exclusions"
        return 1
      fi

      log_debug "Installing CUDA toolkit..."
      if ! pm_install cuda-toolkit; then
        log_error "Failed to install CUDA toolkit"
        return 1
      fi
      ;;
    #TODO: Research more about arch and debian to make sure they are correct
    arch)
      log_debug "Installing CUDA from official repositories..."
      if ! pm_install cuda cuda-tools; then
        log_error "Failed to install CUDA toolkit"
        return 1
      fi
      ;;
    debian)
      log_debug "Installing CUDA from NVIDIA repository..."
      # Add NVIDIA CUDA repository
      local cuda_keyring="/usr/share/keyrings/cuda-archive-keyring.gpg"
      if [[ ! -f "$cuda_keyring" ]]; then
        log_debug "Downloading CUDA keyring..."
        wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
        if ! sudo dpkg -i cuda-keyring_1.1-1_all.deb; then
          log_error "Failed to install CUDA keyring"
          rm -f cuda-keyring_1.1-1_all.deb
          return 1
        fi
        rm -f cuda-keyring_1.1-1_all.deb
        sudo apt-get update
      fi

      log_debug "Installing CUDA toolkit..."
      if ! pm_install cuda-toolkit; then
        log_error "Failed to install CUDA toolkit"
        return 1
      fi
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac

  # Verify installation
  if ! command -v nvcc &>/dev/null; then
    log_error "CUDA toolkit installation failed - nvcc not found"
    log_info "You may need to add CUDA to your PATH:"
    log_info "export PATH=/usr/local/cuda/bin:\$PATH"
    return 1
  fi

  log_info "CUDA setup completed successfully"
  log_debug "Note: You may need to add CUDA libraries to your LD_LIBRARY_PATH"
  return 0
}

# Function: switch_nvidia_open
# Purpose: Switch to NVIDIA open source drivers (cross-distro)
# Returns: 0 on success, 1 on failure
switch_nvidia_open() {
  log_info "Switching to NVIDIA open source drivers..."

  local distro
  distro=$(detect_distro) || return 1

  # Check if system has NVIDIA GPU
  if ! lspci | grep -i nvidia &>/dev/null; then
    log_error "No NVIDIA GPU detected in this system"
    return 1
  fi

  # Check for root privileges
  if [[ $EUID -ne 0 ]]; then
    log_error "This function must be run as root or with sudo privileges"
    return 1
  fi

  case "$distro" in
    fedora)
      local nvidia_kmod_macro="/etc/rpm/macros.nvidia-kmod"
      log_debug "Creating NVIDIA kmod macro file..."
      if ! echo "%_with_kmod_nvidia_open 1" | sudo tee "$nvidia_kmod_macro" >/dev/null; then
        log_error "Failed to create NVIDIA kmod macro file"
        return 1
      fi

      local current_kernel
      current_kernel=$(uname -r)
      log_debug "Rebuilding NVIDIA modules for kernel $current_kernel..."
      if ! akmods --kernels "$current_kernel" --rebuild; then
        log_warn "Initial rebuild failed, attempting with --force..."
        if ! akmods --kernels "$current_kernel" --rebuild --force; then
          log_error "Failed to rebuild NVIDIA modules"
          return 1
        fi
      fi

      log_debug "Disabling RPMFusion non-free NVIDIA driver repository..."
      if ! sudo dnf --disablerepo rpmfusion-nonfree-nvidia-driver; then
        log_error "Failed to disable RPMFusion non-free NVIDIA driver repository"
        return 1
      fi

      log_info "NVIDIA open source driver setup completed"
      log_info "Please wait 10-20 minutes for the NVIDIA modules to build, then reboot"
      log_info "After reboot, verify installation with:"
      log_info "1. 'modinfo nvidia | grep license' - should show 'Dual MIT/GPL'"
      log_info "2. 'rpm -qa kmod-nvidia*' - should show kmod-nvidia-open package"
      ;;
    #TODO: Research more about arch and debian to make sure they are correct
    arch)
      log_info "Installing NVIDIA open source drivers for Arch..."
      if ! pm_install nvidia-open-dkms nvidia-utils; then
        log_error "Failed to install NVIDIA open drivers"
        return 1
      fi

      log_info "NVIDIA open source driver setup completed"
      log_info "Please reboot for changes to take effect"
      log_info "After reboot, verify installation with:"
      log_info "1. 'modinfo nvidia | grep license' - should show 'Dual MIT/GPL'"
      ;;
    debian)
      log_info "Installing NVIDIA open source drivers for Debian..."
      # Add contrib and non-free repositories if not already added
      if ! grep -q "contrib" /etc/apt/sources.list; then
        log_warn "Enabling contrib and non-free repositories..."
        sudo add-apt-repository -y contrib
        sudo add-apt-repository -y non-free
        sudo apt-get update
      fi

      if ! pm_install nvidia-driver nvidia-kernel-open-dkms; then
        log_error "Failed to install NVIDIA open drivers"
        return 1
      fi

      log_info "NVIDIA open source driver setup completed"
      log_info "Please reboot for changes to take effect"
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac

  return 0
}

# TEST: Setup VA-API for NVIDIA RTX series.
vaapi_setup() {
  log_info "Setting up VA-API for NVIDIA RTX series..."

  # Check if system has NVIDIA GPU
  if ! lspci | grep -i nvidia &>/dev/null; then
    log_error "No NVIDIA GPU detected in this system"
    return 1
  fi

  # Install required packages
  log_debug "Installing VA-API related packages..."
  local packages=(
    "meson"
    "libva-devel"
    "gstreamer1-plugins-bad-freeworld"
    "nv-codec-headers"
    "nvidia-vaapi-driver"
    "gstreamer1-plugins-bad-free-devel"
  )

  if ! sudo dnf install -y "${packages[@]}"; then
    log_error "Failed to install VA-API packages"
    return 1
  fi

  local env_file="/etc/environment"
  local env_vars=(
    "MOZ_DISABLE_RDD_SANDBOX=1"
    "LIBVA_DRIVER_NAME=nvidia"
    "__GLX_VENDOR_LIBRARY_NAME=nvidia"
  )

  log_debug "Setting up environment variables in $env_file..."

  # Check if variables already exist
  local need_append=false
  for var in "${env_vars[@]}"; do
    if ! grep -q "^${var}$" "$env_file" 2>/dev/null; then
      need_append=true
      break
    fi
  done

  if [[ "$need_append" == "true" ]]; then
    if ! printf '%s\n' "${env_vars[@]}" | sudo tee -a "$env_file" >/dev/null; then
      log_error "Failed to update environment variables in $env_file"
      return 1
    fi
  else
    log_debug "Environment variables already set in $env_file"
  fi

  log_info "VA-API setup completed successfully"
  log_debug "Note: You may need to reboot for changes to take effect"
  return 0
}