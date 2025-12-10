"""Setup command implementation."""

import logging
from argparse import Namespace

from aps.core.distro import detect_distro
from aps.core.setup import SetupError, SetupManager

logger = logging.getLogger(__name__)


def cmd_setup(args: Namespace) -> None:
    """Handle 'aps setup' command."""
    distro_info = detect_distro()
    manager = SetupManager(distro_info)

    try:
        manager.setup_component(args.component)
        logger.info("%s setup completed successfully", args.component)
    except SetupError as e:
        logger.error("Setup failed: %s", e)
