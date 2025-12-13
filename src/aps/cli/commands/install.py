"""Install command implementation."""

import logging
import subprocess
from argparse import Namespace
from pathlib import Path

from aps.cli.utils import get_tracking_db_path, load_category_packages
from aps.core.distro import DistroFamily, detect_distro
from aps.core.package_manager import PacmanManager, get_package_manager
from aps.core.package_mapper import PackageMapper
from aps.core.repo_manager import RepositoryManager
from aps.core.tracking import PackageRecord, PackageTracker

logger = logging.getLogger(__name__)


def cmd_install(args: Namespace) -> None:
    """Handle 'aps install' command."""
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

        # Check official repos BEFORE we enable COPR/AUR
        # This is the critical timing fix - check before repo enablement
        mapping = repo_mgr.check_official_before_enabling(pkg, mapping)

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
            logger.info("Would install: %s", p)
        logger.debug("Dry run completed")
    else:
        # Install system packages
        system_to_install = [m.mapped_name for m in official_pkgs + copr_pkgs + ppa_pkgs]
        logger.debug("Installing system packages: %s", system_to_install)
        if system_to_install:
            success, error = pm.install(system_to_install, assume_yes=True)
            if not success:
                logger.error("Failed to install system packages: %s", error)
                return

        # Install AUR packages (Arch only)
        if aur_pkgs:
            aur_to_install = [m.mapped_name for m in aur_pkgs]
            logger.debug("Installing AUR packages: %s", aur_to_install)
            if isinstance(pm, PacmanManager):
                success = pm.install_aur(aur_to_install, assume_yes=True)
                if not success:
                    logger.error("Failed to install AUR packages")
                    return
            else:
                logger.error("AUR packages not supported on this distro")
                return

        # Install flatpak packages
        if flatpak_packages:
            logger.debug("Installing flatpak packages: %s", flatpak_packages)
            # Ensure flathub remote is enabled (for category flatpak)
            if not repo_mgr.is_flatpak_remote_enabled("flathub"):
                logger.info("Enabling flathub remote...")
                if not repo_mgr.enable_flatpak_remote("flathub"):
                    logger.error("Failed to enable flathub remote")
                    return

            # Don't capture output - let user see flatpak installation progress and approve permissions
            cmd = ["flatpak", "install", "flathub"] + flatpak_packages
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
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
            logger.info("Installed: %s", m.original_name)

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
            logger.info("Installed: %s", p)

    logger.debug("aps install command completed")
