#!/usr/bin/env bash
# repo_migration.sh - Repository change detection and migration
# Purpose: Detect repository changes in config and migrate tracked packages

# Source guard to prevent re-sourcing
[[ -n "${_REPO_MIGRATION_SOURCED:-}" ]] && return 0
readonly _REPO_MIGRATION_SOURCED=1

# Source required modules
source src/core/logging.sh
source src/core/package_tracking.sh
source src/core/config.sh
source src/core/package_manager.sh
source src/core/repository_manager.sh

# Function: detect_repo_changes
# Purpose: Detect if any tracked packages have different repositories in config
# Returns: 0 if changes detected, 1 if no changes
detect_repo_changes() {
  if [[ "$TRACKING_INITIALIZED" -ne 1 ]]; then
    log_error "Tracking not initialized"
    return 1
  fi

  log_info "Detecting repository changes..."

  local packages
  packages=$(get_tracked_packages)

  if [[ -z "$packages" ]]; then
    log_debug "No packages tracked"
    return 1
  fi

  local changes_found=0

  while IFS= read -r package; do
    [[ -z "$package" ]] && continue

    local tracked_source
    tracked_source=$(get_package_source "$package")

    local config_source
    config_source=$(get_package_config_source "$package")

    # If package not in config anymore, skip
    if [[ -z "$config_source" ]]; then
      log_debug "Package not in config: $package"
      continue
    fi

    # Compare sources
    if [[ "$tracked_source" != "$config_source" ]]; then
      log_info "Repository change detected for $package:"
      log_info "  Tracked:  $tracked_source"
      log_info "  Config:   $config_source"
      changes_found=1
    fi
  done <<<"$packages"

  if [[ $changes_found -eq 0 ]]; then
    log_success "No repository changes detected"
    return 1
  fi

  return 0
}

# Function: get_package_config_source
# Purpose: Get the repository source for a package from pkgmap.ini
# Arguments:
#   $1 - Package name (original name from packages.ini)
# Returns: Source string or empty
get_package_config_source() {
  local package_name="$1"

  if [[ -z "$package_name" ]]; then
    return 1
  fi

  # Check if package mapping exists in PACKAGE_MAPPINGS
  if [[ -n "${PACKAGE_MAPPINGS[$package_name]:-}" ]]; then
    local mapped="${PACKAGE_MAPPINGS[$package_name]}"

    # Parse mapped value to extract source
    if [[ "$mapped" =~ ^COPR:([^:]+) ]]; then
      echo "COPR:${BASH_REMATCH[1]}"
      return 0
    elif [[ "$mapped" =~ ^AUR:(.+)$ ]]; then
      echo "AUR:${BASH_REMATCH[1]}"
      return 0
    elif [[ "$mapped" =~ ^PPA:([^:]+) ]]; then
      echo "PPA:${BASH_REMATCH[1]}"
      return 0
    else
      # Mapped but no special prefix = official
      echo "official"
      return 0
    fi
  fi

  # Not in mappings = official repository
  echo "official"
  return 0
}

