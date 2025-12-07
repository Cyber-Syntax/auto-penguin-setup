> [!CAUTION]
>
> - This project is still under active development and not all features are fully tested.
> - **IMPORTANT:** I am not responsible for any damage caused by this script. Use at your own risk.
> - **WARNING:** Follow the instructions in the **Releases section** when updating the script.
> - **OS:** Linux distributions only (Fedora, Arch Linux, Debian/Ubuntu).

# auto-penguin-setup 🐧

> [!NOTE]
> **Fully Python-based** command-line tool to automate installation and configuration of packages, services, and system settings for multiple Linux distributions. This project provides an automated setup to make it much easier to set up a new Linux system.

- Optimizes package manager for faster downloads
- Install packages from config file with cross-distro mappings
- Configures hardware-specific features (TLP, NVIDIA, etc.)
- Manages system services and configurations
- **100% Python implementation** - No bash dependencies

## 🎯 Features

### Cross-Distribution Support

- **Automatic Detection**: Detects your distribution and adapts package manager commands
- **Unified Interface**: Same commands work on Fedora (dnf), Arch (pacman/paru), and Debian (apt)
- **Smart Mapping**: Automatically maps package names that differ across distributions
- **Repository Management**: Supports COPR (Fedora), AUR (Arch), and PPA (Debian)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Cyber-Syntax/auto-penguin-setup.git
cd auto-penguin-setup
```

### 2. Install the Python CLI

```bash
# Create virtual environment (recommended)
uv venv
source .venv/bin/activate  # On Linux/Mac

# Install in development mode
uv pip install -e .

# Or with pip
pip install -e .
```

### 3. Configure Your System

Copy example configuration files to your user config directory:

```bash
mkdir -p ~/.config/auto-penguin-setup
cp config_examples/* ~/.config/auto-penguin-setup/
```

Edit the configuration files according to your needs:

- `packages.ini`: Define package categories and lists
- `pkgmap.ini`: Map package names across distributions and specify repositories
- `variables.ini`: Set environment variables for the setup process

### 4. Use the CLI

```bash
# Show help
aps --help

# Run system setup
aps setup

# Install packages
aps install curl wget
```

> [!NOTE]
> All functionality has been migrated to the Python-based `aps` CLI tool. Legacy bash scripts have been removed.

## ⚙️ Configuration

auto-penguin-setup uses INI-based configuration files stored in `~/.config/auto-penguin-setup/`.

### packages.ini

Defines package categories for organized installation:

```ini
[core]
curl
wget
ufw

[apps]
chromium
keepassxc

[dev]
git
python3
```

Available categories include `@core`, `@apps`, `@dev`, `@flatpak`, and custom categories you define.

### pkgmap.ini

Maps package names across distributions and specifies repositories:

```ini
[packages]
fd-find = fd  # Fedora name -> Arch name

[repos]
fd = AUR:fd  # Install fd from AUR on Arch
```

Supports `official`, `COPR:user/repo`, `AUR:package`, `PPA:user/repo`, and `flatpak:remote` sources.

### variables.ini

Environment variables for setup scripts:

```ini
[vars]
OLLAMA_GPU = nvidia
```

## 🐍 Python CLI

The `aps` (Auto Penguin Setup) command-line tool provides a modern, Python-based interface for all system configuration and package management operations.

### Installation

Installation is covered in the Quick Start section above. Here's a quick reference:

```bash
# Create virtual environment (recommended)
uv venv
source .venv/bin/activate

# Install
uv pip install -e .
```

### Usage Examples

```bash
# Show help
aps --help

# Install packages
aps install curl wget

# Install package categories
aps install @core @apps @dev

# Dry-run to preview changes
aps install @core --dry-run

# List tracked packages
aps list

# List packages by source
aps list --source aur

# Remove packages
aps remove curl

# Show system status
aps status

# Setup system components
aps setup aur-helper  # Install paru AUR helper (Arch only)
aps setup ollama      # Install/update Ollama AI runtime

# Sync repository changes (migrate packages when sources change)
aps sync-repos        # Interactive - prompts for confirmation
aps sync-repos --auto # Automatic - no prompts
```

### Features

- **Fast**: Built with Python and orjson for 5-10x faster performance
- **Safe**: Dry-run mode for all operations
- **Cross-platform**: Works on Fedora, Arch, and Debian/Ubuntu
- **Modern**: Type-safe with comprehensive test coverage (>90%)
- **Setup Tools**: Automated installation of system components, applications, and hardware configurations
- **Repository Migration**: Automatically detect and migrate packages when COPR/AUR/PPA sources change
- **Package Tracking**: Maintains detailed records of installed packages and their sources
- **100% Python**: Fully migrated from bash - easier to maintain and extend

## 🏗️ How It Works

auto-penguin-setup abstracts package management across Linux distributions through a layered architecture:

### Core Components

- **Distribution Detection**: Automatically identifies Fedora, Arch, or Debian/Ubuntu
- **Package Mapping**: Translates package names using `pkgmap.ini` (e.g., `fd-find` → `fd`)
- **Repository Management**: Handles COPR, AUR, PPA, and Flatpak sources
- **Package Tracking**: Records installations in `~/.local/share/auto-penguin-setup/package_tracking.ini`

### Data Flow

1. Parse configuration files (`packages.ini`, `pkgmap.ini`)
2. Map package names to distribution-specific equivalents
3. Execute package manager commands (dnf/pacman/apt/flatpak)
4. Track successful installations with source metadata

### Key Directories

- **Configuration**: `~/.config/auto-penguin-setup/` (packages.ini, pkgmap.ini, variables.ini)
- **Tracking Database**: `~/.local/share/auto-penguin-setup/package_tracking.ini`
- **Logs**: `~/.local/state/auto-penguin-setup/logs/auto-penguin-setup.log`
- **System Configs**: `configs/` (hardware-specific configurations like TLP, NVIDIA)
