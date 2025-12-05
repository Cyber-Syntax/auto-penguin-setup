## System Overview

### How Everything Fits Together

```
┌─────────────────────────────────────────────────────────────┐
│                        setup.sh                              │
│                   (Main Entry Point)                         │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├─► Detects Distribution (distro_detection.sh)
                │   └─► Sets: CURRENT_DISTRO
                │
                ├─► Initializes Configuration (config.sh)
                │   ├─► Loads variables.ini (via ini_parser)
                │   └─► Loads packages.ini (via ini_parser)
                │
                ├─► Initializes Package Manager (package_manager.sh)
                │   └─► Sets: PM_INSTALL, PM_REMOVE, PM_UPDATE
                │
                └─► Executes Requested Functions
                    ├─► Apps Installation (apps.sh)
                    ├─► Desktop Configuration (desktop.sh)
                    ├─► Laptop Configuration (laptop.sh)
                    └─► General System Config (general.sh)
```

## Module Overview

### Core Modules

#### 1. **logging.sh** - Logging System

**Purpose**: Centralized logging with multiple severity levels

**Features**:

- File logging to `~/.local/state/auto-penguin-setup/logs/`
- Console output with color coding
- Log rotation (3MB max, 3 backups)
- XDG Base Directory compliant

**Functions**:

- `log_debug()` - Debug information
- `log_info()` - General information
- `log_warn()` - Warnings
- `log_error()` - Errors
- `log_success()` - Success messages

**Example**:

```bash
log_info "Installing packages..."
log_error "Failed to install vim"
log_success "Installation completed"
```

#### 2. **distro_detection.sh** - Distribution Detection

**Purpose**: Detect and validate the current Linux distribution

**Functions**:

- `detect_distro()` - Returns: fedora, arch, or debian
- `get_distro_version()` - Returns version string
- `get_distro_pretty_name()` - Returns human-readable name
- `is_fedora()`, `is_arch()`, `is_debian()` - Boolean checks

**Example**:

```bash
DISTRO=$(detect_distro)
if is_fedora; then
    echo "Running on Fedora"
fi
```

#### 3. **package_manager.sh** - Package Manager Abstraction

**Purpose**: Unified interface for package operations across distributions

**Functions**:

- `init_package_manager()` - Initialize for current distro
- `pm_install <packages>` - Install packages
- `pm_remove <packages>` - Remove packages
- `pm_update()` - Update system
- `pm_is_installed <package>` - Check if installed
- `pm_search <query>` - Search for packages

**How it works**:

```bash
# Initialize once at startup
init_package_manager

# Use anywhere in the script
pm_install vim neovim htop
pm_remove nano
pm_update
```

**Behind the scenes**:

- Fedora: `sudo dnf install -y vim neovim htop`
- Arch: `sudo pacman -S --noconfirm vim neovim htop`
- Debian: `sudo apt-get install -y vim neovim htop`

#### 4. **package_mapping.sh** - Package Name Translation

**Purpose**: Translate package names that differ across distributions

**Functions**:

- `load_package_mappings()` - Load mappings from `pkgmap.ini` (INI)
- `map_package_name <name> [distro]` - Map single package
- `map_package_list <distro> <packages...>` - Map multiple packages
- `get_device_packages <type> <config>` - Get device-specific packages
- `get_common_packages <category> <config>` - Get common packages

**Example**:

```bash
# Load mappings
load_package_mappings "$PACKAGES_FILE"

# Map a package name
MAPPED=$(map_package_name "python3-devel")
# Returns: "python3-devel" on Fedora
#          "python" on Arch
#          "python3-dev" on Debian
```

#### 5. **repository_manager.sh** - Repository Management

**Purpose**: Abstract repository operations (COPR, AUR, PPA)

**Functions**:

- `repo_add <identifier>` - Add repository
- `repo_enable <name>` - Enable repository
- `repo_disable <name>` - Disable repository
- `repo_update()` - Update repository metadata
- `enable_rpm_fusion_distro_agnostic()` - Enable extra repos

**Example**:

