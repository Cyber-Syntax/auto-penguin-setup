"""CLI command implementations for Auto Penguin Setup."""

import logging
import subprocess
from argparse import Namespace
from pathlib import Path

from aps.core.config_parser import APSConfigParser
from aps.core.distro import detect_distro
from aps.core.package_manager import PackageManagerError, get_package_manager
from aps.core.repo_manager import RepositoryManager
from aps.core.setup import SetupError, SetupManager
from aps.core.tracking import PackageRecord, PackageTracker


def get_tracking_db_path() -> Path:
    """Get the path to the package tracking database."""
    return Path.home() / ".config" / "auto-penguin-setup" / "metadata.jsonl"


def load_category_packages(category: str) -> list[str]:
    """Load packages for a given category from config files."""
    config_dir = Path(__file__).parent.parent.parent.parent / "config_examples"
    parser = APSConfigParser()
    parser.load(config_dir / "packages.ini")

    if not parser.has_section(category):
        raise ValueError(f"Category '{category}' not found in packages.ini")

    return parser.get_section_packages(category)


def cmd_install(args: Namespace) -> None:
    """Handle 'aps install' command."""
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    repo_mgr = RepositoryManager(distro_info, pm)
    tracker = PackageTracker(get_tracking_db_path())

    # Collect all packages to install
    system_packages = []
    flatpak_packages = []
    package_categories = {}  # pkg -> category

    for pkg in args.packages:
        if pkg.startswith("@"):
            # Install category
            category = pkg[1:]
            packages = load_category_packages(category)
            if category == "flatpak":
                flatpak_packages.extend(packages)
                for p in packages:
                    package_categories[p] = category
            else:
                system_packages.extend(packages)
                for p in packages:
                    package_categories[p] = category
        else:
            system_packages.append(pkg)
            package_categories[pkg] = None

    all_packages = system_packages + flatpak_packages

    if args.dry_run:
        for p in all_packages:
            print(f"Would install: {p}")
    else:
        # Install system packages
        if system_packages:
            success, error = pm.install(system_packages, assume_yes=True)
            if not success:
                print(f"Failed to install system packages: {error}")
                return

        # Install flatpak packages
        if flatpak_packages:
            # Ensure flathub remote is enabled
            if not repo_mgr.is_flatpak_remote_enabled("flathub"):
                print("Enabling flathub remote...")
                if not repo_mgr.enable_flatpak_remote("flathub"):
                    print("Failed to enable flathub remote")
                    return

            # Install flatpak packages
            cmd = ["sudo", "flatpak", "install", "-y", "flathub"] + flatpak_packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to install flatpak packages: {result.stderr}")
                return

        # Track all installed packages
        for p in all_packages:
            if p in flatpak_packages:
                record = PackageRecord.create(
                    name=p, source="flatpak:flathub", category=package_categories[p], mapped_name=p
                )
            else:
                record = PackageRecord.create(
                    name=p, source="official", category=package_categories[p], mapped_name=p
                )
            tracker.track_install(record)
            print(f"Installed: {p}")


def cmd_remove(args: Namespace) -> None:
    """Handle 'aps remove' command."""
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    tracker = PackageTracker(get_tracking_db_path())

    for pkg in args.packages:
        if args.dry_run:
            print(f"Would remove: {pkg}")
        else:
            success, error = pm.remove([pkg])
            if success:
                tracker.remove_package(pkg)
                print(f"Removed: {pkg}")
            else:
                print(f"Failed to remove {pkg}: {error}")


