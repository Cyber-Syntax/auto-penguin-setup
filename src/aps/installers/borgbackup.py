"""Borgbackup installer module."""

import contextlib
import pwd
import subprocess
from pathlib import Path

from aps.core.distro import detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)

_BORG_REPO_PATH = "/mnt/backups/borgbackup/home"


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


def _init_borg_repo(repo_path: str) -> bool:
    """Initialise a borg backup repository if not already initialised.

    Detects an existing repo by checking for the ``data`` subdirectory
    created by ``borg init``.  Runs ``borg init`` directly as the current
    user — **no sudo required**.

    .. note::
        The backup directory (``repo_path``) must be writable by the user
        running this installer before calling this function.  Create the
        directory and set appropriate permissions beforehand, e.g.::

            sudo mkdir -p /mnt/backups/borgbackup/home
            sudo chown $USER /mnt/backups/borgbackup/home

    Args:
        repo_path: Absolute path to the borg repository directory.

    Returns:
        True if the repo exists or was initialised successfully,
        False otherwise.

    """
    if (Path(repo_path) / "data").exists():
        logger.debug("Borg repo already initialised at %s", repo_path)
        return True

    if not Path(repo_path).exists():
        logger.warning(
            "Backup directory %s does not exist. "
            "Create it and ensure it is writable before running "
            "this installer, e.g.: sudo mkdir -p %s && sudo chown $USER %s",
            repo_path,
            repo_path,
            repo_path,
        )
        return False

    logger.info(
        "Initialising borg repo at %s (no sudo required) ...",
        repo_path,
    )
    borg_bin = _first_existing_path(["/usr/bin/borg", "/usr/local/bin/borg"])
    try:
        subprocess.run(  # noqa: S603
            [borg_bin, "init", "--encryption=none", repo_path],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to initialise borg repo at %s", repo_path)
        return False
    return True


def _set_backup_dir_permissions(backup_dir: str) -> bool:
    """Set borg-service ownership and mode on the backup directory.

    Sets ``borg:borg`` ownership and ``755`` permissions.  Skips silently
    if the directory does not yet exist (user may create it later).

    Args:
        backup_dir: Absolute path to the directory to configure.

    Returns:
        True if permissions were set (or directory absent), False on error.

    """
    if not Path(backup_dir).exists():
        logger.warning(
            "Backup directory %s does not exist; skipping permission setup",
            backup_dir,
        )
        return True  # non-fatal

    try:
        run_privileged(["/usr/bin/chown", "-R", "borg:borg", backup_dir])
        run_privileged(["/usr/bin/chmod", "755", backup_dir])
        logger.debug("Set borg:borg ownership and 755 on %s", backup_dir)
    except subprocess.CalledProcessError:
        logger.exception("Failed to set permissions on %s", backup_dir)
        return False
    return True


def install(distro: str | None = None) -> bool:
    """Install borgbackup and systemd timer.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    return _install_user(distro)


def _install_user(distro: str | None = None) -> bool:  # noqa: ARG001, PLR0911
    """Install borgbackup in user mode.

    Copies scripts/excludes to /usr/local/sbin/ and service/timer to
    /etc/systemd/system/. Enables systemd timer.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Setting up borgbackup service (user mode)...")

    if not _ensure_borg_user_exists():
        return False

    distro_info = detect_distro()
    pm = get_package_manager(distro_info)

    pkg_name = "borg" if distro_info.family.name == "ARCH" else "borgbackup"
    success, error = pm.install([pkg_name], assume_yes=True)
    if not success:
        logger.error("Failed to install %s package: %s", pkg_name, error)
        return False
    logger.debug("Installed %s package", pkg_name)

    script_src = resolve_config_file("borg-scripts/borg.sh")
    excludes_src = resolve_config_file("borg-scripts/excludes.txt")
    service_src = resolve_config_file("borg-scripts/borg.service")
    timer_src = resolve_config_file("borg-scripts/borg.timer")

    script_dest = "/usr/local/sbin/borg.sh"
    excludes_dest = "/usr/local/sbin/excludes.txt"
    service_dest = "/etc/systemd/system/borg.service"
    timer_dest = "/etc/systemd/system/borg.timer"

    for src, dest, desc in [
        (script_src, script_dest, "script"),
        (excludes_src, excludes_dest, "excludes"),
        (service_src, service_dest, "service"),
        (timer_src, timer_dest, "timer"),
    ]:
        try:
            run_privileged(["/usr/bin/cp", str(src), str(dest)])
            logger.debug("Copied %s file to %s (privileged)", desc, dest)
        except subprocess.CalledProcessError:
            logger.exception("Failed to copy %s file", desc)
            return False

    try:
        run_privileged(["/usr/bin/chmod", "+x", script_dest])
        logger.debug("Made borgbackup script executable")
    except subprocess.CalledProcessError:
        logger.exception("Failed to make borgbackup script executable")
        return False

    if not _init_borg_repo(_BORG_REPO_PATH):
        return False

    if not _set_backup_dir_permissions(_BORG_REPO_PATH):
        return False

    try:
        run_privileged(["/usr/bin/systemctl", "daemon-reload"])
        logger.debug("Reloaded systemd daemon")
    except subprocess.CalledProcessError:
        logger.exception("Failed to reload systemd daemon")
        return False

    try:
        run_privileged(["/usr/bin/systemctl", "enable", "--now", "borg.timer"])
        logger.debug("Enabled borgbackup timer")
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable borgbackup timer")
        return False

    logger.info("borgbackup user service setup completed.")
    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if borgbackup timer is enabled.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if enabled, False otherwise

    """
    cmd = [
        "/usr/bin/systemctl",
        "is-enabled",
        "borg.timer",
    ]

    try:
        result = subprocess.run(  # noqa: S603
            cmd, check=False, capture_output=True, text=True
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return result.returncode == 0


def uninstall(distro: str | None = None) -> bool:  # noqa: ARG001
    """Uninstall borgbackup timer and service.

    Args:
        distro: Distribution name (optional, for interface compatibility)

    Returns:
        True if uninstallation successful, False otherwise.

    """
    return _uninstall_user()


def _uninstall_user() -> bool:
    """Remove user-mode borgbackup setup from system paths.

    Disables and removes borg.timer, borg.service, and installed files
    from /usr/local/sbin/ and /etc/systemd/system/.

    Returns:
        True if uninstallation successful, False otherwise.
    """
    logger.info("Removing borgbackup service...")

    try:
        run_privileged(
            [
                "/usr/bin/systemctl",
                "disable",
                "--now",
                "borg.timer",
            ]
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to disable borg.timer")
        return False

    with contextlib.suppress(subprocess.CalledProcessError):
        run_privileged(["/usr/bin/systemctl", "stop", "borg.service"])

    files_to_remove = [
        "/usr/local/sbin/borg.sh",
        "/usr/local/sbin/excludes.txt",
        "/etc/systemd/system/borg.service",
        "/etc/systemd/system/borg.timer",
    ]

    for path in files_to_remove:
        try:
            run_privileged(["/usr/bin/rm", "-f", path])
        except subprocess.CalledProcessError:
            logger.warning("Failed to remove %s", path)

    try:
        run_privileged(["/usr/bin/systemctl", "daemon-reload"])
    except subprocess.CalledProcessError:
        logger.warning("Failed to reload systemd daemon after uninstall")

    logger.info("borgbackup service removed.")
    return True
