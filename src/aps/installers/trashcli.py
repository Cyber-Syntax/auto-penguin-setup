"""Trash-cli installer and systemd timer setup."""

import logging
import subprocess
from pathlib import Path

from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

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
        service_src = resolve_config_file("trash-cli/trash-cli.service")
        timer_src = resolve_config_file("trash-cli/trash-cli.timer")

        def copy_with_privilege(src: str, dest: str, desc: str) -> bool:
            try:
                run_privileged(["cp", str(src), str(dest)])
                logger.debug("Copied %s file to %s (privileged)", desc, dest)
                return True
            except subprocess.CalledProcessError as e:
                logger.error("Failed to copy %s file: %s", desc, e.stderr or e)
                return False

        # Copy service file
        if not copy_with_privilege(
            str(service_src), str(service_dest), "service"
        ):
            return False

        # Copy timer file
        if not copy_with_privilege(str(timer_src), str(timer_dest), "timer"):
            return False

        # Reload systemd daemon
        try:
            run_privileged(["systemctl", "daemon-reload"])
        except subprocess.CalledProcessError as e:
            logger.error("Failed to reload systemd daemon: %s", e.stderr)
            return False

        # Enable and start timer
        logger.info("Enabling trash-cli timer...")
        try:
            run_privileged(["systemctl", "enable", "--now", "trash-cli.timer"])
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
