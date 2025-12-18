"""Sudoers configuration management."""

import logging
from datetime import datetime
from pathlib import Path

from aps.utils.privilege import run_privileged

from .base import BaseSystemConfig

logger = logging.getLogger(__name__)


class SudoersConfig(BaseSystemConfig):
    """Configure sudoers file for passwordless operations."""

    def __init__(self) -> None:
        """Initialize sudoers configuration."""
        super().__init__()
        self.sudoers_file = Path("/etc/sudoers")

    def configure(self) -> bool:
        """Configure all sudoers settings.

        Returns:
            bool: True if all configurations were successful, False otherwise.

        """
        logger.info("Starting sudoers configuration...")

        errors = 0

        # Setup terminal timeout configuration
        if not self.configure_terminal_timeout():
            logger.warning("Terminal timeout sudoers setup failed")
            errors += 1

        if errors == 0:
            logger.info("All sudoers configurations completed successfully")
            return True
        logger.warning("Sudoers setup completed with %d error(s)", errors)
        return False

    def configure_terminal_timeout(self) -> bool:
        """Configure terminal password prompt timeout.

        Returns:
            bool: True if configuration was successful, False otherwise.

        """
        marker_start = "# BEGIN auto-penguin-setup: terminal-timeout"
        marker_end = "# END auto-penguin-setup: terminal-timeout"

        logger.info(
            "Configuring sudoers for extended terminal password timeout..."
        )

        # Create backup before modifying
        if not self._create_backup():
            logger.error(
                "Backup failed, aborting terminal timeout sudoers setup"
            )
            return False

        # Configuration to add
        config = f"""{marker_start}
## Increase timeout on terminal password prompt
Defaults timestamp_type=global
Defaults env_reset,timestamp_timeout=20
{marker_end}
"""

        return self._update_sudoers_section(marker_start, marker_end, config)

    def _update_sudoers_section(
        self, marker_start: str, marker_end: str, config: str
    ) -> bool:
        """Update a section in the sudoers file.

        Args:
            marker_start: Start marker for the section
            marker_end: End marker for the section
            config: Configuration content to add

        Returns:
            bool: True if update was successful, False otherwise.

        """
        try:
            # Read current content
            content = self.sudoers_file.read_text()

            # Remove existing section if present
            if marker_start in content:
                logger.info("Removing existing configuration...")
                lines = content.split("\n")
                new_lines = []
                skip = False
                for line in lines:
                    if marker_start in line:
                        skip = True
                    elif marker_end in line:
                        skip = False
                        continue
                    if not skip:
                        new_lines.append(line)
                content = "\n".join(new_lines)

            # Add new configuration
            new_content = content.rstrip() + "\n" + config

            # Write updated content
            run_privileged(
                ["tee", str(self.sudoers_file)],
                stdin_input=new_content,
                capture_output=True,
                text=True,
                check=False,
            )

            # Validate sudoers file syntax
            if not self._validate_sudoers():
                logger.error(
                    "Sudoers file syntax validation failed, restoring from backup"
                )
                self._restore_latest_backup()
                return False

            logger.info("Sudoers configuration updated successfully")
            return True

        except (OSError, PermissionError) as e:
            logger.error("Failed to update sudoers file: %s", e)
            return False

    def _create_backup(self) -> bool:
        """Create backup of sudoers file.

        Returns:
            bool: True if backup was successful, False otherwise.

        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = Path(f"{self.sudoers_file}.bak.{timestamp}")

        logger.info("Creating backup of sudoers file...")

        result = run_privileged(
            ["cp", "-p", str(self.sudoers_file), str(backup_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to create backup of sudoers file")
            return False

        logger.info("Backup created: %s", backup_file)
        return True

    def _validate_sudoers(self) -> bool:
        """Validate sudoers file syntax.

        Returns:
            bool: True if validation passed, False otherwise.

        """
        result = run_privileged(
            ["visudo", "-c", "-f", str(self.sudoers_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        return result.returncode == 0

    def _restore_latest_backup(self) -> bool:
        """Restore the latest backup of the sudoers file.

        Returns:
            bool: True if restore was successful, False otherwise.

        """
        # Find latest backup
        result = run_privileged(
            ["ls", "-t", f"{self.sudoers_file}.bak.*"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            logger.error("No backup files found")
            return False

        latest_backup = result.stdout.strip().split("\n")[0]

        # Restore backup
        restore_result = run_privileged(
            ["cp", latest_backup, str(self.sudoers_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        if restore_result.returncode != 0:
            logger.error("Failed to restore backup")
            return False

        logger.info("Restored from backup: %s", latest_backup)
        return True
