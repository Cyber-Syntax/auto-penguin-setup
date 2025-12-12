> [!CAUTION]
>
> - This project is still under active development and not all features are fully tested.
> - **IMPORTANT:** I am not responsible for any damage caused by this script. Use at your own risk.
> - **WARNING:** Follow the instructions in the **Releases section** when updating the script.
> - **OS:** Linux distributions only (Fedora, Arch Linux, Debian/Ubuntu).

# auto-penguin-setup 🐧

> [!NOTE]
> Command-line tool to automate installation and configuration of packages, services, and system settings for multiple Linux distributions. This project provides an automated setup to make it much easier to set up a new Linux system.

- Optimizes package manager for faster downloads
- Install packages from config file with cross-distro mappings
- Configures hardware-specific features (TLP, NVIDIA, etc.)
- Manages system services and configurations
- Tracks installed packages and their sources

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

### 2. Installation

The easiest way to install `aps` is using the included setup script:

```bash
./setup.sh install
```

This will:

1. Install UV if not already present
2. Install the `aps` CLI tool using `uv tool install .`
3. Setup shell autocomplete for bash and zsh

#### Alternative: Manual installation with UV

If you prefer to install manually:

```bash
# Install UV if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install aps tool
uv tool install .

# Setup autocomplete (optional)
./setup.sh autocomplete
```

#### For development/testing

```bash
# Run without installation
uv run aps --help
```

### 3. Verify Installation

```bash
aps --version
aps --help
aps install --help
aps setup --help
```

### 4. Updating

To update to the latest version:

```bash
./setup.sh update
```

Or manually:

```bash
uv tool install . --force
```

### 5. Uninstallation

```bash
uv tool uninstall auto-penguin-setup
```

Note: This will remove the CLI tool but preserve your configuration files and autocomplete setup.

### 3. Configure Your System

Edit the configuration files according to your needs:

- `packages.ini`: Define package categories and lists
- `pkgmap.ini`: Map package names across distributions and specify repositories
- `variables.ini`: Set environment variables for the setup process

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
[system]
# Change this to your username
user=developer
# Which device this configuration is for (desktop/laptop/homeserver/etc.)
# This used for ssh target selection
current_device=desktop

# Device-specific settings
[desktop]
hostname=arch

[laptop]
hostname=arch-laptop

[ssh]
# Service configuration
enable_service=true         # Enable SSH server on this device
port=22                     # SSH port (default: 22)
```
