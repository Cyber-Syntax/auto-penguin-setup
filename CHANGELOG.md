# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-alpha]

### Added

- **Complete Python Migration**: Migrated entire codebase from Bash to Python for better maintainability, performance, and testability
- **Python CLI Framework**: New command-line interface built with Python using argparse and rich for enhanced user experience
- **Package Management Abstraction**: Unified package management system supporting Fedora, Arch, and Debian-based distributions
- **Comprehensive Test Suite**: 106+ pytest tests covering all core functionality with high coverage
- **Hardware Detection Module**: Python implementation for detecting and configuring hardware-specific settings
- **System Configuration Module**: Python-based system setup and configuration management
- **Window Manager Support**: Python modules for configuring various window managers (Qtile, i3, Hyprland)
- **Display Manager Setup**: Python implementation for configuring display managers (GDM, LightDM, SDDM)
- **Repository Management**: Enhanced repository handling with automatic migration and cleanup
- **Package Tracking System**: Improved tracking with metadata storage and repository migration capabilities
- **Configuration Parser**: Robust INI configuration parsing with validation and error handling
- **Development Tools**: Added uv package manager support, pre-commit hooks, and development dependencies

### Changed

- **Architecture**: Complete rewrite from shell scripts to object-oriented Python modules
- **Error Handling**: Improved error handling with proper exceptions and logging
- **Type Safety**: Added type hints throughout the codebase for better code quality
- **Testing**: Migrated from BATS to pytest for more comprehensive and maintainable tests
- **Dependency Management**: Switched to modern Python packaging with pyproject.toml
- **CLI Interface**: Enhanced command-line interface with better argument parsing and help messages

### Removed

- **Bash Scripts**: All 50+ Bash scripts replaced with Python equivalents
- **Shell Dependencies**: Eliminated reliance on shell-specific utilities and improved security
- **Legacy Code**: Removed outdated and unmaintained shell script components

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

[0.2.0-alpha]: https://github.com/Cyber-Syntax/auto-penguin-setup/compare/v0.1.0-alpha...v0.2.0-alpha
[0.1.0-alpha]: https://github.com/Cyber-Syntax/auto-penguin-setup/releases/tag/v0.1.0-alpha