# Function: migrate_package_repo
# Purpose: Migrate a single package to a new repository
# Arguments:
#   $1 - Package name
#   $2 - Old repository source
#   $3 - New repository source
# Returns: 0 on success, 1 on failure
migrate_package_repo() {
  local package_name="$1"
  local old_source="$2"
  local new_source="$3"

  if [[ -z "$package_name" || -z "$old_source" || -z "$new_source" ]]; then
    log_error "Package name, old source, and new source are required"
    return 1
  fi

  log_info "Migrating $package_name: $old_source -> $new_source"

  # Step 1: Disable old repository if it's a COPR
  if [[ "$old_source" =~ ^COPR:(.+)$ ]]; then
    local old_repo="${BASH_REMATCH[1]}"
    log_info "Disabling old COPR repository: $old_repo"
    if ! repo_disable_copr "$old_repo"; then
      log_warn "Failed to disable old COPR repository: $old_repo"
      # Continue anyway - the repo might not be enabled
    fi
  fi

  # Step 2: Remove the package
  log_info "Removing package from old source..."
  if ! pm_remove "$package_name"; then
    log_error "Failed to remove package: $package_name"
    return 1
  fi

  # Step 3: Add new repository if needed
  if [[ "$new_source" != "official" ]]; then
    local repo=""
    if [[ "$new_source" =~ ^(COPR|AUR|PPA):(.+)$ ]]; then
      repo="${BASH_REMATCH[2]}"
      log_info "Adding new repository: $repo"
      if ! repo_add "$repo"; then
        log_error "Failed to add repository: $repo"
        # Try to reinstall from old source
        log_warn "Attempting to reinstall from old source"
        _rollback_migration "$package_name" "$old_source"
        return 1
      fi
    fi
  fi

  # Step 4: Install package from new source
  log_info "Installing package from new source..."
  if ! pm_install "$package_name"; then
    log_error "Failed to install package from new source: $package_name"
    # Try to rollback
    log_warn "Attempting to rollback to old source"
    _rollback_migration "$package_name" "$old_source"
    return 1
  fi

  # Step 5: Update tracking database
  local category
  category=$(get_ini_value "package.${package_name}" "category")
  category="${category:-uncategorized}"

  if ! track_package_install "$package_name" "$new_source" "$category" "$package_name"; then
    log_warn "Package migrated but tracking update failed"
  fi

  # Step 6: Clean up old repository if no other packages use it
  if [[ "$old_source" != "official" ]]; then
    _cleanup_unused_repo "$old_source"
  fi

  log_success "Successfully migrated $package_name to $new_source"
  return 0
}

# Function: _rollback_migration
# Purpose: Attempt to rollback a failed migration
# Arguments:
#   $1 - Package name
#   $2 - Old source
# Returns: 0 on success, 1 on failure
_rollback_migration() {
  local package_name="$1"
  local old_source="$2"

  log_warn "Rolling back migration for $package_name"

  # Re-add old repository if needed
  if [[ "$old_source" != "official" ]]; then
    if [[ "$old_source" =~ ^(COPR|AUR|PPA):(.+)$ ]]; then
      local repo="${BASH_REMATCH[2]}"
      repo_add "$repo" 2>/dev/null || true
    fi
  fi

  # Try to reinstall package
  if pm_install "$package_name" 2>/dev/null; then
    log_success "Rollback successful"
    return 0
  else
    log_error "Rollback failed - manual intervention required"
    return 1
  fi
}

# Function: _cleanup_unused_repo
# Purpose: Remove repository if no other tracked packages use it
# Arguments:
#   $1 - Repository source (e.g., "COPR:user/repo")
# Returns: 0 if cleaned up, 1 if still in use or error
_cleanup_unused_repo() {
  local repo_source="$1"

  # Get packages from this repo
  local packages
  packages=$(get_packages_from_repo "$repo_source")

  # If no packages use this repo, remove it
  if [[ -z "$packages" ]]; then
    log_info "No packages use repository $repo_source, removing..."

    if [[ "$repo_source" =~ ^COPR:(.+)$ ]]; then
      local repo="${BASH_REMATCH[1]}"
      if repo_remove_copr "$repo"; then
        log_success "Removed unused COPR repository: $repo"
        return 0
      else
        log_warn "Failed to remove COPR repository: $repo"
        return 1
      fi
    elif [[ "$repo_source" =~ ^AUR:(.+)$ ]]; then
      log_debug "AUR packages don't require repository cleanup"
      return 0
    elif [[ "$repo_source" =~ ^PPA:(.+)$ ]]; then
      local repo="${BASH_REMATCH[1]}"
      if repo_remove_ppa "ppa:$repo"; then
        log_success "Removed unused PPA repository: $repo"
        return 0
      else
        log_warn "Failed to remove PPA repository: $repo"
        return 1
      fi
    fi
  else
    log_debug "Repository $repo_source still in use by other packages"
    return 1
  fi
}

