"""Brave Browser installer module."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from aps.core.logger import get_logger

from .base import BaseInstaller

logger = get_logger(__name__)


class BraveInstaller(BaseInstaller):
    """Installer for Brave Browser with keyring configuration."""

    def install(self) -> bool:
        """Install Brave Browser and configure it to use basic password store.

        Returns:
            bool: True if installation was successful, False otherwise.

        """
        logger.info("Installing Brave Browser...")

        if self._is_installed():
            logger.info("Brave Browser is already installed")
        else:
            logger.info("Installing Brave Browser for %s...", self.distro)

            if not shutil.which("curl"):
                logger.error("curl is required for Brave installation")
                return False

            if not self._install_brave():
                logger.error("Failed to install Brave Browser")
                return False

            logger.info("Brave Browser installed successfully")

        if not self._disable_keyring():
            logger.warning(
                "Failed to modify Brave desktop file, but continuing"
            )

        return True

    def _is_installed(self) -> bool:
        """Check if Brave is already installed.

        Returns:
            bool: True if Brave is installed, False otherwise.

        """
        return (
            shutil.which("brave") is not None
            or shutil.which("brave-browser") is not None
        )

    def _install_brave(self) -> bool:
        """Install Brave using the official install script.

        Returns:
            bool: True if installation was successful, False otherwise.

        """
        try:
            # Download and execute official Brave install script
            curl_process = subprocess.Popen(
                ["curl", "-fsS", "https://dl.brave.com/install.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            bash_process = subprocess.Popen(
                ["bash"],
                stdin=curl_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if curl_process.stdout:
                curl_process.stdout.close()

            _, stderr = bash_process.communicate()

            if bash_process.returncode != 0:
                logger.error("Installation script failed: %s", stderr.decode())
                return False

            return True

        except Exception as e:
            logger.error("Error installing Brave: %s", e)
            return False

    def _disable_keyring(self) -> bool:
        """Modify Brave desktop file to use basic password store.

        Returns:
            bool: True if desktop file was modified successfully, False otherwise.

        """
        xdg_data_home = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
        user_desktop_dir = Path(xdg_data_home) / "applications"
        user_desktop_file = user_desktop_dir / "brave-browser.desktop"

        system_desktop_file = self._get_system_desktop_file()

        user_desktop_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("User desktop directory: %s", user_desktop_dir)

        if not user_desktop_file.exists():
            if system_desktop_file.exists():
                logger.info("Copying system desktop file to user directory...")
                shutil.copy2(system_desktop_file, user_desktop_file)
            else:
                logger.error(
                    "Brave desktop file not found at: %s", system_desktop_file
                )
                return False

        if self._is_already_modified(user_desktop_file):
            logger.info("Desktop file already modified - no changes needed")
            return True

        backup_file = Path(f"{user_desktop_file}.bak")
        logger.debug("Creating backup at %s", backup_file)
        try:
            shutil.copy2(user_desktop_file, backup_file)
        except Exception as e:
            logger.warning(
                "Failed to create backup file: %s, but proceeding anyway", e
            )

        if not self._modify_desktop_file(user_desktop_file):
            logger.error("Failed to modify desktop file")
            if backup_file.exists():
                logger.debug("Restoring from backup")
                shutil.copy2(backup_file, user_desktop_file)
            return False

        logger.info("Successfully modified Brave desktop file")
        return True

    def _get_system_desktop_file(self) -> Path:
        """Get the path to the system Brave desktop file.

        Returns:
            Path: Path to the system desktop file.

        """
        standard_path = Path("/usr/share/applications/brave-browser.desktop")

        if self.distro in ("fedora", "debian", "ubuntu"):
            return standard_path

        if self.distro in ("arch", "archlinux", "manjaro", "cachyos"):
            # Try different locations for Arch-based distros
            if standard_path.exists():
                return standard_path

            opt_path = Path("/opt/brave-bin/brave-browser.desktop")
            if opt_path.exists():
                return opt_path

            return standard_path

        return Path("/usr/share/applications/brave-browser.desktop")

    def _is_already_modified(self, desktop_file: Path) -> bool:
        """Check if desktop file is already modified.

        Args:
            desktop_file: Path to the desktop file.

        Returns:
            bool: True if already modified, False otherwise.

        """
        try:
            content = desktop_file.read_text()
            return "--password-store=basic" in content
        except Exception as e:
            logger.error("Error reading desktop file: %s", e)
            return False

    def _modify_desktop_file(self, desktop_file: Path) -> bool:
        """Modify Exec lines in desktop file to add password store flag.

        Args:
            desktop_file: Path to the desktop file.

        Returns:
            bool: True if modification was successful, False otherwise.

        """
        try:
            content = desktop_file.read_text()
            original_content = content
            modified = False

            # Pattern 1: /usr/bin/brave-browser-stable
            if re.search(
                r"^Exec=/usr/bin/brave-browser-stable", content, re.MULTILINE
            ):
                logger.debug(
                    "Modifying Exec lines with /usr/bin/brave-browser-stable"
                )
                content = re.sub(
                    r"^Exec=/usr/bin/brave-browser-stable(.*)$",
                    r"Exec=/usr/bin/brave-browser-stable --password-store=basic\1",
                    content,
                    flags=re.MULTILINE,
                )
                modified = True

            # Pattern 2: bare 'brave' command
            if re.search(r"^Exec=brave(\s|$)", content, re.MULTILINE):
                logger.debug("Modifying Exec lines with bare 'brave' command")
                content = re.sub(
                    r"^Exec=brave(\s.*)$",
                    r"Exec=brave --password-store=basic\1",
                    content,
                    flags=re.MULTILINE,
                )
                content = re.sub(
                    r"^Exec=brave$",
                    r"Exec=brave --password-store=basic",
                    content,
                    flags=re.MULTILINE,
                )
                modified = True

            if not modified:
                logger.error(
                    "Failed to modify desktop file - no matching Exec lines found"
                )
                logger.debug("Desktop file Exec lines:")
                for line in content.split("\n"):
                    if line.startswith("Exec="):
                        logger.debug("  %s", line)
                return False

            desktop_file.write_text(content)
            return content != original_content

        except Exception as e:
            logger.error("Error modifying desktop file: %s", e)
            return False
