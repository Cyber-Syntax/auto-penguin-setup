"""Qtile window manager configuration."""

import logging
import subprocess
from pathlib import Path

from aps.wm.base import BaseWMConfig

logger = logging.getLogger(__name__)


class QtileConfig(BaseWMConfig):
    """Qtile window manager configuration and setup."""

    def install(self, packages: list[str] | None = None) -> bool:
        """Install Qtile and its dependencies.

        Args:
            packages: Optional list of additional packages to install

        Returns:
            True on success
        """
        logger.info("Installing Qtile and WM-common packages...")

        if packages is None:
            packages = []

        # Default Qtile packages if none provided
        if not packages:
            logger.warning("No Qtile packages specified")
            return True

        # Install packages using package manager
        try:
            success, message = self.pm.install(packages)
            if success:
                logger.info("Qtile and WM-common packages installation completed")
            else:
                logger.error("Failed to install packages: %s", message)
            return success
        except Exception as e:
            logger.error("Failed to install Qtile packages: %s", e)
            return False

    def setup_backlight_rules(self, qtile_rules_src: str | Path, backlight_src: str | Path) -> bool:
        """Setup udev rules for backlight control on Qtile.

        Args:
            qtile_rules_src: Path to qtile.rules source file
            backlight_src: Path to backlight.conf source file

        Returns:
            True on success
        """
        logger.info("Setting up udev rule for Qtile...")

        qtile_rules_dest = Path("/etc/udev/rules.d/99-qtile.rules")
        backlight_dest = Path("/etc/X11/xorg.conf.d/99-backlight.conf")

        # Ensure destination directories exist
        for dest in [qtile_rules_dest.parent, backlight_dest.parent]:
            if not dest.exists():
                logger.info("%s does not exist, creating...", dest)
                result = subprocess.run(
                    ["sudo", "mkdir", "-p", str(dest)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    logger.error("Failed to create %s: %s", dest, result.stderr)
                    return False

        # Copy qtile udev rules
        result = subprocess.run(
            ["sudo", "cp", str(qtile_rules_src), str(qtile_rules_dest)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to copy udev rule for Qtile: %s", result.stderr)
            return False

        logger.info("Udev rule for Qtile setup completed.")

        # Copy backlight configuration
        result = subprocess.run(
            ["sudo", "cp", str(backlight_src), str(backlight_dest)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to copy backlight configuration: %s", result.stderr)
            return False

        logger.info("Backlight configuration completed.")

        # Reload udev rules
        result = subprocess.run(
            ["sudo", "udevadm", "control", "--reload-rules"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to reload udev rules: %s", result.stderr)
            return False

        result = subprocess.run(
            ["sudo", "udevadm", "trigger"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to trigger udev: %s", result.stderr)
            return False

        logger.info("Udev rules reloaded.")
        return True

    def configure(self) -> bool:
        """Configure Qtile window manager.

        Returns:
            True on success
        """
        logger.info("Qtile configuration is typically done via Python config files")
        logger.info("Place your config.py in ~/.config/qtile/")
        return True
