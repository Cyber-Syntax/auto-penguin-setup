"""Install command implementation."""

import subprocess
from argparse import Namespace
from pathlib import Path

from aps.cli.utils import get_tracking_db_path, load_category_packages
from aps.core.config import APSConfigParser
from aps.core.distro import DistroFamily, detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import PacmanManager, get_package_manager
from aps.core.package_mapper import PackageMapper, PackageMapping
from aps.core.repo_manager import RepositoryManager
from aps.core.tracking import PackageRecord, PackageTracker
from aps.utils.privilege import ensure_sudo

logger = get_logger(__name__)


def cmd_install(args: Namespace) -> None:
    """Handle 'aps install' command."""
    logger.debug("Starting aps install command")

    # Pre-authenticate sudo for privileged operations
    ensure_sudo()

    # Validate configuration - check for legacy [flatpak] section
    config_dir = Path.home() / ".config" / "auto-penguin-setup"
    packages_config = APSConfigParser(config_dir / "packages.ini")
    packages_config.validate_no_flatpak_category()

    distro_info = detect_distro()
    logger.debug(
        "Detected distro: %s %s", distro_info.name, distro_info.version
    )

    pm = get_package_manager(distro_info)
    repo_mgr = RepositoryManager(distro_info, pm)
    tracker = PackageTracker(get_tracking_db_path())
    mapper = PackageMapper(config_dir / "pkgmap.ini", distro_info)

    logger.debug("Package mapper loaded from %s", config_dir / "pkgmap.ini")
    logger.debug("Mapper has %s mappings", len(mapper.mappings))

    # Collect all packages to install
    packages_to_map: list[tuple[str, str | None]] = []  # (package, category)

    for pkg in args.packages:
        if pkg.startswith("@"):
            # Install category
            category = pkg[1:]
            cat_packages = load_category_packages(category)
            logger.debug("Loaded category '%s': %s", category, cat_packages)
            packages_to_map.extend([(p, category) for p in cat_packages])
        else:
            packages_to_map.append((pkg, None))

    logger.debug("Packages to map: %s", packages_to_map)

    # Map all packages through the mapper
    mapped_packages: list[PackageMapping] = []
    for pkg, category in packages_to_map:
        mapping = mapper.map_package(pkg, category)

        # Check official repos BEFORE we enable COPR/AUR
        # This is the critical timing fix - check before repo enablement
        mapping = repo_mgr.check_official_before_enabling(pkg, mapping)

        mapped_packages.append(mapping)
        logger.debug(
            "Mapped %s -> %s (source: %s)",
            pkg,
            mapping.mapped_name,
            mapping.source,
        )

    # Separate by source (only for relevant distro families)
    official_pkgs: list[PackageMapping] = [
        m for m in mapped_packages if m.is_official
    ]
    copr_pkgs: list[PackageMapping] = (
        [m for m in mapped_packages if m.is_copr]
        if distro_info.family == DistroFamily.FEDORA
        else []
    )
    aur_pkgs: list[PackageMapping] = (
        [m for m in mapped_packages if m.is_aur]
        if distro_info.family == DistroFamily.ARCH
        else []
    )
    flatpak_pkgs: list[PackageMapping] = [
        m for m in mapped_packages if m.is_flatpak
    ]

    logger.debug(
        "Official packages: %s", [m.mapped_name for m in official_pkgs]
    )
    if distro_info.family == DistroFamily.FEDORA:
        logger.debug("COPR packages: %s", [m.mapped_name for m in copr_pkgs])
    if distro_info.family == DistroFamily.ARCH:
        logger.debug("AUR packages: %s", [m.mapped_name for m in aur_pkgs])
    logger.debug("Flatpak packages: %s", [m.mapped_name for m in flatpak_pkgs])

    # Enable Flatpak remotes (based on mapped packages)
    flatpak_remotes_to_enable: set[str] = set()
    for m in flatpak_pkgs:
        remote = m.get_repo_name()
        if remote:
            flatpak_remotes_to_enable.add(remote)

    if flatpak_remotes_to_enable:
        for remote in flatpak_remotes_to_enable:
            if not repo_mgr.is_flatpak_remote_enabled(remote):
                if args.dry_run:
                    logger.info("Would enable flatpak remote %s", remote)
                else:
                    logger.info("Enabling flatpak remote %s...", remote)
                    if not repo_mgr.enable_flatpak_remote(remote):
                        logger.error(
                            "Failed to enable flatpak remote %s", remote
                        )
                        return
            elif not args.dry_run:
                logger.info("Flatpak remote %s is already enabled", remote)

    # Enable COPR repos (Fedora only)
    if distro_info.family == DistroFamily.FEDORA:
        for m in copr_pkgs:
            repo = m.get_repo_name()
            if repo:
                if not repo_mgr.is_copr_enabled(repo):
                    if args.dry_run:
                        logger.info("Would enable COPR repo %s", repo)
                    else:
                        logger.info("Enabling COPR repo %s...", repo)
                        if not repo_mgr.enable_copr(repo):
                            logger.error("Failed to enable COPR repo %s", repo)
                            return
                elif not args.dry_run:
                    logger.info("COPR repo %s is already enabled", repo)

    all_packages: list[str] = [m.mapped_name for m in mapped_packages]

    if args.dry_run:
        for p in all_packages:
            logger.info("Would install: %s", p)
        logger.debug("Dry run completed")
    else:
        # Install system packages (official + COPR)
        system_to_install: list[str] = [
            m.mapped_name for m in official_pkgs + copr_pkgs
        ]
        logger.debug("Installing system packages: %s", system_to_install)
        if system_to_install:
            success, error = pm.install(
                system_to_install, assume_yes=args.noconfirm
            )
            if not success:
                logger.error("Failed to install system packages: %s", error)
                return

        # Install AUR packages (Arch only)
        if aur_pkgs:
            aur_to_install: list[str] = [m.mapped_name for m in aur_pkgs]
            logger.debug("Installing AUR packages: %s", aur_to_install)
            if isinstance(pm, PacmanManager):
                success = pm.install_aur(
                    aur_to_install, assume_yes=args.noconfirm
                )
                if not success:
                    logger.error("Failed to install AUR packages")
                    return
            else:
                logger.error("AUR packages not supported on this distro")
                return

        # Install flatpak packages
        if flatpak_pkgs:
            flatpak_names = [m.mapped_name for m in flatpak_pkgs]
            logger.debug("Installing flatpak packages: %s", flatpak_names)
            # Use remote from mapping (already enabled above)
            for remote in flatpak_remotes_to_enable:
                cmd = ["flatpak", "install", remote] + [
                    m.mapped_name
                    for m in flatpak_pkgs
                    if m.get_repo_name() == remote
                ]
                logger.debug("Running: %s", cmd)
                result = subprocess.run(cmd, check=False)  # noqa: S603
                if result.returncode != 0:
                    logger.error(
                        "Failed to install flatpak packages from %s",
                        remote,
                    )
                    return

        # Track all packages
        installed_packages = []
        for m in mapped_packages:
            record = PackageRecord.create(
                name=m.original_name,
                source=m.source,
                category=m.category,
                mapped_name=m.mapped_name,
            )
            tracker.track_install(record)
            logger.debug(
                "Tracked package: %s from %s", m.original_name, m.source
            )
            installed_packages.append(m.original_name)

        # Display all installed packages on one line
        if installed_packages:
            logger.info("Installed: %s", ", ".join(installed_packages))

    logger.debug("aps install command completed")
