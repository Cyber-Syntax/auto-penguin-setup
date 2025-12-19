"""Package manager abstraction for cross-distro package operations."""

import shutil
import subprocess
from abc import ABC, abstractmethod

from aps.core.distro import DistroFamily, DistroInfo
from aps.utils.privilege import run_privileged

from .logger import get_logger

logger = get_logger(__name__)


class PackageManagerError(Exception):
    """Base exception for package manager operations."""

    pass


class PackageManager(ABC):
    """Abstract base class for package manager implementations."""

    def __init__(self, distro: DistroInfo) -> None:
        """Initialize package manager.

        Args:
            distro: Distribution information

        """
        self.distro = distro

    @abstractmethod
    def install(
        self, packages: list[str], assume_yes: bool = False
    ) -> tuple[bool, str]:
        """Install packages.

        Args:
            packages: List of package names to install
            assume_yes: Auto-confirm installation (default: False)

        Returns:
            Tuple of (success: bool, error_message: str)
            error_message is empty string if success

        """
        pass

    @abstractmethod
    def remove(
        self, packages: list[str], assume_yes: bool = False
    ) -> tuple[bool, str]:
        """Remove packages.

        Args:
            packages: List of package names to remove
            assume_yes: Auto-confirm removal (default: False)

        Returns:
            Tuple of (success: bool, error_message: str)
            error_message is empty string if success

        """
        pass

    @abstractmethod
    def search(self, query: str) -> list[str]:
        """Search for packages matching query.

        Args:
            query: Search query string

        Returns:
            List of matching package names

        """
        pass

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """Check if a package is installed.

        Args:
            package: Package name to check

        Returns:
            True if package is installed, False otherwise

        """
        pass

    @abstractmethod
    def update_cache(self) -> bool:
        """Update package manager cache/database.

        Returns:
            True if update succeeded, False otherwise

        """
        pass

    @abstractmethod
    def is_available_in_official_repos(self, package: str) -> bool:
        """Check if package is available in official repositories.

        Args:
            package: Package name to check

        Returns:
            True if package is available in official repos, False otherwise

        """
        pass


