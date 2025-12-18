"""Touchpad configuration."""

import logging
import os

from aps.hardware.base import BaseHardwareConfig
from aps.utils.paths import resolve_config_file

logger = logging.getLogger(__name__)


class TouchpadConfig(BaseHardwareConfig):
    """Touchpad configuration manager."""

    def __init__(self, distro: str):
        """Initialize touchpad configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)
        """
        super().__init__(distro)

    def setup(self, config_source: str | None = None) -> bool:
        """Setup touchpad configuration.

        Args:
            config_source: Path to touchpad configuration file

        Returns:
            True if setup succeeds, False otherwise
        """
        if config_source is None:
            config_source = str(resolve_config_file("99-touchpad.conf"))

        self.logger.info("Setting up touchpad configuration...")

        destination = "/etc/X11/xorg.conf.d/99-touchpad.conf"

        if not os.path.exists(config_source):
            self.logger.error(
                "Touchpad configuration file not found: %s", config_source
            )
            return False

        if self._copy_config_file(config_source, destination):
            self.logger.info("Touchpad configuration completed.")
            return True

        return False

    def configure(self, **kwargs) -> bool:
        """Configure touchpad.

        Supported operations via kwargs:
            - setup: bool - Setup touchpad configuration
            - config_source: str - Path to touchpad config file (default: resolved from package)

        Args:
            **kwargs: Configuration options

        Returns:
            True if all requested operations succeed
        """
        if kwargs.get("setup", False):
            config_source = kwargs.get(
                "config_source", str(resolve_config_file("99-touchpad.conf"))
            )
            return self.setup(config_source)

        return True
