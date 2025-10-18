#!/usr/bin/env bash
# NOTE: This function installs or updates Ollama.
# On Arch the package manager (pacman) should be used via pm_install;
# on other distributions fall back to the official install script.

#TODO: simplify and test

install_ollama() {
  local action

  # Check if Ollama is already installed
  if command -v ollama &>/dev/null; then
    action="Updating"
    log_info "$action Ollama..."
  else
    action="Installing"
    log_info "$action Ollama..."
  fi

  case "$CURRENT_DISTRO" in
    arch)
      # On Arch choose the appropriate package based on GPU detected by
      # the shared utility. Prefer vendor-specific packages when available.
      log_debug "Detecting GPU to select correct Ollama package for Arch..."

      # Source gpu detection utility (quiet when sourced)
      if [[ -f "${PROJECT_ROOT:-src}/src/utils/gpu_detect.sh" ]]; then
        # shellcheck disable=SC1090
        source "${PROJECT_ROOT:-src}/src/utils/gpu_detect.sh"
      else
        # shellcheck disable=SC1090
        source "$(dirname "${BASH_SOURCE[0]}")/../utils/gpu_detect.sh"
      fi

      gpu=$(detect_gpu_vendor)
      log_debug "GPU detection result: ${gpu}"

      case "$gpu" in
        nvidia) pkg="ollama-cuda" ;; 
        amd)    pkg="ollama-rocm" ;; 
        *)      pkg="ollama" ;;
      esac

      log_info "Attempting to ${action} Ollama package '${pkg}' via package manager..."
      if pm_install "${pkg}"; then
        if command -v ollama &>/dev/null; then
          log_info "Ollama ${action,,} completed successfully (package ${pkg})"
          return 0
        else
          log_warn "Package ${pkg} installed but 'ollama' binary not found. Falling back to official installer."
        fi
      else
        log_warn "Failed to install package ${pkg} via package manager. Falling back to official installer."
      fi

      ;;
    *)
      log_debug "Downloading and running Ollama install script..."
      # Execute curl command directly instead of passing it to log_cmd with pipes
      if ! curl -fsSL https://ollama.com/install.sh | sed 's/--add-repo/addrepo/' | sh; then
        log_error "Failed to $action Ollama"
        return 1
      fi
      ;;
  esac

  # Verify installation/update
  if command -v ollama &>/dev/null; then
    log_info "Ollama ${action,,} completed successfully"
    return 0
  else
    log_error "Ollama binary not found after $action"
    return 1
  fi
}