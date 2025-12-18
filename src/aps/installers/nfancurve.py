"""Nfancurve installer for NVIDIA GPU fan control."""

import logging
import subprocess
from pathlib import Path

from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class NfancurveInstaller(BaseInstaller):
    """Installer for nfancurve NVIDIA fan control with systemd service."""

    def install(self) -> bool:
        """Install and configure nfancurve.

        Returns:
            True if installation successful, False otherwise

        """
        logger.info("Setting up nfancurve for NVIDIA fan control...")

        # Create /opt/nfancurve directory
        opt_nfancurve = Path("/opt/nfancurve")
        if not opt_nfancurve.exists():
            logger.debug("Creating /opt/nfancurve directory...")
            try:
                run_privileged(
                    ["mkdir", "-p", str(opt_nfancurve)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Failed to create /opt/nfancurve directory: %s", e.stderr
                )
                return False

        # Copy temp.sh script to /opt/nfancurve
        script_dest = Path("/opt/nfancurve/temp.sh")
        script_src = resolve_config_file("nfancurve/temp.sh")

        if not script_dest.exists():
            logger.debug("Copying temp.sh to /opt/nfancurve...")
            if not script_src.exists():
                logger.error("Nfancurve script not found at %s", script_src)
                return False

            try:
                run_privileged(
                    ["cp", str(script_src), str(script_dest)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to copy nfancurve script: %s", e.stderr)
                return False
        else:
            logger.debug("temp.sh already exists in /opt/nfancurve")

        # Copy config file to /opt/nfancurve
        config_dest = Path("/opt/nfancurve/config")
        config_src = resolve_config_file("nfancurve/config")

        if not config_dest.exists():
            logger.debug("Copying config to /opt/nfancurve/config...")
            if not config_src.exists():
                logger.error("Nfancurve config not found at %s", config_src)
                return False

            try:
                run_privileged(
                    ["cp", str(config_src), str(config_dest)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to copy nfancurve config: %s", e.stderr)
                return False
        else:
            logger.debug("config already exists in /opt/nfancurve")

        # Copy systemd service file
        service_dest = Path("/etc/systemd/system/nfancurve.service")
        service_src = resolve_config_file("nfancurve/nfancurve.service")

        if not service_src.exists():
            logger.error("Nfancurve service file not found at %s", service_src)
            return False

        try:
            run_privileged(
                ["cp", str(service_src), str(service_dest)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Copied service file")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to copy nfancurve service file: %s", e.stderr)
            return False

        # Enable and start service
        logger.debug("Enabling nfancurve service...")
        try:
            run_privileged(
                ["systemctl", "daemon-reload"],
                check=True,
                capture_output=True,
                text=True,
            )
            run_privileged(
                ["systemctl", "enable", "--now", "nfancurve.service"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable nfancurve service: %s", e.stderr)
            return False

        logger.info("nfancurve setup completed successfully")
        return True

    def is_installed(self) -> bool:
        """Check if nfancurve service is enabled.

        Returns:
            True if enabled, False otherwise

        """
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", "nfancurve.service"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False