```bash
# Fedora COPR
repo_add "atim/lazygit"

# Arch AUR (via helper)
repo_add "brave-bin"

# Debian PPA
repo_add "ppa:neovim-ppa/unstable"
```

#### 6. **config.sh** - Configuration Management

**Purpose**: Load and manage INI configuration files

**Key Functions**:

- `check_and_create_config()` - Interactive config setup
- `load_ini_config <filename>` - Load config file
- `load_variables()` - Load variables into environment (from INI)
- `load_package_arrays()` - Load package lists (from INI)
- `parse_ini <file> <filter>` - Parse INI with ini_parser
- `init_config()` - Initialize all configuration

**Configuration Files**:

**variables.ini** structure:

```ini
[system]
user = username

[laptop]
host = laptop-hostname
ip = 192.168.1.54
session = hyprland
display_manager = sddm

[desktop]
host = desktop-hostname
ip = 192.168.1.100
session = qtile
display_manager = sddm

[browser]
firefox_profile = profile-name
firefox_profile_path = /path/to/profile
```

**packages.ini** structure:

```ini
[core]
curl
wget

[apps]
kitty
neovim

[desktop]
nvidia-open
virt-manager

[laptop]
tlp
thinkfan

[pkgmap.fedora]
# mappings section follows: key = distro-specific-name
```

    "package-name": {
      "fedora": "fedora-name",
      "arch": "arch-name",
      "debian": "debian-name"
    }

}
}

````

### Feature Modules

#### 7. **apps.sh** - Third-Party Application Installation

**Purpose**: Install applications requiring custom repositories

**Functions**:

- `install_lazygit()` - Terminal UI for git
- `install_brave()` - Brave Browser
- `install_vscode()` - Visual Studio Code
- `install_protonvpn()` - ProtonVPN
- `install_auto_cpufreq()` - CPU frequency optimizer
- `disable_keyring_for_brave()` - Configure Brave desktop file

**Cross-Distro Implementation**:
Each function contains distribution-specific logic:

