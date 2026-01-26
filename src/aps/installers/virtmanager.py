"""Virt-manager installer for virtualization management."""

import getpass
import subprocess

from aps.core.distro import detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:
    """Install virt-manager and configure virtualization.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    distro_info = detect_distro()
    if distro is None:
        distro = distro_info.id

    logger.info("Setting up virtualization...")

    if distro == "fedora":
        return _install_fedora()
    if distro == "arch":
        return _install_arch()
    logger.error("Unsupported distribution: %s", distro)
    return False


def _install_fedora() -> bool:
    """Install virtualization packages on Fedora."""
    logger.info("Installing virtualization packages for Fedora")

    # Fedora uses dnf groups for virtualization
    try:
        run_privileged(
            ["dnf", "install", "-y", "@virtualization"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to install virtualization group")
        return False

    # Install optional packages
    try:
        run_privileged(
            [
                "dnf",
                "group",
                "install",
                "-y",
                "--with-optional",
                "virtualization",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except subprocess.SubprocessError:
        logger.warning("Failed to install optional virtualization packages")

    return _configure_libvirt()


def _install_arch() -> bool:
    """Install virtualization packages on Arch."""
    logger.info("Installing virtualization packages for Arch")

    # Arch packages for virtualization
    arch_pkgs = [
        "libvirt",
        "qemu",
        "virt-manager",
        "virt-install",
        "dnsmasq",
        "ebtables",
        "bridge-utils",
    ]

    # Use --ask=4 to auto-resolve conflicts (like iptables vs iptables-nft)
    try:
        subprocess.run(  # noqa: S603
            ["paru", "--ask=4", "-S", "--noconfirm", *arch_pkgs],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to install virtualization packages")
        return False

    return _configure_libvirt()


def _configure_libvirt() -> bool:
    """Configure libvirt and add user to libvirt group."""
    # Ensure libvirt group exists
    try:
        result = subprocess.run(
            ["getent", "group", "libvirt"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.info("Creating libvirt group")
            run_privileged(
                ["groupadd", "libvirt"],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError:
        logger.exception("Failed to create libvirt group")
        return False

    # Add current user to libvirt group
    try:
        username = getpass.getuser()
        run_privileged(
            ["usermod", "-aG", "libvirt", username],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Added user %s to libvirt group", username)
    except subprocess.CalledProcessError:
        logger.exception("Failed to add user to libvirt group")
        return False

    # Enable and start libvirtd service
    logger.info("Enabling libvirtd service...")
    try:
        run_privileged(
            ["systemctl", "enable", "--now", "libvirtd"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("Enabled libvirtd service")
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable libvirtd service")
        return False

    # Configure default network
    logger.info("Configuring default libvirt network...")
    try:
        # Check if default network exists
        result = run_privileged(
            ["virsh", "net-list", "--all"],
            check=True,
            capture_output=True,
            text=True,
        )

        if "default" in result.stdout:
            # Start and autostart default network
            run_privileged(
                ["virsh", "net-start", "default"],
                check=False,
                capture_output=True,
                text=True,
            )
            run_privileged(
                ["virsh", "net-autostart", "default"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Configured default network")
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to configure default network: %s", e.stderr)

    logger.info("Virtualization setup completed successfully")
    logger.info(
        "Note: You may need to log out and back in for "
        "group changes to take effect"
    )

    return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if virt-manager is installed.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installed, False otherwise

    """
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    return pm.is_installed("virt-manager")
