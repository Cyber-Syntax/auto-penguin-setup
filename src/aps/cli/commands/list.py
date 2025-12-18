"""List command implementation."""

import logging
from argparse import Namespace

from aps.cli.utils import get_tracking_db_path
from aps.core.tracking import PackageTracker

logger = logging.getLogger(__name__)


def cmd_list(args: Namespace) -> None:
    """Handle 'aps list' command."""
    tracker = PackageTracker(get_tracking_db_path())
    packages = tracker.get_tracked_packages()

    if args.source:
        # Extract prefix from source (before ':' if present) and compare case-insensitively
        # Handles both simple sources ("official") and compound sources ("COPR:user/repo")
        filter_prefix = args.source.lower()
        packages = [
            p
            for p in packages
            if p.source.split(":")[0].lower() == filter_prefix
        ]

    if not packages:
        return

    name_width = 30
    source_width = 25
    category_width = 15
    date_width = 24

    logger.info("Tracked Packages:")
    logger.info(
        "=" * (name_width + source_width + category_width + date_width + 3)
    )
    logger.info(
        "%s %s %s %s",
        "Name".ljust(name_width),
        "Source".ljust(source_width),
        "Category".ljust(category_width),
        "Installed At".ljust(date_width),
    )
    logger.info(
        "%s %s %s %s",
        "-" * name_width,
        "-" * source_width,
        "-" * category_width,
        "-" * date_width,
    )
    for pkg in packages:
        logger.info(
            "%s %s %s %s",
            pkg.name.ljust(name_width),
            pkg.source.ljust(source_width),
            (pkg.category or "N/A").ljust(category_width),
            pkg.installed_at.ljust(date_width),
        )
