# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0-alpha]

### Changed

- Enhanced CLI installation logic and configuration clarity.
- Adopted custom logger across modules for consistent logging.
- Improved type hints and docstrings for maintainability.
- Cleaned up imports and module structure.
- Updated documentation and applied code formatting.
- Improved and refactored test cases.

### Fixed

- Added missing source paths for qtile configuration.

### Removed

- Removed Debian/Ubuntu Support: Debian-based distributions are no longer supported to reduce complexity and maintenance burden
- Entry point script `run.py`.
- Removed borgbackup due to maintenance overhead.
- Removed network.py and bootloader.py modules: network module wasn't give so much benefit to desktop linux setup by enabling tcp_bbr and bootloader module was changing grub timeout to 0 which it's not good for dual boot systems. So, those are removed to keep codebase clean.

## [0.2.0-alpha]

### Added

- Comprehensive tests for system and window manager configurations
- --noconfirm option to commands for skipping confirmation prompts
- Enhanced CLI and distribution tests with additional scenarios
- Type hints and improved readability in tests
- Check official repo before AUR/COPR repo installs
- Autocomplete and CLI installation script
- Flatpak management functions and updated installation logic
- Entry point script for auto-penguin-setup development
- All setup components to setup command

### Changed

- Updated AGENTS.md and todos for improved guidelines and testing organization
- Reorganized package lists and improved logging in AMD and Ueberzugpp installers
- Added privilege escalation in installers and system configurations
- Updated timer and service descriptions for monthly cleanup in trash-cli
- Enhanced type annotations for better clarity and maintainability
- Improved error logging and output handling in auto-cpufreq installer
- Migrated better naming
- Removed outdated documentation files and updated docs
- Moved configs/ and default configs to cli folder
- Enhanced distribution detection with package manager validation and improved logging
- Improved configuration handling and package mapping logic
- Reorganized CLI command implementations into separate modules for improved maintainability
- Replaced print statements with logger calls for improved logging consistency
- Enhanced package tracking logic to prevent duplicates and improve logging
- Added verbose flag to all CLI commands for improved output control
- Centralized logging setup and improved log message levels
- Enabled package manager output shows on terminal
- Optimized distribution-specific logic and logger performance
- Migrated auto-penguin-setup from bash to python

### Fixed

- Improved source filtering to be case-insensitive and handle copr/aur in list command
- Added AUR installation handling and error logging in vscode
- Strip inline comments before comma-split to avoid parsing comment text as packages in config
- Updated vscode package reference
- Oh-my-zsh setup to work on automated install

### Removed

- Outdated installation script for mpv

## [0.1.0-alpha]

### Added

- **Package Tracking System**: Automatic tracking of all installed packages with repository sources, timestamps, and categories
    - New tracking database at `~/.local/share/auto-penguin-setup/package_tracking.ini` (INI format)
    - Tracks packages from official repos, COPR, AUR, and PPA sources
    - Automatic tracking during all package installations via `pm_install`
    - **Integrated with existing config system**: Works seamlessly with `packages.ini` and `pkgmap.ini`
    - New CLI commands:
        - `--list-tracked`: List all tracked packages with sources and categories (shows both original and installed names)
        - `--track-info <package>`: Show detailed information for a specific package
        - `--check-repos`: Check for repository changes in `pkgmap.ini` without migrating
        - `--sync-repos`: Automatically migrate packages when `pkgmap.ini` changes
        - `--show-mappings`: Display current package mappings from `pkgmap.ini`
- **Repository Migration**: Intelligent package migration when repositories change in `pkgmap.ini`
    - Detects repository changes by comparing tracking database with current `pkgmap.ini`
    - Interactive migration with user confirmation
    - Automatic rollback on migration failure
    - Cleans up unused repositories after migration
    - Supports COPR, AUR, and PPA repository changes
    - **No config format changes required**: Users edit `pkgmap.ini` as before
- **Repository Management Extensions**:
    - `repo_remove_copr()`: Remove COPR repositories (Fedora)
    - `repo_remove_ppa()`: Remove PPA repositories (Debian/Ubuntu)
- **Package Mapping Metadata System**: Captures repository information during package mapping
    - `PACKAGE_MAPPING_METADATA`: Global associative array for tracking metadata
    - `_store_mapping_metadata()`: Stores package source, category, and final name during mapping
    - `get_package_metadata()`: Retrieves stored metadata for tracking
    - Enhanced `map_package_list()`: Now accepts category parameter for better tracking
- **Package Manager Integration**: Seamless tracking integration with existing package installation
    - `_track_installed_package_with_metadata()`: Tracks packages using stored mapping metadata
    - `_track_package()`: Enhanced to accept original package name
    - Integrated with all distribution-specific install functions
- **Enhanced Tracking Database Schema**:
    - Added `original_name` field to track package name from `packages.ini`
    - Distinguishes between original generic name and distribution-specific installed name
- **Comprehensive Documentation**:
    - User guide: `docs/PACKAGE_TRACKING.md`
    - Architecture documentation: `docs/architecture/package_tracking.arch.md`
    - Integration guide: `docs/TRACKING_INTEGRATION_SUMMARY.md`
    - Implementation plan: `plan/tracking-integration-with-existing-config.md`
    - Implementation summary: `docs/IMPLEMENTATION_SUMMARY.md`
- **Test Coverage**:
    - BATS test suite for core tracking functionality (20+ tests)
    - BATS test suite for metadata integration (8 tests passing)

### Changed

- `src/core/package_mapping.sh`:
    - Added `PACKAGE_MAPPING_METADATA` global array for tracking integration
    - Modified `map_package_list()` to accept category parameter and store metadata
    - Added `_store_mapping_metadata()` and `get_package_metadata()` functions
- `src/core/package_manager.sh`:
    - Integrated automatic package tracking after installations using metadata
    - Added `_track_installed_package_with_metadata()` for metadata-based tracking
    - Modified `_pm_install_fedora()`, `_pm_install_arch()`, and `_pm_install_debian()` for tracking
- `src/core/package_tracking.sh`:
    - Enhanced `track_package_install()` to accept `original_name` parameter
    - Updated database schema to include `original_name` field
    - Modified `list_tracked_packages()` to display both original and installed names
- `src/core/install_packages.sh`:
    - Updated all `install_*_packages()` functions to pass category to `map_package_list()`
- `src/core/repo_migration.sh`:
    - Rewrote `get_package_config_source()` to read from `pkgmap.ini` via `PACKAGE_MAPPINGS`
    - Added automatic `pkgmap.ini` loading in migration functions
- `src/core/repository_manager.sh`:
    - Added repository removal functions
    - Improved code formatting

[0.3.0-alpha]: https://github.com/Cyber-Syntax/auto-penguin-setup/compare/v0.2.0-alpha...v0.3.0-alpha
[0.2.0-alpha]: https://github.com/Cyber-Syntax/auto-penguin-setup/compare/v0.1.0-alpha...v0.2.0-alpha
[0.1.0-alpha]: https://github.com/Cyber-Syntax/auto-penguin-setup/releases/tag/v0.1.0-alpha