class DnfManager(PackageManager):
    """Package manager for Fedora and RHEL-based distributions using dnf."""

    def install(
        self, packages: list[str], assume_yes: bool = False
    ) -> tuple[bool, str]:
        logger.info("Installing packages: %s", ", ".join(packages))

        cmd: list[str] = ["dnf", "install"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        logger.debug("Executing command: %s", " ".join(cmd))
        # Don't capture output - let it display to user
        result = run_privileged(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            logger.info("Successfully installed packages")
            return True, ""
        logger.error("Failed to install packages %s", packages)
        return False, "Package installation failed"

    def remove(
        self, packages: list[str], assume_yes: bool = True
    ) -> tuple[bool, str]:
        logger.info("Removing packages: %s", ", ".join(packages))

        cmd: list[str] = ["dnf", "remove"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(packages)

        logger.debug("Executing command: %s", " ".join(cmd))
        # Don't capture output - let it display to user
        result = run_privileged(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            logger.info("Successfully removed packages")
            return True, ""
        logger.error("Failed to remove packages %s", packages)
        return False, "Package removal failed"

    def search(self, query: str) -> list[str]:
        cmd: list[str] = ["dnf", "search", "--quiet", query]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return []

        packages: list[str] = []
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
        cmd = ["dnf", "makecache"]
        result = run_privileged(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def is_available_in_official_repos(self, package: str) -> bool:
        """Check if package is available in official Fedora repositories.

        This should be called BEFORE enabling COPR repos. When called before
        COPR repos are enabled, dnf repoquery will only find packages in
        official repositories (fedora, updates, etc.).

        Uses 'dnf repoquery' to check availability, then 'dnf list' to verify
        the package is not from an already-enabled COPR repo.

        Args:
            package: Package name to check

        Returns:
            True if package is available in official repos, False otherwise

        """
        # First check if package exists at all
        cmd = ["dnf", "repoquery", package]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0 or not result.stdout.strip():
            return False

        # Package found - verify it's not from an already-enabled COPR repo
        # by checking with dnf list to see which repo provides it
        list_cmd = ["dnf", "list", package]
        list_result = subprocess.run(
            list_cmd, capture_output=True, text=True, check=False
        )

        if list_result.returncode == 0:
            # Check if output contains "copr:" which indicates COPR repo
            if "copr:" in list_result.stdout.lower():
                logger.debug(
                    "Package %s found but from COPR repo, not official",
                    package,
                )
                return False
            return True

        return False


class PacmanManager(PackageManager):
    """Package manager for Arch-based distributions using pacman."""

    def __init__(self, distro: DistroInfo) -> None:
        super().__init__(distro)
        self.aur_helper = self._detect_aur_helper()

    def _detect_aur_helper(self) -> str | None:
        """Detect available AUR helper.

        Preference order: paru > yay > None

        Returns:
            Name of AUR helper if found, None otherwise

        """
        for helper in ["paru", "yay"]:
            if shutil.which(helper):
                return helper
        return None

    def install_paru(self, assume_yes: bool = False) -> bool:
        """Install paru AUR helper.

        Args:
            assume_yes: Auto-confirm installation

        Returns:
            True if paru was installed successfully, False otherwise

        """
        import tempfile

        logger.info("Installing paru AUR helper...")

        # Check if paru is already installed
        if shutil.which("paru"):
            logger.info("paru is already installed")
            return True

        # Install base-devel first
        logger.info("Installing base-devel...")
        cmd = ["pacman", "-S", "--needed"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.append("base-devel")

        result = run_privileged(cmd, check=False, capture_output=False)
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

            from pathlib import Path

            paru_dir = Path(tmpdir) / "paru"
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
        logger.error("paru installation verification failed")
        return False

    def install(
        self, packages: list[str], assume_yes: bool = False
    ) -> tuple[bool, str]:
        logger.info("Installing packages: %s", ", ".join(packages))

        cmd = ["pacman", "-S", "--needed"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        logger.debug("Executing command: %s", " ".join(cmd))
        # Don't capture output - let it display to user
        result = run_privileged(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            logger.info("Successfully installed packages")
            return True, ""
        logger.error("Failed to install packages %s", packages)
        return False, "Package installation failed"

    def install_aur(
        self, packages: list[str], assume_yes: bool = False
    ) -> bool:
        """Install packages from AUR using detected helper.

        Args:
            packages: List of AUR package names
            assume_yes: Auto-confirm installation (default: False)

        Returns:
            True if installation succeeded, False otherwise

        Raises:
            PackageManagerError: If no AUR helper is available and installation fails

        """
        if not self.aur_helper:
            logger.info("No AUR helper found. Installing paru...")
            if not self.install_paru(assume_yes=assume_yes):
                raise PackageManagerError("Failed to install paru AUR helper")

        logger.info("Installing AUR packages: %s", ", ".join(packages))

        # aur_helper should be set at this point
        if not self.aur_helper:
            raise PackageManagerError("AUR helper not available")

        cmd = [self.aur_helper, "-S"]
        # Note: Do NOT use --noconfirm for AUR installs to allow interactive conflict resolution
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        logger.debug("Executing command: %s", " ".join(cmd))
        # Don't capture output - let it display to user
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            logger.info("Successfully installed AUR packages")
            return True
        logger.error("Failed to install AUR packages")
        return False

    def remove(
        self, packages: list[str], assume_yes: bool = False
    ) -> tuple[bool, str]:
        """Remove packages.

        Args:
            packages: List of package names to remove
            assume_yes: Auto-confirm removal (default: False)

        Returns:
            Tuple of (success: bool, error_message: str)
            error_message is empty string if success

        """
        cmd = ["pacman", "-R"]
        if assume_yes:
            cmd.append("--noconfirm")
        cmd.extend(packages)

        logger.debug("Executing command: %s", " ".join(cmd))
        result = run_privileged(
            cmd, capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return True, ""
        logger.error(
            "Failed to remove packages %s: %s", packages, result.stderr
        )
        return False, result.stderr

    def search(self, query: str) -> list[str]:
        cmd = ["pacman", "-Ss", query]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

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
        cmd = ["pacman", "-Sy"]
        result = run_privileged(cmd, capture_output=True, check=False)
        return result.returncode == 0

    def is_available_in_official_repos(self, package: str) -> bool:
        """Check if package is available in official Arch repositories.

        Uses 'pacman -Ss' to check core, extra, and community repos.
        Excludes AUR and other third-party repos.

        Args:
            package: Package name to check

        Returns:
            True if package is available in official repos, False otherwise

        """
        cmd = ["pacman", "-Ss", f"^{package}$"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return False

        # Check if package is in official repos (core, extra, community)
        # Format: "repo/package version"
        for line in result.stdout.splitlines():
            if "/" in line and not line.startswith(" "):
                repo_pkg = line.split()[0]
                repo = repo_pkg.split("/")[0]
                pkg = repo_pkg.split("/")[1]
                # Check if it's in official repos and matches exact package name
                if pkg == package and repo in [
                    "core",
                    "extra",
                    "community",
                    "multilib",
                ]:
                    return True
        return False


def get_package_manager(distro: DistroInfo) -> PackageManager:
    """Factory function to get appropriate package manager for distribution.

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
        case _:
            raise ValueError(
                f"Unsupported distribution family: {distro.family}. "
                f"Supported families: Fedora, Arch"
            )
