"""i3 window manager configuration."""

import logging

from aps.wm.base import BaseWMConfig

logger = logging.getLogger(__name__)


class I3Config(BaseWMConfig):
    """i3 window manager configuration and setup."""

    def install(self, packages: list[str] | None = None) -> bool:
        """Install i3 and its dependencies.

        Args:
            packages: Optional list of additional packages to install

        Returns:
            True on success
        """
        logger.info("Installing i3 and WM-common packages...")

        if packages is None:
            packages = []

        # Default i3 packages if none provided
        if not packages:
            logger.warning("No i3 packages specified")
            return True

        # Install packages using package manager
        try:
            success, message = self.pm.install(packages)
            if success:
                logger.info("i3 and WM-common packages installation completed")
            else:
                logger.error("Failed to install packages: %s", message)
            return success
        except Exception as e:
            logger.error("Failed to install i3 packages: %s", e)
            return False

    def configure(self) -> bool:
        """Configure i3 window manager.

        Returns:
            True on success
        """
        logger.info("i3 configuration is typically done via text config files")
        logger.info("Place your config in ~/.config/i3/config")
        return True
