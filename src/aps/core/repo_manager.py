"""Repository management for COPR, AUR, and PPA sources."""

import subprocess

from aps.core.distro import DistroFamily, DistroInfo
from aps.core.package_manager import PackageManager, PackageManagerError, PacmanManager


class RepositoryManager:
    """Manages third-party repositories across different distributions."""

    def __init__(self, distro: DistroInfo, package_manager: PackageManager) -> None:
        """
        Initialize repository manager.

        Args:
            distro: Distribution information
            package_manager: Package manager instance
        """
        self.distro = distro
        self.pm = package_manager

    def enable_copr(self, repo: str) -> bool:
        """
        Enable COPR repository (Fedora only).

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository was enabled successfully

        Raises:
            PackageManagerError: If not running on Fedora
        """
        if self.distro.family != DistroFamily.FEDORA:
            raise PackageManagerError(f"COPR is only available on Fedora, not {self.distro.name}")

        cmd = ["sudo", "dnf", "copr", "enable", "-y", repo]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def disable_copr(self, repo: str) -> bool:
        """
        Disable COPR repository (Fedora only).

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository was disabled successfully
        """
        if self.distro.family != DistroFamily.FEDORA:
            raise PackageManagerError(f"COPR is only available on Fedora, not {self.distro.name}")

        cmd = ["sudo", "dnf", "copr", "disable", "-y", repo]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def is_copr_enabled(self, repo: str) -> bool:
        """
        Check if COPR repository is enabled.

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository is enabled
        """
        if self.distro.family != DistroFamily.FEDORA:
            return False

        # List enabled repos and check if our COPR is present
        cmd = ["dnf", "repolist", "enabled"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # COPR repos show up with format like "copr:copr.fedorainfracloud.org:user:repo"
        repo_id = repo.replace("/", ":")
        return repo_id in result.stdout

    def install_aur_package(self, package: str) -> bool:
        """
        Install package from AUR (Arch only).

        Args:
            package: AUR package name

        Returns:
            True if package was installed successfully

        Raises:
            PackageManagerError: If not running on Arch or no AUR helper available
        """
        if self.distro.family != DistroFamily.ARCH:
            raise PackageManagerError(f"AUR is only available on Arch, not {self.distro.name}")

        if not isinstance(self.pm, PacmanManager):
            raise PackageManagerError("Package manager is not PacmanManager")

        return self.pm.install_aur([package])

    def add_ppa(self, ppa: str) -> bool:
        """
        Add PPA repository (Ubuntu/Debian only).

        Args:
            ppa: PPA in format "user/repo"

        Returns:
            True if PPA was added successfully

        Raises:
            PackageManagerError: If not running on Ubuntu/Debian
        """
        if self.distro.family != DistroFamily.DEBIAN:
            raise PackageManagerError(
                f"PPA is only available on Debian/Ubuntu, not {self.distro.name}"
            )

        cmd = ["sudo", "add-apt-repository", "-y", f"ppa:{ppa}"]
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0:
            # Update apt cache after adding PPA
            self.pm.update_cache()
            return True

        return False

    def remove_ppa(self, ppa: str) -> bool:
        """
        Remove PPA repository (Ubuntu/Debian only).

        Args:
            ppa: PPA in format "user/repo"

        Returns:
            True if PPA was removed successfully
        """
        if self.distro.family != DistroFamily.DEBIAN:
            raise PackageManagerError(
                f"PPA is only available on Debian/Ubuntu, not {self.distro.name}"
            )

        cmd = ["sudo", "add-apt-repository", "-y", "--remove", f"ppa:{ppa}"]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def enable_flatpak_remote(self, remote_name: str, remote_url: str | None = None) -> bool:
        """
        Enable Flatpak remote repository.

        Args:
            remote_name: Name of the remote (e.g., "flathub")
            remote_url: Optional URL for the remote (uses flathub by default)

        Returns:
            True if remote was enabled successfully
        """
        if remote_url is None and remote_name.lower() == "flathub":
            remote_url = "https://flathub.org/repo/flathub.flatpakrepo"

        if remote_url is None:
            raise ValueError(f"remote_url is required for remote: {remote_name}")

        cmd = ["sudo", "flatpak", "remote-add", "--if-not-exists", remote_name, remote_url]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def is_flatpak_remote_enabled(self, remote_name: str) -> bool:
        """
        Check if Flatpak remote is enabled.

        Args:
            remote_name: Name of the remote to check

        Returns:
            True if remote is enabled
        """
        cmd = ["flatpak", "remotes"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return False

        # Check if remote name appears in output
        return remote_name in result.stdout

    def install_flatpak(self, package: str, remote: str = "flathub") -> bool:
        """
        Install Flatpak package from remote.

        Args:
            package: Flatpak package ID (e.g., "org.mozilla.firefox")
            remote: Remote name (default: "flathub")

        Returns:
            True if package was installed successfully
        """
        cmd = ["sudo", "flatpak", "install", "-y", remote, package]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    def remove_flatpak(self, package: str) -> bool:
        """
        Remove Flatpak package.

        Args:
            package: Flatpak package ID

        Returns:
            True if package was removed successfully
        """
        cmd = ["sudo", "flatpak", "uninstall", "-y", package]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
