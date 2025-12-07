"""GRUB bootloader configuration."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .base import BaseSystemConfig

logger = logging.getLogger(__name__)


class BootloaderConfig(BaseSystemConfig):
    """Configure GRUB bootloader settings."""

    def __init__(self) -> None:
        """Initialize bootloader configuration."""
        super().__init__()
        self.grub_file = Path("/etc/default/grub")

    def configure(self) -> bool:
        """Configure GRUB timeout (main entry point).

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        return self.set_timeout(0)

    def set_timeout(self, timeout: int = 0) -> bool:
        """Configure GRUB timeout setting.

        Args:
            timeout: Timeout value in seconds (default: 0)

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        logger.info("Configuring GRUB timeout to %d seconds...", timeout)

        # Check if GRUB is installed
        if not self.grub_file.exists():
            logger.warning("GRUB configuration not found, skipping GRUB timeout setup")
            return True

        # Create backup before modifying
        if not self._create_backup():
            logger.error("Backup failed, aborting GRUB timeout setup")
            return False

        # Update or add GRUB_TIMEOUT setting
        try:
            content = self.grub_file.read_text()

            if "GRUB_TIMEOUT=" in content:
                logger.debug("Updating existing GRUB_TIMEOUT setting...")
                # Replace existing GRUB_TIMEOUT line
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if line.startswith("GRUB_TIMEOUT="):
                        new_lines.append(f"GRUB_TIMEOUT={timeout}")
                    else:
                        new_lines.append(line)
                new_content = "\n".join(new_lines)
            else:
                logger.debug("Adding new GRUB_TIMEOUT setting...")
                # Add after GRUB_CMDLINE_LINUX if exists, otherwise at the end
                if "GRUB_CMDLINE_LINUX=" in content:
                    lines = content.split("\n")
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if line.startswith("GRUB_CMDLINE_LINUX="):
                            new_lines.append(f"GRUB_TIMEOUT={timeout}")
                    new_content = "\n".join(new_lines)
                else:
                    new_content = content + f"\nGRUB_TIMEOUT={timeout}\n"

            # Write updated content
            with subprocess.Popen(
                ["sudo", "tee", str(self.grub_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            ) as proc:
                proc.communicate(input=new_content)

            # Verify the change
            updated_content = self.grub_file.read_text()
            if f"GRUB_TIMEOUT={timeout}" not in updated_content:
                logger.error("Failed to set GRUB_TIMEOUT to %d", timeout)
                return False

            logger.info("GRUB_TIMEOUT set to %d successfully", timeout)

        except (OSError, PermissionError) as e:
            logger.error("Failed to update GRUB configuration: %s", e)
            return False

        # Regenerate GRUB configuration
        if not self._regenerate_config():
            logger.error("Failed to regenerate GRUB configuration")
            logger.warning("You may need to manually run the appropriate command:")
            logger.warning("  Fedora: sudo grub2-mkconfig -o /boot/grub2/grub.cfg")
            logger.warning("  Arch:   sudo grub-mkconfig -o /boot/grub/grub.cfg")
            logger.warning("  Debian: sudo update-grub")
            return False

        logger.info("GRUB timeout configuration completed successfully")
        return True

    def _create_backup(self) -> bool:
        """Create backup of GRUB configuration file.

        Returns:
            bool: True if backup was successful, False otherwise.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = Path(f"{self.grub_file}.bak.{timestamp}")

        logger.info("Creating backup of GRUB configuration...")

        if not self.grub_file.exists():
            logger.error("GRUB configuration file not found: %s", self.grub_file)
            return False

        result = subprocess.run(
            ["sudo", "cp", "-p", str(self.grub_file), str(backup_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to create backup of GRUB configuration")
            return False

        logger.info("Backup created: %s", backup_file)
        return True

    def _regenerate_config(self) -> bool:
        """Regenerate GRUB configuration based on distribution.

        Returns:
            bool: True if regeneration was successful, False otherwise.
        """
        logger.info("Regenerating GRUB configuration for %s...", self.distro)

        if self.distro == "fedora":
            # Fedora uses grub2-mkconfig and /boot/grub2/grub.cfg
            cmd = ["sudo", "grub2-mkconfig", "-o", "/boot/grub2/grub.cfg"]
            check_cmd = "grub2-mkconfig"
        elif self.distro == "arch":
            # Arch uses grub-mkconfig and /boot/grub/grub.cfg
            cmd = ["sudo", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"]
            check_cmd = "grub-mkconfig"
        elif self.distro == "debian":
            # Debian/Ubuntu uses update-grub (wrapper for grub-mkconfig)
            # Try update-grub first, fall back to grub-mkconfig
            check_result = subprocess.run(
                ["which", "update-grub"], capture_output=True, check=False
            )
            if check_result.returncode == 0:
                cmd = ["sudo", "update-grub"]
            else:
                check_result = subprocess.run(
                    ["which", "grub-mkconfig"], capture_output=True, check=False
                )
                if check_result.returncode == 0:
                    cmd = ["sudo", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"]
                else:
                    logger.error("Neither update-grub nor grub-mkconfig found")
                    return False
            check_cmd = None  # Already verified above
        else:
            logger.error("Unsupported distribution for GRUB configuration: %s", self.distro)
            return False

        # Verify command exists (if not already checked)
        if check_cmd:
            check_result = subprocess.run(["which", check_cmd], capture_output=True, check=False)
            if check_result.returncode != 0:
                logger.error("%s command not found", check_cmd)
                return False

        # Run the GRUB config regeneration command
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            logger.error("Failed to regenerate GRUB configuration")
            if result.stderr:
                logger.debug("Error output: %s", result.stderr)
            return False

        logger.info("GRUB configuration regenerated successfully")
        return True
