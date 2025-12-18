"""Sync repos command implementation."""

import logging
from argparse import Namespace
from pathlib import Path

from aps.cli.utils import get_tracking_db_path
from aps.core.config import APSConfigParser, ensure_config_files
from aps.core.distro import detect_distro
from aps.core.package_manager import PackageManagerError, get_package_manager
from aps.core.tracking import PackageRecord, PackageTracker
from aps.utils.privilege import ensure_sudo

logger = logging.getLogger(__name__)


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


def cmd_sync_repos(args: Namespace) -> None:
    """Handle 'aps sync-repos' command."""
    # Pre-authenticate sudo for privileged operations (may need to reinstall packages)
    ensure_sudo()

    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    tracker = PackageTracker(get_tracking_db_path())

    # Load package configuration
    config_dir = Path.home() / ".config" / "auto-penguin-setup"

    # Ensure config files exist, creating them from examples if needed
    ensure_config_files(config_dir)

    pkgmap_ini = config_dir / "pkgmap.ini"

    # Parse package mappings to get sources
    pkgmap_parser = APSConfigParser()
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
    changes: list[
        tuple[PackageRecord, str, str]
    ] = []  # (record, old_source, new_source)

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
        logger.info("No repository changes detected.")
        logger.info("All tracked packages are in sync with configuration.")
        return

    # Display detected changes
    logger.info("Repository Changes Detected:")
    logger.info("=" * 80)
    logger.info(
        "%s %s %s",
        "Package".ljust(25),
        "Old Source".ljust(25),
        "New Source".ljust(25),
    )
    logger.info("-" * 80)
    for pkg, old_source, new_source in changes:
        logger.info(
            "%s %s %s",
            pkg.name.ljust(25),
            old_source.ljust(25),
            new_source.ljust(25),
        )
    logger.info("=" * 80)
    logger.info("\nTotal packages to migrate: %s", len(changes))

    # Confirmation prompt (unless --auto flag is set)
    if not getattr(args, "auto", False):
        response = input("\nProceed with migration? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            logger.info("Migration cancelled.")
            return

    # Execute migrations
    logger.info("\nMigrating packages...")
    success_count = 0
    failed_migrations: list[tuple[str, str]] = []  # (package, error)

    for pkg, old_source, new_source in changes:
        logger.info(
            "\nMigrating %s: %s -> %s", pkg.name, old_source, new_source
        )

        # Get the actual package name to install/remove
        package_name = pkg.mapped_name if pkg.mapped_name else pkg.name
        new_package_name = _extract_package_name(
            mappings.get(pkg.name, pkg.name)
        )

        try:
            # Step 1: Remove from old source
            logger.info("  Removing from %s...", old_source)
            success, error = pm.remove(
                [package_name], assume_yes=args.noconfirm
            )
            if not success:
                raise PackageManagerError(f"Failed to remove: {error}")

            # Step 2: Install from new source
            logger.info("  Installing from %s...", new_source)
            success, error = pm.install(
                [new_package_name], assume_yes=args.noconfirm
            )
            if not success:
                # Rollback: try to reinstall from old source
                logger.warning("  Installation failed. Attempting rollback...")
                rollback_success, _ = pm.install(
                    [package_name], assume_yes=args.noconfirm
                )
                if rollback_success:
                    raise PackageManagerError(
                        f"Failed to install from new source, rolled back to {old_source}"
                    )
                raise PackageManagerError(
                    f"Failed to install from new source AND rollback failed: {error}"
                )

            # Step 3: Update tracking
            tracker.remove_package(pkg.name)
            new_record = PackageRecord.create(
                name=pkg.name,
                source=new_source,
                category=pkg.category,
                mapped_name=new_package_name
                if new_package_name != pkg.name
                else None,
            )
            tracker.track_install(new_record)

            logger.info("  ✓ Successfully migrated %s", pkg.name)
            success_count += 1

        except PackageManagerError as e:
            error_msg = str(e)
            logger.error("  ✗ Failed to migrate %s: %s", pkg.name, error_msg)
            failed_migrations.append((pkg.name, error_msg))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Migration Summary")
    logger.info("=" * 80)
    logger.info("Total packages: %s", len(changes))
    logger.info("Successful: %s", success_count)
    logger.info("Failed: %s", len(failed_migrations))

    if failed_migrations:
        logger.info("\nFailed Migrations:")
        for pkg_name, error in failed_migrations:
            logger.info("  - %s: %s", pkg_name, error)
        logger.info(
            "\nPlease review the errors and try again or install manually."
        )
    else:
        logger.info("\n✓ All packages migrated successfully!")
