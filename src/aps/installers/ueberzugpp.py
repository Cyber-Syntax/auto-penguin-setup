"""Ueberzugpp installer for image preview in terminals."""

import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = get_logger(__name__)


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

    def is_installed(self) -> bool:
        """Check if ueberzugpp is installed.

        Returns:
            True if installed, False otherwise

        """
        return self.pm.is_installed("ueberzugpp")
