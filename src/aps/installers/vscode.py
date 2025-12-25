"""Visual Studio Code installer module."""

from collections.abc import Callable
from pathlib import Path

from aps.core.distro import DistroInfo, detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import PackageManager, get_package_manager
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:
    """Install Visual Studio Code with appropriate repository configuration.

    Args:
        distro: Distribution ID (optional, auto-detected if not provided).

    Returns:
        True if installation was successful, False otherwise.

    """
    distro_info: DistroInfo = detect_distro()
    distro_id = distro or distro_info.id
    pm = get_package_manager(distro_info)

    logger.info("Installing Visual Studio Code...")

    if distro_id in ("fedora", "rhel", "nobara"):
        return _install_fedora(pm, distro_info)
    if distro_id in ("arch", "archlinux", "manjaro", "cachyos"):
        return _install_arch(pm, distro_info)
    logger.error("Unsupported distribution: %s", distro_id)
    return False


def _install_fedora(pm: PackageManager, distro_info: DistroInfo) -> bool:  # noqa: ARG001
    """Install VS Code on Fedora-based distributions.

    Args:
        pm: Package manager instance.
        distro_info: Distribution information.

    Returns:
        True if installation was successful, False otherwise.

    """

    def install_with_repo() -> bool:
        """Fallback: Add Microsoft repo and install."""
        logger.info("Adding Visual Studio Code repository for Fedora...")

        if not _import_microsoft_gpg_rpm():
            logger.error("Failed to import Microsoft GPG key")
            return False

        if not _create_fedora_repo():
            logger.error("Failed to create VS Code repository file")
            return False

        if not pm.update_cache():
            logger.warning("Repository update had warnings, continuing...")

        success, error = pm.install(["vscode"])
        if not success:
            logger.error("Failed to install Visual Studio Code: %s", error)
            return False

        logger.info("Visual Studio Code installation completed.")
        return True

    # Try official repos first (Nobara might have it)
    return _try_official_first(pm, "vscode", install_with_repo)


def _install_arch(pm: PackageManager, distro_info: DistroInfo) -> bool:  # noqa: ARG001
    """Install VS Code on Arch-based distributions.

    Args:
        pm: Package manager instance.
        distro_info: Distribution information.

    Returns:
        True if installation was successful, False otherwise.

    """

    def install_from_aur() -> bool:
        """Fallback: Install from AUR."""
        logger.info("Installing Visual Studio Code from AUR...")

        from aps.core.package_manager import PacmanManager  # noqa: PLC0415

        try:
            if isinstance(pm, PacmanManager):
                success = pm.install_aur(["visual-studio-code-bin"])
                if not success:
                    logger.error("Failed to install Visual Studio Code")
                    return False
                logger.info("Visual Studio Code installation completed.")
                return True

            logger.error(
                "AUR install not supported with this package manager instance."
            )
        except Exception:
            logger.exception("Failed to install Visual Studio Code")
        return False

    # Try official repos first (package might be 'vscode' in extra repo)
    return _try_official_first(pm, "vscode", install_from_aur)


def _try_official_first(
    pm: PackageManager,
    official_name: str,
    fallback_install: Callable[[], bool],
) -> bool:
    """Try installing from official repos first, fall back to custom method.

    Args:
        pm: Package manager instance.
        official_name: Package name to check in official repos.
        fallback_install: Function to call if not in official repos.

    Returns:
        True if installation succeeded (from either source).

    """
    if pm.is_available_in_official_repos(official_name):
        logger.info(
            "Package '%s' found in official repositories, "
            "installing from official",
            official_name,
        )
        success, error = pm.install([official_name])
        if success:
            return True
        logger.warning(
            "Failed to install from official repos: %s. "
            "Trying fallback method.",
            error,
        )

    # Not in official repos or official install failed
    logger.debug("Using custom installation method for %s", official_name)
    return fallback_install()


def _import_microsoft_gpg_rpm() -> bool:
    """Import Microsoft GPG key for RPM-based systems.

    Returns:
        True if successful, False otherwise.

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
    except Exception:
        logger.exception("Error importing GPG key")
        return False
    else:
        return result.returncode == 0


def _create_fedora_repo() -> bool:
    """Create VS Code repository file for Fedora.

    Returns:
        True if successful, False otherwise.

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
    except Exception:
        logger.exception("Error creating repository file")
        return False
    else:
        return result.returncode == 0
