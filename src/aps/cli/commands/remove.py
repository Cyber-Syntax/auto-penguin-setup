"""Remove command implementation."""

import subprocess
from argparse import Namespace

from aps.cli.utils import get_tracking_db_path
from aps.core.distro import detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.core.setup import SetupError, SetupManager
from aps.core.tracking import PackageTracker
from aps.utils.privilege import ensure_sudo

logger = get_logger(__name__)


def cmd_remove(args: Namespace) -> None:  # noqa: C901, PLR0912
    """Handle 'aps remove' command."""
    # Pre-authenticate sudo for privileged operations
    ensure_sudo()

    # Validate that at least one target is specified
    has_packages = bool(args.packages)
    has_setup = args.setup is not None

    if not has_packages and not has_setup:
        logger.error("No packages or setup component specified")
        return

    if has_setup:
        if args.dry_run:
            logger.info("Would remove setup component: %s", args.setup)
            return

        distro_info = detect_distro()
        manager = SetupManager(distro_info)
        try:
            manager.remove_component(args.setup)
            logger.info("Successfully removed setup component: %s", args.setup)
        except SetupError:
            logger.exception("Failed to remove setup component %s", args.setup)
        return

    if has_packages:
        distro_info = detect_distro()
        pm = get_package_manager(distro_info)
        tracker = PackageTracker(get_tracking_db_path())

        for pkg in args.packages:
            if args.dry_run:
                logger.info("Would remove: %s", pkg)
            else:
                # Check if package came from Flatpak
                package_record = tracker.get_package(pkg)
                is_flatpak = (
                    package_record is not None
                    and package_record.source.startswith("flatpak:")
                )

                if is_flatpak and package_record is not None:
                    # Use flatpak uninstall for Flatpak-sourced packages
                    flatpak_cmd = [
                        "flatpak",
                        "uninstall",
                        package_record.mapped_name or pkg,
                    ]
                    if args.noconfirm:
                        flatpak_cmd.append("--assumeyes")

                    result = subprocess.run(flatpak_cmd, check=False)  # noqa: S603
                    if result.returncode == 0:
                        tracker.remove_package(pkg)
                        logger.info("Removed: %s", pkg)
                    else:
                        logger.error(
                            "Failed to remove Flatpak package: %s", pkg
                        )
                else:
                    # Use package manager for system packages
                    success, error = pm.remove(
                        [pkg], assume_yes=args.noconfirm
                    )
                    if success:
                        tracker.remove_package(pkg)
                        logger.info("Removed: %s", pkg)
                    else:
                        logger.error("Failed to remove %s: %s", pkg, error)
