#!/usr/bin/env bash
# ini_parser.sh - Pure Bash INI file parser
# Purpose: Parse INI configuration files without external dependencies

# Source guard to prevent re-sourcing
[[ -n "${_INI_PARSER_SOURCED:-}" ]] && return 0
readonly _INI_PARSER_SOURCED=1

source src/core/logging.sh

# Global storage for INI data
declare -gA INI_DATA
declare -ga INI_SECTIONS

# Function: parse_ini_file
# Purpose: Parse INI file and load into memory
# Arguments:
#   $1 - Path to INI file
# Returns: 0 on success, 1 on failure
parse_ini_file() {
  local ini_file="$1"
  local section=""
  local line_num=0
  
  if [[ ! -f "$ini_file" ]]; then
    log_error "INI file not found: $ini_file"
    return 1
  fi
  
  log_debug "Parsing INI file: $ini_file"
  
  # Clear existing data
  INI_DATA=()
  INI_SECTIONS=()
  
  # Save IFS and set to newline for reading
  local oldIFS=$IFS
  IFS=$'\n'
  
  while read -r line || [[ -n "$line" ]]; do
    ((line_num++))
    
    # Trim leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[#\;] ]] && continue
    
    # Section header: [section]
    if [[ "$line" =~ ^\[(.+)\]$ ]]; then
      section="${BASH_REMATCH[1]}"
      section="${section#"${section%%[![:space:]]*}"}"
      section="${section%"${section##*[![:space:]]}"}"
      
      if [[ -z "$section" ]]; then
        log_warn "Empty section name at line $line_num in $ini_file"
        continue
      fi
      
      # Add section if not already present
      if [[ ! " ${INI_SECTIONS[*]} " =~ " ${section} " ]]; then
        INI_SECTIONS+=("$section")
      fi
      
      log_debug "Found section: [$section]"
      continue
    fi
    
    # Key-value pair: key=value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local value="${BASH_REMATCH[2]}"
      
      # Trim whitespace from key and value
      key="${key#"${key%%[![:space:]]*}"}"
      key="${key%"${key##*[![:space:]]}"}"
      value="${value#"${value%%[![:space:]]*}"}"
      value="${value%"${value##*[![:space:]]}"}"
      
      if [[ -z "$section" ]]; then
        log_warn "Key-value pair outside of section at line $line_num: $line"
        continue
      fi
      
      if [[ -z "$key" ]]; then
        log_warn "Empty key at line $line_num in $ini_file"
        continue
      fi
      
      # Store in associative array
      local storage_key="${section}:${key}"
      if [[ -n "${INI_DATA[$storage_key]:-}" ]]; then
        log_debug "Overwriting duplicate key: $storage_key"
      fi
      
      INI_DATA["$storage_key"]="$value"
      log_debug "  $key = $value"
      continue
    fi
    
    # If we're in a section and line doesn't have '=', treat as value-only (for package lists)
    if [[ -n "$section" && ! "$line" =~ = ]]; then
      # This is a package list item (value only, no key)
      # Store with auto-incrementing index
      local idx=0
      while [[ -n "${INI_DATA["${section}:${idx}"]:-}" ]]; do
        ((idx++))
      done
      
      INI_DATA["${section}:${idx}"]="$line"
      log_debug "  [$idx] = $line"
      continue
    fi
    
    log_warn "Unrecognized line $line_num in $ini_file: $line"
  done < "$ini_file"
  
  IFS=$oldIFS
  
  log_info "Parsed INI file: ${#INI_SECTIONS[@]} sections, ${#INI_DATA[@]} entries"
  return 0
}

# Function: get_ini_value
# Purpose: Get a single value from INI data
# Arguments:
#   $1 - Section name
#   $2 - Key name
# Returns: Value or empty string
get_ini_value() {
  local section="$1"
  local key="$2"
  local storage_key="${section}:${key}"
  
  echo "${INI_DATA[$storage_key]:-}"
}

# Function: get_ini_section
# Purpose: Get all values in a section as array
# Arguments:
#   $1 - Section name
# Returns: Array of values (newline-separated)
get_ini_section() {
  local section="$1"
  local values=()
  
  for key in "${!INI_DATA[@]}"; do
    if [[ "$key" =~ ^${section}: ]]; then
      values+=("${INI_DATA[$key]}")
    fi
  done
  
  printf '%s\n' "${values[@]}"
}

# Function: get_ini_section_keys
# Purpose: Get all key names in a section
# Arguments:
#   $1 - Section name
# Returns: Array of key names (newline-separated)
get_ini_section_keys() {
  local section="$1"
  local keys=()
  
  for key in "${!INI_DATA[@]}"; do
    if [[ "$key" =~ ^${section}:(.+)$ ]]; then
      keys+=("${BASH_REMATCH[1]}")
    fi
  done
  
  printf '%s\n' "${keys[@]}"
}

# Function: list_ini_sections
# Purpose: Get all section names
# Returns: Array of section names (newline-separated)
list_ini_sections() {
  printf '%s\n' "${INI_SECTIONS[@]}"
}

# Function: ini_section_exists
# Purpose: Check if section exists
# Arguments:
#   $1 - Section name
# Returns: 0 if exists, 1 if not
ini_section_exists() {
  local section="$1"
  
  for s in "${INI_SECTIONS[@]}"; do
    [[ "$s" == "$section" ]] && return 0
  done
  
  return 1
}

# Function: ini_key_exists
# Purpose: Check if key exists in section
# Arguments:
#   $1 - Section name
#   $2 - Key name
# Returns: 0 if exists, 1 if not
ini_key_exists() {
  local section="$1"
  local key="$2"
  local storage_key="${section}:${key}"
  
  [[ -n "${INI_DATA[$storage_key]:-}" ]] && return 0
  return 1
}

export -f parse_ini_file
export -f get_ini_value
export -f get_ini_section
export -f get_ini_section_keys
export -f list_ini_sections
export -f ini_section_exists
export -f ini_key_exists
