# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. Simple is better than complex.
2. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
3. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
4. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.

## Project Overview

auto-penguin-setup is a cross-distribution Linux system setup automation tool written in Bash. It automates installation and configuration across arch linux, fedora, debian with intelligent distribution detection and package name mapping.

### Key Technologies

- Bash 4.5+ (primary language)
- INI configuration (using the project's INI parser `src/core/ini_parser.sh`). See `docs/architecture/config.arch.md` for the canonical INI schema and examples.
- BATS (Bash Automated Testing System)
- Multiple package managers: dnf/copr (Fedora), pacman/paru (Arch), apt/deb (Debian/Ubuntu)

## Setup Commands

### Running the Setup

```bash
# Show help and available options
./setup.sh -h
```

## Development Workflow

### Module Loading Order

**CRITICAL**: Modules must be sourced in strict dependency order:

1. `src/core/logging.sh` - **ALWAYS FIRST** (provides logging functions)
2. `src/core/distro_detection.sh` - Detects distribution
3. `src/core/package_manager.sh` - Initializes package manager abstraction
4. `src/core/package_mapping.sh` - Sets up package name mappings
5. `src/core/repository_manager.sh` - Repository management
6. `src/core/config.sh` - Loads user configurations
7. `src/core/install_packages.sh` - Package installation wrapper
8. Feature modules (apps/system/hardware/display/wm) - **Order doesn't matter**

### Working with Core Modules

**DO NOT** modify core module loading order in `setup.sh`. The order is critical for functionality.

**When adding to core modules**:

- Add source guards: `[[ -n "${_MODULENAME_SOURCED:-}" ]] && return 0`
- Use logging functions (after logging.sh is loaded)
- Follow abstraction patterns - no distribution-specific code outside core

### File Organization

- Keep related functionality together in categorical directories
- One primary feature per module file
- Helper functions can stay in the same file if they're only used there
- Share common utilities through core modules, not by copying code

### Abstraction Rules

**NEVER write distribution-specific code outside core modules**:

❌ Wrong:

```bash
if [[ "$DETECTED_DISTRO" == "fedora" ]]; then
  sudo dnf install package
elif [[ "$DETECTED_DISTRO" == "arch" ]]; then
  sudo pacman -S package
fi
```

✅ Correct:

```bash
pm_install "package"  # Handles all distributions automatically
```

**Use abstraction functions**:

- `pm_install <package>` - Install packages
- `pm_remove <package>` - Remove packages
- `pm_search <package>` - Search for packages
- `pm_update` - Update package database
- `pm_upgrade` - Upgrade all packages
- `repo_add <repo>` - Add repository (COPR/AUR/PPA)
- `map_package <generic_name>` - Get distro-specific package name

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
