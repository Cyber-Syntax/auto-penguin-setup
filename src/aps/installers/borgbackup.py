"""Borgbackup installer and systemd timer setup."""

import logging
import subprocess
from pathlib import Path

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class BorgbackupInstaller(BaseInstaller):
    """Installer for Borgbackup with systemd timer for automated backups."""

    def install(self) -> bool:
        """Install and configure Borgbackup with systemd timer.

        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Setting up Borgbackup...")

        # Create /opt/borg directory
        opt_borg = Path("/opt/borg")
        if not opt_borg.exists():
            logger.debug("Creating /opt/borg directory...")
            try:
                subprocess.run(
                    ["sudo", "mkdir", "-p", str(opt_borg)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to create /opt/borg directory: %s", e.stderr)
                return False

        # Copy backup script to /opt/borg
        script_dest = Path("/opt/borg/home-borgbackup.sh")
        script_src = Path("configs/borg/home-borgbackup.sh")

        if not script_dest.exists():
            logger.debug("Copying home-borgbackup.sh to /opt/borg...")
            if not script_src.exists():
                logger.error("Borgbackup script not found at %s", script_src)
                return False

            try:
                subprocess.run(
                    ["sudo", "cp", str(script_src), str(script_dest)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to copy borgbackup script: %s", e.stderr)
                return False
        else:
            logger.debug("home-borgbackup.sh already exists in /opt/borg")

        # Ensure borgbackup is installed
        if not self.pm.is_installed("borgbackup"):
            logger.debug("Borgbackup is not installed, installing...")
            success, error = self.pm.install(["borgbackup"])
            if not success:
                logger.error("Failed to install Borgbackup: %s", error)
                return False
        else:
            logger.debug("Borgbackup is already installed")

        # Copy systemd service and timer files
        service_dest = Path("/etc/systemd/system/borgbackup-home.service")
        timer_dest = Path("/etc/systemd/system/borgbackup-home.timer")
        service_src = Path("configs/borg/borgbackup-home.service")
        timer_src = Path("configs/borg/borgbackup-home.timer")

        if not service_src.exists() or not timer_src.exists():
            logger.error("Borgbackup service/timer files not found in configs/borg/")
            return False

        try:
            subprocess.run(
                ["sudo", "cp", str(service_src), str(service_dest)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "cp", str(timer_src), str(timer_dest)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Copied service and timer files")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to copy service/timer files: %s", e.stderr)
            return False

        # Enable and start timer
        logger.debug("Enabling and starting borgbackup timer...")
        try:
            subprocess.run(
                ["sudo", "systemctl", "daemon-reload"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "systemctl", "enable", "--now", "borgbackup-home.timer"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable borgbackup timer: %s", e.stderr)
            return False

        logger.info("Borgbackup setup completed successfully")
        logger.debug("Borgbackup timer is enabled and started")
        return True

    def is_installed(self) -> bool:
        """Check if Borgbackup timer is enabled.

        Returns:
            True if enabled, False otherwise
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", "borgbackup-home.timer"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False
