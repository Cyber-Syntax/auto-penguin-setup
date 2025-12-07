"""ProtonVPN installer with distro-specific repository setup."""

import hashlib
import logging
import subprocess
import tempfile
from pathlib import Path

from .base import BaseInstaller

logger = logging.getLogger(__name__)


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
        elif self.distro == "arch":
            return self._install_arch()
        elif self.distro == "debian":
            return self._install_debian()
        else:
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
            subprocess.run(
                ["sudo", "rpm", "--import", key_url],
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

            with tempfile.NamedTemporaryFile(suffix=".rpm", delete=False) as tmp_rpm:
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
                subprocess.run(
                    ["sudo", "dnf", "install", "--setopt=assumeyes=1", str(tmp_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to setup ProtonVPN repository: %s", e.stderr)
                tmp_path.unlink(missing_ok=True)
                return False
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            logger.info("ProtonVPN repository already installed")

        # Refresh repositories
        logger.info("Refreshing package repositories...")
        subprocess.run(
            ["sudo", "dnf", "check-update", "--refresh", "--setopt=assumeyes=1"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Install ProtonVPN
        success, error = self.pm.install(["proton-vpn-gnome-desktop"])
        if not success:
            logger.error("Failed to install ProtonVPN GNOME desktop integration: %s", error)
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

    def _install_debian(self) -> bool:
        """Install ProtonVPN on Debian/Ubuntu."""
        logger.info("Installing ProtonVPN for Debian...")

        # Install prerequisites
        success, error = self.pm.install(["wget"])
        if not success:
            logger.error("Failed to install prerequisites: %s", error)
            return False

        repo_package = "protonvpn-stable-release_1.0.8_all.deb"
        repo_url = f"https://repo.protonvpn.com/debian/dists/stable/main/binary-all/{repo_package}"
        expected_checksum = "0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            deb_file = tmp_path / repo_package

            # Download repository package
            logger.info("Downloading ProtonVPN repository package...")
            try:
                subprocess.run(
                    ["wget", "-O", str(deb_file), repo_url],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to download ProtonVPN repository package: %s", e.stderr)
                return False

            # Verify checksum
            logger.info("Verifying package checksum...")
            try:
                sha256_hash = hashlib.sha256()
                with deb_file.open("rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                actual_checksum = sha256_hash.hexdigest()

                if actual_checksum != expected_checksum:
                    logger.error("Checksum verification failed")
                    logger.error("Expected: %s", expected_checksum)
                    logger.error("Actual: %s", actual_checksum)
                    return False
            except OSError as e:
                logger.error("Failed to verify checksum: %s", e)
                return False

            # Install repository package
            logger.info("Installing ProtonVPN repository...")
            try:
                subprocess.run(
                    ["sudo", "dpkg", "-i", str(deb_file)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error("Failed to install ProtonVPN repository package: %s", e.stderr)
                return False

        # Update package lists
        if not self.pm.update_cache():
            logger.error("Failed to update package lists")
            return False

        # Install ProtonVPN
        success, error = self.pm.install(["proton-vpn-gnome-desktop"])
        if not success:
            logger.error("Failed to install ProtonVPN GNOME desktop integration: %s", error)
            return False

        logger.info("ProtonVPN installation completed successfully")
        return True

    def is_installed(self) -> bool:
        """Check if ProtonVPN is installed.

        Returns:
            True if installed, False otherwise
        """
        if self.distro == "fedora" or self.distro == "debian":
            return self.pm.is_installed("proton-vpn-gnome-desktop")
        elif self.distro == "arch":
            return self.pm.is_installed("proton-vpn-gtk-app")
        return False
