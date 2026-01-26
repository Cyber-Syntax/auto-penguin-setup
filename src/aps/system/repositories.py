"""Repository management for non-free software."""

import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def configure(distro: str, **kwargs) -> bool:  # noqa: ARG001, ANN003
    """Enable non-free repositories based on distribution.

    Args:
        distro: Distribution identifier.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        bool: True if configuration was successful, False otherwise.

    """
    logger.info("Enabling non-free repositories for %s", distro)

    if distro == "fedora":
        return _enable_rpm_fusion()
    if distro == "arch":
        return _enable_arch_extras()
    logger.warning("Unsupported distribution: %s", distro)
    return False


def _enable_rpm_fusion() -> bool:
    """Enable RPM Fusion repositories on Fedora.

    Returns:
        bool: True if successful, False otherwise.

    """
    logger.info("Enabling RPM Fusion repositories for Fedora")

    # Get Fedora version
    version_result = subprocess.run(
        ["rpm", "-E", "%fedora"],
        capture_output=True,
        text=True,
        check=False,
    )
    if version_result.returncode != 0:
        logger.error("Failed to detect Fedora version")
        return False

    fedora_version = version_result.stdout.strip()
    logger.debug("Detected Fedora version: %s", fedora_version)

    # RPM Fusion repository URLs
    free_repo = f"https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-{fedora_version}.noarch.rpm"
    nonfree_repo = f"https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-{fedora_version}.noarch.rpm"

    result = run_privileged(
        ["dnf", "install", "-y", free_repo, nonfree_repo],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error("Failed to enable RPM Fusion repositories")
        return False

    logger.info("RPM Fusion repositories enabled successfully")
    return True


def _enable_arch_extras() -> bool:
    """Enable extra repositories on Arch Linux.

    Returns:
        bool: True if successful, False otherwise.

    """
    logger.info("Arch Linux uses AUR for additional packages")
    logger.info("No additional repositories needed (using AUR helper)")
    return True
