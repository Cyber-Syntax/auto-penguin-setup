"""Package manager optimization module."""

import logging
import subprocess
from pathlib import Path

from .base import BaseSystemConfig

logger = logging.getLogger(__name__)


class PackageManagerOptimizer(BaseSystemConfig):
    """Optimize package manager configuration across distributions."""

    def configure(self) -> bool:
        """Optimize package manager configuration based on distribution.

        Returns:
            bool: True if optimization was successful, False otherwise.
        """
        logger.info("Optimizing package manager configuration for %s...", self.distro)

        if self.distro in ("fedora", "rhel", "centos", "nobara"):
            success = self._optimize_dnf()
        elif self.distro in ("arch", "archlinux", "manjaro", "cachyos"):
            success = self._optimize_pacman()
        elif self.distro in ("debian", "ubuntu", "linuxmint", "pop"):
            success = self._optimize_apt()
        else:
            logger.error("Unsupported distribution: %s", self.distro)
            return False

        if success:
            logger.info("Package manager optimization completed successfully")
        return success

    def _optimize_dnf(self) -> bool:
        """Optimize DNF configuration for Fedora-based systems.

        Returns:
            bool: True if optimization was successful, False otherwise.
        """
        logger.info("Configuring DNF for improved performance...")
        dnf_conf = Path("/etc/dnf/dnf.conf")

        if not self._create_backup(dnf_conf):
            logger.error("Failed to create backup of %s", dnf_conf)
            return False

        settings = {
            "max_parallel_downloads": "20",
            "pkg_gpgcheck": "True",
            "skip_if_unavailable": "True",
            "timeout": "15",
            "retries": "5",
        }

        for key, value in settings.items():
            if not self._add_or_update_setting(dnf_conf, key, value):
                return False

        logger.info("DNF configuration updated successfully")
        return True

    def _optimize_pacman(self) -> bool:
        """Optimize pacman configuration for Arch-based systems.

        Returns:
            bool: True if optimization was successful, False otherwise.
        """
        logger.info("Configuring pacman for improved performance...")
        pacman_conf = Path("/etc/pacman.conf")

        if not self._create_backup(pacman_conf):
            logger.error("Failed to create backup of %s", pacman_conf)
            return False

        settings = {"ParallelDownloads": "20"}

        for key, value in settings.items():
            if not self._add_or_update_setting(pacman_conf, key, value, separator=" = "):
                return False

        if not self._enable_pacman_color(pacman_conf):
            return False

        logger.info("Pacman configuration updated successfully")
        return True

    def _optimize_apt(self) -> bool:
        """Optimize APT configuration for Debian-based systems.

        Returns:
            bool: True if optimization was successful, False otherwise.
        """
        logger.info("Configuring APT for improved performance...")
        apt_conf = Path("/etc/apt/apt.conf.d/99custom")

        apt_config = """APT::Acquire::Queue-Mode "host";
APT::Acquire::Retries "3";
Acquire::http::Timeout "15";
Acquire::https::Timeout "15";
"""

        try:
            result = subprocess.run(
                ["sudo", "tee", str(apt_conf)],
                input=apt_config,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error("Failed to create APT configuration file")
                return False

            logger.info("APT configuration updated successfully")
            return True

        except Exception as e:
            logger.error("Error configuring APT: %s", e)
            return False

    def _create_backup(self, config_file: Path) -> bool:
        """Create a backup of the configuration file if it doesn't exist.

        Args:
            config_file: Path to the configuration file.

        Returns:
            bool: True if backup was created or already exists, False on error.
        """
        backup_file = Path(f"{config_file}.bak")

        if backup_file.exists():
            logger.debug("Backup already exists: %s", backup_file)
            return True

        try:
            result = subprocess.run(
                ["sudo", "cp", str(config_file), str(backup_file)],
                capture_output=True,
                check=False,
            )

            if result.returncode != 0:
                return False

            logger.debug("Created backup: %s", backup_file)
            return True

        except Exception as e:
            logger.error("Error creating backup: %s", e)
            return False

    def _add_or_update_setting(
        self, config_file: Path, key: str, value: str, separator: str = "="
    ) -> bool:
        """Add or update a setting in a configuration file.

        Args:
            config_file: Path to the configuration file.
            key: Setting key.
            value: Setting value.
            separator: Separator between key and value (default: "=").

        Returns:
            bool: True if setting was added/updated successfully, False otherwise.
        """
        try:
            content = config_file.read_text()
            setting_line = f"{key}{separator}{value}"

            # Check if key exists
            import re

            pattern = rf"^{re.escape(key)}\s*{re.escape(separator.strip())}\s*(.+)$"
            match = re.search(pattern, content, re.MULTILINE)

            if match:
                current_value = match.group(1).strip()
                if current_value == value:
                    logger.debug("%s is already set to %s", key, value)
                    return True

                # Update existing setting
                logger.debug("Updating %s from %s to %s", key, current_value, value)
                new_content = re.sub(pattern, setting_line, content, flags=re.MULTILINE)

                result = subprocess.run(
                    ["sudo", "tee", str(config_file)],
                    input=new_content,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode != 0:
                    logger.error("Failed to update setting: %s", key)
                    return False

                logger.info("Updated %s to %s", key, value)
                return True

            # Add new setting
            logger.debug("Adding setting: %s", setting_line)
            result = subprocess.run(
                ["sudo", "tee", "-a", str(config_file)],
                input=f"\n{setting_line}\n",
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error("Failed to add setting: %s", key)
                return False

            logger.info("Added %s = %s", key, value)
            return True

        except Exception as e:
            logger.error("Error adding/updating setting %s: %s", key, e)
            return False

    def _enable_pacman_color(self, pacman_conf: Path) -> bool:
        """Enable color output in pacman configuration.

        Args:
            pacman_conf: Path to pacman.conf.

        Returns:
            bool: True if color was enabled successfully, False otherwise.
        """
        try:
            content = pacman_conf.read_text()

            if "^Color$" in content:
                logger.debug("Color output already enabled")
                return True

            if "#Color" in content:
                logger.debug("Uncommenting Color option in pacman")
                new_content = content.replace("#Color", "Color")
            else:
                logger.debug("Adding Color option to pacman")
                new_content = content + "\nColor\n"

            result = subprocess.run(
                ["sudo", "tee", str(pacman_conf)],
                input=new_content,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error("Failed to enable color output")
                return False

            logger.info("Enabled color output in pacman")
            return True

        except Exception as e:
            logger.error("Error enabling pacman color: %s", e)
            return False
