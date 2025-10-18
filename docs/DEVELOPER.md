# Auto-Penguin-Setup Developer Guide

**Comprehensive Reference for Contributing Developers**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Module Reference](#module-reference)
4. [Function Call Chains](#function-call-chains)
5. [Adding New Features](#adding-new-features)
6. [Code Style & Conventions](#code-style--conventions)
7. [Testing Guide](#testing-guide)
8. [Common Development Tasks](#common-development-tasks)
9. [Debugging Tips](#debugging-tips)
10. [Contributing Guidelines](#contributing-guidelines)

---

## Getting Started

### Prerequisites

**Required Tools**:

- Bash 4.0+
- `src/core/ini_parser.sh` (project INI parser)
- `git`
- One of: Fedora 41+, Arch Linux, or Debian/Ubuntu

**Recommended Tools**:

- `shellcheck` (bash linter)
- `shfmt` (bash formatter)
- `bats` (Bash Automated Testing System)
- Docker/Podman (for cross-distro testing)

### Setting Up Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/auto-penguin-setup.git
cd auto-penguin-setup

# 2. Install development dependencies
# Fedora
sudo dnf install shellcheck shfmt bats

# Arch
sudo pacman -S shellcheck shfmt bats

# Debian/Ubuntu
sudo apt install shellcheck shfmt bats

# 3. Set up test configuration
mkdir -p ~/.config/auto-penguin-setup
cp config_examples/* ~/.config/auto-penguin-setup/

# 4. Run tests to verify setup
cd tests
bats test_*.sh
```

### Project Structure Quick Reference

```
auto-penguin-setup/
├── setup.sh                    # Main entry point
├── src/                        # Source modules
│   ├── logging.sh             # Must be loaded first
│   ├── distro_detection.sh    # Core: distro detection
│   ├── package_manager.sh     # Core: PM abstraction
│   ├── package_mapping.sh     # Core: package name mapping
│   ├── repository_manager.sh  # Core: repo management
│   ├── config.sh              # Config loading
│   ├── constants.sh           # Global constants
│   ├── apps.sh                # Third-party apps
│   ├── desktop.sh             # Desktop functions
│   ├── laptop.sh              # Laptop functions
│   ├── general.sh             # General utilities
│   └── display_manager.sh     # Display manager config
├── configs/                    # System config templates
├── config_examples/           # User config examples
├── docs/                      # Documentation
└── tests/                     # Test suite
```

---

## Development Environment

### Editor Setup

#### VS Code

Recommended extensions:

```json
{
  "recommendations": [
    "timonwong.shellcheck",
    "foxundermoon.shell-format",
    "mads-hartmann.bash-ide-vscode"
  ]
}
```

Settings (`.vscode/settings.json`):

```json
{
  "shellcheck.enable": true,
  "shellcheck.run": "onType",
  "shellformat.effectLanguages": ["shellscript"],
  "shellformat.flag": "-i 2 -ci -bn"
}
```

#### Vim/Neovim

Add to `.vimrc`:

```vim
" Bash syntax checking
let g:syntastic_sh_checkers = ['shellcheck']

" Auto-format on save
autocmd FileType sh autocmd BufWritePre <buffer> %!shfmt -i 2 -ci -bn
```

### Git Hooks

Set up pre-commit hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running pre-commit checks..."

# 1. Run shellcheck
for file in $(git diff --cached --name-only | grep '\.sh$'); do
  echo "Checking $file..."
  shellcheck "$file" || exit 1
done

# 2. Run shfmt
for file in $(git diff --cached --name-only | grep '\.sh$'); do
  echo "Formatting $file..."
  shfmt -i 2 -ci -bn -w "$file"
  git add "$file"
done

# 3. Run tests
echo "Running tests..."
cd tests && bats test_*.sh || exit 1

echo "All checks passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Module Reference

### Core Modules

#### logging.sh

**Purpose**: Centralized logging system with file and console output.

**Dependencies**: None (must be loaded first)

**Global Variables**:

```bash
LOG_LEVEL=1              # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
LOG_FILE=""              # Set by init_logging()
LOG_DIR=""               # Default: ~/.local/state/auto-penguin-setup/logs/
MAX_LOG_SIZE=3145728     # 3MB in bytes
MAX_BACKUPS=3            # Number of rotated logs to keep
```

**Public Functions**:

```bash
# Initialize logging (called automatically when sourced)
init_logging()

# Log functions (use these in your code)
log_debug <message>     # Debug info (only in debug mode)
log_info <message>      # General information
log_warn <message>      # Warnings
log_error <message>     # Errors
log_success <message>   # Success messages (green)

# Utility functions
log_cmd <command>       # Execute and log command
rotate_logs()           # Rotate log files
cleanup_old_logs <days> # Clean up old logs
```

**Usage Example**:

```bash
# In your function
my_function() {
  log_info "Starting my_function..."
  
  if ! some_command; then
    log_error "some_command failed"
    return 1
  fi
  
  log_success "my_function completed successfully"
  return 0
}
```

**Implementation Details**:

- Log files are stored in XDG-compliant location
- Automatic log rotation when file exceeds 3MB
- Console output is color-coded by level
- File logging includes timestamps
- Process-specific guard prevents duplicate console messages

---

#### distro_detection.sh

**Purpose**: Detect and validate Linux distribution.

**Dependencies**: `logging.sh`

**Global Variables**:

```bash
SUPPORTED_DISTROS=("fedora" "arch" "debian")
```

**Public Functions**:

```bash
# Main detection function
detect_distro() → "fedora" | "arch" | "debian"

# Get distribution version
get_distro_version() → "41" | "rolling" | "12"

# Get human-readable name
get_distro_pretty_name() → "Fedora Linux 41"

# Validate distribution support
validate_distro_support [distro] → 0 | 1

# Boolean checks
is_fedora() → 0 | 1
is_arch() → 0 | 1
is_debian() → 0 | 1
```

**Usage Example**:

```bash
# Detect distribution
DISTRO=$(detect_distro) || {
  log_error "Unsupported distribution"
  exit 1
}

# Conditional logic
if is_fedora; then
  # Fedora-specific code
elif is_arch; then
  # Arch-specific code
elif is_debian; then
  # Debian-specific code
fi
```

**Implementation Details**:

- Reads `/etc/os-release` file
- Normalizes distribution IDs (e.g., "archlinux" → "arch")
- Maps derivatives to base (e.g., Ubuntu → debian, Manjaro → arch)
- Returns 1 and logs error for unsupported distributions

**Adding New Distribution**:

```bash
# In detect_distro()
case "${ID,,}" in
  fedora) distro="fedora" ;;
  arch|archlinux|manjaro) distro="arch" ;;  # Add manjaro
  debian|ubuntu|linuxmint|pop|elementary) distro="debian" ;;  # Add elementary
  *)
    log_error "Unsupported distribution: $ID"
    return 1
    ;;
esac
```

---

#### package_manager.sh

**Purpose**: Unified package manager abstraction layer.

**Dependencies**: `logging.sh`, `distro_detection.sh`

**Global Variables**:

```bash
PM_INSTALL=""         # Command to install packages
PM_REMOVE=""          # Command to remove packages
PM_UPDATE=""          # Command to update system
PM_SEARCH=""          # Command to search packages
PM_IS_INSTALLED=""    # Command to check if installed
PM_SUDO=""            # "sudo" or "" (for AUR helpers)
CURRENT_DISTRO=""     # Detected distribution
```

**Public Functions**:

```bash
# Initialize (MUST be called before using other functions)
init_package_manager() → 0 | 1

# Package operations
pm_install <packages...> → 0 | 1
pm_remove <packages...> → 0 | 1
pm_update() → 0 | 1
pm_search <query> → search_results
pm_is_installed <package> → 0 | 1

# Batch installation
pm_install_array <packages_array[@]> → 0 | 1
```

**Usage Example**:

```bash
# Initialize once at startup
init_package_manager || exit 1

# Install single package
pm_install vim

# Install multiple packages
pm_install vim neovim htop

# Install from array
PACKAGES=("vim" "neovim" "htop")
pm_install_array "${PACKAGES[@]}"

# Check if installed
if pm_is_installed vim; then
  log_info "vim is already installed"
fi
```

**Implementation Details**:

**Initialization**:

```bash
init_package_manager() {
  CURRENT_DISTRO=$(detect_distro) || return 1
  
  case "$CURRENT_DISTRO" in
    fedora)
      PM_INSTALL="dnf install -y"
      PM_REMOVE="dnf remove -y"
      PM_UPDATE="dnf update -y"
      PM_SEARCH="dnf search"
      PM_IS_INSTALLED="rpm -q"
      PM_SUDO="sudo"
      ;;
    arch)
      # Prefer pacman, fallback to AUR helpers
      if command -v pacman &>/dev/null; then
        PM_INSTALL="pacman -S --noconfirm"
        # ... other commands
        PM_SUDO="sudo"
      elif command -v paru &>/dev/null; then
        PM_INSTALL="paru -S --noconfirm"
        # ... paru handles sudo internally
        PM_SUDO=""
      fi
      ;;
    debian)
      PM_INSTALL="apt-get install -y"
      PM_REMOVE="apt-get remove -y"
      PM_UPDATE="apt-get update && apt-get upgrade -y"
      PM_SEARCH="apt-cache search"
      PM_IS_INSTALLED="dpkg -l"
      PM_SUDO="sudo"
      ;;
  esac
}
```

**Error Handling**:

- All functions validate PM is initialized
- Return 1 on failure, 0 on success
- Comprehensive error logging
- `pm_install_array` tries batch first, then individual on failure

---

#### package_mapping.sh

**Purpose**: Translate package names across distributions.

**Dependencies**: `logging.sh`, `distro_detection.sh`

**Global Variables**:

```bash
declare -A PACKAGE_MAPPINGS  # Associative array of mappings
```

**Public Functions**:

```bash
# Load mappings from JSON
load_package_mappings <config_file> → 0 | 1

# Map single package name
map_package_name <package> [distro] → mapped_name

# Map list of packages
map_package_list <distro> <packages...> → mapped_names

# Get device-specific packages
get_device_packages <laptop|desktop> <config_file> → packages

# Get category packages
get_common_packages <category> <config_file> → packages

# Validate mappings
validate_mappings <config_file> → 0 | 1
```

**Usage Example**:

```bash
# Load mappings
load_package_mappings "$CONFIG_DIR/packages.ini"

# Map a single package
MAPPED=$(map_package_name "python3-devel")
# Returns: python3-devel (Fedora), python (Arch), python3-dev (Debian)

# Map a list
DISTRO=$(detect_distro)
MAPPED_LIST=$(map_package_list "$DISTRO" "fd-find" "python3-devel")

# Get laptop-specific packages
LAPTOP_PKGS=$(get_device_packages "laptop" "$CONFIG_DIR/packages.ini")
```

**Mapping Data Structure**:

```bash
# In memory after load_package_mappings():
PACKAGE_MAPPINGS["fd-find:fedora"]="fd-find"
PACKAGE_MAPPINGS["fd-find:arch"]="fd"
PACKAGE_MAPPINGS["fd-find:debian"]="fd-find"

PACKAGE_MAPPINGS["python3-devel:fedora"]="python3-devel"
PACKAGE_MAPPINGS["python3-devel:arch"]="python"
PACKAGE_MAPPINGS["python3-devel:debian"]="python3-dev"
```

**Adding New Mappings**:

In `packages.ini`:

```json
{
  "mappings": {
    "new-package": {
      "fedora": "fedora-package-name",
      "arch": "arch-package-name",
      "debian": "debian-package-name"
    }
  }
}
```

---

#### repository_manager.sh

**Purpose**: Abstract repository management (COPR, AUR, PPA).

**Dependencies**: `logging.sh`, `distro_detection.sh`

**Public Functions**:

```bash
# Add repository
repo_add <identifier> → 0 | 1

# Enable/disable repository
repo_enable <name> → 0 | 1
repo_disable <name> → 0 | 1

# Update repository metadata
repo_update() → 0 | 1

# Enable extra repositories (distro-agnostic)
enable_rpm_fusion_distro_agnostic() → 0 | 1
```

**Usage Example**:

```bash
# Fedora COPR
repo_add "atim/lazygit"

# Arch AUR (via helper)
repo_add "brave-bin"

# Debian PPA
repo_add "ppa:neovim-ppa/unstable"

# Enable extra repos
enable_rpm_fusion_distro_agnostic
```

**Implementation Details**:

Repository identifier formats:

- **Fedora COPR**: `user/repo` (e.g., `atim/lazygit`)
- **Arch AUR**: `package-name` (installed via AUR helper)
- **Debian PPA**: `ppa:user/repo` (e.g., `ppa:neovim-ppa/unstable`)

**Cross-Distro Repo Setup**:

```bash
enable_rpm_fusion_distro_agnostic() {
  local distro
  distro=$(detect_distro) || return 1
  
  case "$distro" in
    fedora)
      # Enable RPM Fusion free and nonfree
      ;;
    arch)
      # AUR provides extra packages
      log_info "Using AUR for additional packages"
      ;;
    debian)
      # Enable contrib and non-free
      sudo add-apt-repository -y contrib
      sudo add-apt-repository -y non-free
      ;;
  esac
}
```

---

#### config.sh

**Purpose**: Configuration file management and JSON parsing.

**Dependencies**: `logging.sh`, `distro_detection.sh`, `package_manager.sh`, `package_mapping.sh`

**Global Variables**:

```bash
readonly SCRIPT_DIR           # Source directory
readonly PROJECT_ROOT         # Project root directory
readonly CONFIG_DIR           # ~/.config/auto-penguin-setup
readonly EXAMPLES_DIR         # config_examples/

# Loaded configuration
export user                   # Current user
export hostname_desktop       # Desktop hostname
export hostname_laptop        # Laptop hostname
export laptop_session         # Laptop DE session
export desktop_session        # Desktop DE session
# ... many more exported variables

# Package arrays
CORE_PACKAGES=()
APPS_PACKAGES=()
DEV_PACKAGES=()
DESKTOP_PACKAGES=()
LAPTOP_PACKAGES=()
QTILE_PACKAGES=()
FLATPAK_PACKAGES=()
```

**Public Functions**:

```bash
# Configuration initialization
check_and_create_config() → 0 | 1
init_config() → 0 | exits

# File operations
load_ini_config <filename> → filepath | ""
parse_ini <file> <filter> → value | ""

# Variable loading
load_variables() → 0 | 1
load_package_arrays() → 0 | 1

# Variable getters
get_variable <jq_path> → value

# Package getters
load_packages <category> → space_separated_list

# Schema management
update_config_schema [post_migration] → 0 | 1
backup_config_file <file> → 0 | 1

# Default creation
create_default_packages_ini <output_file> → 0 | 1
create_default_variables_ini <output_file> → 0 | 1
customize_variables_ini <file> → 0 | 1
```

**Usage Example**:

```bash
# Initialize all configuration
init_config  # Calls all necessary functions

# After init_config, variables are available:
echo "User: $user"
echo "Desktop hostname: $hostname_desktop"
echo "Core packages: ${CORE_PACKAGES[@]}"

# Manual loading
variables_file=$(load_ini_config "variables.ini")
user_name=$(parse_ini "$variables_file" "user")

# Get a specific variable
browser=$(get_variable ".browser.firefox_profile")

# Load specific package category
dev_packages=$(load_packages "dev")
```

**Configuration Flow**:

1. **check_and_create_config**:
   - Checks if `~/.config/auto-penguin-setup/` exists
   - Prompts user to create if missing
   - Copies examples with customization

2. **load_variables**:

- Loads `variables.ini`
- Parses all variables with the project's INI parser
- Exports to environment

3. **load_package_arrays**:

- Loads `packages.ini`
- Populates bash arrays for each category
- Exports arrays

**Schema Update Process**:

When configuration schema changes:

```bash
update_config_schema() {
  # 1. Detect missing keys by comparing with examples
  # 2. Prompt user to update
  # 3. Create backup (.bak)
  # 4. Merge: user values + new keys from examples
  # 5. Validate config structure
  # 6. Replace config file
}
```

---

### Feature Modules

#### apps.sh

**Purpose**: Third-party application installation.

**Dependencies**: All core modules, `config.sh`

**Global Variables**:

```bash
readonly CURRENT_DISTRO  # From package_manager
```

**Public Functions**:

```bash
# Application installers
install_lazygit() → 0 | 1
install_brave() → 0 | 1
install_vscode() → 0 | 1
install_protonvpn() → 0 | 1
install_auto_cpufreq() → 0 | 1

# Configuration
disable_keyring_for_brave() → 0 | 1

# Helpers
install_lazygit_from_github() → 0 | 1
```

**Function Template**:

```bash
install_application() {
  log_info "Installing Application..."
  
  case "$CURRENT_DISTRO" in
    fedora)
      # 1. Add repository (if needed)
      # 2. Import GPG key (if needed)
      # 3. Install package
      ;;
    arch)
      # Install from AUR or official repos
      ;;
    debian)
      # 1. Add repository
      # 2. Import GPG key
      # 3. Update package lists
      # 4. Install package
      ;;
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac
  
  log_success "Application installation completed"
  return 0
}
```

**Adding New Application**:

1. Create function following template
2. Handle each supported distribution
3. Add to `setup.sh` options
4. Add tests
5. Document in help message

Example:

```bash
install_my_app() {
  log_info "Installing My App..."
  
  case "$CURRENT_DISTRO" in
    fedora)
      repo_add "user/myapp-copr"
      pm_install myapp
      ;;
    arch)
      repo_add "myapp-bin"
      ;;
    debian)
      repo_add "ppa:user/myapp"
      pm_update
      pm_install myapp
      ;;
  esac
  
  # Verify installation
  if ! command -v myapp &>/dev/null; then
    log_error "My App installation failed"
    return 1
  fi
  
  log_success "My App installed successfully"
  return 0
}
```

---

#### desktop.sh

**Purpose**: Desktop/gaming system configurations.

**Dependencies**: Core modules, `config.sh`

**Public Functions**:

```bash
# AI/ML
install_ollama() → 0 | 1

# Hardware management
nfancurve_setup() → 0 | 1
zenpower_setup() → 0 | 1

# NVIDIA
nvidia_cuda_setup() → 0 | 1
switch_nvidia_open() → 0 | 1
vaapi_setup() → 0 | 1

# System utilities
borgbackup_setup() → 0 | 1
trash_cli_setup() → 0 | 1
gdm_auto_login() → 0 | 1
remove_gnome() → 0 | 1
```

**Example Implementation**:

```bash
nvidia_cuda_setup() {
  log_info "Setting up NVIDIA CUDA..."
  
  # Validate NVIDIA GPU present
  if ! lspci | grep -i nvidia &>/dev/null; then
    log_error "No NVIDIA GPU detected"
    return 1
  fi
  
  local distro
  distro=$(detect_distro) || return 1
  
  case "$distro" in
    fedora)
      local version
      version=$(get_distro_version)
      # Add CUDA repository
      # Install cuda-toolkit
      ;;
    arch)
      pm_install cuda cuda-tools
      ;;
    debian)
      # Add NVIDIA CUDA repository
      # Install cuda-toolkit
      ;;
  esac
  
  # Verify installation
  if ! command -v nvcc &>/dev/null; then
    log_error "CUDA installation failed"
    return 1
  fi
  
  log_success "CUDA setup completed"
  return 0
}
```

---

#### laptop.sh

**Purpose**: Laptop-specific configurations and power management.

**Dependencies**: Core modules, `config.sh`

**Public Functions**:

```bash
# System
laptop_hostname_change() → 0 | 1

# Power management
tlp_setup() → 0 | 1
thinkfan_setup() → 0 | 1

# Graphics
xorg_setup_intel() → 0 | 1

# Input devices
touchpad_setup() → 0 | 1
setup_qtile_backlight_rules() → 0 | 1

# Networking
ssh_setup_laptop() → 0 | 1
```

**TLP Setup Process**:

```bash
tlp_setup() {
  log_info "Setting up TLP..."
  
  # 1. Install TLP if not present
  if ! pm_is_installed tlp; then
    pm_install tlp || return 1
  fi
  
  # 2. Copy configuration
  sudo cp "$tlp_file" "$dir_tlp"
  
  # 3. Handle conflicting services (distro-specific)
  local distro
  distro=$(detect_distro)
  
  case "$distro" in
    fedora)
      # Disable TuneD on Fedora 41+
      systemctl disable --now tuned tuned-ppd
      pm_remove tuned tuned-ppd
      
      # Disable power-profiles-daemon on older Fedora
      systemctl disable --now power-profiles-daemon
      ;;
    arch|debian)
      # Disable power-profiles-daemon
      systemctl disable --now power-profiles-daemon
      ;;
  esac
  
  # 4. Enable TLP services
  systemctl enable --now tlp tlp-sleep
  
  # 5. Mask rfkill (let TLP handle radios)
  systemctl mask systemd-rfkill.service systemd-rfkill.socket
  
  # 6. Enable TLP radio device handling
  tlp-rdw enable
  
  log_success "TLP setup completed"
  return 0
}
```

---

#### general.sh

**Purpose**: General system optimizations and utilities.

**Dependencies**: Core modules, `config.sh`

**Public Functions**:

```bash
# Package manager optimization
speed_up_package_manager() → 0 | 1
speed_up_package_manager() → 0 | 1
speed_up_pacman() → 0 | 1
speed_up_apt() → 0 | 1

# System configuration
grub_timeout() → 0 | 1
sudoers_setup() → 0 | 1
tcp_bbr_setup() → 0 | 1
selinux_context() → 0 | 1

# Firewall
switch_ufw_setup() → 0 | 1

# Media
ffmpeg_swap() → 0 | 1

# Repositories
enable_rpm_fusion() → 0 | 1

# Display managers
switch_lightdm() → 0 | 1
lightdm_autologin() → 0 | 1

# Services
syncthing_setup() → 0 | 1
virt_manager_setup() → 0 | 1

# Shell
oh_my_zsh_setup() → 0 | 1

# Applications
setup_default_applications() → 0 | 1
app_name_to_desktop_file <app_name> → desktop_file
```

**Cross-Distro Pattern Example**:

```bash
speed_up_package_manager() {
  local distro
  distro=$(detect_distro) || return 1
  
  log_info "Optimizing package manager for $distro..."
  
  case "$distro" in
    fedora)
      speed_up_package_manager
      ;;
    arch)
      speed_up_pacman
      ;;
    debian)
      speed_up_apt
      ;;
    *)
      log_error "Unsupported distribution: $distro"
      return 1
      ;;
  esac
  
  log_success "Package manager optimization completed"
}
```

---

## Function Call Chains

### Typical Installation Flow

```
setup.sh -i (install core packages)
    │
    ├─► source logging.sh
    ├─► source distro_detection.sh
    ├─► source package_manager.sh
    ├─► source config.sh
    │
    ├─► init_config()
    │   ├─► check_and_create_config()
    │   ├─► load_variables()
    │   └─► load_package_arrays()
    │
    ├─► init_package_manager()
    │   ├─► detect_distro()
    │   └─► Set PM_* variables
    │
    └─► Install core packages
        ├─► Get CORE_PACKAGES[@]
        ├─► Map package names (if needed)
        └─► pm_install "${mapped_packages[@]}"
            └─► Execute distro-specific install command
```

### Application Installation Chain

```
install_brave()
    │
    ├─► log_info "Installing Brave Browser..."
    │
    ├─► Check $CURRENT_DISTRO
    │
    ├─► case "$CURRENT_DISTRO" in
    │   │
    │   ├─► fedora:
    │   │   ├─► sudo rpm --import <gpg_key>
    │   │   ├─► sudo dnf config-manager --add-repo <repo_url>
    │   │   └─► pm_install "brave-browser"
    │   │       └─► sudo dnf install -y brave-browser
    │   │
    │   ├─► arch:
    │   │   └─► repo_add "brave-bin"
    │   │       └─► paru -S --noconfirm brave-bin
    │   │
    │   └─► debian:
    │       ├─► curl <gpg_key> | sudo tee <keyring>
    │       ├─► echo <repo> | sudo tee <sources_list>
    │       ├─► pm_update
    │       │   └─► sudo apt-get update
    │       └─► pm_install "brave-browser"
    │           └─► sudo apt-get install -y brave-browser
    │
    ├─► disable_keyring_for_brave()
    │   ├─► Copy system desktop file to user dir
    │   ├─► Create backup
    │   └─► Modify with sed to add --password-store=basic
    │
    └─► log_success "Brave Browser installation completed"
```

### TLP Setup Chain (Laptop)

```
tlp_setup()
    │
    ├─► detect_distro() and get_distro_version()
    │
    ├─► Check if TLP installed
    │   └─► If not: pm_install tlp
    │
    ├─► Copy TLP configuration
    │   └─► sudo cp ./configs/01-mytlp.conf /etc/tlp.d/
    │
    ├─► Handle conflicting services (distro-specific)
    │   ├─► Fedora 41+:
    │   │   ├─► systemctl disable --now tuned tuned-ppd
    │   │   └─► pm_remove tuned tuned-ppd
    │   │
    │   ├─► Fedora <41:
    │   │   ├─► systemctl disable --now power-profiles-daemon
    │   │   └─► pm_remove power-profiles-daemon
    │   │
    │   └─► Arch/Debian:
    │       └─► systemctl disable --now power-profiles-daemon
    │
    ├─► Enable TLP services
    │   ├─► systemctl enable --now tlp
    │   └─► systemctl enable --now tlp-sleep
    │
    ├─► Mask rfkill services
    │   ├─► systemctl mask systemd-rfkill.service
    │   └─► systemctl mask systemd-rfkill.socket
    │
    ├─► Enable TLP radio device handling
    │   └─► tlp-rdw enable
    │
    └─► log_success "TLP setup completed"
```

---

## Adding New Features

### Adding a New Distribution

**Steps**:

1. **Update `distro_detection.sh`**:

```bash
detect_distro() {
  source /etc/os-release
  
  case "${ID,,}" in
    fedora) distro="fedora" ;;
    arch|archlinux|manjaro) distro="arch" ;;
    debian|ubuntu|linuxmint|pop) distro="debian" ;;
    opensuse*) distro="opensuse" ;;  # NEW
    *)
      log_error "Unsupported distribution: $ID"
      return 1
      ;;
  esac
  
  echo "$distro"
}

# Add helper function
is_opensuse() {
  local distro
  distro=$(detect_distro) || return 1
  [[ "$distro" == "opensuse" ]]
}
```

2. **Update `package_manager.sh`**:

```bash
init_package_manager() {
  CURRENT_DISTRO=$(detect_distro) || return 1
  
  case "$CURRENT_DISTRO" in
    # ... existing cases
    opensuse)  # NEW
      PM_INSTALL="zypper install -y"
      PM_REMOVE="zypper remove -y"
      PM_UPDATE="zypper update -y"
      PM_SEARCH="zypper search"
      PM_IS_INSTALLED="rpm -q"
      PM_SUDO="sudo"
      ;;
  esac
}
```

3. **Update `repository_manager.sh`**:

```bash
repo_add() {
  case "$distro" in
    # ... existing cases
    opensuse)  # NEW
      # openSUSE uses OBS (Open Build Service)
      sudo zypper addrepo -f "$1"
      sudo zypper refresh
      ;;
  esac
}
```

4. **Update `package_mapping.sh`**:

```bash
# Add openSUSE mappings to packages.ini
{
  "mappings": {
    "python3-devel": {
      "fedora": "python3-devel",
      "arch": "python",
      "debian": "python3-dev",
      "opensuse": "python3-devel"  # NEW
    }
  }
}
```

5. **Update feature functions** in `apps.sh`, `desktop.sh`, etc.:

```bash
install_application() {
  case "$CURRENT_DISTRO" in
    fedora) # ... ;;
    arch) # ... ;;
    debian) # ... ;;
    opensuse)  # NEW
      # openSUSE-specific installation
      ;;
  esac
}
```

6. **Add tests**:

```bash
# tests/test_packages.sh
@test "openSUSE package manager initialization" {
  export OS_RELEASE_ID="opensuse-tumbleweed"
  run init_package_manager
  [ "$status" -eq 0 ]
  [ "$PM_INSTALL" = "zypper install -y" ]
}
```

7. **Update documentation**:
   - README.md: Add to supported distributions table
   - WIKI.md: Add openSUSE examples
   - ARCHITECTURE.md: Document openSUSE-specific patterns

---

### Adding a New Application Installer

**Template**:

```bash
# In src/apps.sh

# Function: install_my_app
# Purpose: Installs My App with distro-specific repository setup
# Returns: 0 on success, 1 on failure
install_my_app() {
  log_info "Installing My App..."
  
  case "$CURRENT_DISTRO" in
    fedora)
      # Fedora/RPM-based installation
      log_info "Adding My App repository for Fedora..."
      
      # Import GPG key (if needed)
      if ! sudo rpm --import https://example.com/gpg.key; then
        log_error "Failed to import My App GPG key"
        return 1
      fi
      
      # Add repository
      if ! repo_add "user/myapp-copr"; then
        log_error "Failed to add My App repository"
        return 1
      fi
      
      # Install package
      if ! pm_install "myapp"; then
        log_error "Failed to install My App"
        return 1
      fi
      ;;
      
    arch)
      # Arch Linux installation
      log_info "Installing My App from AUR..."
      if ! repo_add "myapp-bin"; then
        log_error "Failed to install My App from AUR"
        return 1
      fi
      ;;
      
    debian)
      # Debian/Ubuntu installation
      log_info "Adding My App repository for Debian..."
      
      # Import GPG key
      if ! wget -qO- https://example.com/gpg.key | sudo apt-key add -; then
        log_error "Failed to import My App GPG key"
        return 1
      fi
      
      # Add repository
      if ! repo_add "ppa:user/myapp"; then
        log_error "Failed to add My App repository"
        return 1
      fi
      
      # Update and install
      if ! pm_update; then
        log_error "Failed to update package lists"
        return 1
      fi
      
      if ! pm_install "myapp"; then
        log_error "Failed to install My App"
        return 1
      fi
      ;;
      
    *)
      log_error "Unsupported distribution: $CURRENT_DISTRO"
      return 1
      ;;
  esac
  
  # Verify installation
  if ! command -v myapp &>/dev/null; then
    log_error "My App installation failed - binary not found"
    return 1
  fi
  
  log_success "My App installation completed"
  return 0
}
```

**Add to `setup.sh`**:

```bash
# In usage()
-m    Install My App.

# In getopts
while getopts "...m..." opt; do
  case "$opt" in
    m) myapp_option=true ;;
  esac
done

# In execution
if $myapp_option; then
  install_my_app
fi
```

**Add tests**:

```bash
# tests/test_apps.sh
@test "install_my_app succeeds on Fedora" {
  export CURRENT_DISTRO="fedora"
  run install_my_app
  [ "$status" -eq 0 ]
}
```

---

## Code Style & Conventions

### Naming Conventions

**Functions**:

- Lowercase with underscores: `function_name()`
- Descriptive and action-oriented: `install_package()`, `load_variables()`
- Module-prefixed for public functions: `pm_install()`, `repo_add()`

**Variables**:

- Global constants: UPPERCASE_WITH_UNDERSCORES
- Local variables: lowercase_with_underscores
- Exported config: lowercase (matching JSON keys)

**Example**:

```bash
# Good
readonly SCRIPT_DIR
readonly CURRENT_DISTRO
local package_name
export user

# Bad
readonly scriptdir
readonly currentDistro
local PackageName
export USER
```

### Function Documentation

**Template**:

```bash
# Function: function_name
# Purpose: Brief description of what the function does
# Parameters:
#   $1 - First parameter description
#   $2 - Second parameter description
# Returns: 0 on success, 1 on failure
# Environment: Variables used/modified (if any)
function_name() {
  # Implementation
}
```

**Example**:

```bash
# Function: pm_install
# Purpose: Install packages using the detected package manager
# Parameters:
#   $@ - Package names to install
# Returns: 0 on success, 1 on failure
# Environment: Requires PM_INSTALL and PM_SUDO to be set by init_package_manager
pm_install() {
  if [[ -z "$PM_INSTALL" ]]; then
    log_error "Package manager not initialized"
    return 1
  fi
  
  if [[ $# -eq 0 ]]; then
    log_warn "No packages specified"
    return 0
  fi
  
  log_info "Installing packages: $*"
  
  if [[ -n "$PM_SUDO" ]]; then
    $PM_SUDO $PM_INSTALL "$@" || return 1
  else
    $PM_INSTALL "$@" || return 1
  fi
  
  log_success "Packages installed successfully"
  return 0
}
```

### Error Handling Pattern

```bash
function_name() {
  # 1. Validate inputs
  if [[ -z "$1" ]]; then
    log_error "Parameter required"
    return 1
  fi
  
  # 2. Check preconditions
  if [[ ! -f "$file" ]]; then
    log_error "File not found: $file"
    return 1
  fi
  
  # 3. Create backup (if modifying)
  if ! cp "$file" "$file.bak"; then
    log_error "Failed to create backup"
    return 1
  fi
  
  # 4. Perform operation
  if ! operation; then
    log_error "Operation failed"
    return 1
  fi
  
  # 5. Verify result
  if ! verify; then
    log_error "Verification failed"
    return 1
  fi
  
  # 6. Success
  log_success "Operation completed"
  return 0
}
```

### Bash Best Practices

**Use strict mode**:

```bash
set -euo pipefail
```

**Quote variables**:

```bash
# Good
if [[ -f "$file" ]]; then
  echo "$message"
fi

# Bad
if [[ -f $file ]]; then
  echo $message
fi
```

**Use [[ ]] instead of [ ]**:

```bash
# Good
if [[ "$var" == "value" ]]; then

# Bad (can break with special characters)
if [ "$var" = "value" ]; then
```

**Check command existence**:

```bash
if command -v mycommand &>/dev/null; then
  # Command exists
fi
```

**Array handling**:

```bash
# Declare
declare -a my_array=()

# Append
my_array+=("element")

# Iterate
for item in "${my_array[@]}"; do
  echo "$item"
done

# Pass to function
my_function "${my_array[@]}"
```

---

## Testing Guide

### Running Tests

```bash
# Run all tests
cd tests
bats test_*.sh

# Run specific test file
bats test_packages.sh

# Run with verbose output
bats -t test_packages.sh

# Run single test
bats -f "test name" test_packages.sh
```

### Writing Tests

**Test file template**:

```bash
#!/usr/bin/env bats
# Test suite for module_name.sh

# Load test helper
load test_helper

setup() {
  # Set up test environment
  export BATS_TEST_TMPDIR="$(mktemp -d)"
  export PATH="$BATS_TEST_DIRNAME/mocks:$PATH"
  
  # Source module
  source src/module_name.sh
}

teardown() {
  # Clean up
  rm -rf "$BATS_TEST_TMPDIR"
}

@test "function_name succeeds with valid input" {
  run function_name "valid_input"
  
  [ "$status" -eq 0 ]
  [ "$output" = "expected output" ]
}

@test "function_name fails with invalid input" {
  run function_name "invalid_input"
  
  [ "$status" -eq 1 ]
  [[ "$output" =~ "error message" ]]
}
```

### Mocking Commands

Create mock scripts in `tests/mocks/`:

```bash
# tests/mocks/dnf
#!/usr/bin/env bash

case "$*" in
  "install -y vim")
    echo "Installing: vim"
    exit 0
    ;;
  "install -y nonexistent")
    echo "Error: No match for argument: nonexistent"
    exit 1
    ;;
  *)
    echo "Mock dnf: $*"
    exit 0
    ;;
esac
```

Make executable:

```bash
chmod +x tests/mocks/dnf
```

Use in tests:

```bash
setup() {
  export PATH="$BATS_TEST_DIRNAME/mocks:$PATH"
}

@test "pm_install uses mocked dnf" {
  export CURRENT_DISTRO="fedora"
  init_package_manager
  
  run pm_install vim
  [ "$status" -eq 0 ]
}
```

---

## Common Development Tasks

### Task 1: Add a Configuration Variable

Keep configuration examples centralized in `docs/architecture/config.arch.md` (and `config_examples/`). Update `variables.ini` there; then read it in `config.sh` with the INI helpers. Example usage:

```bash
# Load the user's INI file (done by init_config)
variables_file=$(load_ini_config "variables.ini")

# Read a value (ini parser provides parse_ini)
new_option1=$(parse_ini "$variables_file" "new_setting.option1" || echo "default")
export new_option1
```

---

### Task 2: Add a Package Category

Add the new section to `config_examples/packages.ini` and `docs/architecture/config.arch.md` (so examples and migrations stay centralized). Then load it via the standard helpers and convert to an array:

```bash
packages_file=$(load_ini_config "packages.ini")
# read each line under [my_new_category] into an array
mapfile -t MY_NEW_CATEGORY_PACKAGES < <(parse_ini_lines "$packages_file" "my_new_category")
```

# ... existing arrays
  
# New category

# Assuming packages are listed under [my_new_category]

  mapfile -t MY_NEW_CATEGORY_PACKAGES < <(awk 'BEGIN{in=0} /^\\[my_new_category\]/{in=1;next} /^\[/{in=0} in && NF{print $0}' "$packages_file")
  export MY_NEW_CATEGORY_PACKAGES
}

```

**3. Create installation function**:

```bash
install_my_new_category() {
  log_info "Installing my new category packages..."
  
  if [[ ${#MY_NEW_CATEGORY_PACKAGES[@]} -eq 0 ]]; then
    log_warn "No my new category packages defined"
    return 0
  fi
  
  pm_install_array "${MY_NEW_CATEGORY_PACKAGES[@]}"
}
```

**4. Add to `setup.sh`**:

```bash
# In usage
-y    Install my new category packages.

# In getopts
while getopts "...y..." opt; do
  case "$opt" in
    y) my_new_category_option=true ;;
  esac
done

# In execution
if $my_new_category_option; then
  install_my_new_category
fi
```

---

### Task 3: Add Cross-Distro Hardware Support

**Example**: Add Intel GPU configuration

**1. Create configuration file**:

```bash
# configs/20-intel.conf
Section "Device"
  Identifier  "Intel Graphics"
  Driver      "intel"
  Option      "TearFree" "true"
EndSection
```

**2. Create function** in appropriate module (`general.sh` or `desktop.sh`):

```bash
# Function: setup_intel_gpu
# Purpose: Configure Intel GPU with optimal settings
# Returns: 0 on success, 1 on failure
setup_intel_gpu() {
  log_info "Setting up Intel GPU configuration..."
  
  # Check if Intel GPU present
  if ! lspci | grep -i "intel.*graphics" &>/dev/null; then
    log_error "No Intel GPU detected"
    return 1
  fi
  
  local distro
  distro=$(detect_distro) || return 1
  
  # Install driver (if not present)
  case "$distro" in
    fedora)
      pm_install xorg-x11-drv-intel
      ;;
    arch)
      pm_install xf86-video-intel
      ;;
    debian)
      pm_install xserver-xorg-video-intel
      ;;
  esac
  
  # Copy configuration
  local config_file="./configs/20-intel.conf"
  local target_dir="/etc/X11/xorg.conf.d"
  local target_file="$target_dir/20-intel.conf"
  
  # Create directory if needed
  if [[ ! -d "$target_dir" ]]; then
    sudo mkdir -p "$target_dir"
  fi
  
  # Backup if exists
  if [[ -f "$target_file" && ! -f "${target_file}.bak" ]]; then
    sudo cp "$target_file" "${target_file}.bak"
  fi
  
  # Copy configuration
  if ! sudo cp "$config_file" "$target_file"; then
    log_error "Failed to copy Intel GPU configuration"
    return 1
  fi
  
  # Set permissions
  sudo chmod 644 "$target_file"
  
  log_success "Intel GPU configuration completed"
  log_info "Reboot required for changes to take effect"
  return 0
}
```

**3. Add to `setup.sh`**:

```bash
# Add option, implement, test
```

---

## Debugging Tips

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=0

# Run script
sudo ./setup.sh -i
```

### Trace Execution

```bash
# Enable bash tracing
bash -x ./setup.sh -i

# Or in script
set -x  # Enable tracing
# ... code to trace
set +x  # Disable tracing
```

### Check Logs

```bash
# Tail the log file
tail -f ~/.local/state/auto-penguin-setup/logs/auto-penguin-setup.log

# Search logs for errors
grep ERROR ~/.local/state/auto-penguin-setup/logs/auto-penguin-setup.log

# View last 100 lines
tail -n 100 ~/.local/state/auto-penguin-setup/logs/auto-penguin-setup.log
```

### Test Individual Functions

```bash
# Source modules manually
source src/logging.sh
source src/distro_detection.sh
source src/package_manager.sh

# Initialize
init_package_manager

# Test function
pm_install vim
```

### Interactive Debugging

Use bash debugger:

```bash
# Install bashdb
sudo dnf install bashdb  # Fedora
sudo apt install bashdb  # Debian

# Run with debugger
bashdb ./setup.sh -i
```

Commands in debugger:

- `n` - Next line
- `s` - Step into function
- `c` - Continue
- `p $var` - Print variable
- `l` - List code
- `q` - Quit

---

## Contributing Guidelines

### Before Contributing

1. Read all documentation (WIKI.md, ARCHITECTURE.md, this file)
2. Set up development environment
3. Run existing tests to ensure they pass
4. Check issues and PRs to avoid duplicate work

### Contribution Process

**1. Fork and Clone**:

```bash
git clone https://github.com/yourusername/auto-penguin-setup.git
cd auto-penguin-setup
git remote add upstream https://github.com/original/auto-penguin-setup.git
```

**2. Create Feature Branch**:

```bash
git checkout -b feature/my-new-feature
```

**3. Make Changes**:

- Follow code style guide
- Add tests for new functionality
- Update documentation
- Ensure all tests pass

**4. Commit**:

```bash
# Use conventional commits
git add .
git commit -m "feat: add support for openSUSE"
git commit -m "fix: resolve issue with TLP on Arch"
git commit -m "docs: update DEVELOPER.md with new examples"
```

**5. Push and PR**:

```bash
git push origin feature/my-new-feature
# Create pull request on GitHub
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added (if applicable)
- [ ] Tested on: Fedora / Arch / Debian (specify)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added to complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## Conclusion

This developer guide provides comprehensive reference material for contributing to auto-penguin-setup. Key takeaways:

1. **Understand the Architecture**: Abstraction layers make cross-distro support possible
2. **Follow Patterns**: Use established templates for new features
3. **Test Thoroughly**: Add tests for all new functionality
4. **Document Well**: Help future contributors understand your code
5. **Respect the Philosophy**: Keep it simple, modular, and configuration-driven

For questions or clarifications, open an issue or discussion on GitHub.

---

**Last Updated**: October 15, 2025  
**Version**: 2.0.0  
**License**: BSD 3-Clause
