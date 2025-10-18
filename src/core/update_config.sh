#!/usr/bin/env bash

#TODO: refactor for new INI system

# Function: update_config_schema
# Purpose: Update existing configuration files with any new keys from example configs
#          while preserving existing user values
# Arguments: $1 - Optional flag indicating if this is running after migration
# Returns: 0 on success, 1 on failure
update_config_schema() {
  local post_migration="${1:-false}"
  log_info "Checking for configuration schema updates..."

  echo -e "\n===== Configuration Update ====="
  echo "This script can update your configuration files with any new settings"
  echo "that have been added since your last update."
  echo "Your existing settings will be preserved, and backups will be created."
  echo

  local updated=0
  local config_files=("variables.json" "packages.json")

  for file in "${config_files[@]}"; do
    local user_config="$CONFIG_DIR/$file"
    local example_config="$EXAMPLES_DIR/$file"

    # Skip if user doesn't have this config or example doesn't exist
    if [[ ! -f "$user_config" || ! -f "$example_config" ]]; then
      log_debug "Skipping schema update for $file (file missing)"
      continue
    fi

    log_info "Checking for schema updates in $file..."

    # For variables.json, we need to do a deep merge to preserve nested structures
    if [[ "$file" == "variables.json" ]]; then
      # Check if there are differences in the structure
      local needs_update=false

      # This jq command will detect if the user config needs an update
      # It checks both for missing keys and flat vs. nested structure differences
      local jq_check_cmd="
                # Load the configs
                def user_config: $user;
                def example_config: $example;

                # First check for completely missing keys
                def has_missing_keys:
                    def check_missing($u; $e):
                        if ($e | type) == "object" then
                            ($e | keys) as $ekeys |
                            ($u | keys) as $ukeys |
                            ($ekeys - $ukeys | length > 0) or
                            ($ekeys | map(select($u[.] != null and ($u[.] | type) == "object" and ($e[.] | type) == "object") |
                                check_missing($u[.]; $e[.])) | any)
                        else false end;
                    check_missing(user_config; example_config);

                # Then check for flat vs. nested structure differences
                def has_structure_differences:
                    # Define flat key equivalents to check
                    [
                        # Add mappings from flat to nested keys
                        {flat: "laptop_ip", nested: ["laptop", "ip"]},
                        {flat: "session", nested: ["desktop", "session"]},
                        {flat: "laptop_session", nested: ["laptop", "session"]},
                        {flat: "desktop_session", nested: ["desktop", "session"]}
                    ] |
                    # Check if any flat key exists that should be nested
                    map(
                        user_config[.flat] != null and
                        example_config[.nested[0]][.nested[1]] != null
                    ) |
                    any;

                # Return true if either check finds issues
                has_missing_keys or has_structure_differences
            "

      needs_update=$(jq --argjson user "$(cat "$user_config")" --argjson example "$(cat "$example_config")" "$jq_check_cmd" 2>/dev/null)

      if [[ "$needs_update" == "true" ]]; then
        # Determine default answer based on post_migration flag
        local default_answer="n"
        local prompt_options="[y/N]"
        local timeout=15

        if [[ "$post_migration" == "true" ]]; then
          default_answer="y"
          prompt_options="[Y/n]"
          echo -e "\n>> ATTENTION: Additional updates available after migration <<"
          echo "Even though your configuration was just migrated, there are still"
          echo "additional settings that can be updated to the latest version."
        fi

        echo "Found configuration updates needed for $file:"
        echo "- New keys or sections need to be added"
        echo "- Configuration structure needs modernizing from flat to nested format"
        echo -e "\n>>> WAITING FOR INPUT: Please respond to continue <<<"
        echo "Auto-continuing in $timeout seconds with default ($default_answer)..."

        # Add timeout to read command to prevent indefinite blocking
        read -t $timeout -p "Would you like to update your configuration while preserving your custom values? $prompt_options " answer || true
        echo

        # If no answer provided or read timed out, use the default
        if [[ -z "$answer" ]]; then
          answer="$default_answer"
          echo "Using default answer: $default_answer (read timed out)"
        fi

        if [[ "$answer" =~ ^[Yy]$ ]]; then
          # Create backup of user's current config
          backup_config_file "$user_config"

          # Use jq to merge configs while handling both nested structures and flat keys
          jq -s '
                        # User and example configs
                        def user_cfg: .[0];
                        def example_cfg: .[1];

                        # Recursive function to merge objects
                        def deep_merge(a; b):
                          if (a | type) == "object" and (b | type) == "object" then
                            # Create an object that has all keys from both objects
                            a + b |
                            # For each key in the combined object
                            to_entries |
                            map(
                              # If both a and b have the key and both values are objects, merge them recursively
                              if a[.key] != null and b[.key] != null and (a[.key] | type) == "object" and (b[.key] | type) == "object" then
                                {key: .key, value: deep_merge(a[.key]; b[.key])}
                              # Otherwise keep the value (preference given to a, the user config)
                              else
                                .
                              end
                            ) |
                            from_entries
                          # If not both objects, prefer a (user config)
                          elif a != null then
                            a
                          else
                            b
                          end;

                        # Start with a deep copy of the example config
                        example_cfg |

                        # Special handling for flat keys migration
                        . as $result |

                        # Migrate flat keys to nested structure
                        if user_cfg.laptop_ip != null and $result.laptop.ip != null then
                            $result | .laptop.ip = user_cfg.laptop_ip
                        else . end |

                        if user_cfg.session != null and $result.desktop.session != null then
                            $result | .desktop.session = $user_cfg.session
                        else . end |

                        if user_cfg.laptop_session != null and $result.laptop.session != null then
                            $result | .laptop.session = $user_cfg.laptop_session
                        else . end |

                        if user_cfg.desktop_session != null and $result.desktop.session != null then
                            $result | .desktop.session = $user_cfg.desktop_session
                        else . end |

                        # Copy over common shared fields directly
                        if user_cfg.user != null then
                            $result | .user = $user_cfg.user
                        else . end |

                        if user_cfg.hostnames != null then
                            $result | .hostnames = $user_cfg.hostnames
                        else . end |

                        if user_cfg.browser != null then
                            $result | .browser = $user_cfg.browser
                        else . end |

                        if user_cfg.system != null then
                            $result | .system = $user_cfg.system
                        else . end |

                        # Also update nested hostnames to match flat structure if needed
                        if user_cfg.hostnames.desktop != null and $result.desktop.host != null then
                            $result | .desktop.host = $user_cfg.hostnames.desktop
                        else . end |

                        if user_cfg.hostnames.laptop != null and $result.laptop.host != null then
                            $result | .laptop.host = $user_cfg.hostnames.laptop
                        else . end
                    ' "$user_config" "$example_config" >"${user_config}.new"

          # Check if jq succeeded
          if [[ $? -eq 0 ]] && jq empty "${user_config}.new" 2>/dev/null; then
            # Replace the old config with the new one
            mv "${user_config}.new" "$user_config"
            log_info "Updated schema for $file successfully"
            updated=$((updated + 1))
          else
            log_error "Failed to update schema for $file"
            rm -f "${user_config}.new" 2>/dev/null
          fi
        else
          log_info "Schema update for $file skipped by user"
        fi
      else
        log_info "No schema updates needed for $file"
      fi

    # For packages.json, ensure all categories exist
    elif [[ "$file" == "packages.json" ]]; then
      # Get all package categories from example
  local example_categories
  mapfile -t example_categories < <(jq 'keys[]' -r "$example_config")
  local user_categories
  mapfile -t user_categories < <(jq 'keys[]' -r "$user_config")
      local missing_categories=()

      # Find categories in example that are missing in user config
      for category in "${example_categories[@]}"; do
        if ! echo "${user_categories[@]}" | grep -qw "$category"; then
          missing_categories+=("$category")
        fi
      done

      # If we have missing categories, update the user config
      if [[ ${#missing_categories[@]} -gt 0 ]]; then
        # Determine default answer based on post_migration flag
        local default_answer="n"
        local prompt_options="[y/N]"
        local timeout=15

        if [[ "$post_migration" == "true" ]]; then
          default_answer="y"
          prompt_options="[Y/n]"
          echo -e "\n>> ATTENTION: Additional package categories available after migration <<"
        fi

        echo "Found new package categories in packages.json that are missing in your config:"
        for category in "${missing_categories[@]}"; do
          echo "  - $category"
        done

        echo -e "\n>>> WAITING FOR INPUT: Please respond to continue <<<"
        echo "Auto-continuing in $timeout seconds with default ($default_answer)..."

        # Add timeout to read command to prevent indefinite blocking
        read -t $timeout -p "Would you like to add these new categories to your configuration? $prompt_options " answer || true
        echo

        # If no answer provided or read timed out, use the default
        if [[ -z "$answer" ]]; then
          answer="$default_answer"
          echo "Using default answer: $default_answer (read timed out)"
        fi

        if [[ "$answer" =~ ^[Yy]$ ]]; then
          # Create backup of user's current config
          backup_config_file "$user_config"

          # Create a temporary file for the merged result
          local temp_file
          temp_file=$(mktemp)

          # Start with the user's config
          cp "$user_config" "$temp_file"

          # Add each missing category with its default values
          for category in "${missing_categories[@]}"; do
            # Extract the default packages for this category from the example
            local default_packages
            default_packages=$(jq --arg cat "$category" '.[$cat]' "$example_config")

            # Add the category with default packages to user config
            jq --argjson pkgs "$default_packages" --arg cat "$category" '.[$cat] = $pkgs' "$temp_file" >"${temp_file}.new"

            if [[ $? -eq 0 ]]; then
              mv "${temp_file}.new" "$temp_file"
            else
              log_error "Failed to add category $category to packages.json"
              rm -f "${temp_file}.new" 2>/dev/null
            fi
          done

          # Check if the updated file is valid JSON
          if jq empty "$temp_file" 2>/dev/null; then
            # Replace the old config with the new one
            mv "$temp_file" "$user_config"
            log_info "Added new package categories to packages.json successfully"
            updated=$((updated + 1))
          else
            log_error "Failed to create valid JSON when updating packages.json"
            rm -f "$temp_file" 2>/dev/null
          fi
        else
          log_info "Package category updates skipped by user"
        fi
      else
        log_info "No new package categories to add to packages.json"
      fi
    fi
  done

  # Report status
  if [[ "$updated" -gt 0 ]]; then
    echo -e "\n===== Configuration Update Complete ====="
    echo "$updated configuration files have been updated with new keys/settings."
    echo "Your existing settings have been preserved, and backups were created with .bak extension."
    echo
    return 0
  else
    log_info "No configuration updates were needed"
    return 1
  fi
}