def cmd_list(args: Namespace) -> None:
    """Handle 'aps list' command."""
    tracker = PackageTracker(get_tracking_db_path())
    packages = tracker.get_tracked_packages()

    if args.source:
        packages = [p for p in packages if p.source.startswith(args.source)]

    if not packages:
        return

    name_width = 30
    source_width = 25
    category_width = 15
    date_width = 24

    print("Tracked Packages:")
    print("=" * (name_width + source_width + category_width + date_width + 3))
    print(
        f"{'Name':<{name_width}} {'Source':<{source_width}} {'Category':<{category_width}} {'Installed At':<{date_width}}"
    )
    print(f"{'-' * name_width} {'-' * source_width} {'-' * category_width} {'-' * date_width}")
    for pkg in packages:
        print(
            f"{pkg.name:<{name_width}} {pkg.source:<{source_width}} {(pkg.category or 'N/A'):<{category_width}} {pkg.installed_at:<{date_width}}"
        )


def cmd_sync_repos(args: Namespace) -> None:
    """Handle 'aps sync-repos' command."""
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    tracker = PackageTracker(get_tracking_db_path())

    # Load package configuration
    config_dir = Path.home() / ".config" / "auto-penguin-setup"
    packages_ini = config_dir / "packages.ini"
    pkgmap_ini = config_dir / "pkgmap.ini"

    if not packages_ini.exists():
        print(f"Error: Configuration file not found: {packages_ini}")
        print("Please create configuration files before running sync-repos.")
        return

    # Parse package mappings to get sources
    pkgmap_parser = APSConfigParser()
    if pkgmap_ini.exists():
        pkgmap_parser.load(pkgmap_ini)

    # Get distro-specific section
    distro_section = f"pkgmap.{distro_info.name.lower()}"
    mappings = (
        pkgmap_parser.get_package_mappings(distro_section)
        if pkgmap_parser.has_section(distro_section)
        else {}
    )

    # Compare tracked packages with config sources
    tracked_packages = tracker.get_tracked_packages()
    changes: list[tuple[PackageRecord, str, str]] = []  # (record, old_source, new_source)

    for pkg in tracked_packages:
        # Skip Flatpak packages - they can't be migrated
        if pkg.source.startswith("flatpak:"):
            continue

        # Determine new source from config
        config_value = mappings.get(pkg.name, pkg.name)
        new_source = _parse_package_source(config_value)

        # Check if source changed
        if new_source != pkg.source:
            changes.append((pkg, pkg.source, new_source))

    if not changes:
        print("No repository changes detected.")
        print("All tracked packages are in sync with configuration.")
        return

    # Display detected changes
    print("Repository Changes Detected:")
    print("=" * 80)
    print(f"{'Package':<25} {'Old Source':<25} {'New Source':<25}")
    print("-" * 80)
    for pkg, old_source, new_source in changes:
        print(f"{pkg.name:<25} {old_source:<25} {new_source:<25}")
    print("=" * 80)
    print(f"\nTotal packages to migrate: {len(changes)}")

    # Confirmation prompt (unless --auto flag is set)
    if not getattr(args, "auto", False):
        response = input("\nProceed with migration? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Migration cancelled.")
            return

    # Execute migrations
    print("\nMigrating packages...")
    success_count = 0
    failed_migrations: list[tuple[str, str]] = []  # (package, error)

    for pkg, old_source, new_source in changes:
        print(f"\nMigrating {pkg.name}: {old_source} -> {new_source}")

        # Get the actual package name to install/remove
        package_name = pkg.mapped_name if pkg.mapped_name else pkg.name
        new_package_name = _extract_package_name(mappings.get(pkg.name, pkg.name))

        try:
            # Step 1: Remove from old source
            print(f"  Removing from {old_source}...")
            success, error = pm.remove([package_name], assume_yes=True)
            if not success:
                raise PackageManagerError(f"Failed to remove: {error}")

            # Step 2: Install from new source
            print(f"  Installing from {new_source}...")
            success, error = pm.install([new_package_name], assume_yes=True)
            if not success:
                # Rollback: try to reinstall from old source
                print("  Installation failed. Attempting rollback...")
                rollback_success, _ = pm.install([package_name], assume_yes=True)
                if rollback_success:
                    raise PackageManagerError(
                        f"Failed to install from new source, rolled back to {old_source}"
                    )
                else:
                    raise PackageManagerError(
                        f"Failed to install from new source AND rollback failed: {error}"
                    )

            # Step 3: Update tracking
            tracker.remove_package(pkg.name)
            new_record = PackageRecord.create(
                name=pkg.name,
                source=new_source,
                category=pkg.category,
                mapped_name=new_package_name if new_package_name != pkg.name else None,
            )
            tracker.track_install(new_record)

            print(f"  ✓ Successfully migrated {pkg.name}")
            success_count += 1

        except PackageManagerError as e:
            error_msg = str(e)
            print(f"  ✗ Failed to migrate {pkg.name}: {error_msg}")
            failed_migrations.append((pkg.name, error_msg))
            logging.error("Migration failed for %s: %s", pkg.name, error_msg)

    # Summary
    print("\n" + "=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"Total packages: {len(changes)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_migrations)}")

    if failed_migrations:
        print("\nFailed Migrations:")
        for pkg_name, error in failed_migrations:
            print(f"  - {pkg_name}: {error}")
        print("\nPlease review the errors and try again or install manually.")
    else:
        print("\n✓ All packages migrated successfully!")


