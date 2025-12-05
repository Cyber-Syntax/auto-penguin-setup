## Configuration System

### XDG Base Directory Compliance

The script follows XDG specifications:

- **Config**: `~/.config/auto-penguin-setup/`
    - `variables.ini`
    - `packages.ini`
    - `pkgmap.ini`
- **State/Logs**: `~/.local/state/auto-penguin-setup/logs/`
- **Cache**: Not used (packages are managed by system PM)

### Configuration Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    First Run                            │
└───────────────┬─────────────────────────────────────────┘
                │
         ┌──────▼──────┐
         │ Config Dir  │
         │   Exists?   │
         └──┬─────┬────┘
            │ No  │ Yes
            │     └─────────────────────────┐
      ┌─────▼──────┐                       │
      │ Prompt User│                       │
      │ to Create  │                       │
      └─────┬──────┘                       │
            │                              │
    ┌───────▼────────┐              ┌──────▼───────┐
    │ Copy Examples  │              │ Load Existing│
    │ Customize User │              │ Configuration│
    └───────┬────────┘              └──────┬───────┘
            │                              │
            └──────────┬───────────────────┘
                       │
                ┌──────▼──────┐
                │ Parse INI   │
                │ Load Arrays │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │Initialize PM│
                │ Load Mappings│
                └──────┬──────┘
                       │
                       ▼
                  Ready for Use
