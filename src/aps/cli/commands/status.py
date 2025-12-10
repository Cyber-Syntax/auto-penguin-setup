"""Status command implementation."""

import logging
from argparse import Namespace

from aps.cli.commands._utils import get_tracking_db_path
from aps.core.distro import detect_distro
from aps.core.tracking import PackageTracker

logger = logging.getLogger(__name__)


def cmd_status(args: Namespace) -> None:  # noqa: ARG001
    """Handle 'aps status' command."""
    distro_info = detect_distro()
    tracker = PackageTracker(get_tracking_db_path())

    logger.info("Distribution: %s %s", distro_info.name, distro_info.version)
    logger.info("Package Manager: %s", distro_info.package_manager.value)

    packages = tracker.get_tracked_packages()
    logger.info("Tracked Packages: %s", len(packages))

    # Count by source
    sources: dict[str, int] = {}
    for pkg in packages:
        source_type = pkg.source.split(":")[0] if ":" in pkg.source else pkg.source
        sources[source_type] = sources.get(source_type, 0) + 1

    logger.info("By Source:")
    for source, count in sources.items():
        logger.info("  %s: %s", source, count)
