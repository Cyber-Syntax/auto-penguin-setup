# Package Tracking System

## Overview

The package tracking system automatically records all packages installed through `auto-penguin-setup`, including their source repositories, installation timestamps, and categories. This enables advanced features like repository migration and package management.

## Features

- **Automatic Tracking**: All packages installed via `pm_install` are automatically tracked
- **Repository Information**: Records whether packages come from official repos, COPR, AUR, or PPA
- **Change Detection**: Detects when package repositories change in your config files
- **Migration Support**: Automatically migrate packages to new repositories
- **Statistics**: View installation statistics and package sources

## Tracking Database

The tracking database is stored at:

~/.local/share/auto-penguin-setup/package_tracking.ini

This file uses INI format and contains:

- Metadata (version, last updated, distribution)
- Package entries with name, source, category, installation time

**Note**: This file is automatically managed. Do not edit it manually.

## Command Reference

### List All Tracked Packages

Display all tracked packages with their sources and categories:

```bash
./setup.sh --list-tracked
```

Example output:

```bash
Tracked Packages:
====================
lazygit                        COPR:atim/lazygit         dev             2024-01-15T10:25:00Z
qtile-extras                   COPR:frostyx/qtile        qtile           2024-01-14T09:15:00Z
neovim                         official                  apps            2024-01-14T09:10:00Z
thinkfan                       AUR:thinkfan              laptop          2024-01-14T09:20:00Z
```

### Show Package Details

Get detailed information about a specific tracked package:

```bash
./setup.sh --track-info <package_name>
```

Example:

```bash
./setup.sh --track-info lazygit
```

Output:

```
name=lazygit
source=COPR:atim/lazygit
mapped_name=lazygit
installed_at=2024-01-15T10:25:00Z
install_method=pm_install
category=dev
```

### Check for Repository Changes

Check if any tracked packages have different repositories in your config files:

```bash
./setup.sh --check-repos
```

This will display packages whose repository sources differ between:

- What's currently tracked in the database
- What's specified in your configuration files

Example output:

```
Repository Status:
====================
lazygit                       : COPR:atim/lazygit -> COPR:dejan/lazygit
qtile-extras                  : COPR:frostyx/qtile -> COPR:qtile-extras/qtile-extras

Use 'setup.sh --sync-repos' to migrate packages
```

### Migrate Packages to New Repositories

Automatically migrate packages when their repositories change:

```bash
./setup.sh --sync-repos
```

This command:

1. Detects all packages with repository changes
2. Shows you the planned migrations
3. Asks for confirmation (interactive mode)
4. Removes packages from old repositories
5. Adds new repositories if needed
6. Reinstalls packages from new sources
7. Updates the tracking database
8. Cleans up unused repositories

Example workflow:

```bash
$ ./setup.sh --sync-repos

Repository Changes Detected:
============================
lazygit                       : COPR:atim/lazygit -> COPR:dejan/lazygit

Migrate all packages? [y/N]: y
Migrating lazygit: COPR:atim/lazygit -> COPR:dejan/lazygit
Removing package from old source...
Adding new repository: dejan/lazygit
Installing package from new source...
Successfully migrated lazygit to COPR:dejan/lazygit
No packages use repository COPR:atim/lazygit, removing...

Migration complete: 1 succeeded, 0 failed
```

## Use Cases

### Use Case 1: Changing COPR Repository

You're using `lazygit` from `atim/lazygit` but want to switch to `dejan/lazygit`:

1. Edit your config file:

   ```ini
   [dev]
   lazygit=COPR:dejan/lazygit
   ```

2. Check what will change:

   ```bash
   ./setup.sh --check-repos
   ```

3. Apply the migration:

   ```bash
   ./setup.sh --sync-repos
   ```

The system will:

- Remove the old package
- Add the new COPR repository
- Install from the new repository
- Remove the old COPR if no other packages use it
- Update tracking database

### Use Case 2: Moving from AUR to Official

You installed a package from AUR, but it's now available in official repos:

1. Update config:

   ```ini
   [apps]
   package-name  # Remove AUR: prefix
   ```

2. Sync:

   ```bash
   ./setup.sh --sync-repos
   ```

### Use Case 3: Audit Your Installation

See what you've installed and from where:

```bash
./setup.sh --list-tracked
```

This helps you:

- Track third-party repositories
- Identify packages that might need attention
- Document your system configuration
- Find packages installed from unofficial sources

## How Tracking Works

### Automatic Tracking

When you install packages using the setup script, tracking happens automatically:

