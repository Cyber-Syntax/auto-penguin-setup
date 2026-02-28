"""Borgbackup installer module."""

import pwd
import subprocess
from pathlib import Path

from aps.core.distro import detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def _first_existing_path(candidates: list[str]) -> str:
    """Return the first existing path from candidates.

    Args:
        candidates: Candidate absolute paths. The last entry is used as a
            fallback if none exist.

    Returns:
        The first path that exists, else the last candidate.

    """
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return candidates[-1]


def _borg_user_exists(username: str = "borg") -> bool:
    """Return True if the borg service user exists.

    Uses Python's NSS-backed user lookup when possible and falls back to
    `getent` if NSS lookup fails for environmental reasons.

    Args:
        username: Username to check.

    Returns:
        True if the user exists, False otherwise.

    """
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    except OSError:
        # Extremely defensive: if NSS is misconfigured, `pwd` can raise.
        # Fall back to `getent` (also NSS-backed, but often works when `pwd`
        # doesn't due to container/minimal env quirks).
        try:
            result = subprocess.run(  # noqa: S603
                ["/usr/bin/getent", "passwd", username],
                check=False,
                capture_output=True,
                text=True,
            )
        except (subprocess.SubprocessError, OSError):
            return False
        else:
            return result.returncode == 0
    else:
        return True


def _ensure_borg_user_exists() -> bool:
    """Ensure the `borg` system user exists.

    The shipped systemd service runs as `User=borg`, so installation must be
    able to create the user on first run and be idempotent on subsequent runs.

    Returns:
        True if the user exists or was created successfully, False otherwise.

    """
    if _borg_user_exists("borg"):
        logger.debug("borg user already exists")
        return True

    logger.info("Creating borg system user...")

    useradd = _first_existing_path(
        [
            "/usr/sbin/useradd",
            "/usr/bin/useradd",
        ]
    )
    nologin = _first_existing_path(
        [
            "/usr/sbin/nologin",
            "/usr/bin/nologin",
            "/sbin/nologin",
            "/bin/false",
        ]
    )

    try:
        run_privileged(
            [
                useradd,
                "--system",
                "--home-dir",
                "/var/lib/borg",
                "--no-create-home",
                "--shell",
                nologin,
                "--comment",
                "BorgBackup service user",
                "borg",
            ]
        )
    except subprocess.CalledProcessError as exc:
        stderr = (getattr(exc, "stderr", "") or "").strip()
        if stderr:
            logger.exception("Failed to create borg user (stderr: %s)", stderr)
        else:
            logger.exception("Failed to create borg user")
        return False

    return True


def install(distro: str | None = None) -> bool:  # noqa: ARG001, C901, PLR0911
    """Install borgbackup and systemd timer.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Setting up borgbackup service...")

    # Create /opt/borg directory
    try:
        run_privileged(["/usr/bin/mkdir", "-p", "/opt/borg"])
        logger.debug("Created /opt/borg directory")
    except subprocess.CalledProcessError:
        logger.exception("Failed to create /opt/borg directory")
        return False

    if not _ensure_borg_user_exists():
        return False

    # Install borgbackup package via detected package manager
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)

    pkg_name = "borg" if distro_info.family.name == "ARCH" else "borgbackup"
    success, error = pm.install([pkg_name], assume_yes=True)
    if not success:
        logger.error("Failed to install %s package: %s", pkg_name, error)
        return False
    logger.debug("Installed %s package", pkg_name)

    # Define source and destination paths
    script_src = resolve_config_file("borg-scripts/home-borgbackup.sh")
    excludes_src = resolve_config_file("borg-scripts/borg-home-excludes.txt")
    service_src = resolve_config_file("borg-scripts/home-borgbackup.service")
    timer_src = resolve_config_file("borg-scripts/home-borgbackup.timer")

    script_dest = Path("/opt/borg/home-borgbackup.sh")
    excludes_dest = Path("/opt/borg/borg-home-excludes.txt")
    service_dest = Path("/etc/systemd/system/home-borgbackup.service")
    timer_dest = Path("/etc/systemd/system/home-borgbackup.timer")

    def _copy_with_privilege(src: str, dest: str, desc: str) -> bool:
        try:
            run_privileged(["/usr/bin/cp", str(src), str(dest)])
            logger.debug("Copied %s file to %s (privileged)", desc, dest)
        except subprocess.CalledProcessError:
            logger.exception("Failed to copy %s file", desc)
            return False
        else:
            return True

    # Copy script file
    if not _copy_with_privilege(str(script_src), str(script_dest), "script"):
        return False

    # Copy excludes file
    if not _copy_with_privilege(
        str(excludes_src), str(excludes_dest), "excludes"
    ):
        return False

    # Copy service file
    if not _copy_with_privilege(
        str(service_src), str(service_dest), "service"
    ):
        return False

    # Copy timer file
    if not _copy_with_privilege(str(timer_src), str(timer_dest), "timer"):
        return False

    # Make script executable
    try:
        run_privileged(["/usr/bin/chmod", "+x", str(script_dest)])
        logger.debug("Made borgbackup script executable")
    except subprocess.CalledProcessError:
        logger.exception("Failed to make borgbackup script executable")
        return False

    # Enable and start timer
    logger.info("Enabling borgbackup timer...")
    try:
        run_privileged(
            ["/usr/bin/systemctl", "enable", "--now", "home-borgbackup.timer"]
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable borgbackup timer")
        return False

    # Reload systemd daemon
    try:
        run_privileged(["/usr/bin/systemctl", "daemon-reload"])
        logger.debug("Reloaded systemd daemon")
    except subprocess.CalledProcessError:
        logger.exception("Failed to reload systemd daemon")
        return False

    logger.info("borgbackup service setup completed.")
    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if borgbackup timer is enabled.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if enabled, False otherwise

    """
    try:
        result = subprocess.run(
            ["/usr/bin/systemctl", "is-enabled", "home-borgbackup.timer"],
            check=False,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    else:
        return result.returncode == 0


# TODO(phase-6): init repo if not exists  # noqa: FIX002
# use variables.ini for repo path, I use mnt/backups for example.
# borg init --encryption=none /mnt/backups/borgbackup/home-repo
# need to mkdir borgbackup folder before init home-repo