```

### Schema Updates

When the project adds new configuration options, existing users are automatically prompted to update via `update_config_schema()`.

This function:

1. Detects missing keys in user's config
2. Prompts user to add new keys
3. Creates backup before making changes
4. Merges new keys while preserving user values

### Variable Loading

Variables from `variables.ini` are exported as environment variables. The file supports device-specific sections, browser settings, SSH configuration, default applications, and MIME type associations.

Example keys exported:

```bash
# After load_variables()
echo $user                    # Current user
echo $current_device          # Device type (desktop/laptop)
echo $hostname_desktop        # Desktop hostname
echo $hostname_laptop         # Laptop hostname
echo $firefox_profile_path    # Firefox profile path
echo $session_desktop         # Desktop session
echo $session_laptop          # Laptop session
echo $display_manager_desktop # Desktop display manager
echo $display_manager_laptop  # Laptop display manager
echo $enable_service          # SSH service enabled
echo $port                    # SSH port
echo $browser                 # Default browser
```

Device-specific settings are grouped under `[desktop]`, `[laptop]`, etc. SSH device mapping and targets are defined in `[ssh_devices]` and `[ssh_targets]`. Default applications and MIME types are used for mimeapps.list generation.

### Package Array Loading

Package lists are loaded into arrays, grouped by category. Each section in `packages.ini` represents a package group.

```bash
# After load_package_arrays()
echo "${CORE_PACKAGES[@]}"      # Core system packages
echo "${APPS_PACKAGES[@]}"      # Application packages
echo "${DEV_PACKAGES[@]}"       # Development tools
echo "${DESKTOP_PACKAGES[@]}"   # Desktop-specific packages
echo "${LAPTOP_PACKAGES[@]}"    # Laptop-specific packages
echo "${QTILE_PACKAGES[@]}"     # Qtile window manager packages
echo "${I3_PACKAGES[@]}"        # i3 window manager packages
echo "${WM_COMMON_PACKAGES[@]}" # Common window manager packages
echo "${GAMES_PACKAGES[@]}"     # Gaming packages
echo "${FLATPAK_PACKAGES[@]}"   # Flatpak packages
```

**Note:** Comments on the right side of package lines are not supported and will cause errors.

---

# Configuration Architecture (INI)

This document centralizes the configuration design for auto-penguin-setup. The project uses INI files parsed by the project's INI parser (src/core/ini_parser.sh). See `config_examples/` for canonical examples.

## Canonical Files

- `variables.ini` — global variables exported into the environment, including device-specific, browser, SSH, default apps, and MIME types
- `packages.ini` — package lists grouped by category (e.g., [core], [apps], [dev], [desktop], [laptop], [homeserver], [qtile], [i3], [wm-common], [games], [flatpak])
- `pkgmap.ini` — package name mappings per-distro, supporting AUR/COPR prefixes and explicit mapping rules

## Loading Rules

- Config files are looked up in the user's config directory (e.g., ~/.config/auto-penguin-setup/). If missing, examples from `config_examples/` are copied.
- Use the core helper `init_config()` which:
    - ensures config directory exists
    - copies examples if needed
    - loads `variables.ini`, `packages.ini`, and `pkgmap.ini` via the ini parser
    - exports variables and populates arrays
    - supports device-specific, SSH, browser, and MIME type configuration

## INI Parser Usage

The project provides `src/core/ini_parser.sh` with helpers such as `load_ini_config` and `parse_ini`.

Example: load variables and export

```bash
# inside init_config()
load_ini_config "variables.ini" || return 1
parse_ini variables.ini "user"
export USERNAME="$user"
parse_ini variables.ini "current_device"
export CURRENT_DEVICE="$current_device"
parse_ini_section variables.ini desktop
export HOSTNAME_DESKTOP="$hostname"
export SESSION_DESKTOP="$session"
export DISPLAY_MANAGER_DESKTOP="$display_manager"
parse_ini_section variables.ini laptop
export HOSTNAME_LAPTOP="$hostname"
export SESSION_LAPTOP="$session"
export DISPLAY_MANAGER_LAPTOP="$display_manager"
```

Example: load package lists into arrays

```bash
load_ini_config "packages.ini"
mapfile -t CORE_PACKAGES < <(parse_ini_section_lines packages.ini core)
mapfile -t APPS_PACKAGES < <(parse_ini_section_lines packages.ini apps)
mapfile -t DEV_PACKAGES < <(parse_ini_section_lines packages.ini dev)
mapfile -t DESKTOP_PACKAGES < <(parse_ini_section_lines packages.ini desktop)
mapfile -t LAPTOP_PACKAGES < <(parse_ini_section_lines packages.ini laptop)
mapfile -t QTILE_PACKAGES < <(parse_ini_section_lines packages.ini qtile)
mapfile -t I3_PACKAGES < <(parse_ini_section_lines packages.ini i3)
mapfile -t WM_COMMON_PACKAGES < <(parse_ini_section_lines packages.ini wm-common)
mapfile -t GAMES_PACKAGES < <(parse_ini_section_lines packages.ini games)
mapfile -t FLATPAK_PACKAGES < <(parse_ini_section_lines packages.ini flatpak)
```

## Package Mapping

Package name mapping is stored in `pkgmap.ini`. Load it with `load_package_mappings` and use `map_package_name` or `map_package_list` to translate names for the detected distro.

Mappings support:

- Direct mapping: `fd-find=fd` (Arch), `fd-find=fd-find` (Fedora/Debian)
- AUR/COPR prefixes: `qtile-extras=AUR:qtile-extras` (Arch), `qtile-extras=COPR:frostyx/qtile` (Fedora)
- Explicit package names and repository handling
- Comments and warnings for repo status and migration notes

**Note:** The left side of the mapping must match the package name in `packages.ini`.

## Migration Notes

- If you previously used an older configuration format, migrate it to INI sections. Keep examples in `config_examples/` as ground truth.
- Tests and CI that relied on JSON should be updated to read from INI or use the project's parser mocks.
- Comments in example files provide warnings, migration notes, and TODOs for users (e.g., gaming section, repo status).

## Configuration Architecture (INI)

## Configuration Architecture

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                  User Configuration                      │
│         ~/.config/auto-penguin-setup/*.ini             │
│                                                          │
│  ┌────────────────────┐  ┌──────────────────────┐     │
│  │  variables.ini     │  │   packages.ini        │     │
│  │                    │  │                        │     │
│  │ • user             │  │ • core[]               │     │
│  │ • current_device   │  │ • apps[]               │     │
│  │ • desktop {}       │  │ • dev[]                │     │
│  │ • laptop {}        │  │ • desktop[]            │     │
│  │ • browser {}       │  │ • laptop[]             │     │
│  │ • ssh {}           │  │ • homeserver[]         │     │
│  │ • ssh_devices {}   │  │ • qtile[]              │     │
│  │ • ssh_targets {}   │  │ • i3[]                 │     │
│  │ • default_apps {}  │  │ • wm-common[]          │     │
│  │ • mime_* {}        │  │ • games[]              │     │
│  │                    │  │ • flatpak[]            │     │
│  └────────────────────┘  └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Configuration Loading Layer                 │
│                                                          │
│  1. load_ini_config() - Find config files               │
│  2. parse_ini() - Extract values with the project's INI parser (src/core/ini_parser.sh) │
│  3. load_variables() - Set environment variables        │
│  4. load_package_arrays() - Populate package lists      │
│  5. load_package_mappings() - Map package names for current distro │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                Runtime Environment                       │
│                                                          │
│  • Environment Variables: $user, $current_device, $hostname_desktop, $hostname_laptop, $firefox_profile_path, $session_desktop, $session_laptop, $display_manager_desktop, $display_manager_laptop, $enable_service, $port, $browser │
│  • Bash Arrays: CORE_PACKAGES[@], APPS_PACKAGES[@], DEV_PACKAGES[@], DESKTOP_PACKAGES[@], LAPTOP_PACKAGES[@], QTILE_PACKAGES[@], I3_PACKAGES[@], WM_COMMON_PACKAGES[@], GAMES_PACKAGES[@], FLATPAK_PACKAGES[@] │
│  • Global Constants: CURRENT_DISTRO, PM_INSTALL         │
└─────────────────────────────────────────────────────────┘
```

