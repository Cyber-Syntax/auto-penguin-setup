"""Hostname configuration."""

import logging
import subprocess

from aps.hardware.base import BaseHardwareConfig

logger = logging.getLogger(__name__)


class HostnameConfig(BaseHardwareConfig):
    """Hostname configuration manager."""

    def __init__(self, distro: str):
        """Initialize hostname configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)

        """
        super().__init__(distro)

    def set_hostname(self, hostname: str) -> bool:
        """Set system hostname.

        Args:
            hostname: New hostname to set

        Returns:
            True if hostname is set successfully

        """
        self.logger.info("Changing hostname to %s...", hostname)

        if not hostname:
            self.logger.error("Hostname cannot be empty")
            return False

        try:
            result = subprocess.run(
                ["hostnamectl", "set-hostname", hostname],
                check=False,
            )
            if result.returncode != 0:
                self.logger.error("Failed to change hostname")
                return False

            self.logger.info("Hostname changed to %s.", hostname)
            return True
        except FileNotFoundError:
            self.logger.error("hostnamectl command not found")
            return False
        except Exception as e:
            self.logger.error("Failed to set hostname: %s", e)
            return False

    def configure(self, **kwargs) -> bool:
        """Configure hostname.

        Supported operations via kwargs:
            - hostname: str - New hostname to set

        Args:
            **kwargs: Configuration options

        Returns:
            True if hostname is set successfully

        """
        hostname = kwargs.get("hostname")
        if hostname:
            return self.set_hostname(hostname)

        self.logger.error("No hostname provided")
        return False
