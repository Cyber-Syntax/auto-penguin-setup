"""Ueberzugpp installer for image preview in terminals."""

import logging
import subprocess
from pathlib import Path

from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class UeberzugppInstaller(BaseInstaller):
    """Installer for ueberzugpp with OpenSUSE repository setup."""

    def install(self) -> bool:
        """Install ueberzugpp with distro-specific repository setup.

        Returns:
            True if installation successful, False otherwise

        """
        logger.info("Installing ueberzugpp...")

        if self.distro == "fedora":
            return self._install_fedora()
        if self.distro == "arch":
            return self._install_arch()
        if self.distro == "debian":
            return self._install_debian()

        logger.error("Unsupported distribution: %s", self.distro)
        return False

    def _install_fedora(self) -> bool:
        """Install ueberzugpp on Fedora with OpenSUSE repository."""
        logger.info("Adding ueberzugpp repository for Fedora...")

        version = self.distro_info.version

        # Map version to repository name
        repo_map = {
            "40": "Fedora_40",
            "41": "Fedora_41",
            "42": "Fedora_42",
        }

        repo_version = repo_map.get(version, "Fedora_Rawhide")
        if version not in repo_map:
            logger.warning(
                "Unknown Fedora version '%s', using Rawhide repository",
                version,
            )

        repo_url = f"https://download.opensuse.org/repositories/home:justkidding/{repo_version}/home:justkidding.repo"
        logger.info("Adding repository from: %s", repo_url)

        try:
            run_privileged(
                [
                    "dnf",
                    "config-manager",
                    "addrepo",
                    f"--from-repofile={repo_url}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Successfully added ueberzugpp repository")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to add ueberzugpp repository: %s", e.stderr)
            return False

        # Install ueberzugpp
        success, error = self.pm.install(["ueberzugpp"])
        if not success:
            logger.error("Failed to install ueberzugpp: %s", error)
            return False

        logger.info("ueberzugpp installation completed")
        return True

    def _install_arch(self) -> bool:
        """Install ueberzugpp on Arch (available in official repos)."""
        logger.info("Installing ueberzugpp from Arch repositories...")

        success, error = self.pm.install(["ueberzugpp"])
        if not success:
            logger.error("Failed to install ueberzugpp: %s", error)
            return False

        logger.info("ueberzugpp installation completed")
        return True

    def _install_debian(self) -> bool:
        """Install ueberzugpp on Debian/Ubuntu with OpenSUSE repository."""
        logger.info("Adding ueberzugpp repository for Debian/Ubuntu...")

        # Read /etc/os-release for OS ID
        os_id = self.distro_info.id
        version = self.distro_info.version

        # Map version to repository name
        if os_id in ["ubuntu", "pop", "linuxmint"]:
            ubuntu_map = {
                "22.04": "xUbuntu_22.04",
                "23.04": "xUbuntu_23.04",
                "24.04": "xUbuntu_24.04",
                "24.10": "xUbuntu_24.10",
                "25.04": "xUbuntu_25.04",
            }
            repo_name = ubuntu_map.get(version, "xUbuntu_24.04")
            if version not in ubuntu_map:
                logger.warning(
                    "Unknown Ubuntu version '%s', using 24.04 repository",
                    version,
                )
        elif os_id == "debian":
            debian_map = {
                "12": "Debian_12",
                "13": "Debian_13",
            }
            repo_name = debian_map.get(version, "Debian_Testing")
            if version not in debian_map:
                logger.warning(
                    "Unknown Debian version '%s', using Testing repository",
                    version,
                )
        else:
            logger.warning(
                "Unknown Debian-based system, using Debian Testing repository"
            )
            repo_name = "Debian_Testing"

        repo_url = f"http://download.opensuse.org/repositories/home:/justkidding/{repo_name}/"
        key_url = f"https://download.opensuse.org/repositories/home:justkidding/{repo_name}/Release.key"

        logger.info("Adding repository: %s", repo_url)

        # Add repository to sources list
        sources_list = Path("/etc/apt/sources.list.d/home:justkidding.list")
        try:
            run_privileged(
                ["tee", str(sources_list)],
                stdin_input=f"deb {repo_url} /\n",
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to add repository to sources list: %s", e.stderr
            )
            return False

        # Add GPG key
        logger.info("Adding repository GPG key...")
        try:
            # Download key
            key_result = subprocess.run(
                ["curl", "-fsSL", key_url],
                check=True,
                capture_output=True,
                text=True,
            )

            # Dearmor and save
            subprocess.run(
                ["gpg", "--dearmor"],
                input=key_result.stdout.encode("utf-8"),
                check=True,
                capture_output=True,
            )

            run_privileged(
                ["tee", "/etc/apt/trusted.gpg.d/home_justkidding.gpg"],
                stdin_input=key_result.stdout,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to add repository GPG key: %s", e.stderr)
            return False

        # Update package lists
        logger.info("Updating package lists...")
        if not self.pm.update_cache():
            logger.error("Failed to update package lists")
            return False

        # Install ueberzugpp
        success, error = self.pm.install(["ueberzugpp"])
        if not success:
            logger.error("Failed to install ueberzugpp: %s", error)
            return False

        logger.info("ueberzugpp installation completed")
        return True

    def is_installed(self) -> bool:
        """Check if ueberzugpp is installed.

        Returns:
            True if installed, False otherwise

        """
        return self.pm.is_installed("ueberzugpp")