### Configuration File Design

#### Why INI?

1. **Human-Readable**: Simple key/value pairs and sections are easy to edit
2. **Simple Structure**: Well-suited for lists and mappings used by this project
3. **No External Dependency**: Uses the bundled `ini_parser.sh` rather than requiring `jq`
4. **Version Control Friendly**: Plain text, clear diffs

#### Schema Design Principles

1. **Sections for Related Data**:

```ini
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

Better than flattened keys because related values are grouped under a section.

2. **Lists as section entries**:

```ini
[core]
curl
wget
ufw
trash-cli
syncthing
borgbackup
backintime
flatpak
jq
```

3. **Explicit Mappings and Repository Prefixes**:

Mappings are defined per-distro, with support for AUR/COPR prefixes:

```ini
[pkgmap.arch]
fd-find=fd
qtile-extras=AUR:qtile-extras

[pkgmap.fedora]
fd-find=fd-find
qtile-extras=COPR:frostyx/qtile

[pkgmap.debian]
fd-find=fd-find
```

**Note:** The left side of the mapping must match the package name in `packages.ini`.

### Configuration Migration Strategy

When the schema evolves, `update_config_schema()` handles migration:

```bash
update_config_schema() {
  # 1. Detect schema version differences
  # 2. Prompt user with clear explanation
  # 3. Create backup
  # 4. Merge: new keys from example + user values
  # 5. Validate result
}
```

**Migration Types Supported**:

1. **Adding New Keys**: Merge with defaults
2. **Renaming Keys**: Manual mapping in migration code
3. **Restructuring** (flat → nested): Special handling
4. **Removing Keys**: Keep in user config (no harm)

**Warnings and TODOs:** Example files include comments for migration notes, repo status, and unsupported features (e.g., right-side comments in packages.ini, gaming repo handling).

---

This file centralizes the configuration format and loading strategy used by auto-penguin-setup.

Files: `~/.config/auto-penguin-setup/variables.ini`, `packages.ini`, `pkgmap.ini`

Parser: `src/core/ini_parser.sh` — a small INI parsing helper used throughout the project.

Design highlights:

- Use sections for related data (e.g. `[desktop]`, `[laptop]`, `[system]`, `[browser]`, `[ssh]`, `[ssh_devices]`, `[ssh_targets]`, `[default_applications]`, `[mime_*]`).
- Lists are represented as one entry per line inside a section (see `packages.ini`).
- Mappings use per-distro sections (`[pkgmap.fedora]`, `[pkgmap.arch]`, `[pkgmap.debian]`), with support for AUR/COPR prefixes and explicit mapping rules.
- All configuration-loading helpers live in `src/core/config.sh` and call into the INI parser.

Examples

variables.ini

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

[browser]
firefox_profile=sqwu9kep.default-release
firefox_profile_path=/home/developer/.mozilla/firefox/sqwu9kep.default-release
librewolf_dir=/home/developer/.librewolf/
librewolf_profile=/home/developer/.librewolf/profiles.ini

[ssh]
enable_service=true
port=22
password_auth=no
permit_root_login=no
key_auth=yes

[ssh_devices]
desktop=developer@192.168.1.100:22
laptop=developer@192.168.1.101:22

[ssh_targets]
desktop=laptop
laptop=desktop

[default_applications]
browser=brave
terminal=alacritty
file_manager=pcmanfm
image_viewer=feh
text_editor=nvim

[mime_browser]
text/html
application/xhtml+xml
image/jpeg
image/png
x-scheme-handler/http
x-scheme-handler/https

[mime_image_viewer]
image/jpeg
image/png
image/webp

[mime_text_editor]
text/plain
application/x-shellscript

[mime_file_manager]
inode/directory

[mime_terminal]
```

