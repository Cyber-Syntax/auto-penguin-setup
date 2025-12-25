"""File operation utilities for hardware and system configuration."""

import shutil
from pathlib import Path

from aps.core.logger import get_logger

logger = get_logger(__name__)


def copy_config_file(source: str, destination: str) -> bool:
    """Copy configuration file to destination.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        True if copy succeeds, False otherwise

    """
    try:
        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)
    except OSError:
        logger.exception("Failed to copy %s to %s", source, destination)
        return False
    else:
        logger.info("Copied %s to %s", source, destination)
        return True
