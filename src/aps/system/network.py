"""Network configuration management."""

import logging
import shutil
import subprocess
from pathlib import Path

from .base import BaseSystemConfig

logger = logging.getLogger(__name__)


class NetworkConfig(BaseSystemConfig):
    """Configure network settings including TCP BBR."""

    def configure(self) -> bool:
        """Configure TCP BBR for improved network performance."""
        logger.info("Setting up TCP BBR configuration...")

        source_file = Path("configs/99-tcp-bbr.conf")
        dest_file = Path("/etc/sysctl.d/99-tcp-bbr.conf")

        if not source_file.exists():
            logger.error("TCP BBR configuration file not found: %s", source_file)
            return False

        try:
            # Copy configuration file
            shutil.copy2(source_file, dest_file)
            logger.info("TCP BBR configuration copied to %s", dest_file)

            # Reload sysctl settings
            result = subprocess.run(
                ["sudo", "sysctl", "--system"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("Failed to reload sysctl settings")
                return False

            logger.info("Network configuration completed successfully")
            return True

        except (OSError, PermissionError) as e:
            logger.error("Failed to configure TCP BBR: %s", e)
            return False