packages.ini

```ini
[core]
curl
wget
ufw
trash-cli
syncthing
borgbackup
backintime
flatpak
jq

[apps]
seahorse
xournalpp
alacritty
keepassxc
neovim
vim
pavucontrol
chromium

[dev]
s-tui
starship
papirus-icon-theme
git-credential-libsecret
gh
ruff
lm_sensors
htop
btop
pip
zoxide
fzf
bat
eza
fd-find
zsh-autosuggestions
zsh-syntax-highlighting
zsh
luarocks
cargo
yarnpkg
bash-language-server
python3-devel
dbus-devel
shfmt
shellcheck
lazygit

[desktop]
virt-manager
libvirt
lightdm
lightdm-gtk-greeter
sysbench
ckb-next
solaar

[laptop]
brightnessctl
powertop
thinkfan
acpi
tlp
auto-cpufreq

[homeserver]
fail2ban

[qtile]
python3-dbus-fast
python-xlib
qtile-extras

[i3]
polybar
i3

[wm-common]
i3lock
rofi
lxappearance
gammastep
numlockx
dunst
flameshot
playerctl
xev
xset
feh
picom
xautolock
pcmanfm

[games]
wine

[flatpak]
org.signal.Signal
io.github.martchus.syncthingtray
com.tutanota.Tutanota
dev.zed.Zed
md.obsidian.Obsidian
com.spotify.Client
```

pkgmap.ini

```ini
[pkgmap.arch]
python3-dbus-fast=python-dbus-fast
gh=github-cli
fd-find=fd
pip=python-pip
python3-devel=python
dbus-devel=dbus
qtile-extras=AUR:qtile-extras
lazygit=AUR:lazygit
yarnpkg=yarn
git-credential-libsecret=libsecret
xset=xorg-xset
xev=xorg-xev
xautolock=AUR:xautolock
thinkfan=AUR:thinkfan

[pkgmap.fedora]
qtile-extras=COPR:frostyx/qtile
lazygit=COPR:dejan/lazygit
shellcheck=ShellCheck
starship=COPR:atim/starship

[pkgmap.debian]
git-credential-libsecret=libsecret-1-0
pip=python3-pip
python3-devel=python3
dbus-devel=dbus
xset=x11-xserver-utils
xev=x11-utils
```

Usage

- `init_config()` locates the user's INI files (looks under XDG config dir, falls back to `config_examples/`) and calls `ini_parser` helpers to populate environment variables and arrays used by other modules.
- If a file is missing, the project provides defaults in `config_examples/` which are copied on first-run or by the `create_config` helpers.

Migration

- Config evolution is handled by `update_config_schema()` which merges new keys from the example INI into the user's file while preserving values and backing up the original.

Reference: `src/core/ini_parser.sh`, `src/core/config.sh`
