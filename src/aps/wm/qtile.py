"""Qtile window manager configuration."""

import logging
from pathlib import Path

from aps.utils.privilege import run_privileged
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
                logger.info(
                    "Qtile and WM-common packages installation completed"
                )
            else:
                logger.error("Failed to install packages: %s", message)
            return success
        except Exception as e:
            logger.error("Failed to install Qtile packages: %s", e)
            return False

    def setup_backlight_rules(self) -> bool:
        """Copy udev rules for Qtile and backlight configuration.

        Returns:
            True on success

        """
        logger.info("Setting up udev rule for Qtile...")

        # Source paths from configs folder
        configs_dir = Path(__file__).parent.parent / "configs"
        qtile_rules_src = configs_dir / "99-qtile.rules"
        backlight_src = configs_dir / "99-backlight.conf"

        qtile_rules_dest = Path("/etc/udev/rules.d/99-qtile.rules")
        backlight_dest = Path("/etc/X11/xorg.conf.d/99-backlight.conf")

        # Ensure destination directories exist
        for dest in [qtile_rules_dest.parent, backlight_dest.parent]:
            if not dest.exists():
                logger.info("%s does not exist, creating...", dest)
                result = run_privileged(
                    ["mkdir", "-p", str(dest)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    logger.error(
                        "Failed to create %s: %s", dest, result.stderr
                    )
                    return False

        # Copy qtile udev rules
        result = run_privileged(
            ["cp", str(qtile_rules_src), str(qtile_rules_dest)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "Failed to copy udev rule for Qtile: %s", result.stderr
            )
            return False

        logger.info("Udev rule for Qtile setup completed.")

        # Copy backlight configuration
        result = run_privileged(
            ["cp", str(backlight_src), str(backlight_dest)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "Failed to copy backlight configuration: %s", result.stderr
            )
            return False

        logger.info("Backlight configuration completed.")

        # Reload udev rules
        result = run_privileged(
            ["udevadm", "control", "--reload-rules"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to reload udev rules: %s", result.stderr)
            return False

        result = run_privileged(
            ["udevadm", "trigger"],
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
        logger.info("Configuring Qtile window manager...")

        # Setup udev rules for backlight permissions
        if not self.setup_backlight_rules():
            logger.error("Failed to setup backlight rules")
            return False

        logger.info(
            "Qtile configuration is typically done via Python config files"
        )
        logger.info("Place your config.py in ~/.config/qtile/")
        return True
