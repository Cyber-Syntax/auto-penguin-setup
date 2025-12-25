"""Ueberzugpp installer for image preview in terminals."""

import subprocess

from aps.core.distro import DistroInfo, detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: ARG001
    """Install ueberzugpp with distro-specific repository setup.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Installing ueberzugpp...")

    distro_info = detect_distro()
    if distro_info.name == "fedora":
        return _install_fedora(distro_info)
    if distro_info.name == "arch":
        return _install_arch(distro_info)

    logger.error("Unsupported distribution: %s", distro_info.name)
    return False


def _install_fedora(distro_info: DistroInfo) -> bool:
    """Install ueberzugpp on Fedora with OpenSUSE repository.

    Args:
        distro_info: Distribution information

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Adding ueberzugpp repository for Fedora...")

    version = distro_info.version

    # Map version to repository name
    repo_map = {
        "40": "Fedora_40",
        "41": "Fedora_41",
        "42": "Fedora_42",
    }

    repo_version = repo_map.get(version, "Fedora_Rawhide")
    if version not in repo_map:
        logger.warning(
            "Unknown Fedora version '%s', using Rawhide repository",
            version,
        )

    repo_url = (
        "https://download.opensuse.org/repositories/"
        f"home:justkidding/{repo_version}/home:justkidding.repo"
    )
    logger.info("Adding repository from: %s", repo_url)

    try:
        run_privileged(
            [
                "/usr/bin/dnf",
                "config-manager",
                "addrepo",
                f"--from-repofile={repo_url}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to add ueberzugpp repository")
        return False
    else:
        logger.info("Successfully added ueberzugpp repository")

    # Install ueberzugpp
    pm = get_package_manager(distro_info)
    success, error = pm.install(["ueberzugpp"])
    if not success:
        logger.error("Failed to install ueberzugpp: %s", error)
        return False

    logger.info("ueberzugpp installation completed")
    return True


def _install_arch(distro_info: DistroInfo) -> bool:
    """Install ueberzugpp on Arch (available in official repos).

    Args:
        distro_info: Distribution information

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Installing ueberzugpp from Arch repositories...")

    pm = get_package_manager(distro_info)
    success, error = pm.install(["ueberzugpp"])
    if not success:
        logger.error("Failed to install ueberzugpp: %s", error)
        return False

    logger.info("ueberzugpp installation completed")
    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if ueberzugpp is installed.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installed, False otherwise

    """
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    return pm.is_installed("ueberzugpp")
