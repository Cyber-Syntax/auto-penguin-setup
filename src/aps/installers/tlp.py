"""TLP installer for laptop power management."""

import shutil
import subprocess
from pathlib import Path

from aps.core.distro import detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.utils.paths import resolve_config_file
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: ARG001
    """Install and configure TLP.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    logger.info("Setting up TLP for power management...")

    distro_info = detect_distro()
    pm = get_package_manager(distro_info)

    # Install TLP if not already installed
    if not pm.is_installed("tlp"):
        logger.info("TLP is not installed. Installing...")
        success, error = pm.install(["tlp"])
        if not success:
            logger.error("Failed to install TLP: %s", error)
            return False

    # Create tlp.d directory if it doesn't exist
    tlp_dir = Path("/etc/tlp.d")
    if not tlp_dir.exists():
        try:
            run_privileged(
                ["mkdir", "-p", str(tlp_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Failed to create /etc/tlp.d directory")
            return False

    # Backup existing configuration
    conf_dest = Path("/etc/tlp.d/01-mytlp.conf")
    backup_file = Path("/etc/tlp.d/01-mytlp.conf.bak")

    if conf_dest.exists() and not backup_file.exists():
        try:
            run_privileged(
                ["cp", str(conf_dest), str(backup_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Created backup of TLP configuration")
        except subprocess.CalledProcessError:
            logger.warning("Failed to create backup of TLP configuration")

    # Copy new configuration
    conf_src = resolve_config_file("01-mytlp.conf")
    if not conf_src.exists():
        logger.error("TLP config file not found at %s", conf_src)
        return False

    try:
        run_privileged(
            ["cp", str(conf_src), str(conf_dest)],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("Copied TLP configuration")
    except subprocess.CalledProcessError:
        logger.exception("Failed to copy TLP configuration")
        return False

    # Disable conflicting power services
    if not _disable_conflicting_services():
        logger.error("Failed to disable conflicting power services")
        return False

    # Enable TLP services
    logger.info("Configuring TLP services...")
    for service in ["tlp", "tlp-sleep"]:
        service_file = Path(f"/usr/lib/systemd/system/{service}.service")
        if service_file.exists():
            try:
                run_privileged(
                    ["systemctl", "enable", "--now", service],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.debug("Enabled service: %s", service)
            except subprocess.CalledProcessError:
                logger.exception("Failed to enable %s", service)
                return False
        else:
            logger.warning("%s service not found", service)

    # Mask rfkill services to allow TLP to handle radios
    for rfkill_service in [
        "systemd-rfkill.service",
        "systemd-rfkill.socket",
    ]:
        try:
            run_privileged(
                ["systemctl", "mask", rfkill_service],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Masked %s", rfkill_service)
        except subprocess.CalledProcessError:
            logger.warning("Failed to mask %s", rfkill_service)

    # Check if tlp-rdw is available and install if needed
    if not shutil.which("tlp-rdw"):
        logger.info("tlp-rdw command not found. Attempting to install...")
        success, error = pm.install(["tlp-rdw"])
        if not success:
            logger.warning("Failed to install tlp-rdw package: %s", error)
        else:
            logger.info("tlp-rdw installed successfully")

    # Enable TLP radio device handling if available
    if shutil.which("tlp-rdw"):
        try:
            run_privileged(
                ["tlp-rdw", "enable"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Enabled TLP radio device handling")
        except subprocess.CalledProcessError:
            logger.warning("Failed to enable TLP radio device handling")
    else:
        logger.warning(
            "tlp-rdw command not available. Skipping radio device handling."
        )

    # Remove conflicting packages now that TLP is working
    if not _remove_conflicting_packages(pm):
        logger.warning(
            "TLP is working, but failed to remove conflicting packages"
        )

    logger.info("TLP setup completed successfully.")
    return True


def _disable_conflicting_services() -> bool:
    """Disable services that conflict with TLP."""
    logger.info("Disabling services that conflict with TLP...")

    services_to_check = [
        "tuned",
        "tuned-ppd",
        "power-profiles-daemon",
        "power-profile-daemon",
    ]
    services_to_disable = []

    # Check which services exist
    for service in services_to_check:
        try:
            result = subprocess.run(
                ["systemctl", "list-unit-files", f"{service}.service"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and service in result.stdout:
                services_to_disable.append(service)
        except subprocess.SubprocessError:
            continue

    # Disable found services
    if services_to_disable:
        logger.info(
            "Disabling conflicting services: %s",
            ", ".join(services_to_disable),
        )
        for service in services_to_disable:
            try:
                run_privileged(
                    ["systemctl", "disable", "--now", service],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            except subprocess.SubprocessError:
                logger.warning("Failed to disable %s", service)
    else:
        logger.debug("No conflicting services found to disable")

    return True


def _remove_conflicting_packages(pm) -> bool:  # noqa: ANN001
    """Remove packages that conflict with TLP."""
    logger.info("Removing packages that conflict with TLP...")

    packages_to_check = [
        "tuned",
        "tuned-ppd",
        "power-profiles-daemon",
        "power-profile-daemon",
    ]
    packages_to_remove = []

    # Check which packages are installed
    for pkg in packages_to_check:
        if pm.is_installed(pkg):
            packages_to_remove.append(pkg)

    # Remove found packages
    if packages_to_remove:
        logger.info(
            "Removing conflicting packages: %s",
            ", ".join(packages_to_remove),
        )
        success, error = pm.remove(packages_to_remove)
        if not success:
            logger.error("Failed to remove conflicting packages: %s", error)
            return False
        logger.info("Successfully removed conflicting packages")
    else:
        logger.debug("No conflicting packages found to remove")

    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if TLP is installed.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installed, False otherwise

    """
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    return pm.is_installed("tlp")
