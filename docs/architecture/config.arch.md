## Configuration System

### XDG Base Directory Compliance

The script follows XDG specifications:

- **Config**: `~/.config/auto-penguin-setup/`
    - `variables.json`
    - `packages.json`
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
                │ Parse JSON  │
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

Variables from `variables.json` are exported as environment variables:

```bash
# After load_variables()
echo $user                    # Current user
echo $hostname_desktop        # Desktop hostname
echo $laptop_session          # Laptop desktop session
echo $firefox_profile_path    # Firefox profile path
```

### Package Array Loading

Package lists are loaded into arrays:

```bash
# After load_package_arrays()
echo "${CORE_PACKAGES[@]}"      # Core system packages
echo "${APPS_PACKAGES[@]}"      # Application packages
echo "${DESKTOP_PACKAGES[@]}"   # Desktop-specific packages
echo "${LAPTOP_PACKAGES[@]}"    # Laptop-specific packages
```

---

# Configuration Architecture (INI)

This document centralizes the configuration design for auto-penguin-setup. The project uses INI files parsed by the project's INI parser (src/core/ini_parser.sh). See `config_examples/` for canonical examples.

## Canonical Files

- `variables.ini` — global variables exported into the environment
- `packages.ini` — package lists grouped by category (e.g., [core], [desktop])
- `pkgmap.ini` — package name mappings per-distro

## Loading Rules

- Config files are looked up in the user's config directory (e.g., ~/.config/auto-penguin-setup/). If missing, examples from `config_examples/` are copied.
- Use the core helper `init_config()` which:
    - ensures config directory exists
    - copies examples if needed
    - loads `variables.ini` and `packages.ini` via the ini parser
    - exports variables and populates arrays

## INI Parser Usage

The project provides `src/core/ini_parser.sh` with helpers such as `load_ini_config` and `parse_ini`.

Example: load variables and export

```bash
# inside init_config()
load_ini_config "variables.ini" || return 1
parse_ini variables.ini "user"
export USERNAME="$user"
```

Example: load package lists into arrays

```bash
load_ini_config "packages.ini"
mapfile -t CORE_PACKAGES < <(parse_ini_section_lines packages.ini core)
```

## Package Mapping

Package name mapping is stored in `pkgmap.ini`. Load it with `load_package_mappings` and use `map_package_name` or `map_package_list` to translate names for the detected distro.

## Migration Notes

- If you previously used JSON + jq, migrate by translating JSON objects into INI sections. Keep examples in `config_examples/` as ground truth.
- Tests and CI that relied on JSON should be updated to read from INI or use the project's parser mocks.

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
│  │ • hostnames        │  │ • apps[]               │     │
│  │ • desktop {}       │  │ • desktop[]            │     │
│  │ • laptop {}        │  │ • laptop[]             │     │
│  │ • browser {}       │  │ • mappings {}          │     │
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
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                Runtime Environment                       │
│                                                          │
│  • Environment Variables: $user, $hostname_desktop      │
│  • Bash Arrays: CORE_PACKAGES[@], DESKTOP_PACKAGES[@]  │
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
  host = desktop-hostname
  session = qtile
  ```

  Better than flattened keys because related values are grouped under a section.

2. **Lists as section entries**:

  ```ini
  [core]
  curl
  wget
  jq
  ```

3. **Explicit Mappings**:

  ```ini
   "mappings": {
     "package-name": {
       "fedora": "fedora-name",
       "arch": "arch-name"
     }
   }
   ```

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

---

This file centralizes the configuration format and loading strategy used by auto-penguin-setup.

Files: `~/.config/auto-penguin-setup/variables.ini`, `packages.ini`, `pkgmap.ini`

Parser: `src/core/ini_parser.sh` — a small INI parsing helper used throughout the project.

Design highlights:

- Use sections for related data (e.g. `[desktop]`, `[laptop]`, `[system]`).
- Lists are represented as one entry per line inside a section (see `packages.ini`).
- Mappings use per-distro sections (`[pkgmap.fedora]`, `[pkgmap.arch]`, etc.).
- All configuration-loading helpers live in `src/core/config.sh` and call into the INI parser.

Examples

variables.ini

```ini
[system]
user = developer
mirror_country = de

[desktop]
hostname = desktop-host
session = qtile

[laptop]
hostname = laptop-host
session = hyprland
```

packages.ini

```ini
[core]
curl
wget
ufw

[qtile]
qtile-extras
rofi
```

pkgmap.ini

```ini
[pkgmap.fedora]
fd-find = fd-find

[pkgmap.arch]
fd-find = fd

[pkgmap.debian]
fd-find = fd-find
```

Usage

- `init_config()` locates the user's INI files (looks under XDG config dir, falls back to `configs/`) and calls `ini_parser` helpers to populate environment variables and arrays used by other modules.
- If a file is missing, the project provides defaults in `config_examples/` which are copied on first-run or by the `create_config` helpers.

Migration

- Config evolution is handled by `update_config_schema()` which merges new keys from the example INI into the user's file while preserving values and backing up the original.

Reference: `src/core/ini_parser.sh`, `src/core/config.sh`
