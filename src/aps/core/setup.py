"""Setup manager for installing and configuring system components."""

from typing import Any, ClassVar

from aps.core.distro import DistroInfo
from aps.core.logger import get_logger
from aps.hardware import amd, intel, nvidia, touchpad
from aps.installers import (
    autocpufreq,
    borgbackup,
    brave,
    ohmyzsh,
    ollama,
    paru,
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
from aps.wm import qtile

logger = get_logger(__name__)


class SetupError(Exception):
    """Raised when setup operation fails."""


class SetupManager:
    """Manages setup operations for system components."""

    # Registry of available setup components
    COMPONENT_REGISTRY: ClassVar[dict[str, dict[str, Any]]] = {
        "aur-helper": {
            "description": "Install paru AUR helper (Arch Linux only)",
            "installer_module": paru,
        },
        "ollama": {
            "description": "Install/update Ollama AI runtime",
            "installer_module": ollama,
        },
        "ohmyzsh": {
            "description": "Install Oh-My-Zsh with custom plugins",
            "installer_module": ohmyzsh,
        },
        "brave": {
            "description": "Install Brave browser",
            "installer_module": brave,
        },
        "borgbackup": {
            "description": "Install Borgbackup and enable backup timer",
            "installer_module": borgbackup,
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

    def _platform_key(self) -> str:
        """Return a canonical distro key for component modules.

        Many installer/config modules implement logic keyed on distro *family*
        (e.g. "arch" vs "fedora") rather than a specific derivative ID.
        Normalizing here prevents Arch derivatives like CachyOS from being
        treated as unsupported.

        Returns:
            Canonical distro key (e.g. "arch", "fedora"). Falls back to the
            raw distro ID when the family is unknown.

        """
        family_key = self.distro.family.value
        if family_key != "unknown":
            return family_key
        return self.distro.id

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

    def setup_component(self, component: str) -> None:
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
        installer_module = component_info.get("installer_module")
        config_module = component_info.get("config_module")

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
                    distro=self._platform_key(), **default_kwargs
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
                success = installer_module.install(distro=self._platform_key())
                if not success:
                    msg = f"Failed to setup {component}"
                    raise SetupError(msg)  # noqa: TRY301
                logger.info("%s setup completed successfully", component)
            except Exception as e:
                msg = f"Error during {component} setup: {e}"
                raise SetupError(msg) from e

    def setup_aur_helper(self) -> None:
        """Install paru AUR helper for Arch Linux.

        Delegates to the paru installer module.

        Raises:
            SetupError: If installation fails

        """
        if not paru.install(distro=self._platform_key()):
            msg = "Failed to install paru AUR helper"
            raise SetupError(msg)

    def setup_ollama(self) -> None:
        """Install or update Ollama.

        Delegates to the ollama installer module.

        Raises:
            SetupError: If installation fails

        """
        if not ollama.install(distro=self._platform_key()):
            msg = "Failed to install Ollama"
            raise SetupError(msg)
