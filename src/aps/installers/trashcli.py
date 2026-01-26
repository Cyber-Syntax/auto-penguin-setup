"""Trash-cli installer and systemd timer setup."""

import subprocess
from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: ARG001
    """Install trash-cli systemd service and timer.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Setting up trash-cli service...")

    # Define paths
    service_dest = Path("/etc/systemd/system/trash-cli.service")
    timer_dest = Path("/etc/systemd/system/trash-cli.timer")
    service_src = resolve_config_file("trash-cli/trash-cli.service")
    timer_src = resolve_config_file("trash-cli/trash-cli.timer")

    def _copy_with_privilege(src: str, dest: str, desc: str) -> bool:
        try:
            run_privileged(["/usr/bin/cp", str(src), str(dest)])
            logger.debug("Copied %s file to %s (privileged)", desc, dest)
        except subprocess.CalledProcessError:
            logger.exception("Failed to copy %s file", desc)
            return False
        else:
            return True

    # Copy service file
    if not _copy_with_privilege(
        str(service_src), str(service_dest), "service"
    ):
        return False

    # Copy timer file
    if not _copy_with_privilege(str(timer_src), str(timer_dest), "timer"):
        return False

    # Reload systemd daemon
    try:
        run_privileged(["/usr/bin/systemctl", "daemon-reload"])
    except subprocess.CalledProcessError:
        logger.exception("Failed to reload systemd daemon")
        return False

    # Enable and start timer
    logger.info("Enabling trash-cli timer...")
    try:
        run_privileged(
            ["/usr/bin/systemctl", "enable", "--now", "trash-cli.timer"]
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable trash-cli timer")
        return False

    logger.info("trash-cli service setup completed.")
    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if trash-cli timer is enabled.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if enabled, False otherwise

    """
    try:
        result = subprocess.run(
            ["/usr/bin/systemctl", "is-enabled", "trash-cli.timer"],
            check=False,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    else:
        return result.returncode == 0