def _parse_package_source(config_value: str) -> str:
    """Parse package source from config value (e.g., 'AUR:pkg', 'COPR:user/repo', 'pkg')."""
    if ":" not in config_value:
        return "official"

    # Handle AUR:package format
    if config_value.startswith("AUR:"):
        return config_value  # Keep full "AUR:package" format

    # Handle COPR:user/repo or COPR:user/repo:package format
    if config_value.startswith("COPR:"):
        parts = config_value.split(":")
        if len(parts) >= 2:
            return f"COPR:{parts[1]}"  # Return "COPR:user/repo"

    # Handle PPA:user/repo format
    if config_value.startswith("PPA:"):
        parts = config_value.split(":")
        if len(parts) >= 2:
            return f"PPA:{parts[1]}"

    return "official"


def _extract_package_name(config_value: str) -> str:
    """Extract actual package name from config value."""
    if ":" not in config_value:
        return config_value

    # AUR:package -> package
    if config_value.startswith("AUR:"):
        return config_value.split(":", 1)[1]

    # COPR:user/repo:package -> package
    # COPR:user/repo -> infer from context (caller should handle)
    if config_value.startswith("COPR:"):
        parts = config_value.split(":")
        if len(parts) >= 3:
            return parts[2]
        # If only COPR:user/repo, package name same as key
        return config_value

    # PPA:user/repo:package -> package
    if config_value.startswith("PPA:"):
        parts = config_value.split(":")
        if len(parts) >= 3:
            return parts[2]
        return config_value

    return config_value


def cmd_status(args: Namespace) -> None:  # noqa: ARG001
    """Handle 'aps status' command."""
    distro_info = detect_distro()
    tracker = PackageTracker(get_tracking_db_path())

    print(f"Distribution: {distro_info.name} {distro_info.version}")
    print(f"Package Manager: {distro_info.package_manager.value}")

    packages = tracker.get_tracked_packages()
    print(f"Tracked Packages: {len(packages)}")

    # Count by source
    sources: dict[str, int] = {}
    for pkg in packages:
        source_type = pkg.source.split(":")[0] if ":" in pkg.source else pkg.source
        sources[source_type] = sources.get(source_type, 0) + 1

    print("By Source:")
    for source, count in sources.items():
        print(f"  {source}: {count}")


def cmd_setup(args: Namespace) -> None:
    """Handle 'aps setup' command."""
    distro_info = detect_distro()
    manager = SetupManager(distro_info)

    try:
        if args.component == "aur-helper":
            manager.setup_aur_helper()
            print("AUR helper setup completed successfully")
        elif args.component == "ollama":
            manager.setup_ollama()
            print("Ollama setup completed successfully")
        else:
            print(f"Unknown component: {args.component}")
            print("Available components: aur-helper, ollama")
    except SetupError as e:
        print(f"Setup failed: {e}")
