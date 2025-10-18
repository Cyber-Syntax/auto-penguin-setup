## Security Considerations

### Principle of Least Privilege

**Problem**: Script requires root for system-wide changes.

**Mitigation**:

1. Run with `sudo ./setup.sh`, not as root user
2. Each sudo call is explicit and logged
3. User can review script before running

### Input Validation

**All external inputs are validated**:

```bash
install_package() {
  local package="$1"
  
  # Validate input
  if [[ -z "$package" ]]; then
    log_error "Package name cannot be empty"
    return 1
  fi
  
  # Sanitize (prevent command injection)
  if [[ "$package" =~ [^a-zA-Z0-9._-] ]]; then
    log_error "Invalid package name: $package"
    return 1
  fi
  
  # Proceed
  pm_install "$package"
}
```

### File Permission Management

**Proper permissions on created files**:

```bash
create_config() {
  local config_file="$1"
  
  # Create with restricted permissions
  touch "$config_file"
  chmod 644 "$config_file"  # rw-r--r--
  
  # Sensitive files: 600
  if [[ "$config_file" == *".conf" ]]; then
    chmod 600 "$config_file"  # rw-------
  fi
}
```

### Backup Strategy

**Always backup before modification**

### Repository Trust

**Verify repository sources**:

1. **COPR/PPA**: User explicitly adds (informed consent)
2. **GPG Keys**: Imported before adding repos
3. **Checksums**: Verified for downloaded packages (ProtonVPN example)