"""Virt-manager installer for virtualization management."""

import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = get_logger(__name__)


class VirtManagerInstaller(BaseInstaller):
    """Installer for virt-manager and libvirt virtualization."""

    def install(self) -> bool:
        """Install virt-manager and configure virtualization.

        Returns:
            True if installation successful, False otherwise

        """
        logger.info("Setting up virtualization...")

        if self.distro == "fedora":
            return self._install_fedora()
        if self.distro == "arch":
            return self._install_arch()
        if self.distro == "debian":
            return self._install_debian()
        logger.error("Unsupported distribution: %s", self.distro)
        return False

    def _install_fedora(self) -> bool:
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
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to install virtualization group: %s", e.stderr
            )
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
            logger.warning(
                "Failed to install optional virtualization packages"
            )

        return self._configure_libvirt()

    def _install_arch(self) -> bool:
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
            subprocess.run(
                ["paru", "--ask=4", "-S", "--noconfirm"] + arch_pkgs,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to install virtualization packages: %s", e.stderr
            )
            return False

        return self._configure_libvirt()

    def _install_debian(self) -> bool:
        """Install virtualization packages on Debian/Ubuntu."""
        logger.info("Installing virtualization packages for Debian/Ubuntu")

        deb_pkgs = [
            "libvirt-daemon-system",
            "libvirt-clients",
            "qemu-kvm",
            "virt-manager",
            "bridge-utils",
        ]

        success, error = self.pm.install(deb_pkgs)
        if not success:
            logger.error(
                "Failed to install virtualization packages: %s", error
            )
            return False

        return self._configure_libvirt()

    def _configure_libvirt(self) -> bool:
        """Configure libvirt and add user to libvirt group."""
        # Ensure libvirt group exists
        try:
            result = subprocess.run(
                ["getent", "group", "libvirt"],
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
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create libvirt group: %s", e.stderr)
            return False

        # Add current user to libvirt group
        try:
            import getpass

            username = getpass.getuser()
            run_privileged(
                ["usermod", "-aG", "libvirt", username],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Added user %s to libvirt group", username)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to add user to libvirt group: %s", e.stderr)
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
        except subprocess.CalledProcessError as e:
            logger.error("Failed to enable libvirtd service: %s", e.stderr)
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
            "Note: You may need to log out and back in for group changes to take effect"
        )

        return True

    def is_installed(self) -> bool:
        """Check if virt-manager is installed.

        Returns:
            True if installed, False otherwise

        """
        return self.pm.is_installed("virt-manager")
