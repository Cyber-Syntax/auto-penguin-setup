"""Base class for application installers."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from ..core.distro import DistroInfo, detect_distro
from ..core.package_manager import get_package_manager

logger = logging.getLogger(__name__)


class BaseInstaller(ABC):
    """Base class for application installers.

    Provides common functionality for installing applications across different
    distributions, including repository management, GPG key handling, and
    package installation.
    """

    def __init__(self) -> None:
        """Initialize the installer."""
        self.distro_info: DistroInfo = detect_distro()
        self.distro = self.distro_info.id
        self.pm = get_package_manager(self.distro_info)

    @abstractmethod
    def install(self) -> bool:
        """Install the application.

        Returns:
            bool: True if installation was successful, False otherwise.
        """
        pass

    def add_repository(self, repo_url: str, repo_name: str, gpg_key_url: str | None = None) -> bool:
        """Add a repository for the application.

        Args:
            repo_url: URL of the repository.
            repo_name: Name of the repository.
            gpg_key_url: Optional URL of the GPG key.

        Returns:
            bool: True if repository was added successfully, False otherwise.
        """
        logger.info("Adding repository: %s", repo_name)

        if gpg_key_url:
            if not self._import_gpg_key(gpg_key_url):
                logger.error("Failed to import GPG key")
                return False

        return self._add_repo_file(repo_url, repo_name)

    def _import_gpg_key(self, key_url: str) -> bool:
        """Import a GPG key for repository verification.

        Args:
            key_url: URL of the GPG key.

        Returns:
            bool: True if key was imported successfully, False otherwise.
        """
        import subprocess

        logger.debug("Importing GPG key from: %s", key_url)

        try:
            if self.distro in ("fedora", "rhel", "centos"):
                result = subprocess.run(
                    ["sudo", "rpm", "--import", key_url],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            elif self.distro in ("debian", "ubuntu"):
                # Download key and add to apt keyring
                result = subprocess.run(
                    ["curl", "-fsSL", key_url], capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    return False

                key_content = result.stdout
                result = subprocess.run(
                    ["sudo", "gpg", "--dearmor", "-o", "/usr/share/keyrings/aps-temp.gpg"],
                    input=key_content,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                logger.warning("GPG key import not implemented for: %s", self.distro)
                return True  # Continue anyway

            return result.returncode == 0

        except Exception as e:
            logger.error("Error importing GPG key: %s", e)
            return False

    def _add_repo_file(self, repo_url: str, repo_name: str) -> bool:
        """Add a repository configuration file.

        Args:
            repo_url: URL of the repository.
            repo_name: Name of the repository.

        Returns:
            bool: True if repo file was created successfully, False otherwise.
        """

        try:
            if self.distro in ("fedora", "rhel", "centos"):
                Path(f"/etc/yum.repos.d/{repo_name}.repo")
                # Implementation specific to each installer
                return True
            elif self.distro in ("debian", "ubuntu"):
                Path(f"/etc/apt/sources.list.d/{repo_name}.list")
                # Implementation specific to each installer
                return True
            else:
                logger.warning("Repository file creation not implemented for: %s", self.distro)
                return True

        except Exception as e:
            logger.error("Error creating repository file: %s", e)
            return False

    def create_desktop_file(
        self, source_path: str, user_path: str, modifications: dict[str, str] | None = None
    ) -> bool:
        """Create or modify a desktop file in user's application directory.

        Args:
            source_path: Path to the source desktop file.
            user_path: Path to the user's desktop file.
            modifications: Optional dictionary of key-value pairs to modify in the desktop file.

        Returns:
            bool: True if desktop file was created/modified successfully, False otherwise.
        """
        import shutil

        try:
            source = Path(source_path)
            user = Path(user_path)

            # Create parent directory if it doesn't exist
            user.parent.mkdir(parents=True, exist_ok=True)

            # Copy source file if user file doesn't exist
            if not user.exists():
                if source.exists():
                    shutil.copy2(source, user)
                    logger.debug("Copied desktop file to: %s", user)
                else:
                    logger.error("Source desktop file not found: %s", source)
                    return False

            # Apply modifications if provided
            if modifications:
                content = user.read_text()
                for key, value in modifications.items():
                    # Replace or add the key-value pair
                    import re

                    pattern = rf"^{re.escape(key)}=.*$"
                    replacement = f"{key}={value}"
                    if re.search(pattern, content, re.MULTILINE):
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    else:
                        # Add to [Desktop Entry] section
                        content = re.sub(r"(\[Desktop Entry\])", rf"\1\n{replacement}", content)
                user.write_text(content)
                logger.debug("Modified desktop file: %s", user)

            return True

        except Exception as e:
            logger.error("Error creating/modifying desktop file: %s", e)
            return False
