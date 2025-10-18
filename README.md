> [!CAUTION]
>
> - This project is still under active development and not all features are fully tested.
> - **IMPORTANT:** I am not responsible for any damage caused by this script. Use at your own risk.
> - **WARNING:** Follow the instructions in the **Releases section** when updating the script.
> - **OS:** Linux distributions only (Fedora, Arch Linux, Debian/Ubuntu).

# auto-penguin-setup 🐧

> [!NOTE]
> Command-line tool to automate installation and configuration of packages, services, and system settings for multiple Linux distributions. This project is focused to be automated setup to make it much easier to set up a new Linux system.

- Optimizes package manager for faster downloads
- Install packages from config file with cross-distro mappings
- Configures hardware-specific features (TLP, NVIDIA, etc.)
- Manages system services and configurations

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

### 2. Configure Your System

Edit configuration files according to your needs:

1. Modify `configs/` according to your preferences.
2. Edit other config files in `~/.config/auto-penguin-setup/` as needed.

### 3. Run the Script

```bash
# Run without sudo, it will handle sudo internally
./setup.sh -h  # Show all options
```
