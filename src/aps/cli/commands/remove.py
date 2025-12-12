"""Remove command implementation."""

import logging
from argparse import Namespace

from aps.cli.utils import get_tracking_db_path
from aps.core.distro import detect_distro
from aps.core.package_manager import get_package_manager
from aps.core.tracking import PackageTracker

logger = logging.getLogger(__name__)


def cmd_remove(args: Namespace) -> None:
    """Handle 'aps remove' command."""
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    tracker = PackageTracker(get_tracking_db_path())

    for pkg in args.packages:
        if args.dry_run:
            logger.info("Would remove: %s", pkg)
        else:
            success, error = pm.remove([pkg])
            if success:
                tracker.remove_package(pkg)
                logger.info("Removed: %s", pkg)
            else:
                logger.error("Failed to remove %s: %s", pkg, error)
