#!/usr/bin/env bash
# string_utils.sh - String utility functions

# Source guard to prevent re-sourcing
[[ -n "${_STRING_UTILS_SOURCED:-}" ]] && return 0
readonly _STRING_UTILS_SOURCED=1

# Function: split_string_to_array
# Purpose: Convert space-separated string to array, handling custom IFS
# Parameters:
#   $1 - String to split (required)
#   $2 - Variable name to store result array (required)
# Usage:
#   split_string_to_array "curl wget jq" result_array
#   echo "${result_array[@]}"  # outputs: curl wget jq
# Returns: 0 on success, 1 on error
split_string_to_array() {
  if [[ $# -lt 2 ]]; then
    echo "ERROR: split_string_to_array requires 2 arguments: string and target_array_name" >&2
    return 1
  fi
  
  local input_string="$1"
  local array_name="$2"
  
  # Save current IFS
  local saved_ifs="$IFS"
  
  # Set IFS to space, tab, newline for proper splitting
  IFS=$' \t\n'
  
  # Read string into array using nameref (Bash 4.3+) or eval fallback
  if [[ "${BASH_VERSINFO[0]}" -ge 5 ]] || { [[ "${BASH_VERSINFO[0]}" -eq 4 ]] && [[ "${BASH_VERSINFO[1]}" -ge 3 ]]; }; then
    # Use nameref (safer, available in Bash 4.3+)
    local -n target_array="$array_name"
    read -r -a target_array <<< "$input_string"
  else
    # Fallback for older Bash versions
    # shellcheck disable=SC2086,SC2162
    read -r -a temp_array <<< "$input_string"
    eval "$array_name=(\"\${temp_array[@]}\")"
  fi
  
  # Restore IFS
  IFS="$saved_ifs"
  
  return 0
}

# Function: join_array_to_string
# Purpose: Join array elements with a delimiter
# Parameters:
#   $1 - Delimiter (default: space)
#   $@ - Array elements
# Usage:
#   result=$(join_array_to_string "," "${my_array[@]}")
# Returns: Joined string to stdout
join_array_to_string() {
  local delimiter="${1:-" "}"
  shift
  
  if [[ $# -eq 0 ]]; then
    return 0
  fi
  
  local first=1
  for item in "$@"; do
    if [[ $first -eq 1 ]]; then
      printf "%s" "$item"
      first=0
    else
      printf "%s%s" "$delimiter" "$item"
    fi
  done
}

# Export functions for use in other scripts
export -f split_string_to_array
export -f join_array_to_string
