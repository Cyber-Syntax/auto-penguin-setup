"""AMD CPU configuration - zenpower setup for Ryzen 5000 series."""

import logging
import subprocess
from pathlib import Path

from aps.hardware.base import BaseHardwareConfig
from aps.utils.privilege import run_privileged

logger = logging.getLogger(__name__)


class AMDConfig(BaseHardwareConfig):
    """AMD CPU configuration manager."""

    def __init__(self, distro: str):
        """Initialize AMD configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)

        """
        super().__init__(distro)

    def _is_amd_cpu(self) -> bool:
        """Check if system has AMD CPU.

        Returns:
            True if AMD CPU is detected

        """
        try:
            with Path("/proc/cpuinfo").open(encoding="utf-8") as f:
                return "AMD" in f.read()
        except FileNotFoundError:
            self.logger.warning(
                "Cannot detect CPU type - /proc/cpuinfo not found"
            )
            return False

    def _is_k10temp_loaded(self) -> bool:
        """Check if k10temp module is loaded.

        Returns:
            True if k10temp is loaded

        """
        try:
            result = subprocess.run(
                ["lsmod"], capture_output=True, text=True, check=False
            )
            return "k10temp" in result.stdout
        except FileNotFoundError:
            return False

    def setup_zenpower(self) -> bool:
        """Set up zenpower for AMD Ryzen 5000 series.

        Returns:
            True if setup succeeds, False otherwise

        """
        self.logger.info("Setting up zenpower for Ryzen 5000 series...")

        if not self._is_amd_cpu():
            self.logger.error("This system does not appear to have an AMD CPU")
            return False

        if self.distro not in ["fedora", "arch", "debian"]:
            self.logger.error("Unsupported distribution: %s", self.distro)
            return False

        # Unload k10temp if loaded
        if self._is_k10temp_loaded():
            self.logger.info(
                "k10temp module is currently loaded, unloading..."
            )
            result = run_privileged(
                ["modprobe", "-r", "k10temp"],
                check=False,
            )
            if result.returncode != 0:
                self.logger.error("Failed to unload k10temp module")
                return False

        # Create blacklist file
        blacklist_file = "/etc/modprobe.d/zenpower.conf"
        self.logger.debug(
            "Creating k10temp blacklist file at %s...", blacklist_file
        )

        try:
            with Path(blacklist_file).open("w", encoding="utf-8") as f:
                f.write("blacklist k10temp\n")
        except OSError as e:
            self.logger.error("Failed to create k10temp blacklist file: %s", e)
            return False

        # Install zenpower based on distribution
        try:
            if self.distro == "fedora":
                return self._setup_zenpower_fedora()
            if self.distro == "arch":
                return self._setup_zenpower_arch()
            if self.distro == "debian":
                return self._setup_zenpower_debian()
            self.logger.error("Unsupported distribution: %s", self.distro)
            return False
        except Exception as e:
            self.logger.error("Failed to setup zenpower: %s", e)
            return False

    def _setup_zenpower_fedora(self) -> bool:
        """Set up zenpower on Fedora.

        Returns:
            True if successful

        """
        self.logger.debug("Enabling zenpower3 COPR repository...")
        result = run_privileged(
            ["dnf", "copr", "enable", "shdwchn10/zenpower3", "-y"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to enable zenpower3 COPR repository")
            return False

        self.logger.debug("Installing zenpower3 and zenmonitor3...")
        result = run_privileged(
            ["dnf", "install", "-y", "zenpower3", "zenmonitor3"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error(
                "Failed to install zenpower3 and zenmonitor3 packages"
            )
            return False

        return self._load_zenpower_module()

    def _setup_zenpower_arch(self) -> bool:
        """Set up zenpower on Arch Linux.

        Returns:
            True if successful

        """
        self.logger.debug("Installing zenpower3-dkms from AUR...")

        # Check if AUR helper is available
        aur_helper = None
        for helper in ["paru", "yay"]:
            result = subprocess.run(
                ["which", helper], capture_output=True, check=False
            )
            if result.returncode == 0:
                aur_helper = helper
                break

        if not aur_helper:
            self.logger.error("No AUR helper found (paru or yay required)")
            return False

        result = subprocess.run(
            [aur_helper, "-S", "--noconfirm", "zenpower3-dkms"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install zenpower3 from AUR")
            return False

        # Try to install zenmonitor3 (optional)
        result = subprocess.run(
            [aur_helper, "-S", "--noconfirm", "zenmonitor3"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.warning(
                "Failed to install zenmonitor3 from AUR (optional)"
            )

        return self._load_zenpower_module()

    def _setup_zenpower_debian(self) -> bool:
        """Set up zenpower on Debian/Ubuntu.

        Returns:
            True if successful

        """
        self.logger.warning(
            "Zenpower is not officially packaged for Debian/Ubuntu"
        )
        self.logger.info("Manual installation from source may be required")
        self.logger.info("See: https://github.com/ocerman/zenpower3")
        return False

    def _load_zenpower_module(self) -> bool:
        """Load zenpower kernel module.

        Returns:
            True if module loads successfully

        """
        self.logger.debug("Loading zenpower module...")
        result = run_privileged(
            ["modprobe", "zenpower3"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to load zenpower3 module")
            self.logger.info(
                "A system restart may be required to load the zenpower3 "
                "module. Please reboot and try again."
            )
            return False

        self.logger.info("zenpower3 module loaded successfully")
        return True

    def configure(self, **kwargs) -> bool:
        """Configure AMD hardware.

        Supported operations via kwargs:
            - zenpower: bool - Setup zenpower for Ryzen 5000 series

        Args:
            **kwargs: Configuration options

        Returns:
            True if all requested operations succeed

        """
        if kwargs.get("zenpower", False):
            return self.setup_zenpower()

        return True
