# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. Simple is better than complex.
2. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
3. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
4. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.
5. **ALWAYS** use `shellcheck` on each file you modify to ensure proper formatting and linting. This runs both syntax and lint checks on individual files. Unless you want to lint and format multiple files, then use `shellcheck -f` and `shellcheck -l` instead.
6. When creating bash scripts, prefer plain bash constructs and avoid unnecessary complexity. Keep functions small and focused. Use built-in bash features where appropriate, but avoid overusing them.

## Linting and Formatting

### ShellCheck

```bash
# Check a single file
shellcheck setup.sh

# Check all shell scripts
find . -name "*.sh" -type f -exec shellcheck {} \;

# Check with specific severity (error, warning, info, style)
shellcheck -S error setup.sh

```

### shfmt

```bash
# Format a file (in-place)
shfmt -w setup.sh

# Format all shell scripts
find . -name "*.sh" -type f -exec shfmt -w {} \;

# Format options used in this project:
# -i 2    : indent with 2 spaces
# -ci     : indent switch cases
# -bn     : binary ops like && and | may start a line
shfmt -i 2 -ci -bn -w setup.sh
```

## Project Overview

auto-penguin-setup is a cross-distribution Bash framework for automating OS setup and package/configuration provisioning across Fedora, Arch, and Debian/Ubuntu families. The project organizes functionality into a small set of core modules that together provide: robust distro detection, mapping of generic package keys to distro/provider-specific identifiers, repository/provider management (COPR/AUR/PPA), a distribution-agnostic package-manager abstraction, configuration discovery and parsing, and higher-level install flows (core/apps/dev/flatpaks).

### Core modules and responsibilities

- `src/core/logging.sh` — initialize file-backed logging, rotation and provide `log_*` helpers (must be sourced first).
- `src/core/distro_detection.sh` — canonical distro detection and helper predicates (`is_fedora`, `is_arch`, `is_debian`, `detect_distro`).
- `src/core/ini_parser.sh` — lightweight INI parser used to read `variables.ini`, `packages.ini`, and `pkgmap.ini`.
- `src/core/package_mapping.sh` — load `pkgmap.ini` and translate generic package keys into distro/provider tokens (supports `COPR:`, `AUR:`, `PPA:` prefixes) while storing mapping metadata.
- `src/core/package_manager.sh` — distribution-agnostic wrapper (`init_package_manager`, `pm_install`, `pm_remove`, `pm_update`, `pm_search`, `pm_is_installed`) and provider flows (enable COPR, install AUR via paru/yay).
- `src/core/repository_manager.sh` — cross-distro repo helpers (add/enable/disable COPR, AUR, PPA and refresh metadata).
- `src/core/config.sh` — configuration discovery and loading (`init_config`, `load_variables`, `load_package_arrays`); exports package arrays and env vars.
- `src/core/install_packages.sh` — high-level installers that map package keys and delegate installation (core/apps/dev/games/system-specific, Flatpak support).

### Key technologies

- Bash 4.5+ (POSIX-friendly shell scripts)
- INI-based configuration and `src/core/ini_parser.sh` for parsing `variables.ini`, `packages.ini`, and `pkgmap.ini`
- BATS for tests and small unit-style test harnesses
- Native package managers and providers: `dnf`/COPR (Fedora), `pacman` + AUR helpers (Arch), `apt`/PPA (Debian/Ubuntu), plus Flatpak for Flatpak installs

### Recommended initialization flow

1. Source and initialize logging (`src/core/logging.sh`) — this is intentionally the first module so other modules can log during init.
2. Detect distro via `src/core/distro_detection.sh` and call `init_package_manager()` to set `CURRENT_DISTRO` and package-manager command templates.
3. Call `init_config()` from `src/core/config.sh` to discover/load `variables.ini` and `packages.ini` and to locate/load `pkgmap.ini` where present.
4. Load package mappings (`load_package_mappings`) and map package lists with `map_package_list` to obtain provider-aware identifiers.
5. Use `pm_install` / `pm_install_array` to install mapped packages; `package_manager.sh` coordinates provider flows and integrates with `repository_manager.sh` as needed.
6. Prefer high-level installers in `install_packages.sh` (`install_core_packages`, `install_app_packages`, `install_flatpak_packages`) for common workflows.

## Setup Commands

### Running the Setup

> Never run setup.sh as root directly, script handles sudo internally.

```bash
# Show help and available options
./setup.sh -h
```
