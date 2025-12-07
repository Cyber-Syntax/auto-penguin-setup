"""Intel graphics configuration."""

import logging
import os

from aps.hardware.base import BaseHardwareConfig

logger = logging.getLogger(__name__)


class IntelConfig(BaseHardwareConfig):
    """Intel graphics configuration manager."""

    def __init__(self, distro: str):
        """Initialize Intel configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)
        """
        super().__init__(distro)

    def setup_xorg(self, config_source: str = "./configs/20-intel.conf") -> bool:
        """Setup Xorg configuration for Intel graphics.

        Args:
            config_source: Path to Intel Xorg configuration file

        Returns:
            True if setup succeeds, False otherwise
        """
        self.logger.info("Setting up xorg configuration...")

        destination = "/etc/X11/xorg.conf.d/20-intel.conf"

        if not os.path.exists(config_source):
            self.logger.error("Intel configuration file not found: %s", config_source)
            return False

        if self._copy_config_file(config_source, destination):
            self.logger.info("Xorg configuration completed.")
            return True

        return False

    def configure(self, **kwargs) -> bool:
        """Configure Intel hardware.

        Supported operations via kwargs:
            - xorg: bool - Setup Xorg configuration
            - config_source: str - Path to Intel config file (default: ./configs/20-intel.conf)

        Args:
            **kwargs: Configuration options

        Returns:
            True if all requested operations succeed
        """
        if kwargs.get("xorg", False):
            config_source = kwargs.get("config_source", "./configs/20-intel.conf")
            return self.setup_xorg(config_source)

        return True
