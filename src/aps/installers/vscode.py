"""Visual Studio Code installer module."""

import logging
import subprocess
from pathlib import Path

from aps.utils.privilege import run_privileged

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class VSCodeInstaller(BaseInstaller):
    """Installer for Visual Studio Code with distro-specific repository setup."""

    def install(self) -> bool:
        """Install Visual Studio Code with appropriate repository configuration.

        Returns:
            bool: True if installation was successful, False otherwise.

        """
        logger.info("Installing Visual Studio Code...")

        if self.distro in ("fedora", "rhel", "nobara"):
            return self._install_fedora()
        if self.distro in ("arch", "archlinux", "manjaro", "cachyos"):
            return self._install_arch()
        if self.distro in ("debian", "ubuntu", "linuxmint", "pop"):
            return self._install_debian()
        logger.error("Unsupported distribution: %s", self.distro)
        return False

    def _install_fedora(self) -> bool:
        """Install VS Code on Fedora-based distributions.

        Returns:
            bool: True if installation was successful, False otherwise.

        """

        def install_with_repo() -> bool:
            """Fallback: Add Microsoft repo and install."""
            logger.info("Adding Visual Studio Code repository for Fedora...")

            if not self._import_microsoft_gpg_rpm():
                logger.error("Failed to import Microsoft GPG key")
                return False

            if not self._create_fedora_repo():
                logger.error("Failed to create VS Code repository file")
                return False

            if not self.pm.update_cache():
                logger.warning("Repository update had warnings, continuing...")

            success, error = self.pm.install(["vscode"])
            if not success:
                logger.error("Failed to install Visual Studio Code: %s", error)
                return False

            logger.info("Visual Studio Code installation completed.")
            return True

        # Try official repos first (Nobara might have it)
        return self.try_official_first("vscode", install_with_repo)

    def _install_arch(self) -> bool:
        """Install VS Code on Arch-based distributions.

        Returns:
            bool: True if installation was successful, False otherwise.

        """

        def install_from_aur() -> bool:
            """Fallback: Install from AUR."""
            logger.info("Installing Visual Studio Code from AUR...")

            # Import here to avoid unused import if not Arch
            from aps.core.package_manager import PacmanManager

            try:
                if isinstance(self.pm, PacmanManager):
                    success = self.pm.install_aur(["visual-studio-code-bin"])
                    if not success:
                        logger.error("Failed to install Visual Studio Code")
                        return False
                    logger.info("Visual Studio Code installation completed.")
                    return True

                logger.error(
                    "AUR install not supported with this package manager instance."
                )
                return False
            except Exception as e:
                logger.error("Failed to install Visual Studio Code: %s", e)
                return False

        # Try official repos first (package might be 'vscode' in extra repo)
        return self.try_official_first("vscode", install_from_aur)

    def _install_debian(self) -> bool:
        """Install VS Code on Debian-based distributions.

        Returns:
            bool: True if installation was successful, False otherwise.

        """
        logger.info("Adding Visual Studio Code repository for Debian...")

        if not self._install_debian_prerequisites():
            logger.error("Failed to install prerequisites")
            return False

        if not self._import_microsoft_gpg_debian():
            logger.error("Failed to import Microsoft GPG key")
            return False

        if not self._create_debian_repo():
            logger.error("Failed to add VS Code repository")
            return False

        if not self.pm.update_cache():
            logger.error("Failed to update package lists")
            return False

        success, error = self.pm.install(["vscode"])
        if not success:
            logger.error("Failed to install Visual Studio Code: %s", error)
            return False

        logger.info("Visual Studio Code installation completed.")
        return True

    def _import_microsoft_gpg_rpm(self) -> bool:
        """Import Microsoft GPG key for RPM-based systems.

        Returns:
            bool: True if successful, False otherwise.

        """
        try:
            result = run_privileged(
                [
                    "rpm",
                    "--import",
                    "https://packages.microsoft.com/keys/microsoft.asc",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error("Error importing GPG key: %s", e)
            return False

    def _create_fedora_repo(self) -> bool:
        """Create VS Code repository file for Fedora.

        Returns:
            bool: True if successful, False otherwise.

        """
        repo_file = Path("/etc/yum.repos.d/vscode.repo")

        if repo_file.exists():
            logger.debug("Repository file already exists")
            return True

        repo_content = """[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc"""

        try:
            result = run_privileged(
                ["tee", str(repo_file)],
                stdin_input=repo_content,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error("Error creating repository file: %s", e)
            return False

    def _install_debian_prerequisites(self) -> bool:
        """Install prerequisites for Debian-based systems.

        Returns:
            bool: True if successful, False otherwise.

        """
        success, error = self.pm.install(["wget", "gpg"])
        if not success:
            logger.error("Failed to install prerequisites: %s", error)
            return False
        return True

    def _import_microsoft_gpg_debian(self) -> bool:
        """Import Microsoft GPG key for Debian-based systems.

        Returns:
            bool: True if successful, False otherwise.

        """
        try:
            wget_process = subprocess.Popen(
                [
                    "wget",
                    "-qO-",
                    "https://packages.microsoft.com/keys/microsoft.asc",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            gpg_process = subprocess.Popen(
                ["gpg", "--dearmor"],
                stdin=wget_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if wget_process.stdout:
                wget_process.stdout.close()

            gpg_output, _ = gpg_process.communicate()

            if gpg_process.returncode != 0:
                return False

            result = run_privileged(
                ["tee", "/usr/share/keyrings/packages.microsoft.gpg"],
                stdin_input=gpg_output.decode()
                if isinstance(gpg_output, bytes)
                else gpg_output,
                capture_output=True,
                check=False,
            )

            if result.returncode != 0:
                return False

            result = run_privileged(
                [
                    "install",
                    "-D",
                    "-o",
                    "root",
                    "-g",
                    "root",
                    "-m",
                    "644",
                    "/usr/share/keyrings/packages.microsoft.gpg",
                    "/usr/share/keyrings/packages.microsoft.gpg",
                ],
                capture_output=True,
                check=False,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error("Error importing GPG key: %s", e)
            return False

    def _create_debian_repo(self) -> bool:
        """Create VS Code repository file for Debian.

        Returns:
            bool: True if successful, False otherwise.

        """
        repo_content = (
            "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/packages.microsoft.gpg] "
            "https://packages.microsoft.com/repos/code stable main"
        )

        try:
            result = run_privileged(
                ["tee", "/etc/apt/sources.list.d/vscode.list"],
                stdin_input=repo_content,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error("Error creating repository file: %s", e)
            return False
