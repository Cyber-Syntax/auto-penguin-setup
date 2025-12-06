# Package Tracking Architecture

## Overview

The package tracking system provides automatic recording and management of installed packages across distributions. It enables repository migration, change detection, and comprehensive package auditing.

## Architecture Goals

1. **Transparency**: Track all package installations without user intervention
2. **Cross-Distribution**: Work consistently across Fedora, Arch, and Debian/Ubuntu
3. **Repository Awareness**: Distinguish between official and third-party sources
4. **Migration Support**: Enable seamless repository changes
5. **Data Integrity**: Maintain accurate tracking database
6. **Minimal Overhead**: Low performance impact on package operations

## System Components

### 1. Core Modules

#### package_tracking.sh

**Purpose**: Core tracking database operations

**Responsibilities**:

- Initialize tracking database
- Track package installations
- Query tracked packages
- Update package records
- Remove package entries
- Generate statistics

**Key Functions**:

```bash
init_package_tracking()          # Initialize system and database
track_package_install()          # Record package installation
untrack_package()                # Remove package from tracking
get_tracked_packages()           # List all tracked packages
get_package_info()               # Get detailed package info
get_package_source()             # Get package repository source
get_packages_from_repo()         # Filter packages by repository
is_package_tracked()             # Check if package is tracked
list_tracked_packages()          # Human-readable package list
get_tracking_stats()             # Installation statistics
```

**Internal Functions**:

```bash
_create_tracking_database()      # Create initial database structure
_add_package_entry()             # Add new package to database
_update_package_entry()          # Update existing package entry
_update_metadata_timestamp()     # Update last_updated timestamp
```

#### repo_migration.sh

**Purpose**: Repository change detection and migration

**Responsibilities**:

- Detect repository changes in config
- Compare tracked vs configured sources
- Migrate packages to new repositories
- Handle migration failures and rollback
- Clean up unused repositories

**Key Functions**:

```bash
detect_repo_changes()            # Detect repository changes
get_package_config_source()      # Get source from config
migrate_package_repo()           # Migrate single package
migrate_all_changed_repos()      # Migrate all changed packages
show_repo_changes()              # Display changes without migrating
```

**Internal Functions**:

```bash
_rollback_migration()            # Rollback failed migration
_cleanup_unused_repo()           # Remove unused repositories
```

### 2. Integration Points

#### package_manager.sh Extensions

**Purpose**: Integrate tracking with package installation

**Additions**:

- `TRACKING_AVAILABLE` flag
- Automatic tracking module loading
- Package tracking after successful installation
- Helper functions for tracking integration

**New Functions**:

```bash
_track_package()                 # Track single package (internal)
_track_installed_packages()      # Track multiple packages (internal)
extract_package_name()           # Extract clean package name
```

**Modified Functions**:

- `init_package_manager()`: Load tracking module
- `_pm_install_arch()`: Track packages after installation
- `_pm_install_debian()`: Track packages after installation

#### repository_manager.sh Extensions

**Purpose**: Repository removal for cleanup

**New Functions**:

```bash
repo_remove_copr()               # Remove COPR repository (Fedora)
repo_remove_ppa()                # Remove PPA repository (Debian/Ubuntu)
```

### 3. Data Layer

#### INI Database Format

**Location**: `~/.local/share/auto-penguin-setup/package_tracking.ini`

**Structure**:

```ini
[metadata]
version=1.0
created_at=2024-01-15T10:30:00Z
last_updated=2024-01-15T10:30:00Z
distro=fedora

[package.<name>]
name=<package_name>
source=<COPR:user/repo|AUR:package|PPA:user/repo|official>
mapped_name=<distro_specific_name>
installed_at=<ISO8601_timestamp>
install_method=pm_install
category=<apps|dev|system|etc>
```

**Schema Design Decisions**:

1. **INI Format**:
    - Simple, human-readable
    - Existing parser infrastructure
    - Easy manual inspection/editing if needed
    - Well-understood format

2. **Package Sections**:
    - One section per package (`[package.<name>]`)
    - Easy to search and update
    - Clear separation between packages

3. **Source Format**:
    - Prefix notation: `COPR:`, `AUR:`, `PPA:`
    - `official` for distribution repositories
    - Consistent with config file format

4. **Timestamps**:
    - ISO 8601 format (UTC)
    - Sortable and parseable
    - Cross-platform compatibility

5. **Metadata Section**:
    - Version for future migrations
    - Distribution tracking
    - Last update timestamp

## Data Flow

### Installation Flow

```
User Command
    |
    v
setup.sh --install apps
    |
    v
install_app_packages()
    |
    v
pm_install_array()
    |
    v
pm_install()
    |
    v
_pm_install_<distro>()
    |
    v
[Package Manager Install]
    |
    v
_track_installed_packages()
    |
    v
track_package_install()
    |
    v
[Update INI Database]
```

