"""Syncthing installer and setup."""

import subprocess

from aps.core.logger import get_logger

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: ARG001
    """Install and enable Syncthing user service.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Setting up Syncthing...")

    # Enable and start Syncthing user service
    try:
        subprocess.run(
            ["/usr/bin/systemctl", "--user", "enable", "--now", "syncthing"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable Syncthing service")
        return False
    else:
        logger.info("Syncthing enabled successfully.")
        return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if Syncthing service is enabled.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if enabled, False otherwise

    """
    try:
        result = subprocess.run(
            ["/usr/bin/systemctl", "--user", "is-enabled", "syncthing"],
            check=False,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    else:
        return result.returncode == 0
