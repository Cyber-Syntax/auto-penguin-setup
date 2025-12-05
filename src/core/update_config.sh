#!/usr/bin/env bash

# Function: update_config_schema
# Purpose: Update existing INI configuration files with any new keys/sections from example configs
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
  local config_files=("variables.ini" "packages.ini")

  # Helper: extract section names from INI
  ini_sections() {
    local file="$1"
    grep -E '^\s*\[.*\]\s*$' "$file" | sed -E 's/^\s*\[|\]\s*$//g'
  }

  # Helper: extract keys for a section from INI (returns key names only)
  ini_keys_in_section() {
    local file="$1"
    local section="$2"
    # Find section header line number
    local start
    start=$(grep -n -E "^[[:space:]]*\\[$section\\][[:space:]]*$" "$file" | head -n1 | cut -d: -f1)
    [[ -z "$start" ]] && return 0
    # Determine end of section (line before next header) using relative search
    local tail_lines rel_next end
    tail_lines=$(tail -n +"$((start + 1))" "$file")
    rel_next=$(printf '%s\n' "$tail_lines" | grep -n -E '^[[:space:]]*\\[.*\\][[:space:]]*$' | head -n1 | cut -d: -f1)
    if [[ -n "$rel_next" ]]; then
      end=$((start + rel_next - 1))
    else
      end=$(wc -l <"$file")
    fi
    # Read lines between start+1 and end, skip comments/blank lines, emit keys (left of =)
    sed -n "$((start + 1)),$end p" "$file" | while IFS= read -r _line || [[ -n "$_line" ]]; do
      # Trim leading/trailing whitespace
      local line="$_line"
      line="${line#"${line%%[![:space:]]*}"}"
      line="${line%"${line##*[![:space:]]}"}"
      # Skip blank or comment lines
      [[ -z "${line//[[:space:]]/}" ]] && continue
      case "$line" in
        '#'* | ';'*) continue ;;
      esac
      if [[ "$line" == *"="* ]]; then
        local key="${line%%=*}"
        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"
        printf '%s\n' "$key"
      fi
    done
  }

  # Helper: extract key=value lines for section from example
  ini_kv_lines_for_section() {
    local file="$1"
    local section="$2"
    # Find section header line number
    local start
    start=$(grep -n -E "^[[:space:]]*\\[$section\\][[:space:]]*$" "$file" | head -n1 | cut -d: -f1)
    [[ -z "$start" ]] && return 0
    # Determine end of section (line before next header)
    local tail_lines rel_next end
    tail_lines=$(tail -n +"$((start + 1))" "$file")
    rel_next=$(printf '%s\n' "$tail_lines" | grep -n -E '^[[:space:]]*\\[.*\\][[:space:]]*$' | head -n1 | cut -d: -f1)
    if [[ -n "$rel_next" ]]; then
      end=$((start + rel_next - 1))
    else
      end=$(wc -l <"$file")
    fi
    # Emit non-blank lines from the section body
    sed -n "$((start + 1)),$end p" "$file" | while IFS= read -r _line || [[ -n "$_line" ]]; do
      # Skip pure-blank lines
      if [[ -z "${_line//[[:space:]]/}" ]]; then
        continue
      fi
      printf '%s\n' "$_line"
    done
  }

  # Helper: append a block of lines (section header + kvs) to a file
  append_section_block() {
    local user_file="$1"
    local section="$2"
    local block_file="$3"
    {
      echo
      echo "[$section]"
      cat "$block_file"
    } >>"$user_file"
  }

  for file in "${config_files[@]}"; do
    local user_config="$CONFIG_DIR/$file"
    local example_config="$EXAMPLES_DIR/$file"

    # Skip if user doesn't have this config or example doesn't exist
    if [[ ! -f "$user_config" || ! -f "$example_config" ]]; then
      log_debug "Skipping schema update for $file (file missing)"
      continue
    fi

    log_info "Checking for schema updates in $file..."

    if [[ "$file" == "variables.ini" ]]; then
      # Compare sections and keys between example and user
      mapfile -t example_sections < <(ini_sections "$example_config")
      mapfile -t user_sections < <(ini_sections "$user_config")

      local sections_missing=()
      declare -A section_missing_keys

      # Find sections missing entirely
      for sec in "${example_sections[@]}"; do
        if ! printf '%s\n' "${user_sections[@]}" | grep -Fxq "$sec"; then
          sections_missing+=("$sec")
        else
          # For sections that exist, check for missing keys
          mapfile -t example_keys < <(ini_keys_in_section "$example_config" "$sec")
          mapfile -t user_keys < <(ini_keys_in_section "$user_config" "$sec")
          local missing_keys=()
          for key in "${example_keys[@]}"; do
            if ! printf '%s\n' "${user_keys[@]}" | grep -Fxq "$key"; then
              missing_keys+=("$key")
            fi
          done
          if [[ ${#missing_keys[@]} -gt 0 ]]; then
            section_missing_keys["$sec"]="${missing_keys[*]}"
          fi
        fi
      done

      # Determine if any updates are needed
      if [[ ${#sections_missing[@]} -gt 0 || ${#section_missing_keys[@]} -gt 0 ]]; then
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
        if [[ ${#sections_missing[@]} -gt 0 ]]; then
          echo "- New sections need to be added:"
          for s in "${sections_missing[@]}"; do echo "  - $s"; done
        fi
        if [[ ${#section_missing_keys[@]} -gt 0 ]]; then
          echo "- Missing keys in existing sections:"
          for s in "${!section_missing_keys[@]}"; do
            echo "  - $s: ${section_missing_keys[$s]}"
          done
        fi

        echo -e "\n>>> WAITING FOR INPUT: Please respond to continue <<<"
        echo "Auto-continuing in $timeout seconds with default ($default_answer)..."

        read -r -t $timeout -p "Would you like to update your configuration while preserving your custom values? $prompt_options " answer || true
        echo

        if [[ -z "$answer" ]]; then
          answer="$default_answer"
          echo "Using default answer: $default_answer (read timed out)"
        fi

        if [[ "$answer" =~ ^[Yy]$ ]]; then
          backup_config_file "$user_config"

          # Add missing sections (copy content from example)
          for sec in "${sections_missing[@]}"; do
            tmp_section=$(mktemp)
            ini_kv_lines_for_section "$example_config" "$sec" >"$tmp_section"
            append_section_block "$user_config" "$sec" "$tmp_section"
            rm -f "$tmp_section"
            log_info "Appended missing section [$sec] to $user_config"
          done

          # For missing keys within existing sections, insert them under the header
          for sec in "${!section_missing_keys[@]}"; do
            # Build temp insert file with key=value lines from example for missing keys
            tmp_insert=$(mktemp)
            IFS=' ' read -r -a missing_arr <<<"${section_missing_keys[$sec]}"
            for key in "${missing_arr[@]}"; do
              # extract the full key=value line from example using sed/grep for portability
              sed -n "/^[[:space:]]*\\[$sec\\][[:space:]]*$/,/^[[:space:]]*\\[/{p}" "$example_config" | sed '1d;$d' \
                | grep -E "^[[:space:]]*${key}[[:space:]]*=" >>"$tmp_insert" || true
            done

            # Insert tmp_insert after the section header in user_config using a portable bash loop
            tmp_out=$(mktemp)
            inserted=0
            while IFS= read -r __line || [[ -n "$__line" ]]; do
              printf '%s\n' "$__line" >>"$tmp_out"
              if [[ $inserted -eq 0 ]]; then
                # Match section header exactly (allow surrounding whitespace)
                if [[ "$__line" =~ ^[[:space:]]*\[$sec\][[:space:]]*$ ]]; then
                  # append the missing key lines
                  while IFS= read -r __il || [[ -n "$__il" ]]; do
                    printf '%s\n' "$__il" >>"$tmp_out"
                  done <"$tmp_insert"
                  inserted=1
                fi
              fi
            done <"$user_config"
            mv "$tmp_out" "$user_config"
            rm -f "$tmp_insert"
            log_info "Inserted missing keys into section [$sec] in $user_config"
          done

          updated=$((updated + 1))
        else
          log_info "Schema update for $file skipped by user"
        fi
      else
        log_info "No schema updates needed for $file"
      fi

    elif [[ "$file" == "packages.ini" ]]; then
      # Ensure all package categories (sections) exist in user file
      mapfile -t example_sections < <(ini_sections "$example_config")
      mapfile -t user_sections < <(ini_sections "$user_config")
      local missing_sections=()

      for sec in "${example_sections[@]}"; do
        if ! printf '%s\n' "${user_sections[@]}" | grep -Fxq "$sec"; then
          missing_sections+=("$sec")
        fi
      done

      if [[ ${#missing_sections[@]} -gt 0 ]]; then
        # Determine default answer based on post_migration flag
        local default_answer="n"
        local prompt_options="[y/N]"
        local timeout=15

        if [[ "$post_migration" == "true" ]]; then
          default_answer="y"
          prompt_options="[Y/n]"
          echo -e "\n>> ATTENTION: Additional package categories available after migration <<"
        fi

        echo "Found new package categories in $file that are missing in your config:"
        for category in "${missing_sections[@]}"; do
          echo "  - $category"
        done

        echo -e "\n>>> WAITING FOR INPUT: Please respond to continue <<<"
        echo "Auto-continuing in $timeout seconds with default ($default_answer)..."

        read -r -t $timeout -p "Would you like to add these new categories to your configuration? $prompt_options " answer || true
        echo

        if [[ -z "$answer" ]]; then
          answer="$default_answer"
          echo "Using default answer: $default_answer (read timed out)"
        fi

        if [[ "$answer" =~ ^[Yy]$ ]]; then
          backup_config_file "$user_config"

          for sec in "${missing_sections[@]}"; do
            tmp_section=$(mktemp)
            ini_kv_lines_for_section "$example_config" "$sec" >"$tmp_section"
            append_section_block "$user_config" "$sec" "$tmp_section"
            rm -f "$tmp_section"
            log_info "Added missing package category [$sec] to $user_config"
          done

          updated=$((updated + 1))
        else
          log_info "Package category updates skipped by user"
        fi
      else
        log_info "No new package categories to add to $file"
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
