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

        result = subprocess.run(cmd, capture_output=True, text=True)
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

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["dnf", "search", "--quiet", query]
        result = subprocess.run(cmd, capture_output=True, text=True)

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
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "dnf", "makecache"]
        result = subprocess.run(cmd, capture_output=True)
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

    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "pacman", "-S", "--needed"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to install packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def install_aur(self, packages: list[str], assume_yes: bool = True) -> bool:
        """
        Install packages from AUR using detected helper.

        Args:
            packages: List of AUR package names
            assume_yes: Auto-confirm installation

        Returns:
            True if installation succeeded, False otherwise

        Raises:
            PackageManagerError: If no AUR helper is available
        """
        if not self.aur_helper:
            raise PackageManagerError("No AUR helper found. Please install paru or yay.")

        cmd = [self.aur_helper, "-S"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["sudo", "pacman", "-R"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["pacman", "-Ss", query]
        result = subprocess.run(cmd, capture_output=True, text=True)

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
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "pacman", "-Sy"]
        result = subprocess.run(cmd, capture_output=True)
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
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
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
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error("Failed to remove packages %s: %s", packages, result.stderr)
            return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["apt-cache", "search", query]
        result = subprocess.run(cmd, capture_output=True, text=True)

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
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def update_cache(self) -> bool:
        cmd = ["sudo", "apt-get", "update"]
        result = subprocess.run(cmd, capture_output=True)
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
