# auto-penguin-setup Wiki

Welcome to the auto-penguin-setup wiki! This guide explains how the core modules work, how configuration is managed, and how package mapping enables seamless cross-distro automation. It’s designed for users who want to understand, customize, or extend their OS setup using this framework.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Modules Overview](#core-modules-overview)
3. [Configuration System](#configuration-system)
4. [Package Mapping Explained](#package-mapping-explained)
5. [Practical Configuration Examples](#practical-configuration-examples)
6. [Setup Flow: How It All Works](#setup-flow-how-it-all-works)
7. [Troubleshooting & Tips](#troubleshooting--tips)
8. [Glossary & Reference](#glossary--reference)

---

## Introduction

**auto-penguin-setup** is a cross-distribution Bash framework for automating OS setup and package/configuration provisioning across Fedora, Arch, and Debian/Ubuntu families.

**Supported Distributions:**

- Fedora (dnf + COPR)
- Arch (pacman + AUR)
- Debian/Ubuntu (apt + PPA)
- Flatpak (all distros)

**Philosophy:**

- Simple, modular, and maintainable
- Distribution-agnostic abstractions
- INI-based configuration for clarity and portability

---

## Core Modules Overview

Each core module has a single responsibility and is loaded in a strict order for reliability.

### 1. `logging.sh`

Initializes file-backed logging, log rotation, and provides helpers (`log_info`, `log_error`, etc.).

### 2. `distro_detection.sh`

Detects the current Linux distribution and provides predicates (`is_fedora`, `is_arch`, `is_debian`).

### 3. `ini_parser.sh`

Pure Bash INI parser for reading configuration files (`variables.ini`, `packages.ini`, `pkgmap.ini`).

### 4. `config.sh`

Discovers, loads, and customizes configuration files. Exports package arrays and environment variables.

### 5. `package_mapping.sh`

Loads `pkgmap.ini` and translates generic package keys into distro/provider-specific tokens (supports `COPR:`, `AUR:`, `PPA:` prefixes).

### 6. `package_manager.sh`

Provides a distribution-agnostic wrapper for package management (`pm_install`, `pm_remove`, etc.) and provider flows (COPR, AUR, PPA).

### 7. `repository_manager.sh`

Cross-distro repository helpers for adding/enabling/disabling COPR, AUR, PPA, and refreshing metadata.

### 8. `install_packages.sh`

High-level installers that map package keys and delegate installation (core/apps/dev/games/system-specific, Flatpak support).

### 9. `package_tracking.sh` & `repo_migration.sh`

Tracks installed packages and handles repository migration if mappings change.

### 10. `constants.sh`

Defines constants and default directories (future use).

---

## Configuration System

Configuration is managed via INI files, typically located in `~/.config/auto-penguin-setup/`. Example configs are provided in `config_examples/`.

### Main Config Files

#### 1. `variables.ini`

Defines system, device, browser, SSH, and application settings.

**Example:**

```ini
[system]
user=developer
current_device=desktop

[desktop]
hostname=fedora
ip=192.168.1.100
session=qtile
display_manager=sddm

[laptop]
hostname=fedora-laptop
ip=192.168.1.101
session=qtile
display_manager=sddm
```

#### 2. `packages.ini`

Lists packages to install, grouped by category.

**Example:**

```ini
[core]
curl
wget
ufw

[apps]
seahorse
xournalpp
alacritty
```

#### 3. `pkgmap.ini`

Maps generic package names to distro-specific names or providers (AUR, COPR, PPA).

**Example:**

```ini
[pkgmap.arch]
qtile-extras=AUR:qtile-extras
gh=github-cli

[pkgmap.fedora]
qtile-extras=COPR:frostyx/qtile
gh=gh

[pkgmap.debian]
gh=gh
```

---

## Package Mapping Explained

auto-penguin-setup uses `pkgmap.ini` to translate generic package names (used in `packages.ini`) into the correct names or sources for each distribution.

**Mapping Types:**

- **Official:** No prefix, uses the distro’s default repo.
- **AUR:** `AUR:package` (Arch User Repository)
- **COPR:** `COPR:user/repo` (Fedora COPR)
- **PPA:** `PPA:user/repo` (Debian/Ubuntu PPA)

**How It Works:**

- When installing, the system checks `pkgmap.ini` for a mapping.
- If a prefix is present, it enables the repo/provider and installs accordingly.
- If no mapping is found, the generic name is used.

---

## Practical Configuration Examples

Here are real-world examples for each mapping type:

### Official Package (All Distros)

**`packages.ini`:**

```INI
[core]
curl
wget
ufw
```

**`pkgmap.ini`:**

```INI
[pkgmap.arch]
curl=curl

[pkgmap.fedora]
curl=curl

[pkgmap.debian]
curl=curl
```

### AUR Package (Arch)

**`packages.ini`:**

```INI
[qtile]
qtile-extras
```

**`pkgmap.ini`:**

```INI
[pkgmap.arch]
qtile-extras=AUR:qtile-extras
```

*Result: Installed via AUR helper (paru/yay).*

### COPR Package (Fedora)

**`packages.ini`:**

```
qtile-extras
```

**`pkgmap.ini`:**

```
[pkgmap.fedora]
qtile-extras=COPR:frostyx/qtile
```

*Result: COPR repo enabled, package installed via dnf.*

### PPA Package (Debian/Ubuntu)

**`packages.ini`:**

```
some-ppa-package
```

**`pkgmap.ini`:**

```
[pkgmap.debian]
some-ppa-package=PPA:user/repo
```

*Result: PPA added, package installed via apt.*

### Flatpak Package (All Distros)

**`packages.ini`:**

```
[flatpak]
org.signal.Signal
com.spotify.Client
```

*Result: Installed via Flatpak from Flathub.*

---

## Setup Flow: How It All Works

1. **Initialize Logging:**  
   `logging.sh` sets up logs for all actions.

2. **Detect Distribution:**  
   `distro_detection.sh` identifies your OS.

3. **Load Configuration:**  
   `config.sh` finds and loads your INI files, customizing them if needed.

4. **Load Package Mappings:**  
   `package_mapping.sh` reads `pkgmap.ini` and prepares mapping metadata.

5. **Install Packages:**  
   High-level installers (`install_packages.sh`) use mapped names and provider flows to install everything, abstracting away distro differences.

6. **Repository Management:**  
   `repository_manager.sh` enables or disables COPR, AUR, or PPA as needed.

7. **Tracking & Migration:**  
   `package_tracking.sh` records installed packages; `repo_migration.sh` helps migrate if mappings change.

---

## Troubleshooting & Tips

- **Missing Configs?**  
  The system will prompt to copy example configs if your files are missing.
- **Updating Configs:**  
  Use the update script to merge new keys/settings from example configs.
- **Logs:**  
  Find logs in `~/.local/state/auto-penguin-setup/logs/` for debugging.
- **Common Issues:**  
    - Right-side comments in INI files are not supported.
    - Ensure package names in `packages.ini` match those in `pkgmap.ini`.

---

## Glossary & Reference

**Key Terms:**

- **COPR:** Fedora’s third-party repo system.
- **AUR:** Arch User Repository.
- **PPA:** Personal Package Archive (Debian/Ubuntu).
- **Flatpak:** Universal Linux app packaging.

**Abstraction Functions:**

- `pm_install <package>` — Install package (any distro)
- `pm_remove <package>` — Remove package
- `pm_update` — Update package database
- `repo_add <repo>` — Add repository (COPR/AUR/PPA)
- `map_package <generic_name>` — Get distro-specific package name

---

**For more details, see the example configs in `config_examples/` and the source code in `src/core/`.**

Happy hacking!
