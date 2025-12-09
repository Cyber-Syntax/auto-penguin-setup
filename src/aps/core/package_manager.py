"""Package manager abstraction for cross-distro package operations."""

import logging
import shutil
import subprocess
from abc import ABC, abstractmethod

from aps.core.distro import DistroFamily, DistroInfo


class PackageManagerError(Exception):
    """Base exception for package manager operations."""

    pass


class PackageManager(ABC):
    """Abstract base class for package manager implementations."""

    def __init__(self, distro: DistroInfo) -> None:
        """
        Initialize package manager.

        Args:
            distro: Distribution information
        """
        self.distro = distro

    @abstractmethod
    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        """
        Install packages.

        Args:
            packages: List of package names to install
            assume_yes: Auto-confirm installation (default: True)

        Returns:
            Tuple of (success: bool, error_message: str)
            error_message is empty string if success
        """
        pass

    @abstractmethod
    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        """
        Remove packages.

        Args:
            packages: List of package names to remove
            assume_yes: Auto-confirm removal (default: True)

        Returns:
            Tuple of (success: bool, error_message: str)
            error_message is empty string if success
        """
        pass

    @abstractmethod
    def search(self, query: str) -> list[str]:
        """
        Search for packages matching query.

        Args:
            query: Search query string

        Returns:
            List of matching package names
        """
        pass

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """
        Check if a package is installed.

        Args:
            package: Package name to check

        Returns:
            True if package is installed, False otherwise
        """
        pass

    @abstractmethod
    def update_cache(self) -> bool:
        """
        Update package manager cache/database.

        Returns:
            True if update succeeded, False otherwise
        """
        pass


class DnfManager(PackageManager):
    """Package manager for Fedora and RHEL-based distributions using dnf."""

    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "dnf", "install"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to install packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "dnf", "remove"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["dnf", "search", "--quiet", query]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            return []

        packages = []
        for line in result.stdout.splitlines():
            if "." in line and ":" in line:
                # Format: "package.arch : description"
                package = line.split(":")[0].strip()
                packages.append(package)

        return packages

    def is_installed(self, package: str) -> bool:
        cmd = ["rpm", "-q", package]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "dnf", "makecache"]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0


class PacmanManager(PackageManager):
    """Package manager for Arch-based distributions using pacman."""

    def __init__(self, distro: DistroInfo) -> None:
        super().__init__(distro)
        self.aur_helper = self._detect_aur_helper()

    def _detect_aur_helper(self) -> str | None:
        """
        Detect available AUR helper.

        Preference order: paru > yay > None

        Returns:
            Name of AUR helper if found, None otherwise
        """
        for helper in ["paru", "yay"]:
            if shutil.which(helper):
                return helper
        return None

    def install_paru(self, assume_yes: bool = True) -> bool:
        """
        Install paru AUR helper.

        Args:
            assume_yes: Auto-confirm installation

        Returns:
            True if paru was installed successfully, False otherwise
        """
        import os
        import tempfile

        logger = logging.getLogger(__name__)
        logger.info("Installing paru AUR helper...")

        # Check if paru is already installed
        if shutil.which("paru"):
            logger.info("paru is already installed")
            return True

        # Install base-devel first
        logger.info("Installing base-devel...")
        cmd = ["sudo", "pacman", "-S", "--needed"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.append("base-devel")

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            logger.error("Failed to install base-devel")
            return False

        # Clone and build paru
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info("Cloning paru from AUR...")
            clone_cmd = ["git", "clone", "https://aur.archlinux.org/paru.git"]
            result = subprocess.run(clone_cmd, cwd=tmpdir, check=False)
            if result.returncode != 0:
                logger.error("Failed to clone paru repository")
                return False

            paru_dir = os.path.join(tmpdir, "paru")
            logger.info("Building paru...")
            build_cmd = ["makepkg", "-si"]
            if assume_yes:
                build_cmd.append("--noconfirm")

            result = subprocess.run(build_cmd, cwd=paru_dir, check=False)
            if result.returncode != 0:
                logger.error("Failed to build and install paru")
                return False

        # Verify installation
        if shutil.which("paru"):
            logger.info("paru installed successfully")
            self.aur_helper = "paru"
            return True
        else:
            logger.error("paru installation verification failed")
            return False

    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        logger = logging.getLogger(__name__)
        logger.info("Installing packages: %s", ", ".join(packages))

        cmd = ["sudo", "pacman", "-S", "--needed"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        # Don't capture output - let it display to user
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            logger.info("Successfully installed packages")
            return True, ""
        else:
            logger.error("Failed to install packages %s", packages)
            return False, "Package installation failed"

    def install_aur(self, packages: list[str], assume_yes: bool = True) -> bool:
        """
        Install packages from AUR using detected helper.

        Args:
            packages: List of AUR package names
            assume_yes: Auto-confirm installation

        Returns:
            True if installation succeeded, False otherwise

        Raises:
            PackageManagerError: If no AUR helper is available and installation fails
        """
        logger = logging.getLogger(__name__)

        if not self.aur_helper:
            logger.info("No AUR helper found. Installing paru...")
            if not self.install_paru(assume_yes=assume_yes):
                raise PackageManagerError("Failed to install paru AUR helper")

        logger.info("Installing AUR packages: %s", ", ".join(packages))

        cmd = [self.aur_helper, "-S"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        # Don't capture output - let it display to user
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            logger.info("Successfully installed AUR packages")
            return True
        else:
            logger.error("Failed to install AUR packages")
            return False

    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "pacman", "-R"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["pacman", "-Ss", query]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            return []

        packages = []
        for line in result.stdout.splitlines():
            # Format: "repo/package version"
            if "/" in line and not line.startswith(" "):
                package = line.split()[0].split("/")[1]
                packages.append(package)

        return packages

    def is_installed(self, package: str) -> bool:
        cmd = ["pacman", "-Q", package]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "pacman", "-Sy"]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0


class AptManager(PackageManager):
    """Package manager for Debian and Ubuntu-based distributions using apt."""

    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "apt-get", "install"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        # Set DEBIAN_FRONTEND to avoid interactive prompts
        env = {"DEBIAN_FRONTEND": "noninteractive"}
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to install packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "apt-get", "remove"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        env = {"DEBIAN_FRONTEND": "noninteractive"}
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["apt-cache", "search", query]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            return []

        packages = []
        for line in result.stdout.splitlines():
            # Format: "package - description"
            if " - " in line:
                package = line.split(" - ")[0].strip()
                packages.append(package)

        return packages

    def is_installed(self, package: str) -> bool:
        cmd = ["dpkg", "-s", package]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "apt-get", "update"]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0


def get_package_manager(distro: DistroInfo) -> PackageManager:
    """
    Factory function to get appropriate package manager for distribution.

    Args:
        distro: Distribution information

    Returns:
        PackageManager instance for the distribution

    Raises:
        ValueError: If distribution is not supported
    """
    match distro.family:
        case DistroFamily.FEDORA:
            return DnfManager(distro)
        case DistroFamily.ARCH:
            return PacmanManager(distro)
        case DistroFamily.DEBIAN:
            return AptManager(distro)
        case _:
            raise ValueError(
                f"Unsupported distribution family: {distro.family}. "
                f"Supported families: Fedora, Arch, Debian"
            )
