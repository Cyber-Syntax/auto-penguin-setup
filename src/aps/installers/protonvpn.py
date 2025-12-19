"""ProtonVPN installer with distro-specific repository setup."""

import subprocess
import tempfile
from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = get_logger(__name__)


class ProtonVPNInstaller(BaseInstaller):
    """Installer for ProtonVPN with repository management."""

    def install(self) -> bool:
        """Install ProtonVPN with distro-specific setup.

        Returns:
            True if installation successful, False otherwise

        """
        logger.info("Installing ProtonVPN...")

        if self.distro == "fedora":
            return self._install_fedora()
        if self.distro == "arch":
            return self._install_arch()
        logger.error("Unsupported distribution: %s", self.distro)
        return False

    def _install_fedora(self) -> bool:
        """Install ProtonVPN on Fedora."""
        logger.info("Installing ProtonVPN for Fedora...")

        # Get Fedora version
        try:
            with Path("/etc/fedora-release").open() as f:
                fedora_version = f.read().split()[2]
        except (OSError, IndexError) as e:
            logger.error("Failed to detect Fedora version: %s", e)
            return False

        repo_url = f"https://repo.protonvpn.com/fedora-{fedora_version}-stable"
        key_url = f"{repo_url}/public_key.asc"
        rpm_url = f"{repo_url}/protonvpn-stable-release/protonvpn-stable-release-1.0.2-1.noarch.rpm"

        # Import GPG key
        logger.info("Importing ProtonVPN GPG key...")
        try:
            run_privileged(
                ["rpm", "--import", key_url],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to import ProtonVPN GPG key: %s", e.stderr)
            return False

        # Check if repo already exists
        repo_file = Path("/etc/yum.repos.d/protonvpn-stable.repo")
        if not repo_file.exists():
            logger.info("Downloading and installing ProtonVPN repository...")

            with tempfile.NamedTemporaryFile(
                suffix=".rpm", delete=False
            ) as tmp_rpm:
                tmp_path = Path(tmp_rpm.name)

            try:
                # Download repository package
                subprocess.run(
                    ["wget", "-O", str(tmp_path), rpm_url],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Install repository package
                run_privileged(
                    ["dnf", "install", "--setopt=assumeyes=1", str(tmp_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Failed to setup ProtonVPN repository: %s", e.stderr
                )
                tmp_path.unlink(missing_ok=True)
                return False
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            logger.info("ProtonVPN repository already installed")

        # Refresh repositories
        logger.info("Refreshing package repositories...")
        run_privileged(
            ["dnf", "check-update", "--refresh", "--setopt=assumeyes=1"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Install ProtonVPN
        success, error = self.pm.install(["proton-vpn-gnome-desktop"])
        if not success:
            logger.error(
                "Failed to install ProtonVPN GNOME desktop integration: %s",
                error,
            )
            return False

        logger.info("ProtonVPN installation completed successfully")
        return True

    def _install_arch(self) -> bool:
        """Install ProtonVPN on Arch Linux."""
        logger.info("Installing ProtonVPN from Arch repositories...")

        success, error = self.pm.install(["proton-vpn-gtk-app"])
        if not success:
            logger.error("Failed to install ProtonVPN: %s", error)
            return False

        logger.info("ProtonVPN installation completed successfully")
        return True

    def is_installed(self) -> bool:
        """Check if ProtonVPN is installed.

        Returns:
            True if installed, False otherwise

        """
        if self.distro == "fedora":
            return self.pm.is_installed("proton-vpn-gnome-desktop")
        if self.distro == "arch":
            return self.pm.is_installed("proton-vpn-gtk-app")
        return False
