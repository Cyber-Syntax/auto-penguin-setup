"""Setup command implementation."""

import logging
from argparse import Namespace

from aps.core.distro import detect_distro
from aps.core.setup import SetupError, SetupManager
from aps.utils.privilege import ensure_sudo

logger = logging.getLogger(__name__)


def cmd_setup(args: Namespace) -> None:
    """Handle 'aps setup' command."""
    # Pre-authenticate sudo for privileged operations
    ensure_sudo()

    distro_info = detect_distro()
    manager = SetupManager(distro_info)

    try:
        manager.setup_component(args.component)
        logger.info("%s setup completed successfully", args.component)
    except SetupError as e:
        logger.error("Setup failed: %s", e)
