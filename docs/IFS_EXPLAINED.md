# IFS (Internal Field Separator) - Understanding and Best Practices

## What is IFS?

IFS is a special Bash variable that determines how the shell splits words. By default, IFS contains:

- Space (` `)
- Tab (`\t`)
- Newline (`\n`)

## Common IFS Patterns

### Pattern 1: Default Behavior (Security Risk)

```bash
# Default IFS=$' \t\n'
# Splits on space, tab, newline

packages="curl wget jq"
for pkg in $packages; do  # UNQUOTED - will split
  echo "$pkg"
done
# Output: curl, wget, jq (three iterations)
```

**Risk**: Unquoted expansions can lead to:

- Word splitting on spaces
- Glob expansion (`*`, `?`, `[...]`)
- Command injection vulnerabilities

### Pattern 2: Restrictive IFS (Security Focused)

```bash
# Restrict splitting to only newline and tab
IFS=$'\n\t'

packages="curl wget jq"
for pkg in $packages; do  # UNQUOTED
  echo "$pkg"
done
# Output: curl wget jq (ONE iteration - no space splitting!)
```

**Purpose**: Prevents accidental word splitting on spaces, forcing explicit quoting.

### Pattern 3: Temporary IFS Change (Our Solution)

```bash
# Save and restore IFS for specific operations
OLD_IFS="$IFS"
IFS=$' \t\n'  # Reset to default for splitting
read -r -a array <<< "$string"
IFS="$OLD_IFS"  # Restore
```

## The Bug We Fixed

### Problem

In `setup.sh`, we had:

```bash
set -euo pipefail
IFS=$'\n\t'  # Global IFS restriction
```

Later in `install_packages.sh`:

```bash
mapped_packages="curl wget jq"
read -r -a mapped_array <<< "$mapped_packages"
# Result: mapped_array=("curl wget jq")  # ONE element!
```

Because IFS didn't include space, `read` didn't split on spaces!

### Solution Options

#### Option A: Reusable Utility Function (Implemented ✓)

**Benefits:**

- DRY (Don't Repeat Yourself) principle
- Centralized IFS handling
- Keeps security-focused global IFS
- Easy to maintain and test

```bash
# In src/utils/string_utils.sh
split_string_to_array() {
  local input_string="$1"
  local array_name="$2"
  local saved_ifs="$IFS"
  IFS=$' \t\n'
  local -n target_array="$array_name"
  read -r -a target_array <<< "$input_string"
  IFS="$saved_ifs"
}

# Usage
split_string_to_array "$mapped_packages" mapped_array
```

#### Option B: Remove Global IFS Override

**Benefits:**

- Simpler code
- Standard Bash behavior
- No need for IFS gymnastics

**Drawbacks:**

- Must be more careful with quoting
- Slightly higher risk of mistakes

```bash
# In setup.sh - remove or comment out:
# IFS=$'\n\t'  # Remove this line

# Then in code, proper quoting handles safety:
packages="curl wget jq"
read -r -a array <<< "$packages"  # Works correctly
```

## When to Use Each Approach

### Use Restrictive IFS (`IFS=$'\n\t'`) When

- Processing untrusted input
- Working with filenames that might contain spaces
- Reading configuration files line-by-line
- Security is paramount

### Use Default IFS When

- Working with known, trusted data
- Need standard word splitting behavior
- Code clarity is important
- Team is experienced with Bash quoting

## Best Practices

### 1. Always Quote Variables

```bash
# GOOD
echo "$var"
for item in "$@"; do

# BAD (unless you specifically want word splitting)
echo $var
for item in $@; do
```

### 2. Use Arrays for Lists

```bash
# GOOD
packages=(curl wget jq)
for pkg in "${packages[@]}"; do

# LESS GOOD
packages="curl wget jq"
for pkg in $packages; do
```

### 3. Localize IFS Changes

```bash
# GOOD - localized
function process_data() {
  local old_ifs="$IFS"
  IFS=","
  # do work
  IFS="$old_ifs"
}

# BAD - global side effects
IFS=","
# do work
# (IFS stays changed!)
```

### 4. Document IFS Usage

```bash
# GOOD - explains why
# Temporarily reset IFS to default for proper space-splitting
local old_ifs="$IFS"
IFS=$' \t\n'
read -r -a array <<< "$string"
IFS="$old_ifs"
```

## Our Implementation

We chose **Option A** (utility function) because:

1. **Maintains Security**: Keeps `IFS=$'\n\t'` globally
2. **Reusable**: Single function for all conversions
3. **Maintainable**: One place to fix if issues arise
4. **Clear Intent**: Function name documents what it does
5. **Testable**: Easy to unit test in isolation

### Usage in Code

```bash
# Before (duplicated 5 times)
local old_ifs="$IFS"
IFS=$' \t\n'
read -r -a mapped_array <<< "$mapped_packages"
IFS="$old_ifs"

# After (centralized)
split_string_to_array "$mapped_packages" mapped_array
```

## Alternative: Remove IFS Override

If you prefer simpler code, you can remove the global IFS restriction:

```bash
# In setup.sh - change:
set -euo pipefail
IFS=$'\n\t'  # ← Remove or comment this line

# Then you don't need the utility function:
read -r -a mapped_array <<< "$mapped_packages"  # Works!
```

**Trade-off**: You must be more vigilant about quoting throughout the codebase.

## Recommendation

For this project:

- **Keep current solution** (utility function) ✓
- **Alternative**: If code simplicity is preferred over defense-in-depth, remove global IFS override

Both are valid approaches. The utility function approach is more defensive but adds a small amount of complexity. The simpler approach (no IFS override) is cleaner but requires discipline with quoting.

## Testing

Test the utility function:

```bash
# Test basic splitting
split_string_to_array "curl wget jq" result
echo "${#result[@]}"  # Should output: 3

# Test with tabs and newlines
split_string_to_array $'curl\twget\njq' result
echo "${#result[@]}"  # Should output: 3

# Test empty string
split_string_to_array "" result
echo "${#result[@]}"  # Should output: 0 or 1 (empty element)
```

## References

- [Bash Manual: Word Splitting](https://www.gnu.org/software/bash/manual/html_node/Word-Splitting.html)
- [ShellCheck SC2086](https://www.shellcheck.net/wiki/SC2086) - Quote to prevent word splitting
- [Bash Pitfalls](https://mywiki.wooledge.org/BashPitfalls#for_f_in_.24.28ls_.2A.mp3.29)
