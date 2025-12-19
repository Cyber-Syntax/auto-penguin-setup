"""SDDM display manager configuration."""

import logging
import subprocess
from pathlib import Path

from aps.display.base import BaseDisplayManager
from aps.utils.privilege import run_privileged

logger = logging.getLogger(__name__)


class SDDMConfig(BaseDisplayManager):
    """SDDM display manager configuration."""

    def install(self) -> bool:
        """Install SDDM display manager.

        Returns:
            True on success

        """
        logger.info("Installing SDDM display manager...")

        # Check if SDDM is already installed
        result = subprocess.run(
            ["rpm", "-q", "sddm"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            logger.info("SDDM is already installed")
            return True

        # Install SDDM
        success, message = self.pm.install(["sddm"])
        if not success:
            logger.error("Failed to install SDDM: %s", message)
            return False

        logger.info("SDDM installed successfully")
        return True

    def switch_to_sddm(self) -> bool:
        """Switch the default display manager to SDDM.

        Returns:
            True on success

        """
        logger.info("Switching to SDDM display manager...")

        # Install if not present
        if not self.install():
            return False

        # Find and disable current display manager
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=active",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            # Look for other display managers
            for dm in ["gdm", "lightdm", "lxdm", "xdm"]:
                if f"{dm}.service" in result.stdout:
                    logger.info("Disabling current display manager: %s", dm)
                    run_privileged(
                        ["systemctl", "disable", "--now", f"{dm}.service"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

        # Enable SDDM
        logger.info("Enabling SDDM service...")
        result = run_privileged(
            ["systemctl", "enable", "--now", "sddm.service"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to enable SDDM service: %s", result.stderr)
            return False

        logger.info("SDDM is now set as the default display manager")
        logger.info(
            "To select your session, choose it from the SDDM session menu at login"
        )
        logger.info(
            "You should reboot your system for the changes to take effect"
        )
        return True

    def configure_autologin(self, username: str, session: str) -> bool:
        """Configure SDDM autologin.

        Args:
            username: Username to autologin
            session: Session name to start (e.g., "qtile", "plasma")

        Returns:
            True on success

        """
        logger.info(
            "Setting up SDDM autologin for user %s with session %s...",
            username,
            session,
        )

        config_file = Path("/etc/sddm.conf")
        config_dir = Path("/etc/sddm.conf.d")

        # Create SDDM config if it doesn't exist
        if not config_file.exists() and not config_dir.exists():
            logger.info("Creating SDDM configuration directory...")
            result = run_privileged(
                ["mkdir", "-p", str(config_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error(
                    "Failed to create SDDM config directory: %s", result.stderr
                )
                return False

        # Create autologin config in drop-in directory
        autologin_conf = config_dir / "autologin.conf"
        autologin_content = f"""[Autologin]
User={username}
Session={session}
"""

        result = run_privileged(
            ["tee", str(autologin_conf)],
            stdin_input=autologin_content,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "Failed to write SDDM autologin configuration: %s",
                result.stderr,
            )
            return False

        logger.info("SDDM autologin configured successfully")
        return True
