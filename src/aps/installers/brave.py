"""Brave Browser installer module."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from aps.core.logger import get_logger

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:
    """Install Brave Browser and configure it to use basic password store.

    Args:
        distro: Distribution ID (optional, for API consistency).

    Returns:
        bool: True if installation was successful, False otherwise.

    """
    logger.info("Installing Brave Browser...")

    if _is_installed():
        logger.info("Brave Browser is already installed")
    else:
        logger.info("Installing Brave Browser...")

        if not shutil.which("curl"):
            logger.error("curl is required for Brave installation")
            return False

        if not _install_brave():
            logger.error("Failed to install Brave Browser")
            return False

        logger.info("Brave Browser installed successfully")

    if not _disable_keyring(distro):
        logger.warning("Failed to modify Brave desktop file, but continuing")

    return True


def _is_installed() -> bool:
    """Check if Brave is already installed.

    Returns:
        bool: True if Brave is installed, False otherwise.

    """
    return (
        shutil.which("brave") is not None
        or shutil.which("brave-browser") is not None
    )


def _install_brave() -> bool:
    """Install Brave using the official install script.

    Returns:
        bool: True if installation was successful, False otherwise.

    """
    try:
        # Download and execute official Brave install script
        curl_process = subprocess.Popen(
            ["curl", "-fsS", "https://dl.brave.com/install.sh"],  # noqa: S607
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        bash_process = subprocess.Popen(
            ["bash"],  # noqa: S607
            stdin=curl_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if curl_process.stdout:
            curl_process.stdout.close()

        _, stderr = bash_process.communicate()

        if bash_process.returncode != 0:
            logger.error("Installation script failed: %s", stderr.decode())
            return False
        return True  # noqa: TRY300

    except Exception:
        logger.exception("Error installing Brave")
        return False


def _disable_keyring(distro: str | None) -> bool:
    """Modify Brave desktop file to use basic password store.

    Args:
        distro: Distribution ID (optional).

    Returns:
        bool: True if desktop file was modified successfully, False otherwise.

    """
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", str(Path("~/.local/share").expanduser())
    )
    user_desktop_dir = Path(xdg_data_home) / "applications"
    user_desktop_file = user_desktop_dir / "brave-browser.desktop"

    system_desktop_file = _get_system_desktop_file(distro)

    user_desktop_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("User desktop directory: %s", user_desktop_dir)

    if not user_desktop_file.exists():
        if system_desktop_file.exists():
            logger.info("Copying system desktop file to user directory...")
            shutil.copy2(system_desktop_file, user_desktop_file)
        else:
            logger.error(
                "Brave desktop file not found at: %s", system_desktop_file
            )
            return False

    if _is_already_modified(user_desktop_file):
        logger.info("Desktop file already modified - no changes needed")
        return True

    backup_file = Path(f"{user_desktop_file}.bak")
    logger.debug("Creating backup at %s", backup_file)
    try:
        shutil.copy2(user_desktop_file, backup_file)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Failed to create backup file: %s, but proceeding anyway", e
        )

    if not _modify_desktop_file(user_desktop_file):
        logger.error("Failed to modify desktop file")
        if backup_file.exists():
            logger.debug("Restoring from backup")
            shutil.copy2(backup_file, user_desktop_file)
        return False

    logger.info("Successfully modified Brave desktop file")
    return True


def _get_system_desktop_file(distro: str | None) -> Path:
    """Get the path to the system Brave desktop file.

    Args:
        distro: Distribution ID (optional).

    Returns:
        Path: Path to the system desktop file.

    """
    standard_path = Path("/usr/share/applications/brave-browser.desktop")

    if distro == "fedora":
        return standard_path

    if distro in ("arch", "archlinux", "manjaro", "cachyos"):
        # Try different locations for Arch-based distros
        if standard_path.exists():
            return standard_path

        opt_path = Path("/opt/brave-bin/brave-browser.desktop")
        if opt_path.exists():
            return opt_path

        return standard_path

    return Path("/usr/share/applications/brave-browser.desktop")


def _is_already_modified(desktop_file: Path) -> bool:
    """Check if desktop file is already modified.

    Args:
        desktop_file: Path to the desktop file.

    Returns:
        bool: True if already modified, False otherwise.

    """
    try:
        content = desktop_file.read_text()
    except Exception:
        logger.exception("Error reading desktop file")
        return False
    else:
        return "--password-store=basic" in content


def _modify_desktop_file(desktop_file: Path) -> bool:
    """Modify Exec lines in desktop file to add password store flag.

    Args:
        desktop_file: Path to the desktop file.

    Returns:
        bool: True if modification was successful, False otherwise.

    """
    try:
        content = desktop_file.read_text()
        original_content = content
        modified = False

        # Pattern 1: /usr/bin/brave-browser-stable
        if re.search(
            r"^Exec=/usr/bin/brave-browser-stable", content, re.MULTILINE
        ):
            logger.debug(
                "Modifying Exec lines with /usr/bin/brave-browser-stable"
            )
            content = re.sub(
                r"^Exec=/usr/bin/brave-browser-stable(.*)$",
                r"Exec=/usr/bin/brave-browser-stable --password-store=basic\1",
                content,
                flags=re.MULTILINE,
            )
            modified = True

        # Pattern 2: bare 'brave' command
        if re.search(r"^Exec=brave(\s|$)", content, re.MULTILINE):
            logger.debug("Modifying Exec lines with bare 'brave' command")
            content = re.sub(
                r"^Exec=brave(\s.*)$",
                r"Exec=brave --password-store=basic\1",
                content,
                flags=re.MULTILINE,
            )
            content = re.sub(
                r"^Exec=brave$",
                r"Exec=brave --password-store=basic",
                content,
                flags=re.MULTILINE,
            )
            modified = True

        if not modified:
            logger.error(
                "Failed to modify desktop file - no matching Exec lines found"
            )
            logger.debug("Desktop file Exec lines:")
            for line in content.split("\n"):
                if line.startswith("Exec="):
                    logger.debug("  %s", line)
            return False

        desktop_file.write_text(content)

    except Exception:
        logger.exception("Error modifying desktop file")
        return False
    else:
        return content != original_content
