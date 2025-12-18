"""AMD CPU configuration - zenpower setup for Ryzen 5000 series."""

import logging
import subprocess
from pathlib import Path

from aps.hardware.base import BaseHardwareConfig
from aps.utils.privilege import run_privileged

logger = logging.getLogger(__name__)


class AMDConfig(BaseHardwareConfig):
    """AMD CPU configuration manager."""

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
            lsmod_result = subprocess.run(
                ["lsmod"],
                capture_output=True,
                text=True,
                check=False,
            )
            if lsmod_result.returncode != 0:
                return False
            grep_result = subprocess.run(
                ["grep", "k10temp"],
                input=lsmod_result.stdout,
                capture_output=True,
                text=True,
                check=False,
            )
            return grep_result.returncode == 0
        except FileNotFoundError:
            return False

    def _is_k10temp_blacklisted(self) -> bool:
        """Check if k10temp is already blacklisted.

        Returns:
            True if k10temp is blacklisted in modprobe.d

        """
        modprobe_dir = Path("/etc/modprobe.d")
        if not modprobe_dir.exists():
            return False

        for conf_file in modprobe_dir.glob("*.conf"):
            try:
                with conf_file.open(encoding="utf-8") as f:
                    if "blacklist k10temp" in f.read():
                        return True
            except OSError:
                continue
        return False

    def _is_zenpower_loaded(self) -> bool:
        """Check if zenpower module is loaded.

        Returns:
            True if zenpower is loaded

        """
        try:
            lsmod_result = subprocess.run(
                ["lsmod"],
                capture_output=True,
                text=True,
                check=False,
            )
            if lsmod_result.returncode != 0:
                return False
            grep_result = subprocess.run(
                ["grep", "zenpower"],
                input=lsmod_result.stdout,
                capture_output=True,
                text=True,
                check=False,
            )
            return grep_result.returncode == 0
        except FileNotFoundError:
            return False

    def setup_zenpower(self) -> bool:
        r"""Set up zenpower for zen3 amd cpu family.

        Because zenpower is using same PCI device as k10temp, you have to
        disable k10temp first. This is automatically done by the AUR package.

        Check if k10temp is active: lsmod | grep k10temp
        Unload k10temp: sudo modprobe -r k10temp
        (optional*) blacklist k10temp: sudo bash -c `sudo echo -e
        "\n# replaced with zenpower\nblacklist k10temp" >>
        /etc/modprobe.d/k10temp-blacklist.conf'
        Activate zenpower: sudo modprobe zenpower

        *If k10temp is not blacklisted, you may have to manually unload
        k10temp after each restart.

        Returns:
            True if setup succeeds, False otherwise

        """
        logger.info("Setting up zenpower3...")

        if not self._is_amd_cpu():
            logger.error("This system does not appear to have an AMD CPU")
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

        # Create blacklist file if not already blacklisted
        if not self._is_k10temp_blacklisted():
            blacklist_file = "/etc/modprobe.d/k10temp-blacklist.conf"
            self.logger.debug(
                "Creating k10temp blacklist file at %s...", blacklist_file
            )

            command = f"echo 'blacklist k10temp' > '{blacklist_file}'"
            result = run_privileged(
                ["sh", "-c", command],
                check=False,
            )
            if result.returncode != 0:
                self.logger.error(
                    "Failed to create blacklist file: %s", result.stderr
                )
                return False
        else:
            self.logger.info("k10temp is already blacklisted")

        # Load zenpower module
        return self._load_zenpower_module()

    def _load_zenpower_module(self) -> bool:
        """Load zenpower kernel module.

        Returns:
            True if module loads successfully

        """
        self.logger.debug("Checking if zenpower module is loaded...")
        if self._is_zenpower_loaded():
            self.logger.info("zenpower module is already loaded")
            return True

        self.logger.debug("Loading zenpower module...")
        result = run_privileged(
            ["modprobe", "zenpower"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to load zenpower module")
            self.logger.info(
                "A system restart may be required to load the zenpower "
                "module. Please reboot and try again."
            )
            return False

        self.logger.info("zenpower module loaded successfully")
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