```bash
install_brave() {
  case "$CURRENT_DISTRO" in
    fedora)
      # Add RPM repository and install
      ;;
    arch)
      # Install from AUR
      ;;
    debian)
      # Add DEB repository and install
      ;;
  esac
}
````

#### 8. **desktop.sh** - Desktop-Specific Configurations

**Purpose**: Functions for desktop/gaming systems

**Functions**:

- `install_ollama()` - AI model manager
- `nfancurve_setup()` - NVIDIA fan curve control
- `borgbackup_setup()` - Backup automation
- `gdm_auto_login()` - GDM autologin configuration
- `zenpower_setup()` - AMD Ryzen monitoring
- `nvidia_cuda_setup()` - CUDA toolkit installation
- `switch_nvidia_open()` - Switch to NVIDIA open drivers
- `vaapi_setup()` - VA-API for hardware acceleration
- `remove_gnome()` - Remove GNOME (keeps NetworkManager)
- `trash_cli_setup()` - Automated trash cleanup

#### 9. **laptop.sh** - Laptop-Specific Configurations

**Purpose**: Power management and laptop hardware

**Functions**:

- `laptop_hostname_change()` - Set laptop hostname
- `tlp_setup()` - Advanced power management
- `thinkfan_setup()` - ThinkPad fan control
- `xorg_setup_intel()` - Intel graphics configuration
- `setup_qtile_backlight_rules()` - Brightness control for Qtile
- `touchpad_setup()` - Touchpad gesture configuration
- `ssh_setup_laptop()` - SSH key deployment

**TLP Setup Details**:

- Disables conflicting services (TuneD, power-profiles-daemon)
- Configures battery charge thresholds
- Enables TLP radio device handling
- Masks systemd-rfkill to let TLP handle radios

#### 10. **general.sh** - General System Configuration

**Purpose**: Universal system optimizations and configurations

**Key Functions**:

- `speed_up_package_manager()` - Optimize PM (dnf/pacman/apt)
- `grub_timeout()` - Set boot timeout to 0
- `sudoers_setup()` - Configure sudo timeout and permissions
- `tcp_bbr_setup()` - Enable TCP BBR congestion control
- `switch_ufw_setup()` - Switch to UFW from firewalld
- `ffmpeg_swap()` - Replace ffmpeg-free with full ffmpeg
- `enable_rpm_fusion()` - Enable additional repositories
- `switch_lightdm()` - Switch to LightDM display manager
- `lightdm_autologin()` - Configure LightDM autologin
- `syncthing_setup()` - Enable Syncthing service
- `virt_manager_setup()` - Virtualization setup
- `setup_default_applications()` - Configure MIME associations

#### 11. **display_manager.sh** - Display Manager Configuration

**Purpose**: Manage display manager settings (SDDM, GDM, LightDM)

**Functions**:

- `sddm_autologin()` - Configure SDDM autologin with session detection

**Session Detection**:
The function intelligently selects the desktop session based on hostname:

```bash
# Desktop: uses desktop_session from variables.ini
# Laptop: uses laptop_session from variables.ini
# Unknown: defaults to qtile
```

---

## Abstraction Layers

### Layer 1: Distribution Detection

**Purpose**: Abstract "What distro am I running on?"

**Interface**:

```bash
detect_distro() → "fedora" | "arch" | "debian"
is_fedora() → 0 | 1
get_distro_version() → "41" | "rolling" | "12"
```

```bash
detect_distro() {
  source /etc/os-release

  case "${ID,,}" in
    fedora) echo "fedora" ;;
    arch|archlinux) echo "arch" ;;
    debian|ubuntu|linuxmint|pop) echo "debian" ;;
    *) log_error "Unsupported distribution: $ID"; return 1 ;;
  esac
}
```

**Implementation**:

- Reads `/etc/os-release`
- Normalizes distribution IDs
- Maps derivatives to base (Ubuntu → debian)

### Layer 2: Package Manager Abstraction

**Purpose**: Abstract "How do I install a package?"

**Interface**:

```bash
init_package_manager()           # Setup
pm_install <packages>            # Install
pm_remove <packages>             # Remove
pm_update()                      # Update system
pm_is_installed <package>        # Check
```

**Implementation**:

```bash
# State stored in global variables
PM_INSTALL=""     # e.g., "dnf install -y"
PM_REMOVE=""      # e.g., "pacman -Rns --noconfirm"
PM_UPDATE=""      # e.g., "apt-get update && apt-get upgrade -y"
PM_SUDO=""        # e.g., "sudo" or "" (for AUR helpers)
```

**Why Global Variables?**

- Simple: No need to pass state through function chains
- Efficient: Set once, use everywhere
- Clear: Named clearly with PM\_ prefix

### Layer 3: Package Name Mapping

**Purpose**: Abstract "What is this package called on this distro?"

**Data Structure**:

```bash
# Associative array in memory
PACKAGE_MAPPINGS["package:fedora"]="fedora-name"
PACKAGE_MAPPINGS["package:arch"]="arch-name"
PACKAGE_MAPPINGS["package:debian"]="debian-name"
```

**Interface**:

```bash
load_package_mappings <config>   # Load from INI via ini_parser
map_package_name <name> [distro] # Translate name
map_package_list <distro> <pkgs> # Translate list
```

**Algorithm**:

```
1. Check if mapping exists for (package, distro)
2. If yes: return mapped name
3. If no: return original name (assume same across distros)
```

### Layer 4: Repository Management

**Purpose**: Abstract "How do I enable additional repos?"

**Interface**:

```bash
repo_add <identifier>           # Add repo
repo_enable <name>              # Enable
repo_disable <name>             # Disable
enable_rpm_fusion_distro_agnostic()  # Enable extra repos
```

**Implementation Strategy**:

```bash
repo_add() {
  case "$CURRENT_DISTRO" in
    fedora)
      # Format: user/repo
      sudo dnf copr enable -y "$1"
      ;;
    arch)
      # Format: package-name (AUR)
      paru -S --noconfirm "$1"
      ;;
    debian)
      # Format: ppa:user/repo
      sudo add-apt-repository -y "$1"
      sudo apt-get update
      ;;
  esac
}
```

---