### Migration Flow

```
User Command
    |
    v
setup.sh --sync-repos
    |
    v
migrate_all_changed_repos()
    |
    v
get_tracked_packages()
    |
    v
FOR EACH package:
  get_package_source()      # From tracking DB
  get_package_config_source()   # From config
  COMPARE
    |
    v
[Show Changes & Confirm]
    |
    v
FOR EACH changed package:
  migrate_package_repo()
    |
    +-- pm_remove()
    |
    +-- repo_add()
    |
    +-- pm_install()
    |
    +-- track_package_install()
    |
    +-- _cleanup_unused_repo()
```

### Query Flow

```
User Command
    |
    v
setup.sh --list-tracked
    |
    v
list_tracked_packages()
    |
    v
get_tracked_packages()
    |
    v
FOR EACH package:
  get_ini_value()
    |
    v
[Display Results]
```

## Module Dependencies

```
setup.sh
  |
  +-- package_tracking.sh
  |     |
  |     +-- logging.sh
  |     +-- ini_parser.sh
  |     +-- distro_detection.sh (indirect)
  |
  +-- repo_migration.sh
  |     |
  |     +-- logging.sh
  |     +-- package_tracking.sh
  |     +-- config.sh
  |     +-- package_manager.sh
  |     +-- repository_manager.sh
  |
  +-- package_manager.sh
  |     |
  |     +-- logging.sh
  |     +-- distro_detection.sh
  |     +-- package_mapping.sh
  |     +-- package_tracking.sh (loaded dynamically)
  |
  +-- repository_manager.sh
        |
        +-- logging.sh
        +-- distro_detection.sh
```

## Loading Order

**Critical**: Modules must be sourced in dependency order:

1. `logging.sh` - Always first
2. `distro_detection.sh`
3. `package_mapping.sh`
4. `package_manager.sh`
5. `repository_manager.sh`
6. `config.sh`
7. `install_packages.sh`
8. `package_tracking.sh` - After INI parser
9. `repo_migration.sh` - Last (depends on most modules)

**Note**: `package_manager.sh` loads `package_tracking.sh` dynamically to avoid circular dependencies.

## Error Handling Strategy

### Graceful Degradation

Tracking failures should NOT break package installation:

```bash
# Package manager continues even if tracking fails
track_package_install "$pkg" "$source" "$category" 2>/dev/null || {
  log_debug "Failed to track package: $pkg"
  return 0  # Success anyway
}
```

### Migration Rollback

Failed migrations attempt automatic rollback:

```bash
migrate_package_repo() {
  pm_remove "$package" || return 1
  repo_add "$new_repo" || { _rollback_migration "$package" "$old_source"; return 1; }
  pm_install "$package" || { _rollback_migration "$package" "$old_source"; return 1; }
  track_package_install "$package" "$new_source" "$category"
}
```

### Database Corruption

On database parse failure:

1. Log error
2. Attempt backup
3. Create new database
4. Continue operation

## Performance Considerations

### Lazy Loading

Package tracking module is loaded only when needed:

- During `init_package_manager()`
- When tracking commands are used
- Not loaded if tracking file doesn't exist

### Batch Operations

Multiple packages tracked efficiently:

```bash
_track_installed_packages() {
  # Single database parse
  # Multiple package entries
  # Single database write
}
```

### Database Size

Estimated growth: ~200 bytes per package

- 500 packages = ~100KB
- 1000 packages = ~200KB
- Minimal storage impact

### I/O Optimization

- Database loaded once during init
- Kept in memory (INI_DATA associative array)
- Written only on updates
- Atomic file operations (write to temp, move)

## Security

### File Permissions

```bash
chmod 600 "$TRACKING_DB_FILE"
```

- User read/write only
- Prevents unauthorized access
- Protects installation history

### Input Validation

All inputs validated:

- Package names sanitized
- Repository sources verified
- Timestamps validated
- Section names checked

### Repository Trust

Repository migration warnings:

- User confirmation required (interactive mode)
- Clear display of changes
- Rollback on failure

## Testing Strategy

### Unit Tests (BATS)

**test_package_tracking.bats**:

- Database initialization
- Package tracking
- Package updates
- Package removal
- Query functions
- Statistics

**test_repo_migration.bats**:

- Change detection
- Migration process
- Rollback handling
- Repository cleanup

### Integration Tests

1. **Install Tracking**: Verify packages are tracked during install
2. **Migration Workflow**: Full migration cycle
3. **Multi-Package**: Track multiple packages correctly
4. **Cross-Distribution**: Works on Fedora, Arch, Debian

### Manual Testing

