#!/usr/bin/env bash
# setup_default_apps.sh - Configure default applications using mimeapps.list
# Uses INI configuration from variables.ini

# Source guard to prevent re-sourcing
[[ -n "${_SETUP_DEFAULT_APPS_SOURCED:-}" ]] && return 0
readonly _SETUP_DEFAULT_APPS_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/config.sh
source src/core/ini_parser.sh

# Helper function to convert application names to proper desktop file names
# and verify if they exist on the system
app_name_to_desktop_file() {
  local app_name="$1"
  local desktop_file=""

  # If app_name already ends with .desktop, use it as is
  if [[ "$app_name" == *.desktop ]]; then
    desktop_file="$app_name"
  else
    # Common application name mappings
    #TODO: need better way to handle this
    case "$app_name" in
      "brave")
        desktop_file="brave-browser.desktop"
        ;;
      "chrome" | "google-chrome" | "googlechrome")
        desktop_file="google-chrome.desktop"
        ;;
      "firefox-esr")
        desktop_file="firefox-esr.desktop"
        ;;
      "vscode" | "code")
        desktop_file="code.desktop"
        ;;
      "librewolf")
        desktop_file="librewolf.desktop"
        ;;
      "chromium")
        desktop_file="chromium-browser.desktop"
        ;;
      "obsidian")
        desktop_file="obsidian.desktop"
        ;;
      *)
        # For standard applications, just append .desktop
        desktop_file="${app_name}.desktop"
        ;;
    esac
  fi

  # Check if the desktop file exists in standard locations
  local found=false
  local search_paths=(
    "/usr/share/applications"
    "/usr/local/share/applications"
    "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  )

  for path in "${search_paths[@]}"; do
    if [[ -f "$path/$desktop_file" ]]; then
      found=true
      break
    fi
  done

  if ! $found; then
    log_warn "Desktop file '$desktop_file' not found. The application may not be installed."
  fi

  # Return the desktop file name regardless of whether it was found
  # This allows the user's configuration to be written even if the app isn't installed yet
  echo "$desktop_file"
}

