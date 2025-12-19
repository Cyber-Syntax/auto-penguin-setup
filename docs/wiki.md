# auto-penguin-setup Wiki

Welcome to the auto-penguin-setup wiki! This guide explains how the core modules work, how configuration is managed, and how package mapping enables seamless cross-distro automation. It’s designed for users who want to understand, customize, or extend their OS setup using this framework.

## Configuration System

Configuration is managed via INI files, typically located in `~/.config/auto-penguin-setup/`.

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
```

---

## Package Mapping Explained

auto-penguin-setup uses `pkgmap.ini` to translate generic package names (used in `packages.ini`) into the correct names or sources for each distribution.

**Mapping Types:**

- **Official:** No prefix, uses the distro’s default repo.
- **AUR:** `AUR:package` (Arch User Repository)
- **COPR:** `COPR:user/repo` (Fedora COPR)

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

### Flatpak Package (All Distros)

**`packages.ini`:**

```
[flatpak]
org.signal.Signal
com.spotify.Client
```

*Result: Installed via Flatpak from Flathub.*