1. Install packages → verify tracking
2. Change repository in config → verify detection
3. Migrate packages → verify success
4. Check database → verify accuracy

## Edge Cases

### 1. Package Already Tracked

**Scenario**: Installing already-tracked package
**Behavior**: Update entry with new timestamp/source
**Implementation**: `_update_package_entry()`

### 2. Package Not in Config

**Scenario**: Tracked package removed from config
**Behavior**: Skip during migration (no error)
**Rationale**: User may have intentionally removed it

### 3. Repository Shared by Multiple Packages

**Scenario**: Multiple packages from same COPR
**Behavior**: Repository removed only when no packages remain
**Implementation**: `get_packages_from_repo()` check

### 4. Migration Failure

**Scenario**: New repository unavailable
**Behavior**: Attempt rollback, log error, continue with other packages
**Implementation**: `_rollback_migration()`

### 5. Distribution Change

**Scenario**: User reinstalls with different distribution
**Behavior**: Database includes distro metadata; new install creates new database
**Consideration**: Future version could detect mismatch and warn

### 6. Concurrent Access

**Scenario**: Multiple instances of setup.sh
**Current**: No locking (race condition possible)
**Future**: Implement file locking with `flock`

### 7. Database Corruption

**Scenario**: Malformed INI file
**Behavior**: Parse fails, create backup, initialize new database
**Implementation**: Error handling in `parse_ini_file()`

## Future Enhancements

### Phase 1 (Immediate)

- [x] Core tracking functionality
- [x] Repository migration
- [x] CLI commands
- [ ] BATS test suite completion

### Phase 2 (Short-term)

- [ ] Version tracking
- [ ] Dependency tracking
- [ ] Installation history
- [ ] Backup/restore commands

### Phase 3 (Medium-term)

- [ ] File locking for concurrent access
- [ ] Database migration system
- [ ] JSON export format
- [ ] Integration with system package manager

## Alternatives Considered

### SQLite Database

**Pros**:

- Better performance for large datasets
- Transaction support
- Complex queries

**Cons**:

- External dependency
- More complex implementation
- Overkill for typical use case (< 1000 packages)
- Not human-readable

**Decision**: INI format sufficient for MVP

### JSON Format (considered)

**Pros**:

- Structured data; widely used and supported by many tools and libraries

**Cons**:

- Less human-readable than simple INI sections and lists
- No native JSON parser is bundled in this project; adopting JSON would require adding and maintaining extra parsing tooling
- Increases complexity for contributors who prefer simple text-based config

**Decision**: INI format preferred (existing `ini_parser.sh` infrastructure and simpler workflow)

### System Package Manager Integration

**Pros**:

- Use native package manager database
- Automatic sync
- No separate tracking needed

**Cons**:

- Distribution-specific implementation
- No control over data format
- Can't track custom metadata (source, category)
- Complex to implement

**Decision**: Separate database provides flexibility

## Compatibility

### Backward Compatibility

**Existing Installations**:

- No tracking database exists
- First run creates new database
- Historical packages not tracked (acceptable)
- No breaking changes to existing functionality

### Forward Compatibility

**Database Versioning**:

```ini
[metadata]
version=1.0
```

Future versions can:

- Detect old database format
- Migrate data structure
- Maintain backward compatibility

### Cross-Distribution

**Portable Design**:

- Works on Fedora, Arch, Debian/Ubuntu
- Distribution-agnostic tracking
- Repository source includes type (COPR/AUR/PPA)

## Documentation

### User Documentation

- `docs/PACKAGE_TRACKING.md` - User guide with examples

### Developer Documentation

- `docs/architecture/package_tracking.arch.md` - This file
- Code comments in source files
- Function documentation headers

### Examples

- Migration workflow examples
- CLI usage examples
- Configuration examples

## Metrics and Monitoring

### Success Metrics

1. **Tracking Accuracy**: All installed packages are tracked
2. **Migration Success Rate**: > 95% successful migrations
3. **Performance Impact**: < 5% overhead on installation
4. **User Adoption**: Tracking used in production

### Error Tracking

Log levels for tracking operations:

- `DEBUG`: Detailed tracking operations
- `INFO`: Package tracked, migration started
- `WARN`: Tracking failed (non-critical)
- `ERROR`: Migration failed, rollback attempted

## Conclusion

The package tracking system provides a robust, cross-distribution solution for managing installed packages and their sources. The INI-based approach balances simplicity with functionality, enabling advanced features like repository migration while maintaining transparency and data integrity.

Key strengths:

- Automatic and transparent operation
- Cross-distribution compatibility
- Safe migration with rollback
- Human-readable database
- Graceful error handling

The modular design allows for future enhancements while maintaining backward compatibility and minimizing dependencies.
