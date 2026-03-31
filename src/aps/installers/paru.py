"""Paru AUR helper installer module."""

import shutil
import subprocess
from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: PLR0911
    """Install paru AUR helper.

    Only available on Arch-based distributions.

    Args:
        distro: Distribution ID (e.g., 'arch'). If None or non-Arch, returns
            False.

    Returns:
        bool: True if installation was successful, False otherwise.

    """
    if distro != "arch":
        logger.info(
            "AUR helper setup is only available for Arch-based distributions"
        )
        return False

    if shutil.which("paru") or shutil.which("yay"):
        logger.info("AUR helper (paru/yay) is already installed")
        return True

    logger.info("Installing paru AUR helper...")

    if not _ensure_gpg_keyring():
        return False

    if not _install_build_deps():
        return False

    if not _build_paru():
        return False

    if not shutil.which("paru"):
        logger.error("paru installation verification failed")
        return False

    logger.info("paru installed successfully")
    return True


def _ensure_gpg_keyring() -> bool:
    """Create GPG keyring if it doesn't exist.

    Returns:
        bool: Always True (creation is optional)

    """
    gpg_dirs = [
        Path.home() / ".local" / "share" / "gnupg",
        Path.home() / ".gnupg",
    ]

    keyring_exists = any((d / "pubring.kbx").exists() for d in gpg_dirs)

    if not keyring_exists:
        logger.info("Creating GPG keyring...")
        subprocess.run(
            ["gpg", "--list-keys"],  # noqa: S607
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    return True


def _install_build_deps() -> bool:
    """Install build dependencies for AUR helper.

    Returns:
        bool: True if installation succeeded, False otherwise.

    """
    logger.info("Installing build dependencies...")
    result = run_privileged(
        ["pacman", "-S", "--needed", "--noconfirm", "base-devel", "git"],
        capture_output=False,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error("Failed to install build dependencies: %s", result.stderr)
        return False

    return True


def _build_paru() -> bool:
    """Build and install paru-bin from AUR.

    Returns:
        bool: True if build succeeded, False otherwise.

    """
    build_dir = Path("/opt/paru-bin")

    try:
        if build_dir.exists():
            logger.info("Cleaning up previous build directory...")
            run_privileged(["rm", "-rf", str(build_dir)], check=True)

        logger.info("Cloning paru-bin repository...")
        result = run_privileged(
            [
                "git",
                "clone",
                "https://aur.archlinux.org/paru-bin.git",
                str(build_dir),
            ],
            capture_output=False,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "Failed to clone paru-bin repository: %s", result.stderr
            )
            return False

        logger.info("Setting directory permissions...")
        user = Path.home().name
        result = run_privileged(
            ["chown", "-R", f"{user}:{user}", str(build_dir)],
            capture_output=False,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "Failed to set directory ownership: %s", result.stderr
            )
            return False

        logger.info("Building and installing paru...")
        result = subprocess.run(
            ["makepkg", "-si", "--noconfirm"],  # noqa: S607
            cwd=build_dir,
            capture_output=False,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to build and install paru: %s", result.stderr)
            return False

        return True

    finally:
        if build_dir.exists():
            logger.info("Cleaning up build directory...")
            run_privileged(
                ["rm", "-rf", str(build_dir)],
                check=False,
                capture_output=False,
            )