# Creates or updates the mimeapps.list file to set default applications
# based on user preferences stored in variables.ini
setup_default_applications() {
  log_info "Setting up default applications with mimeapps.list..."

  # Load variables.ini configuration
  local variables_file
  variables_file=$(load_ini_config "variables.ini")

  # Verify the variables file exists
  if [[ -z "$variables_file" || ! -f "$variables_file" ]]; then
    log_error "Failed to load variables configuration"
    return 1
  fi

  # Parse the INI file
  if ! parse_ini_file "$variables_file"; then
    log_error "Failed to parse variables.ini"
    return 1
  fi

  # Get the user's home directory for creating mimeapps.list
  local user_home
  user_home=$(getent passwd "$USER" | cut -d: -f6)
  local config_dir="${user_home}/.config"
  local mimeapps_file="${config_dir}/mimeapps.list"

  #TODO: are we need this? All of the distros create .config by default
  # # Make sure the config directory exists
  # if [[ ! -d "$config_dir" ]]; then
  #   log_debug "Creating config directory at $config_dir..."
  #   if ! mkdir -p "$config_dir"; then
  #     log_error "Failed to create config directory at $config_dir"
  #     return 1
  #   fi
  # fi

  # Create backup if the file already exists
  if [[ -f "$mimeapps_file" ]]; then
    log_info "Creating backup of existing mimeapps.list..."
    local backup_file
    backup_file="${mimeapps_file}.bak.$(date +%Y%m%d%H%M%S)"
    if ! cp "$mimeapps_file" "$backup_file"; then
      log_error "Failed to create backup of mimeapps.list"
      return 1
    fi
    log_info "Backup created at $backup_file"
  fi

  # Load the default applications from variables.ini
  local browser_name terminal_name file_manager_name image_viewer_name text_editor_name

  browser_name=$(get_ini_value "default_applications" "browser")
  terminal_name=$(get_ini_value "default_applications" "terminal")
  file_manager_name=$(get_ini_value "default_applications" "file_manager")
  image_viewer_name=$(get_ini_value "default_applications" "image_viewer")
  text_editor_name=$(get_ini_value "default_applications" "text_editor")

  # Convert application names to proper desktop file names
  local browser="" terminal="" file_manager="" image_viewer="" text_editor=""

  if [[ -n "$browser_name" ]]; then
    browser=$(app_name_to_desktop_file "$browser_name")
    log_debug "Browser '$browser_name' mapped to desktop file: $browser"
  fi

  if [[ -n "$terminal_name" ]]; then
    terminal=$(app_name_to_desktop_file "$terminal_name")
    log_debug "Terminal '$terminal_name' mapped to desktop file: $terminal"
  fi

  if [[ -n "$file_manager_name" ]]; then
    file_manager=$(app_name_to_desktop_file "$file_manager_name")
    log_debug "File manager '$file_manager_name' mapped to desktop file: $file_manager"
  fi

  if [[ -n "$image_viewer_name" ]]; then
    image_viewer=$(app_name_to_desktop_file "$image_viewer_name")
    log_debug "Image viewer '$image_viewer_name' mapped to desktop file: $image_viewer"
  fi

  if [[ -n "$text_editor_name" ]]; then
    text_editor=$(app_name_to_desktop_file "$text_editor_name")
    log_debug "Text editor '$text_editor_name' mapped to desktop file: $text_editor"
  fi

  # Define the default applications section of mimeapps.list
  log_debug "Generating default applications section..."

  local default_section="[Default Applications]\n"

  # Process browser associations
  if [[ -n "$browser" ]]; then
    local browser_mimes
    mapfile -t browser_mimes < <(get_ini_section "mime_browser")

    for mime in "${browser_mimes[@]}"; do
      [[ -n "$mime" ]] && default_section+="${mime}=${browser}\n"
    done
  fi

  # Process image viewer associations
  if [[ -n "$image_viewer" ]]; then
    local image_mimes
    mapfile -t image_mimes < <(get_ini_section "mime_image_viewer")

    for mime in "${image_mimes[@]}"; do
      [[ -n "$mime" ]] && default_section+="${mime}=${image_viewer}\n"
    done
  fi

  # Process text editor associations
  if [[ -n "$text_editor" ]]; then
    local text_mimes
    mapfile -t text_mimes < <(get_ini_section "mime_text_editor")

    for mime in "${text_mimes[@]}"; do
      [[ -n "$mime" ]] && default_section+="${mime}=${text_editor}\n"
    done
  fi

  # Process file manager associations
  if [[ -n "$file_manager" ]]; then
    local file_mimes
    mapfile -t file_mimes < <(get_ini_section "mime_file_manager")

    for mime in "${file_mimes[@]}"; do
      [[ -n "$mime" ]] && default_section+="${mime}=${file_manager}\n"
    done
  fi

  # Process terminal associations
  if [[ -n "$terminal" ]]; then
    local terminal_mimes
    mapfile -t terminal_mimes < <(get_ini_section "mime_terminal")

    for mime in "${terminal_mimes[@]}"; do
      [[ -n "$mime" ]] && default_section+="${mime}=${terminal}\n"
    done
  fi

  # Define the Added Associations section - adding semicolons for proper formatting
  log_debug "Generating added associations section..."

  local added_section="\n[Added Associations]\n"

  # Add browser associations
  if [[ -n "$browser" ]]; then
    local browser_mimes
    mapfile -t browser_mimes < <(get_ini_section "mime_browser")

    for mime in "${browser_mimes[@]}"; do
      [[ -n "$mime" ]] && added_section+="${mime}=${browser};\n"
    done
  fi

  # Add image viewer associations
  if [[ -n "$image_viewer" ]]; then
    local image_mimes
    mapfile -t image_mimes < <(get_ini_section "mime_image_viewer")

    for mime in "${image_mimes[@]}"; do
      [[ -n "$mime" ]] && added_section+="${mime}=${image_viewer};\n"
    done
  fi

  # Add text editor associations
  if [[ -n "$text_editor" ]]; then
    local text_mimes
    mapfile -t text_mimes < <(get_ini_section "mime_text_editor")

    for mime in "${text_mimes[@]}"; do
      [[ -n "$mime" ]] && added_section+="${mime}=${text_editor};\n"
    done
  fi

  # Add file manager associations
  if [[ -n "$file_manager" ]]; then
    local file_mimes
    mapfile -t file_mimes < <(get_ini_section "mime_file_manager")

    for mime in "${file_mimes[@]}"; do
      [[ -n "$mime" ]] && added_section+="${mime}=${file_manager};\n"
    done
  fi

  # Add terminal associations
  if [[ -n "$terminal" ]]; then
    local terminal_mimes
    mapfile -t terminal_mimes < <(get_ini_section "mime_terminal")

    for mime in "${terminal_mimes[@]}"; do
      [[ -n "$mime" ]] && added_section+="${mime}=${terminal};\n"
    done
  fi

  # Combine everything into the final mimeapps.list content
  local mimeapps_content="${default_section}${added_section}"

  # Write the file
  log_debug "Writing mimeapps.list to $mimeapps_file..."
  if ! echo -e "$mimeapps_content" >"$mimeapps_file"; then
    log_error "Failed to write mimeapps.list"
    return 1
  fi

  log_info "Default applications configured successfully in $mimeapps_file"
  return 0
}