```bash
./setup.sh --install core,apps,dev
```

All packages installed during this process are tracked with:

- Package name
- Source repository (official, COPR, AUR, PPA)
- Category (core, apps, dev, etc.)
- Installation timestamp
- Installation method

### Manual Package Installation

If you install packages manually outside of `auto-penguin-setup`, they won't be tracked. Only packages installed through the script's package management functions are tracked.

### Source Detection

The system determines package sources based on:

1. **Official repositories**: Packages without special prefixes
2. **COPR (Fedora)**: Packages with `COPR:user/repo` prefix
3. **AUR (Arch)**: Packages with `AUR:package` prefix
4. **PPA (Debian/Ubuntu)**: Packages with `PPA:user/repo` prefix

## Repository Migration Process

When you run `--sync-repos`, the system:

1. **Scans**: Compares tracking database with current config
2. **Detects**: Identifies packages with changed repositories
3. **Confirms**: Asks for your approval (interactive mode)
4. **Removes**: Uninstalls package from old source
5. **Adds**: Enables new repository if needed
6. **Installs**: Reinstalls package from new source
7. **Updates**: Records new source in tracking database
8. **Cleans**: Removes unused repositories

### Safety Features

- **Rollback**: If installation from new source fails, attempts to restore from old source
- **Interactive Mode**: Requires confirmation before making changes
- **Error Handling**: Continues with other packages if one fails
- **Summary**: Reports success/failure counts at the end

### Edge Cases

**Multiple packages from same repository**:

- Repository is only removed when NO tracked packages use it

**Package not in config**:

- Migration is skipped (package may have been removed from config intentionally)

**Migration failure**:

- System attempts rollback to previous repository
- Other packages continue to be migrated
- Error is logged with details

## Configuration Format

Your config files should specify repository sources like this:

```ini
[apps]
# Official repository (no prefix)
neovim
firefox

# COPR repository (Fedora)
lazygit=COPR:atim/lazygit

[dev]
# AUR repository (Arch)
thinkfan=AUR:thinkfan

# Official repository
git
```

## Statistics

Get package installation statistics:

```bash
# Currently tracked in the database
./setup.sh --list-tracked | wc -l

# Or implement a future --track-stats command for:
# - Total packages tracked
# - Packages by source (official, COPR, AUR, PPA)
# - Packages by category
# - Installation timeline
```

## Troubleshooting

### Tracking Database Corruption

If the database becomes corrupted:

```bash
# Backup current database
cp ~/.local/share/auto-penguin-setup/package_tracking.ini ~/package_tracking.ini.backup

# Remove corrupted database
rm ~/.local/share/auto-penguin-setup/package_tracking.ini

# Reinitialize (run any command)
./setup.sh --list-tracked
```

The system will create a new database, but historical tracking data will be lost.

### Package Not Tracked

If a package isn't showing up:

1. **Check installation method**: Only packages installed via `pm_install` are tracked
2. **Check timing**: Tracking was added in version X.X - older installations aren't tracked
3. **Manual installation**: Packages installed manually aren't tracked

### Migration Fails

If repository migration fails:

1. **Check logs**: Look for error messages in the output
2. **Verify repository**: Ensure the new repository is valid and accessible
3. **Manual intervention**: You may need to manually install the package
4. **Repository access**: Check network connectivity and repository availability

### Repository Not Removed

If old repositories aren't being removed:

- Check if other packages still use that repository
- Some packages may be tracked with the same repository source
- Use `./setup.sh --track-info <package>` to check package sources

## Security Considerations

### File Permissions

The tracking database is created with `600` permissions (user read/write only) to prevent unauthorized access.

### Repository Sources

Be cautious when migrating between repositories:

- Verify the new repository is trustworthy
- Research the repository maintainer
- Check package signatures when available

### Automatic Migration

Consider the implications of automatic repository migration:

- New repositories may have different security policies
- Package versions may differ
- Dependencies might change

## Future Enhancements

Planned features for the tracking system:

- **Backup/Restore**: Export and import tracking database
- **Conflict Detection**: Warn about package conflicts before migration
- **Version Tracking**: Record package versions
- **Dependency Tracking**: Track package dependencies
- **History**: Maintain installation history with rollback capability
- **Web Dashboard**: Visual interface for package management
- **Integration**: Sync with package manager's native database
- **Notifications**: Alert when tracked packages have updates

## See Also

- [Architecture Documentation](architecture/package_tracking.arch.md)
- [Configuration Guide](CONFIG.md)
- [Repository Management](REPOSITORY_MANAGEMENT.md)
