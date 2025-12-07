"""Trash-cli installer and systemd timer setup."""

import logging
import shutil
import subprocess
from pathlib import Path

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class TrashCLIInstaller(BaseInstaller):
    """Installer for trash-cli with systemd timer for automatic cleanup."""

    def install(self) -> bool:
        """Install trash-cli systemd service and timer.

        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Setting up trash-cli service...")

        # Define paths
        service_dest = Path("/etc/systemd/system/trash-cli.service")
        timer_dest = Path("/etc/systemd/system/trash-cli.timer")
        service_src = Path("configs/trash-cli/trash-cli.service")
        timer_src = Path("configs/trash-cli/trash-cli.timer")

        # Copy service file
        try:
            shutil.copy2(service_src, service_dest)
            logger.debug("Copied service file to %s", service_dest)
        except (OSError, shutil.Error) as e:
            logger.error("Failed to copy trash-cli service file: %s", e)
            return False

        # Copy timer file
        try:
            shutil.copy2(timer_src, timer_dest)
            logger.debug("Copied timer file to %s", timer_dest)
        except (OSError, shutil.Error) as e:
            logger.error("Failed to copy trash-cli timer file: %s", e)
            return False

        # Reload systemd daemon
        try:
            subprocess.run(
                ["sudo", "systemctl", "daemon-reload"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to reload systemd daemon: %s", e.stderr)
            return False

        # Enable and start timer
        logger.info("Enabling trash-cli timer...")
        try:
            subprocess.run(
                ["sudo", "systemctl", "enable", "--now", "trash-cli.timer"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable trash-cli timer: %s", e.stderr)
            return False

        logger.info("trash-cli service setup completed.")
        return True

    def is_installed(self) -> bool:
        """Check if trash-cli timer is enabled.

        Returns:
            True if enabled, False otherwise
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", "trash-cli.timer"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False
