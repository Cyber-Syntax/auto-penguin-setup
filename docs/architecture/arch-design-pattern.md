## Architecture Patterns

### 1. Module System

The project uses a **modular monolith** architecture - a single script that sources independent modules organized by functional categories.

```
┌────────────────────────────────────────────────────────────┐
│                      setup.sh (Orchestrator)                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Command-Line │  │ System Type  │  │    Main      │    │
│  │   Parsing    │→ │  Detection   │→ │  Execution   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Core Modules   │  │Feature Modules  │  │ Config Modules  │
│  (src/core/)    │  │  (Categorized)  │  │  (src/core/)    │
│                 │  │                 │  │                 │
│ • logging       │  │ src/apps/       │  │ • config        │
│ • distro_detect │  │ • brave.sh      │  │ • constants     │
│ • package_mgr   │  │ • vscode.sh     │  │ • create_config │
│ • pkg_mapping   │  │ • ollama.sh     │  │ • update_config │
│ • repo_manager  │  │ • lazygit.sh    │  │                 │
│ • install_pkgs  │  │ • ... (10 more) │  │                 │
│                 │  │                 │  │                 │
│                 │  │ src/system/     │  │                 │
│                 │  │ • grub.sh       │  │                 │
│                 │  │ • network.sh    │  │                 │
│                 │  │ • ufw.sh        │  │                 │
│                 │  │ • ffmpeg.sh     │  │                 │
│                 │  │ • ... (6 more)  │  │                 │
│                 │  │                 │  │                 │
│                 │  │ src/hardware/   │  │                 │
│                 │  │ • nvidia.sh     │  │                 │
│                 │  │ • amd.sh        │  │                 │
│                 │  │ • intel.sh      │  │                 │
│                 │  │ • touchpad.sh   │  │                 │
│                 │  │ • hostname.sh   │  │                 │
│                 │  │                 │  │                 │
│                 │  │ src/display/    │  │                 │
│                 │  │ • sddm.sh       │  │                 │
│                 │  │ • gdm.sh        │  │                 │
│                 │  │ • lightdm.sh    │  │                 │
│                 │  │                 │  │                 │
│                 │  │ src/wm/         │  │                 │
│                 │  │ • qtile.sh      │  │                 │
│                 │  │ • hyprland.sh   │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### Why Modular Monolith with Categorization?

**Advantages**:

- **Simple deployment**: Single script + organized modules
- **Shared state**: Environment variables accessible across modules
- **Easy navigation**: Developers know exactly where to find functionality
- **Clear separation**: Hardware vs. system vs. apps vs. display managers
- **No complex dependency management**: Modules sourced in predictable order
- **Discoverability**: New contributors immediately understand the structure
- **Maintainability**: Changes isolated to specific functional areas

**Category Rationale**:

- **apps/**: Third-party application installers with custom installation logic
- **system/**: Core system configurations affecting OS behavior
- **hardware/**: Hardware-specific drivers and configurations
- **display/**: Display manager and login screen configurations
- **wm/**: Window manager and compositor installations

**Trade-offs**:

- All modules loaded in memory (acceptable for script size ~50KB total)
- Global variable namespace (mitigated by naming conventions)
- Slightly deeper directory structure (benefits outweigh minimal complexity)

### 2. Strategy Pattern

The package manager abstraction implements the **Strategy Pattern**:

```bash
# Strategy Interface (implicit in bash)
pm_install()    # Install packages
pm_remove()     # Remove packages
pm_update()     # Update system
pm_is_installed() # Check installation

# Concrete Strategies (selected at runtime)
Case "$CURRENT_DISTRO" in
  fedora) PM_INSTALL="dnf install -y" ;;
  arch)   PM_INSTALL="pacman -S --noconfirm" ;;
  debian) PM_INSTALL="apt-get install -y" ;;
esac
```

**Benefits**:

- Runtime selection of package manager
- Easy to add new package managers
- Consistent interface regardless of distro

### 3. Template Method Pattern

Feature installation functions follow the **Template Method Pattern**:

```bash
install_application() {
  # Template: Fixed sequence, variable implementation
  
  log_info "Installing application..."  # 1. Log start
  
  case "$CURRENT_DISTRO" in            # 2. Distro-specific logic
    fedora) install_fedora_specific ;;
    arch) install_arch_specific ;;
    debian) install_debian_specific ;;
  esac
  
  verify_installation                   # 3. Verification
  
  log_success "Installation completed"  # 4. Log success
  return 0
}
```

**Benefits**:

- Consistent structure across all functions
- Easy to understand and maintain
- Built-in logging and error handling

### 4. Facade Pattern

The `init_config()` function is a **Facade** that simplifies configuration initialization:

```bash
init_config() {
  # Facade: Simple interface to complex subsystem
  check_and_create_config
  load_variables
  load_package_arrays
  
  # Behind the scenes:
  # - Checks for config files
  # - Prompts user if needed
  # - Parses INI files using the project's ini_parser
  # - Loads into environment
  # - Validates data
}
```

### 5. Factory Pattern

The `detect_distro()` function acts as a **Factory**:

```bash
detect_distro() {
  # Factory: Creates the right "product" based on environment
  source /etc/os-release
  
  case "${ID,,}" in
    fedora) echo "fedora" ;;        # Product A
    arch) echo "arch" ;;             # Product B
    debian) echo "debian" ;;         # Product C
  esac
}
```

---