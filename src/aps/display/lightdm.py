"""LightDM display manager configuration."""

import re
from pathlib import Path

from aps.core.logger import get_logger
from aps.display.base import BaseDisplayManager
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


class LightDMConfig(BaseDisplayManager):
    """LightDM display manager configuration."""

    def install(self) -> bool:
        """Install LightDM display manager.

        Returns:
            True on success

        """
        logger.info("Installing LightDM display manager...")

        success, message = self.pm.install(["lightdm"])
        if not success:
            logger.error("Failed to install LightDM: %s", message)
            return False

        logger.info("LightDM installed successfully")
        return True

    def switch_to_lightdm(self) -> bool:
        """Switch the default display manager to LightDM.

        Returns:
            True on success

        """
        logger.info("Switching to LightDM display manager...")

        # Install if not present
        if not self.install():
            return False

        # Disable GDM if active
        result = run_privileged(
            ["systemctl", "disable", "--now", "gdm"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.warning("Failed to disable GDM (it might not be installed)")

        # Enable LightDM
        result = run_privileged(
            ["systemctl", "enable", "--now", "lightdm"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to enable LightDM: %s", result.stderr)
            return False

        logger.info("Display manager switched to LightDM")
        return True

    def configure_autologin(self, username: str, session: str) -> bool:
        """Configure LightDM autologin.

        Args:
            username: Username to autologin
            session: Session name to start (e.g., "qtile", "hyprland")

        Returns:
            True on success

        """
        logger.info(
            "Setting up LightDM autologin for user %s with session %s",
            username,
            session,
        )

        config_file = Path("/etc/lightdm/lightdm.conf")

        if not config_file.exists():
            logger.error(
                "LightDM configuration file not found: %s", config_file
            )
            return False

        # Create backup
        backup_file = Path(str(config_file) + ".bak")
        if not backup_file.exists():
            result = run_privileged(
                ["cp", str(config_file), str(backup_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("Failed to create backup: %s", result.stderr)
                return False

        # Read current config
        result = run_privileged(
            ["cat", str(config_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to read config file: %s", result.stderr)
            return False

        content = result.stdout

        # Modify configuration
        if "[Seat:*]" in content:
            # Modify existing [Seat:*] section
            logger.info("Modifying existing LightDM configuration...")
            new_content = self._modify_seat_section(content, username, session)
        else:
            # Add new [Seat:*] section
            logger.info("Adding new LightDM autologin configuration...")
            new_content = f"{content}\n\n[Seat:*]\nautologin-user={username}\nautologin-session={session}\n"

        # Write new configuration
        result = run_privileged(
            ["tee", str(config_file)],
            stdin_input=new_content,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to write configuration: %s", result.stderr)
            return False

        logger.info("LightDM autologin configured successfully")
        return True

    def _modify_seat_section(
        self, content: str, username: str, session: str
    ) -> str:
        """Modify the [Seat:*] section in LightDM config.

        Args:
            content: Current config file content
            username: Username for autologin
            session: Session name

        Returns:
            Modified configuration content

        """
        lines = content.split("\n")
        new_lines = []
        in_seat_section = False
        autologin_user_modified = False
        autologin_session_modified = False

        for line in lines:
            # Check for section headers
            if line.strip().startswith("["):
                if in_seat_section and not autologin_user_modified:
                    new_lines.append(f"autologin-user={username}")
                    autologin_user_modified = True
                if in_seat_section and not autologin_session_modified:
                    new_lines.append(f"autologin-session={session}")
                    autologin_session_modified = True

                in_seat_section = line.strip() == "[Seat:*]"
                new_lines.append(line)
                continue

            # Modify autologin lines in [Seat:*] section
            if in_seat_section:
                if re.match(r"^#?autologin-user=", line):
                    new_lines.append(f"autologin-user={username}")
                    autologin_user_modified = True
                    continue
                if re.match(r"^#?autologin-session=", line):
                    new_lines.append(f"autologin-session={session}")
                    autologin_session_modified = True
                    continue

            new_lines.append(line)

        # Add autologin settings if they weren't found in [Seat:*]
        if in_seat_section:
            if not autologin_user_modified:
                new_lines.append(f"autologin-user={username}")
            if not autologin_session_modified:
                new_lines.append(f"autologin-session={session}")

        return "\n".join(new_lines)
