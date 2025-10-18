# Execution Flow

### Script Initialization

```bash
#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# 1. Source core modules
source src/logging.sh
source src/distro_detection.sh
source src/package_manager.sh
source src/package_mapping.sh
source src/repository_manager.sh
source src/config.sh

# 2. Initialize configuration
init_config  # Loads variables.json and packages.json

# 3. Initialize package manager
init_package_manager  # Sets up PM commands for detected distro

# 4. Source feature modules
source src/general.sh
source src/apps.sh
source src/desktop.sh
source src/laptop.sh
```

### Command-Line Option Processing

The script uses getopts for option parsing:

```bash
./setup.sh -i -A -d -r -q
#          │  │  │  │  └─ Install Qtile packages
#          │  │  │  └──── Enable RPM Fusion
#          │  │  └─────── Speed up package manager
#          │  └────────── Install app packages
#          └───────────── Install core packages
```

### All-Option (-a) Execution Flow

When you run `./setup.sh -a`, the script:

1. **Detects System Type** (via hostname)

   ```bash
   SYSTEM_TYPE=$(detect_system_type)  # "desktop" or "laptop"
   ```

2. **Performs Common Setup**
   - Speed up package manager
   - Enable RPM Fusion / extra repos
   - Install core packages
   - Install app packages
   - Install dev packages

3. **Executes System-Specific Setup**

   **Desktop**:
   - Install desktop packages (NVIDIA, virt-manager, etc.)
   - Setup NVIDIA drivers
   - Setup virtualization
   - Configure gaming tools

   **Laptop**:
   - Install laptop packages (TLP, thinkfan, acpi)
   - Setup TLP power management
   - Setup Thinkfan fan control
   - Configure touchpad
   - Setup brightness control

4. **Applies Common Configurations**
   - Configure boot timeout
   - Setup sudoers
   - Enable TCP BBR
   - Configure display manager autologin

---

## Data Flow

### Installation Flow

```text
User Command: sudo ./setup.sh -i
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ 1. Source Core Modules (Strict Order)              │
│    • logging.sh                                     │
│    • distro_detection.sh                            │
│    • package_manager.sh                             │
│    • package_mapping.sh                             │
│    • repository_manager.sh                          │
│    • config.sh                                      │
│    • install_packages.sh                            │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. Auto-Source Feature Modules (Order Independent) │
│    for module in src/{apps,system,hardware,         │
│                      display,wm}/*.sh; do           │
│      [[ -f "$module" ]] && source "$module"         │
│    done                                             │
│                                                     │
│    Loaded modules by category:                     │
│    • apps/*     → 14 application installers        │
│    • system/*   → 10 system configurations         │
│    • hardware/* → 5 hardware-specific modules      │
│    • display/*  → 3 display manager configs        │
│    • wm/*       → 2 window manager installers      │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. Initialize Configuration                         │
│    init_config()                                    │
│    • Load variables.ini → env vars                 │
│    • Load packages.ini → arrays                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Initialize Package Manager                       │
│    init_package_manager()                           │
│    • Detect distro                                  │
│    • Set PM_* variables                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Execute Installation                             │
│    • Get package list: ${CORE_PACKAGES[@]}          │
│    • Map names: map_package_list                    │
│    • Install: pm_install "${mapped[@]}"             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. Log Results                                      │
│    • File: ~/.local/state/auto-penguin-setup/logs/  │
│    • Console: Color-coded output                    │
└─────────────────────────────────────────────────────┘
```

### Configuration Load Flow

```text
init_config()
    │
    ├─► check_and_create_config()
    │   │
    │   ├─► Check: ~/.config/auto-penguin-setup/ exists?
    │   │   ├─► Yes: Continue
    │   │   └─► No: Prompt to create, copy examples
    │   │
    │   └─► Return: Config directory path
    │
  ├─► load_variables()
    │   │
  │   ├─► load_ini_config("variables.ini")
  │   │   └─► Find file in: config dir, fallback, examples
  │   │
  │   ├─► parse_ini() for each variable (via ini_parser)
  │   │   └─► parse_ini variables.ini "user"
    │   │
    │   └─► export variables to environment
    │       ├─► export user="..."
    │       ├─► export hostname_desktop="..."
    │       └─► ...
    │
    └─► load_package_arrays()
        │
    ├─► load_ini_config("packages.ini")
        │
        └─► For each category:
      ├─► parse_ini / read lines under `[core]`
            ├─► mapfile -t CORE_PACKAGES
            └─► export CORE_PACKAGES
```

### Cross-Distro Installation Flow

```text
install_brave()  # From src/apps/brave.sh
    │
    ├─► log_info "Installing Brave Browser..."
    │
    ├─► Get $CURRENT_DISTRO
    │
    ├─► case "$CURRENT_DISTRO" in
    │   │
    │   ├─► fedora:
    │   │   ├─► Import GPG key
    │   │   ├─► Add RPM repository
    │   │   └─► pm_install "brave-browser"
    │   │       └─► sudo dnf install -y brave-browser
    │   │
    │   ├─► arch:
    │   │   └─► repo_add "brave-bin"
    │   │       └─► paru -S --noconfirm brave-bin
    │   │
    │   └─► debian:
    │       ├─► Import GPG key
    │       ├─► Add DEB repository
    │       ├─► pm_update → apt-get update
    │       └─► pm_install "brave-browser"
    │           └─► sudo apt-get install -y brave-browser
    │
    └─► log_success "Brave Browser installed successfully"
```
