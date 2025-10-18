## Error Handling Strategy

### Layered Error Handling

```
┌─────────────────────────────────────────────────────┐
│ Layer 4: User-Facing Functions                     │
│ • Log errors with context                          │
│ • Return 1 on failure                              │
│ • Provide recovery suggestions                     │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ Layer 3: Abstraction Functions (pm_install, etc.)  │
│ • Validate inputs                                  │
│ • Log command execution                            │
│ • Catch command failures                           │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ Layer 2: System Commands                           │
│ • Check return codes                               │
│ • Redirect stderr appropriately                    │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ Layer 1: Bash Error Modes                          │
│ • set -e: Exit on error                            │
│ • set -u: Exit on undefined variable               │
│ • set -o pipefail: Catch pipe failures             │
└─────────────────────────────────────────────────────┘
```

### Error Handling Patterns

#### Pattern 1: Command Execution with Error Checking

```bash
install_package() {
  local package="$1"
  
  # Log what we're doing
  log_info "Installing $package..."
  
  # Execute with error checking
  if ! pm_install "$package"; then
    log_error "Failed to install $package"
    return 1
  fi
  
  # Success path
  log_success "$package installed successfully"
  return 0
}
```

#### Pattern 2: Validation Before Action

```bash
configure_file() {
  local file="$1"
  
  # Validate preconditions
  if [[ ! -f "$file" ]]; then
    log_error "File not found: $file"
    return 1
  fi
  
  if [[ ! -w "$file" ]]; then
    log_error "File not writable: $file"
    return 1
  fi
  
  # Proceed with configuration
  # ...
}
```

#### Pattern 3: Backup Before Modification

```bash
modify_config() {
  local config_file="$1"
  
  # Create backup
  if [[ -f "$config_file" && ! -f "${config_file}.bak" ]]; then
    if ! cp "$config_file" "${config_file}.bak"; then
      log_error "Failed to create backup"
      return 1
    fi
  fi
  
  # Modify (can safely rollback from .bak if needed)
  # ...
}
```

### Logging Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Log Levels                        │
│                                                     │
│  0: DEBUG   - Detailed diagnostic information      │
│  1: INFO    - General informational messages       │
│  2: WARN    - Warning messages                     │
│  3: ERROR   - Error messages                       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                Log Destinations                     │
│                                                     │
│  File:    ~/.local/state/auto-penguin-setup/logs/  │
│           • All levels logged                      │
│           • Timestamped entries                    │
│           • Rotation at 3MB                        │
│                                                     │
│  Console: stdout/stderr                            │
│           • INFO and above                         │
│           • Color-coded                            │
│           • Progress indicators                    │
└─────────────────────────────────────────────────────┘
```

---
