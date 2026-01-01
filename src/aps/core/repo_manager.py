"""Repository management for COPR and AUR sources."""

import shutil
import subprocess

from aps.core.distro import DistroFamily, DistroInfo
from aps.core.logger import get_logger
from aps.core.package_manager import (
    PackageManager,
    PackageManagerError,
    PacmanManager,
)
from aps.core.package_mapper import PackageMapping
from aps.utils.privilege import run_privileged


class RepositoryManager:
    """Manages third-party repositories across different distributions."""

    def __init__(
        self, distro: DistroInfo, package_manager: PackageManager
    ) -> None:
        """Initialize repository manager.

        Args:
            distro: Distribution information
            package_manager: Package manager instance

        """
        self.distro = distro
        self.pm = package_manager
        self.logger = get_logger(__name__)

    def enable_copr(self, repo: str) -> bool:
        """Enable COPR repository (Fedora only).

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository was enabled successfully

        Raises:
            PackageManagerError: If not running on Fedora

        """
        if self.distro.family != DistroFamily.FEDORA:
            msg = f"COPR is only available on Fedora, not {self.distro.name}"
            raise PackageManagerError(msg)

        self.logger.debug("Enabling COPR repository: %s", repo)
        cmd = ["dnf", "copr", "enable", "-y", repo]
        # Don't capture output - let it display to user
        result = run_privileged(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            self.logger.debug("Successfully enabled COPR repository: %s", repo)
        else:
            self.logger.debug("Failed to enable COPR repository: %s", repo)
        return result.returncode == 0

    def disable_copr(self, repo: str) -> bool:
        """Disable COPR repository (Fedora only).

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository was disabled successfully

        """
        if self.distro.family != DistroFamily.FEDORA:
            msg = f"COPR is only available on Fedora, not {self.distro.name}"
            raise PackageManagerError(msg)

        cmd = ["dnf", "copr", "disable", "-y", repo]
        result = run_privileged(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def is_copr_enabled(self, repo: str) -> bool:
        """Check if COPR repository is enabled.

        Args:
            repo: COPR repository in format "user/repo"

        Returns:
            True if repository is enabled

        """
        if self.distro.family != DistroFamily.FEDORA:
            return False

        # List enabled repos and check if our COPR is present
        cmd = ["dnf", "repolist", "--enabled"]
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return False

        # COPR repos show up with format like
        # copr:copr.fedorainfracloud.org:user:repo
        # Convert "user/repo" to "copr:copr.fedorainfracloud.org:user:repo"
        repo_id = f"copr:copr.fedorainfracloud.org:{repo.replace('/', ':')}"
        return repo_id in result.stdout

    def check_official_before_enabling(
        self, package: str, mapping: "PackageMapping"
    ) -> "PackageMapping":
        """Check if package is in official repos BEFORE enabling COPR/AUR.

        This is the critical timing fix - we check before repo enablement,
        not during installation. If the package is available in official repos,
        we warn the user and return a modified mapping with source="official".

        Args:
            package: Original package name
            mapping: Mapping from pkgmap.ini

        Returns:
            Updated mapping with resolved source
            (either original or "official")

        """
        # Only check third-party mappings (COPR, AUR)
        if not (mapping.is_copr or mapping.is_aur):
            return mapping

        # Check if available in official repos (BEFORE enabling COPR/AUR)
        if self.pm.is_available_in_official_repos(mapping.mapped_name):
            source_type = mapping.source.split(":")[0]  # Extract COPR/AUR
            self.logger.warning(
                "Package '%s' is mapped to %s in pkgmap.ini but is available "
                "in official repositories. Installing from official repos "
                "instead. Consider updating pkgmap.ini to remove the %s "
                "mapping.",
                package,
                source_type,
                source_type,
            )

            # Return new mapping with official source
            return PackageMapping(
                original_name=mapping.original_name,
                mapped_name=mapping.mapped_name,
                source="official",
                category=mapping.category,
            )

        return mapping

    def install_aur_package(self, package: str) -> bool:
        """Install package from AUR (Arch only).

        Args:
            package: AUR package name

        Returns:
            True if package was installed successfully

        Raises:
            PackageManagerError: If not running on Arch or
            no AUR helper available

        """
        if self.distro.family != DistroFamily.ARCH:
            msg = f"AUR is only available on Arch, not {self.distro.name}"
            raise PackageManagerError(msg)

        if not isinstance(self.pm, PacmanManager):
            msg = "Package manager is not PacmanManager"
            raise PackageManagerError(msg)

        return self.pm.install_aur([package])

    def is_flatpak_installed(self) -> bool:
        """Check if flatpak command is available.

        Returns:
            True if flatpak is installed

        """
        return shutil.which("flatpak") is not None

    def ensure_flatpak_installed(self, *, assume_yes: bool = False) -> bool:
        """Ensure flatpak is installed, installing it if necessary.

        Args:
            assume_yes: Auto-confirm installation (default: False)

        Returns:
            True if flatpak is available
            (already installed or successfully installed)

        Raises:
            PackageManagerError: If flatpak installation fails

        """
        if self.is_flatpak_installed():
            self.logger.debug("flatpak is already installed")
            return True

        self.logger.info("flatpak not found, installing...")

        # Install flatpak using system package manager
        success, error = self.pm.install(["flatpak"], assume_yes=assume_yes)
        if not success:
            msg = f"Failed to install flatpak: {error}"
            raise PackageManagerError(msg)

        # Verify installation
        if self.is_flatpak_installed():
            self.logger.info("flatpak installed successfully")
            return True
        msg = "flatpak installation verification failed"
        raise PackageManagerError(msg)

    def enable_flatpak_remote(
        self, remote_name: str, remote_url: str | None = None
    ) -> bool:
        """Enable Flatpak remote repository.

        Args:
            remote_name: Name of the remote (e.g., "flathub")
            remote_url: Optional URL for the remote (uses flathub by default)

        Returns:
            True if remote was enabled successfully

        """
        self.ensure_flatpak_installed()

        if remote_url is None and remote_name.lower() == "flathub":
            remote_url = "https://flathub.org/repo/flathub.flatpakrepo"

        if remote_url is None:
            msg = f"remote_url is required for remote: {remote_name}"
            raise ValueError(msg)

        cmd = [
            "flatpak",
            "remote-add",
            "--if-not-exists",
            remote_name,
            remote_url,
        ]
        result = run_privileged(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def is_flatpak_remote_enabled(self, remote_name: str) -> bool:
        """Check if Flatpak remote is enabled.

        Args:
            remote_name: Name of the remote to check

        Returns:
            True if remote is enabled

        """
        # Ensure flatpak is installed before checking remotes
        if not self.is_flatpak_installed():
            self.logger.debug(
                "flatpak not installed, remote cannot be enabled"
            )
            return False

        cmd = ["flatpak", "remotes"]
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return False

        # Check if remote name appears in output
        return remote_name in result.stdout

    def install_flatpak(self, package: str, remote: str = "flathub") -> bool:
        """Install Flatpak package from remote.

        Args:
            package: Flatpak package ID (e.g., "org.mozilla.firefox")
            remote: Remote name (default: "flathub")

        Returns:
            True if package was installed successfully

        """
        self.ensure_flatpak_installed()

        # Don't use -y flag - let user see and approve permissions
        cmd = ["flatpak", "install", remote, package]
        result = run_privileged(cmd, check=False, capture_output=False)
        return result.returncode == 0

    def remove_flatpak(self, package: str) -> bool:
        """Remove Flatpak package.

        Args:
            package: Flatpak package ID

        Returns:
            True if package was removed successfully

        """
        cmd = ["flatpak", "uninstall", "-y", package]
        result = run_privileged(cmd, capture_output=True, check=False)
        return result.returncode == 0
