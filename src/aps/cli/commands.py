"""CLI command implementations for Auto Penguin Setup."""

import logging
import subprocess
from argparse import Namespace
from pathlib import Path

from aps.core.config_parser import APSConfigParser
from aps.core.distro import DistroFamily, detect_distro
from aps.core.package_manager import PackageManagerError, PacmanManager, get_package_manager
from aps.core.package_mapper import PackageMapper
from aps.core.repo_manager import RepositoryManager
from aps.core.setup import SetupError, SetupManager
from aps.core.tracking import PackageRecord, PackageTracker


def get_tracking_db_path() -> Path:
    """Get the path to the package tracking database."""
    return Path.home() / ".config" / "auto-penguin-setup" / "metadata.jsonl"


def load_category_packages(category: str) -> list[str]:
    """Load packages for a given category from config files."""
    config_dir = Path.home() / ".config" / "auto-penguin-setup"
    parser = APSConfigParser()
    parser.load(config_dir / "packages.ini")

    if not parser.has_section(category):
        raise ValueError(f"Category '{category}' not found in packages.ini")

    return parser.get_section_packages(category)


def cmd_install(args: Namespace) -> None:
    """Handle 'aps install' command."""
    logger = logging.getLogger(__name__)
    logger.debug("Starting aps install command")

    distro_info = detect_distro()
    logger.debug("Detected distro: %s %s", distro_info.name, distro_info.version)

    pm = get_package_manager(distro_info)
    repo_mgr = RepositoryManager(distro_info, pm)
    tracker = PackageTracker(get_tracking_db_path())
    config_dir = Path.home() / ".config" / "auto-penguin-setup"
    mapper = PackageMapper(config_dir / "pkgmap.ini", distro_info)

    logger.debug("Package mapper loaded from %s", config_dir / "pkgmap.ini")
    logger.debug("Mapper has %s mappings", len(mapper.mappings))

    # Collect all packages to install
    system_packages = []
    flatpak_packages = []
    package_categories = {}  # pkg -> category

    for pkg in args.packages:
        if pkg.startswith("@"):
            # Install category
            category = pkg[1:]
            packages = load_category_packages(category)
            logger.debug("Loaded category '%s': %s", category, packages)
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

    logger.debug("System packages to install: %s", system_packages)
    logger.debug("Flatpak packages to install: %s", flatpak_packages)

    # Map system packages
    mapped_system = []
    for pkg in system_packages:
        mapping = mapper.map_package(pkg, package_categories.get(pkg))
        mapped_system.append(mapping)
        logger.debug("Mapped %s -> %s (source: %s)", pkg, mapping.mapped_name, mapping.source)

    # Separate by source (only for relevant distro families)
    official_pkgs = [m for m in mapped_system if m.is_official]
    copr_pkgs = (
        [m for m in mapped_system if m.is_copr] if distro_info.family == DistroFamily.FEDORA else []
    )
    aur_pkgs = (
        [m for m in mapped_system if m.is_aur] if distro_info.family == DistroFamily.ARCH else []
    )
    ppa_pkgs = (
        [m for m in mapped_system if m.is_ppa] if distro_info.family == DistroFamily.DEBIAN else []
    )
    flatpak_mapped = [m for m in mapped_system if m.is_flatpak]

    logger.debug("Official packages: %s", [m.mapped_name for m in official_pkgs])
    if distro_info.family == DistroFamily.FEDORA:
        logger.debug("COPR packages: %s", [m.mapped_name for m in copr_pkgs])
    if distro_info.family == DistroFamily.ARCH:
        logger.debug("AUR packages: %s", [m.mapped_name for m in aur_pkgs])
    if distro_info.family == DistroFamily.DEBIAN:
        logger.debug("PPA packages: %s", [m.mapped_name for m in ppa_pkgs])
    logger.debug("Flatpak mapped packages: %s", [m.mapped_name for m in flatpak_mapped])

    # Add mapped flatpak to flatpak_packages
    for m in flatpak_mapped:
        remote = m.get_repo_name()
        if remote and not repo_mgr.is_flatpak_remote_enabled(remote):
            logger.info("Enabling flatpak remote %s...", remote)
            if not repo_mgr.enable_flatpak_remote(remote):
                logger.error("Failed to enable flatpak remote %s", remote)
                return
        flatpak_packages.append(m.mapped_name)
        package_categories[m.original_name] = m.category

    # Enable COPR repos (Fedora only)
    if distro_info.family == DistroFamily.FEDORA:
        for m in copr_pkgs:
            repo = m.get_repo_name()
            if repo:
                if not repo_mgr.is_copr_enabled(repo):
                    logger.info("Enabling COPR repo %s...", repo)
                    if not repo_mgr.enable_copr(repo):
                        logger.error("Failed to enable COPR repo %s", repo)
                        return
                else:
                    logger.info("COPR repo %s is already enabled", repo)

    # Enable PPA repos (Debian/Ubuntu only)
    if distro_info.family == DistroFamily.DEBIAN:
        for m in ppa_pkgs:
            repo = m.get_repo_name()
            if repo:
                logger.info("Adding PPA %s...", repo)
                if not repo_mgr.add_ppa(repo):
                    logger.error("Failed to add PPA %s", repo)
                    return

    all_packages = [m.original_name for m in mapped_system] + flatpak_packages

    if args.dry_run:
        for p in all_packages:
            print(f"Would install: {p}")
        logger.debug("Dry run completed")
    else:
        # Install system packages
        system_to_install = [m.mapped_name for m in official_pkgs + copr_pkgs + ppa_pkgs]
        logger.debug("Installing system packages: %s", system_to_install)
        if system_to_install:
            success, error = pm.install(system_to_install, assume_yes=True)
            if not success:
                print(f"Failed to install system packages: {error}")
                logger.error("Failed to install system packages: %s", error)
                return

        # Install AUR packages (Arch only)
        if aur_pkgs:
            aur_to_install = [m.mapped_name for m in aur_pkgs]
            logger.debug("Installing AUR packages: %s", aur_to_install)
            if isinstance(pm, PacmanManager):
                success = pm.install_aur(aur_to_install, assume_yes=True)
                if not success:
                    print("Failed to install AUR packages")
                    logger.error("Failed to install AUR packages")
                    return
            else:
                print("AUR packages not supported on this distro")
                logger.error("AUR packages not supported on this distro")
                return

        # Install flatpak packages
        if flatpak_packages:
            logger.debug("Installing flatpak packages: %s", flatpak_packages)
            # Ensure flathub remote is enabled (for category flatpak)
            if not repo_mgr.is_flatpak_remote_enabled("flathub"):
                print("Enabling flathub remote...")
                logger.debug("Enabling flathub remote")
                if not repo_mgr.enable_flatpak_remote("flathub"):
                    print("Failed to enable flathub remote")
                    logger.error("Failed to enable flathub remote")
                    return

            # Don't capture output - let user see flatpak installation progress and approve permissions
            cmd = ["flatpak", "install", "flathub"] + flatpak_packages
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                print("Failed to install flatpak packages")
                logger.error("Failed to install flatpak packages")
                return

        # Track packages
        for m in official_pkgs + copr_pkgs + aur_pkgs + ppa_pkgs + flatpak_mapped:
            record = PackageRecord.create(
                name=m.original_name,
                source=m.source,
                category=m.category,
                mapped_name=m.mapped_name,
            )
            tracker.track_install(record)
            logger.debug("Tracked package: %s from %s", m.original_name, m.source)
            print(f"Installed: {m.original_name}")

        # Track category flatpak packages
        for p in flatpak_packages:
            if p in [m.mapped_name for m in flatpak_mapped]:
                continue  # already tracked
            record = PackageRecord.create(
                name=p,
                source="flatpak:flathub",
                category="flatpak",
                mapped_name=p,
            )
            tracker.track_install(record)
            logger.debug("Tracked flatpak package: %s", p)
            print(f"Installed: {p}")

    logger.debug("aps install command completed")


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
        manager.setup_component(args.component)
        print(f"{args.component} setup completed successfully")
    except SetupError as e:
        print(f"Setup failed: {e}")
