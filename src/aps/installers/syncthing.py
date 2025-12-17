"""Syncthing installer and setup."""

import logging
import subprocess

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class SyncthingInstaller(BaseInstaller):
    """Installer for Syncthing file synchronization."""

    def install(self) -> bool:
        """Install and enable Syncthing user service.

        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Setting up Syncthing...")

        # Enable and start Syncthing user service
        try:
            subprocess.run(
                ["systemctl", "--user", "enable", "--now", "syncthing"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Syncthing enabled successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable Syncthing service: %s", e.stderr)
            return False

    def is_installed(self) -> bool:
        """Check if Syncthing service is enabled.

        Returns:
            True if enabled, False otherwise
        """
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-enabled", "syncthing"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False
