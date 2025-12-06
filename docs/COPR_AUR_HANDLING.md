# COPR and AUR Package Handling

## Overview

The auto-penguin-setup system automatically handles packages from special repositories (COPR for Fedora, AUR for Arch) through an intelligent mapping and installation system.

## How It Works

### 1. Package Mapping (`pkgmap.ini`)

Distribution-specific packages are mapped in `pkgmap.ini` with special prefixes:

```ini
[pkgmap.fedora]
# Format: generic_name=COPR:user/repo:package_name
qtile-extras=COPR:frostyx/qtile:qtile-extras
lazygit=COPR:atim/lazygit
starship=COPR:atim/starship

[pkgmap.arch]
# Format: generic_name=AUR:package_name
qtile-extras=AUR:qtile-extras
lazygit=AUR:lazygit
```

### 2. COPR Mapping Formats

**Format 1: Explicit Package Name** (Recommended when repo and package names differ)

```ini
qtile-extras=COPR:frostyx/qtile:qtile-extras
```

- Repository: `frostyx/qtile`
- Package: `qtile-extras`

**Format 2: Inferred Package Name** (When package name matches generic name)

```ini
starship=COPR:atim/starship
```

- Repository: `atim/starship`
- Package: `starship` (inferred from the key)

### 3. Installation Flow

When you install a package group (e.g., `dev` packages):

1. **Package List** → `packages.ini` defines which packages to install

   ```ini
   [dev]
   starship
   lazygit
   shellcheck
   ```

2. **Mapping** → `map_package_list()` converts to distribution-specific names

   ```
   starship     → COPR:atim/starship:starship
   lazygit      → COPR:atim/lazygit:lazygit
   shellcheck   → ShellCheck
   ```

3. **Installation** → `pm_install()` routes to distribution-specific handler
   - Fedora: `_pm_install_fedora()` handles COPR packages
   - Arch: `_pm_install_arch()` handles AUR packages
   - Debian: `_pm_install_debian()` handles regular packages only

4. **Categorization** → Distribution-specific functions separate packages
   - Fedora: Categorizes into regular vs COPR packages
   - Arch: Categorizes into regular vs AUR packages
   - Debian: No categorization (all packages are regular)

5. **Repository Enable & Install** → For COPR packages (Fedora):

   ```bash
   # Enable repositories
   sudo dnf copr enable -y atim/starship
   sudo dnf copr enable -y atim/lazygit
   
   # Install all packages together
   sudo dnf install -y shellcheck starship lazygit
   ```

## AUR Handling

AUR packages work similarly but simpler (no repository enable step):

```ini
[pkgmap.arch]
lazygit=AUR:lazygit
qtile-extras=AUR:qtile-extras
```

Installation uses `paru` or `yay`:

```bash
paru -S --needed --noconfirm lazygit qtile-extras
```

## Key Functions

### Package Mapping (`src/core/package_mapping.sh`)

- `map_package_name()` - Maps single package, appends key to COPR packages
- `map_package_list()` - Maps array of packages
- `is_copr_package()` - Checks if mapped value is COPR package
- `extract_copr_repo()` - Extracts repository from `COPR:user/repo:pkg`
- `extract_copr_package()` - Extracts package name from mapping

### Package Installation (`src/core/package_manager.sh`)

- `pm_install()` - Main entry point, routes to distribution-specific handlers
- `_pm_install_fedora()` - Handles COPR packages on Fedora
- `_pm_install_arch()` - Handles AUR packages on Arch
- `_pm_install_debian()` - Handles regular packages on Debian
- `_enable_copr_repos()` - Enables COPR repositories (Fedora only)
- `_install_aur_packages()` - Installs AUR packages using helper (Arch only)

## Performance Benefits

The distribution-specific routing eliminates unnecessary checks:

- **Debian**: 100% reduction in package categorization checks (no AUR/COPR regex matching)
- **Arch**: 50% reduction (only checks for AUR, not COPR)
- **Fedora**: 50% reduction (only checks for COPR, not AUR)

For a typical installation of 50 packages, this eliminates 50-100 unnecessary regex checks.

## Adding New COPR Packages

1. **Find the COPR repository**:

   ```bash
   dnf copr search <package>
   ```

2. **Add to `pkgmap.ini`**:

   ```ini
   [pkgmap.fedora]
   my-package=COPR:user/repo:actual-package-name
   ```

3. **Add to `packages.ini`**:

   ```ini
   [dev]
   my-package
   ```

4. **Test**:

   ```bash
   ./setup.sh --install-dev
   ```

## Troubleshooting

### Package Name Mismatch

**Problem**: COPR repo `frostyx/qtile` contains package `qtile-extras`

**Solution**: Use explicit format:

```ini
qtile-extras=COPR:frostyx/qtile:qtile-extras
```

### Repository Already Enabled

The system handles this gracefully - if a COPR repo is already enabled, it continues with installation.

### Multiple Packages from Same Repo

Each package is handled independently. If multiple packages come from the same COPR repo, it will be enabled multiple times (harmless).

## Implementation Details

### Why Append Package Name?

The format `COPR:user/repo:package` allows:

1. Correct repository identification for enabling
2. Correct package name for installation
3. Handling cases where repo name ≠ package name

### Parallel Arrays

COPR packages are stored in an associative array during categorization:

```bash
copr_repo_to_pkg["atim/starship"]="starship"
copr_repo_to_pkg["frostyx/qtile"]="qtile-extras"
```

Then converted to parallel arrays for the installation function:

```bash
_install_copr_packages "atim/starship" "frostyx/qtile" -- "starship" "qtile-extras"
```

## See Also

- `docs/architecture/package-manager.arch.md` - Package manager architecture
- `docs/architecture/config.arch.md` - Configuration file formats
- `src/core/package_mapping.sh` - Mapping implementation
- `src/core/package_manager.sh` - Installation implementation
