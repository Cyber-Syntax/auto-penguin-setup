"""Upgrade command implementation."""

import os
import shutil
import sys
from argparse import Namespace

from aps.core.logger import get_logger

logger = get_logger(__name__)


def cmd_upgrade(args: Namespace) -> None:
    """Upgrade aps CLI tool using uv.

    This command uses os.execvp() to replace the current process with the
    uv tool upgrade command, ensuring a clean upgrade without running
    partially-updated code.

    Args:
        args: Command line arguments (currently unused, for future
            enhancements)

    """
    logger.info("Checking for UV availability...")

    if not shutil.which("uv"):
        logger.error("UV not found. Please install UV first.")
        logger.error(
            "Visit https://docs.astral.sh/uv/ for installation instructions"
        )
        sys.exit(1)

    logger.info("Upgrading auto-penguin-setup to latest version...")
    logger.info("Running: uv tool upgrade auto-penguin-setup")

    # Replace current process with upgrade command
    # os.execvp will not return if successful
    # If it returns, an error occurred
    try:
        os.execvp("uv", ["uv", "tool", "upgrade", "auto-penguin-setup"])
    except OSError as e:
        logger.error("Failed to execute upgrade command: %s", e)
        sys.exit(1)
