"""AMD CPU configuration - zenpower setup for Ryzen 5000 series."""

import subprocess
from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def _is_amd_cpu() -> bool:
    """Check if system has AMD CPU.

    Returns:
        True if AMD CPU is detected

    """
    try:
        with Path("/proc/cpuinfo").open(encoding="utf-8") as f:
            return "AMD" in f.read()
    except FileNotFoundError:
        logger.warning("Cannot detect CPU type - /proc/cpuinfo not found")
        return False


def _is_k10temp_loaded() -> bool:
    """Check if k10temp module is loaded.

    Returns:
        True if k10temp is loaded

    """
    try:
        lsmod_result = subprocess.run(
            ["lsmod"],
            capture_output=True,
            text=True,
            check=False,
        )
        if lsmod_result.returncode != 0:
            return False
        grep_result = subprocess.run(
            ["grep", "k10temp"],
            input=lsmod_result.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        return grep_result.returncode == 0
    except FileNotFoundError:
        return False


def _is_k10temp_blacklisted() -> bool:
    """Check if k10temp is already blacklisted.

    Returns:
        True if k10temp is blacklisted in modprobe.d

    """
    modprobe_dir = Path("/etc/modprobe.d")
    if not modprobe_dir.exists():
        return False

    for conf_file in modprobe_dir.glob("*.conf"):
        try:
            with conf_file.open(encoding="utf-8") as f:
                if "blacklist k10temp" in f.read():
                    return True
        except OSError:
            continue
    return False


def _is_zenpower_loaded() -> bool:
    """Check if zenpower module is loaded.

    Returns:
        True if zenpower is loaded

    """
    try:
        lsmod_result = subprocess.run(
            ["lsmod"],
            capture_output=True,
            text=True,
            check=False,
        )
        if lsmod_result.returncode != 0:
            return False
        grep_result = subprocess.run(
            ["grep", "zenpower"],
            input=lsmod_result.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        return grep_result.returncode == 0
    except FileNotFoundError:
        return False


def setup_zenpower(distro: str) -> bool:
    r"""Set up zenpower for zen3 amd cpu family.

    Because zenpower is using same PCI device as k10temp, you have to
    disable k10temp first. This is automatically done by the AUR package.

    Check if k10temp is active: lsmod | grep k10temp
    Unload k10temp: sudo modprobe -r k10temp
    (optional*) blacklist k10temp: sudo bash -c `sudo echo -e
    "\n# replaced with zenpower\nblacklist k10temp" >>
    /etc/modprobe.d/k10temp-blacklist.conf'
    Activate zenpower: sudo modprobe zenpower

    *If k10temp is not blacklisted, you may have to manually unload
    k10temp after each restart.

    Args:
        distro: Distribution name (fedora, arch)

    Returns:
        True if setup succeeds, False otherwise

    """
    logger.info("Setting up zenpower3...")

    if not _is_amd_cpu():
        logger.error("This system does not appear to have an AMD CPU")
        return False

    if distro not in ["fedora", "arch"]:
        logger.error("Unsupported distribution: %s", distro)
        return False

    if _is_k10temp_loaded():
        logger.info("k10temp module is currently loaded, unloading...")
        result = run_privileged(
            ["modprobe", "-r", "k10temp"],
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to unload k10temp module")
            return False

    if not _is_k10temp_blacklisted():
        blacklist_file = "/etc/modprobe.d/k10temp-blacklist.conf"
        logger.debug("Creating k10temp blacklist file at %s...", blacklist_file)

        command = f"echo 'blacklist k10temp' > '{blacklist_file}'"
        result = run_privileged(
            ["sh", "-c", command],
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to create blacklist file: %s", result.stderr)
            return False
    else:
        logger.info("k10temp is already blacklisted")

    return _load_zenpower_module()


def _load_zenpower_module() -> bool:
    """Load zenpower kernel module.

    Returns:
        True if module loads successfully

    """
    logger.debug("Checking if zenpower module is loaded...")
    if _is_zenpower_loaded():
        logger.info("zenpower module is already loaded")
        return True

    logger.debug("Loading zenpower module...")
    result = run_privileged(
        ["modprobe", "zenpower"],
        check=False,
    )
    if result.returncode != 0:
        logger.error("Failed to load zenpower module")
        logger.info(
            "A system restart may be required to load the zenpower "
            "module. Please reboot and try again."
        )
        return False

    logger.info("zenpower module loaded successfully")
    return True


def configure(distro: str, **kwargs) -> bool:
    """Configure AMD hardware.

    Args:
        distro: Distribution name (fedora, arch)
        **kwargs: Configuration options
            - zenpower: bool - Setup zenpower for Ryzen 5000 series

    Returns:
        True if all requested operations succeed

    """
    if kwargs.get("zenpower", False):
        return setup_zenpower(distro)

    return True
