"""Setup manager for installing and configuring system components."""

import shutil
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from aps.core.distro import DistroInfo, PackageManagerType
from aps.core.logger import get_logger
from aps.hardware import amd, intel, nvidia, touchpad
from aps.installers import (
    autocpufreq,
    brave,
    ohmyzsh,
    syncthing,
    thinkfan,
    tlp,
    trashcli,
    ueberzugpp,
    virtmanager,
    vscode,
)
from aps.system import (
    firewall,
    multimedia,
    pm_optimizer,
    repositories,
    ssh,
    sudoers,
)
from aps.utils.privilege import run_privileged
from aps.wm import qtile

logger = get_logger(__name__)


class SetupError(Exception):
    """Raised when setup operation fails."""


class SetupManager:
    """Manages setup operations for AUR helpers, ollama, and components."""

    # Registry of available setup components
    COMPONENT_REGISTRY: ClassVar[dict[str, dict[str, Any]]] = {
        "aur-helper": {
            "description": "Install paru AUR helper (Arch Linux only)",
            "installer": None,  # Built-in method
        },
        "ollama": {
            "description": "Install/update Ollama AI runtime",
            "installer": None,  # Built-in method
        },
        "ohmyzsh": {
            "description": "Install Oh-My-Zsh with custom plugins",
            "installer_module": ohmyzsh,
        },
        "brave": {
            "description": "Install Brave browser",
            "installer_module": brave,
        },
        "tlp": {
            "description": "Install TLP power management",
            "installer_module": tlp,
        },
        "autocpufreq": {
            "description": "Install Auto-CPUFreq power optimization",
            "installer_module": autocpufreq,
        },
        "syncthing": {
            "description": "Install Syncthing file synchronization",
            "installer_module": syncthing,
        },
        "thinkfan": {
            "description": "Install ThinkPad fan control",
            "installer_module": thinkfan,
        },
        "trashcli": {
            "description": "Install Trash-CLI utilities",
            "installer_module": trashcli,
        },
        "ueberzugpp": {
            "description": "Install Ueberzug++ image preview",
            "installer_module": ueberzugpp,
        },
        "virtmanager": {
            "description": "Install Virtual Machine Manager",
            "installer_module": virtmanager,
        },
        "vscode": {
            "description": "Install Visual Studio Code",
            "installer_module": vscode,
        },
        # Hardware configuration components
        "amd": {
            "description": "Configure AMD CPU (zenpower setup for Ryzen)",
            "config_module": amd,
        },
        "intel": {
            "description": "Configure Intel CPU power management",
            "config_module": intel,
        },
        "nvidia": {
            "description": "Configure NVIDIA GPU drivers and CUDA",
            "config_module": nvidia,
        },
        "touchpad": {
            "description": "Configure touchpad settings",
            "config_module": touchpad,
        },
        # System configuration components
        "firewall": {
            "description": "Configure UFW firewall",
            "config_module": firewall,
        },
        "multimedia": {
            "description": "Configure multimedia codecs and settings",
            "config_module": multimedia,
        },
        "pm-optimizer": {
            "description": "Optimize package manager settings",
            "config_module": pm_optimizer,
        },
        "repositories": {
            "description": "Configure additional repositories",
            "config_module": repositories,
        },
        "ssh": {
            "description": "Configure SSH server and client",
            "config_module": ssh,
        },
        "sudoers": {
            "description": "Configure sudo privileges and settings",
            "config_module": sudoers,
        },
        # Window manager configuration components
        "qtile": {
            "description": "Configure Qtile window manager",
            "config_module": qtile,
        },
    }

    def __init__(self, distro_info: DistroInfo) -> None:
        """Initialize setup manager.

        Args:
            distro_info: Distribution information for platform-specific setup

        """
        self.distro = distro_info

    @classmethod
    def get_available_components(cls) -> dict[str, str]:
        """Get all available setup components.

        Returns:
            Dictionary mapping component names to descriptions

        """
        return {
            name: info["description"]
            for name, info in cls.COMPONENT_REGISTRY.items()
        }

    def setup_component(self, component: str) -> None:  # noqa: C901
        """Setup a component by name.

        Args:
            component: Name of the component to setup

        Raises:
            SetupError: If component is unknown or setup fails

        """
        if component not in self.COMPONENT_REGISTRY:
            msg = f"Unknown component: {component}"
            raise SetupError(msg)

        component_info = self.COMPONENT_REGISTRY[component]
        installer_class = component_info.get("installer")
        installer_module = component_info.get("installer_module")
        config_module = component_info.get("config_module")

        # Use built-in methods for aur-helper and ollama
        if (
            installer_class is None
            and installer_module is None
            and config_module is None
        ):
            if component == "aur-helper":
                self.setup_aur_helper()
            elif component == "ollama":
                self.setup_ollama()
            return

        # Use functional config module for configuration components
        if config_module is not None:
            logger.info("Configuring %s...", component)
            try:
                # Default kwargs for configuration components
                default_kwargs = {
                    "amd": {"zenpower": True},
                    "intel": {"xorg": True},
                    "nvidia": {
                        "cuda": True
                    },  # Enable CUDA by default if NVIDIA GPU present
                    "touchpad": {},
                    "firewall": {},
                    "multimedia": {},
                    "pm-optimizer": {},
                    "repositories": {},
                    "ssh": {},
                    "sudoers": {},
                    "qtile": {},
                }.get(component, {})

                # Call the functional configure() function
                success = config_module.configure(
                    distro=self.distro.id, **default_kwargs
                )
                if not success:
                    msg = f"Failed to configure {component}"
                    raise SetupError(msg)  # noqa: TRY301
                logger.info(
                    "%s configuration completed successfully", component
                )
            except Exception as e:
                msg = f"Error during {component} configuration: {e}"
                raise SetupError(msg) from e
            return

        # Use functional installer module for installer components
        if installer_module is not None:
            logger.info("Setting up %s...", component)
            try:
                success = installer_module.install(distro=self.distro.id)
                if not success:
                    msg = f"Failed to setup {component}"
                    raise SetupError(msg)  # noqa: TRY301
                logger.info("%s setup completed successfully", component)
            except Exception as e:
                msg = f"Error during {component} setup: {e}"
                raise SetupError(msg) from e

    def setup_aur_helper(self) -> None:
        """Install paru AUR helper for Arch Linux.

        Uses pre-compiled paru-bin to avoid memory issues during compilation.
        Build directory is /opt to avoid tmpfs memory limitations.

        Raises:
            SetupError: If installation fails

        """
        if self.distro.package_manager != PackageManagerType.PACMAN:
            msg = (
                "AUR helper setup is only available for "
                "Arch-based distributions"
            )
            raise SetupError(msg)

        # Check if already installed
        if shutil.which("paru") or shutil.which("yay"):
            logger.info("AUR helper (paru/yay) is already installed")
            return

        logger.info("Installing paru AUR helper...")

        # Ensure GPG keyring exists
        self._ensure_gpg_keyring()

        # Install build dependencies
        self._install_build_deps()

        # Build and install paru-bin
        self._build_paru()

        # Verify installation
        if not shutil.which("paru"):
            msg = "paru installation verification failed"
            raise SetupError(msg)

        logger.info("paru installed successfully")

    def setup_ollama(self) -> None:
        """Install or update Ollama.

        On Arch, uses package manager with GPU-specific packages.
        On other distributions, uses official install script.

        Raises:
            SetupError: If installation fails

        """
        action = "Updating" if shutil.which("ollama") else "Installing"
        logger.info("%s Ollama...", action)

        if self.distro.package_manager == PackageManagerType.PACMAN:
            self._setup_ollama_arch()
        else:
            self._setup_ollama_official()

        # Verify installation
        if not shutil.which("ollama"):
            msg = f"Ollama binary not found after {action.lower()}"
            raise SetupError(msg)

        logger.info("Ollama %s completed successfully", action.lower())

    def _ensure_gpg_keyring(self) -> None:
        """Create GPG keyring if it doesn't exist."""
        gpg_dirs = [
            Path.home() / ".local" / "share" / "gnupg",
            Path.home() / ".gnupg",
        ]

        keyring_exists = any((d / "pubring.kbx").exists() for d in gpg_dirs)

        if not keyring_exists:
            logger.info("Creating GPG keyring...")
            subprocess.run(
                ["gpg", "--list-keys"],  # noqa: S607
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    def _install_build_deps(self) -> None:
        """Install build dependencies for AUR helper."""
        logger.info("Installing build dependencies...")
        result = run_privileged(
            ["pacman", "-S", "--needed", "--noconfirm", "base-devel", "git"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            msg = f"Failed to install build dependencies: {result.stderr}"
            raise SetupError(msg)

    def _build_paru(self) -> None:
        """Build and install paru-bin from AUR."""
        build_dir = Path("/opt/paru-bin")

        try:
            # Clean up previous attempts
            if build_dir.exists():
                logger.info("Cleaning up previous build directory...")
                run_privileged(["rm", "-rf", str(build_dir)], check=True)

            # Clone paru-bin repository
            logger.info("Cloning paru-bin repository...")
            result = run_privileged(
                [
                    "git",
                    "clone",
                    "https://aur.archlinux.org/paru-bin.git",
                    str(build_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                msg = f"Failed to clone paru-bin repository: {result.stderr}"
                raise SetupError(msg)

            # Set ownership for makepkg (cannot run as root)
            logger.info("Setting directory permissions...")
            user = Path.home().name
            result = run_privileged(
                ["chown", "-R", f"{user}:{user}", str(build_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                msg = f"Failed to set directory ownership: {result.stderr}"
                raise SetupError(msg)

            # Build and install
            logger.info("Building and installing paru...")
            result = subprocess.run(
                ["makepkg", "-si", "--noconfirm"],  # noqa: S607
                cwd=build_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                msg = f"Failed to build and install paru: {result.stderr}"
                raise SetupError(msg)

        finally:
            # Clean up build directory
            if build_dir.exists():
                logger.info("Cleaning up build directory...")
                run_privileged(
                    ["rm", "-rf", str(build_dir)],
                    check=False,
                    capture_output=False,
                )

    def _setup_ollama_arch(self) -> None:
        """Setup Ollama on Arch Linux using package manager."""
        gpu_vendor = self._detect_gpu_vendor()
        logger.info("Detected GPU vendor: %s", gpu_vendor)

        # Select appropriate package
        pkg_map = {
            "nvidia": "ollama-cuda",
            "amd": "ollama-rocm",
        }
        pkg = pkg_map.get(gpu_vendor, "ollama")

        logger.info("Installing Ollama package: %s", pkg)

        # Try package manager installation
        result = run_privileged(
            ["pacman", "-S", "--needed", "--noconfirm", pkg],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0 and shutil.which("ollama"):
            logger.info("Ollama installed successfully via package manager")
            return

        # Fallback to official installer
        logger.warning(
            "Package installation failed, falling back to official installer"
        )
        self._setup_ollama_official()

    def _setup_ollama_official(self) -> None:
        """Setup Ollama using official install script."""
        logger.info("Downloading and running Ollama install script...")

        # Execute the curl | sed | sh pipeline directly like bash version
        # Necessary because Ollama installer needs interactive execution
        cmd = (
            "curl -fsSL https://ollama.com/install.sh | "
            "sed 's/--add-repo/addrepo/' | sh"
        )

        result = subprocess.run(  # noqa: S602
            cmd,
            shell=True,
            check=False,
        )

        if result.returncode != 0:
            msg = "Failed to install Ollama via official installer"
            raise SetupError(msg)

    def _detect_gpu_vendor(self) -> str:
        """Detect GPU vendor for Ollama package selection.

        Returns:
            GPU vendor: "nvidia", "amd", or "unknown"

        """
        # Check for NVIDIA
        if shutil.which("nvidia-smi"):
            return "nvidia"

        # Check for AMD (ROCm)
        result = subprocess.run(
            ["lspci"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            output = result.stdout.lower()
            if "amd" in output and ("vga" in output or "display" in output):
                return "amd"

        return "unknown"