# Function: migrate_all_changed_repos
# Purpose: Migrate all packages with repository changes
# Arguments:
#   $1 - Mode: "interactive" or "auto" (default: interactive)
# Returns: 0 on success, 1 on failure
migrate_all_changed_repos() {
  local mode="${1:-interactive}"

  if [[ "$TRACKING_INITIALIZED" -ne 1 ]]; then
    log_error "Tracking not initialized"
    return 1
  fi

  # Ensure package mappings are loaded
  if [[ ${#PACKAGE_MAPPINGS[@]} -eq 0 ]]; then
    log_info "Loading package mappings for repository comparison..."
    local pkgmap_file="${CONFIG_DIR:-$HOME/.config/auto-penguin-setup}/pkgmap.ini"
    if [[ -f "$pkgmap_file" ]]; then
      load_package_mappings "$pkgmap_file" || {
        log_error "Failed to load package mappings"
        return 1
      }
    else
      log_warn "No pkgmap.ini found, assuming all packages are from official repos"
    fi
  fi

  log_info "Scanning for repository changes..."

  local packages
  packages=$(get_tracked_packages)

  if [[ -z "$packages" ]]; then
    log_info "No packages tracked"
    return 0
  fi

  local changes=()
  declare -A change_map_old
  declare -A change_map_new

  # Collect all changes
  while IFS= read -r package; do
    [[ -z "$package" ]] && continue

    local tracked_source
    tracked_source=$(get_package_source "$package")

    local config_source
    config_source=$(get_package_config_source "$package")

    # Skip if not in config or no change
    if [[ -z "$config_source" || "$tracked_source" == "$config_source" ]]; then
      continue
    fi

    changes+=("$package")
    change_map_old["$package"]="$tracked_source"
    change_map_new["$package"]="$config_source"
  done <<<"$packages"

  if [[ ${#changes[@]} -eq 0 ]]; then
    log_success "No repository changes detected"
    return 0
  fi

  # Display changes
  echo ""
  echo "Repository Changes Detected:"
  echo "============================"
  for package in "${changes[@]}"; do
    printf "%-30s: %s -> %s\n" "$package" "${change_map_old[$package]}" "${change_map_new[$package]}"
  done
  echo ""

  # Handle based on mode
  if [[ "$mode" == "interactive" ]]; then
    read -rp "Migrate all packages? [y/N]: " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
      log_info "Migration cancelled by user"
      return 1
    fi
  fi

  # Perform migrations
  local success_count=0
  local fail_count=0

  for package in "${changes[@]}"; do
    if migrate_package_repo "$package" "${change_map_old[$package]}" "${change_map_new[$package]}"; then
      ((success_count++))
    else
      ((fail_count++))
      log_error "Failed to migrate: $package"
    fi
  done

  echo ""
  log_info "Migration complete: $success_count succeeded, $fail_count failed"

  if [[ $fail_count -gt 0 ]]; then
    return 1
  fi

  return 0
}

# Function: show_repo_changes
# Purpose: Display repository changes without migrating
# Returns: 0 on success
show_repo_changes() {
  if [[ "$TRACKING_INITIALIZED" -ne 1 ]]; then
    log_error "Tracking not initialized"
    return 1
  fi

  # Ensure package mappings are loaded
  if [[ ${#PACKAGE_MAPPINGS[@]} -eq 0 ]]; then
    log_info "Loading package mappings..."
    local pkgmap_file="${CONFIG_DIR:-$HOME/.config/auto-penguin-setup}/pkgmap.ini"
    if [[ -f "$pkgmap_file" ]]; then
      load_package_mappings "$pkgmap_file" || {
        log_error "Failed to load package mappings"
        return 1
      }
    else
      log_warn "No pkgmap.ini found"
    fi
  fi

  log_info "Checking for repository changes..."

  local packages
  packages=$(get_tracked_packages)

  if [[ -z "$packages" ]]; then
    log_info "No packages tracked"
    return 0
  fi

  local changes_found=0

  echo ""
  echo "Repository Status:"
  echo "===================="

  while IFS= read -r package; do
    [[ -z "$package" ]] && continue

    local tracked_source
    tracked_source=$(get_package_source "$package")

    local config_source
    config_source=$(get_package_config_source "$package")

    if [[ -z "$config_source" ]]; then
      continue
    fi

    if [[ "$tracked_source" != "$config_source" ]]; then
      printf "%-30s: %s -> %s\n" "$package" "$tracked_source" "$config_source"
      changes_found=1
    fi
  done <<<"$packages"

  echo ""

  if [[ $changes_found -eq 0 ]]; then
    log_success "No repository changes detected"
  else
    log_info "Use 'setup.sh --sync-repos' to migrate packages"
  fi

  return 0
}

export -f detect_repo_changes
export -f get_package_config_source
export -f migrate_package_repo
export -f migrate_all_changed_repos
export -f show_repo_changes
