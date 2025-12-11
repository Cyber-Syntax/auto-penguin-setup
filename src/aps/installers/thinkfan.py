"""Thinkfan installer for ThinkPad fan control."""

import logging
import shutil
import subprocess
from pathlib import Path

from aps.utils.paths import resolve_config_file

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class ThinkfanInstaller(BaseInstaller):
    """Installer for thinkfan fan control on ThinkPad laptops."""

    def install(self) -> bool:
        """Install and configure thinkfan.

        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Setting up thinkfan for fan control...")

        # Install thinkfan if not already installed
        if not self.pm.is_installed("thinkfan"):
            logger.info(
                "thinkfan not installed — attempting to install for distro: %s", self.distro
            )

            if self.distro == "arch":
                # On Arch, install from AUR
                success, error = self.pm.install(["AUR:thinkfan"])
                if not success:
                    logger.error("Failed to install thinkfan from AUR: %s", error)
                    return False
            else:
                # Debian/Fedora should have thinkfan in official repos
                success, error = self.pm.install(["thinkfan"])
                if not success:
                    logger.error("Failed to install thinkfan from distro repositories: %s", error)
                    return False
        else:
            logger.debug("thinkfan package already installed")

        # Check if thinkfan binary is available
        if not shutil.which("thinkfan"):
            logger.error("thinkfan binary not found after installation")
            return False

        # Backup existing configuration if not already backed up
        conf_file = Path("/etc/thinkfan.conf")
        backup_file = Path("/etc/thinkfan.conf.bak")

        if not backup_file.exists() and conf_file.exists():
            try:
                shutil.copy2(conf_file, backup_file)
                logger.debug("Created backup of thinkfan configuration")
            except (OSError, shutil.Error) as e:
                logger.warning("Failed to create backup of thinkfan configuration: %s", e)

        # Copy new configuration
        source_conf = resolve_config_file("thinkfan.conf")
        if not source_conf.exists():
            logger.error("thinkfan config file not found at %s", source_conf)
            return False

        try:
            subprocess.run(
                ["sudo", "cp", str(source_conf), str(conf_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Copied thinkfan configuration")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to copy thinkfan configuration: %s", e.stderr)
            return False

        # Configure thinkpad_acpi module
        logger.debug("Setting thinkpad_acpi module options...")
        modprobe_conf = Path("/etc/modprobe.d/thinkfan.conf")

        try:
            with modprobe_conf.open("w", encoding="utf-8") as f:
                f.write("options thinkpad_acpi fan_control=1 experimental=1\n")
        except OSError as e:
            logger.error("Failed to create thinkpad_acpi options file: %s", e)
            return False

        # Reload thinkpad_acpi module
        try:
            subprocess.run(
                ["sudo", "modprobe", "-rv", "thinkpad_acpi"],
                check=False,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "modprobe", "-v", "thinkpad_acpi"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to reload thinkpad_acpi module: %s", e.stderr)

        # Enable and start thinkfan services
        logger.info("Enabling and starting thinkfan services...")
        services = ["thinkfan", "thinkfan-sleep", "thinkfan-wakeup"]

        for service in services:
            try:
                subprocess.run(
                    ["sudo", "systemctl", "enable", "--now", service],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.debug("Enabled service: %s", service)
            except subprocess.CalledProcessError:
                logger.warning("Failed to enable service: %s", service)

        # Create thinkfan sleep hack service
        sleep_hack_service = Path("/etc/systemd/system/thinkfan-sleep-hack.service")
        service_content = """[Unit]
Description=Set fan to auto so BIOS can shut off fan during S2 sleep
Before=sleep.target
After=thinkfan-sleep.service

[Service]
Type=oneshot
ExecStart=/usr/bin/logger -t '%N' "Setting /proc/acpi/ibm/fan to 'level auto'"
ExecStart=/usr/bin/bash -c '/usr/bin/echo "level auto" > /proc/acpi/ibm/fan'

[Install]
WantedBy=sleep.target
"""

        try:
            with sleep_hack_service.open("w", encoding="utf-8") as f:
                f.write(service_content)
            logger.debug("Created thinkfan-sleep-hack service")
        except OSError as e:
            logger.error("Failed to create thinkfan-sleep-hack service: %s", e)
            return False

        # Enable sleep hack service
        try:
            subprocess.run(
                ["sudo", "systemctl", "enable", "thinkfan-sleep-hack"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Enabled thinkfan-sleep-hack service")
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to enable thinkfan-sleep-hack service: %s", e.stderr)

        logger.info("Thinkfan setup completed successfully.")
        return True

    def is_installed(self) -> bool:
        """Check if thinkfan is installed and configured.

        Returns:
            True if installed, False otherwise
        """
        return self.pm.is_installed("thinkfan")
