"""NVIDIA GPU configuration and driver management."""

import logging
import os
import subprocess

from aps.hardware.base import BaseHardwareConfig
from aps.utils.privilege import run_privileged

logger = logging.getLogger(__name__)


class NvidiaConfig(BaseHardwareConfig):
    """NVIDIA GPU configuration manager."""

    def __init__(self, distro: str):
        """Initialize NVIDIA configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)
        """
        super().__init__(distro)

    def _has_nvidia_gpu(self) -> bool:
        """Check if system has NVIDIA GPU.

        Returns:
            True if NVIDIA GPU is detected
        """
        try:
            result = subprocess.run(
                ["lspci"], capture_output=True, text=True, check=False
            )
            return "nvidia" in result.stdout.lower()
        except FileNotFoundError:
            self.logger.warning(
                "lspci command not found, cannot detect NVIDIA GPU"
            )
            return False

    def setup_cuda(self) -> bool:
        """Install NVIDIA CUDA toolkit.

        Returns:
            True if installation succeeds, False otherwise
        """
        self.logger.info("Setting up NVIDIA CUDA...")

        if not self._has_nvidia_gpu():
            self.logger.error("No NVIDIA GPU detected in this system")
            return False

        try:
            arch = os.uname().machine

            if self.distro == "fedora":
                return self._setup_cuda_fedora(arch)
            if self.distro == "arch":
                return self._setup_cuda_arch()
            if self.distro == "debian":
                return self._setup_cuda_debian()
            self.logger.error("Unsupported distribution: %s", self.distro)
            return False
        except Exception as e:
            self.logger.error("Failed to setup CUDA: %s", e)
            return False

    def _setup_cuda_fedora(self, arch: str) -> bool:
        """Setup CUDA on Fedora.

        Args:
            arch: System architecture

        Returns:
            True if successful
        """
        # Get Fedora version
        try:
            with open("/etc/fedora-release", encoding="utf-8") as f:
                version = f.read().split()[-2]
        except (FileNotFoundError, IndexError):
            self.logger.error("Failed to detect Fedora version")
            return False

        cuda_repo = (
            f"https://developer.download.nvidia.com/compute/cuda/repos/"
            f"fedora{version}/{arch}/cuda-fedora{version}.repo"
        )

        self.logger.debug("Adding CUDA repository for Fedora %s...", version)
        result = run_privileged(
            [
                "dnf",
                "config-manager",
                "addrepo",
                f"--from-repofile={cuda_repo}",
            ],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to add CUDA repository")
            return False

        self.logger.debug("Cleaning DNF cache...")
        run_privileged(
            ["dnf", "clean", "all"], check=False, capture_output=False
        )

        self.logger.debug("Disabling nvidia-driver module...")
        run_privileged(
            ["dnf", "module", "disable", "-y", "nvidia-driver"],
            check=False,
            capture_output=False,
        )

        self.logger.debug("Setting package exclusions...")
        exclude_pkgs = (
            "nvidia-driver,nvidia-modprobe,nvidia-persistenced,"
            "nvidia-settings,nvidia-libXNVCtrl,nvidia-xconfig"
        )
        run_privileged(
            [
                "dnf",
                "config-manager",
                "setopt",
                f"cuda-fedora{version}-{arch}.exclude={exclude_pkgs}",
            ],
            check=False,
            capture_output=False,
        )

        self.logger.debug("Installing CUDA toolkit...")
        result = run_privileged(
            ["dnf", "install", "-y", "cuda-toolkit"],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install CUDA toolkit")
            return False

        return self._verify_cuda_installation()

    def _setup_cuda_arch(self) -> bool:
        """Setup CUDA on Arch Linux.

        Returns:
            True if successful
        """
        self.logger.debug("Installing CUDA from official repositories...")
        result = run_privileged(
            ["pacman", "-S", "--noconfirm", "cuda", "cuda-tools"],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install CUDA toolkit")
            return False

        return self._verify_cuda_installation()

    def _setup_cuda_debian(self) -> bool:
        """Setup CUDA on Debian/Ubuntu.

        Returns:
            True if successful
        """
        keyring_path = "/usr/share/keyrings/cuda-archive-keyring.gpg"

        if not os.path.exists(keyring_path):
            self.logger.debug("Downloading CUDA keyring...")
            # Download keyring package
            result = subprocess.run(
                [
                    "wget",
                    "https://developer.download.nvidia.com/compute/cuda/repos/"
                    "ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb",
                ],
                check=False,
            )
            if result.returncode != 0:
                self.logger.error("Failed to download CUDA keyring")
                return False

            # Install keyring
            result = run_privileged(
                ["dpkg", "-i", "cuda-keyring_1.1-1_all.deb"],
                check=False,
                capture_output=False,
            )
            subprocess.run(
                ["rm", "-f", "cuda-keyring_1.1-1_all.deb"], check=False
            )

            if result.returncode != 0:
                self.logger.error("Failed to install CUDA keyring")
                return False

            run_privileged(
                ["apt-get", "update"], check=False, capture_output=False
            )

        self.logger.debug("Installing CUDA toolkit...")
        result = run_privileged(
            ["apt-get", "install", "-y", "cuda-toolkit"],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install CUDA toolkit")
            return False

        return self._verify_cuda_installation()

    def _verify_cuda_installation(self) -> bool:
        """Verify CUDA installation.

        Returns:
            True if nvcc is available
        """
        try:
            subprocess.run(
                ["nvcc", "--version"], capture_output=True, check=True
            )
            self.logger.info("CUDA setup completed successfully")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.logger.error(
                "CUDA toolkit installation failed - nvcc not found"
            )
            self.logger.info(
                "You may need to add CUDA to your PATH: export PATH=/usr/local/cuda/bin:$PATH"
            )
            return False

    def switch_to_open_driver(self) -> bool:
        """Switch to NVIDIA open source drivers.

        Returns:
            True if switch succeeds, False otherwise
        """
        self.logger.info("Switching to NVIDIA open source drivers...")

        if not self._has_nvidia_gpu():
            self.logger.error("No NVIDIA GPU detected in this system")
            return False

        if os.geteuid() != 0:
            self.logger.error(
                "This function must be run as root or with sudo privileges"
            )
            return False

        try:
            if self.distro == "fedora":
                return self._switch_to_open_fedora()
            if self.distro == "arch":
                return self._switch_to_open_arch()
            if self.distro == "debian":
                return self._switch_to_open_debian()
            self.logger.error("Unsupported distribution: %s", self.distro)
            return False
        except Exception as e:
            self.logger.error("Failed to switch to open driver: %s", e)
            return False

    def _switch_to_open_fedora(self) -> bool:
        """Switch to open driver on Fedora.

        Returns:
            True if successful
        """
        macro_file = "/etc/rpm/macros.nvidia-kmod"
        self.logger.debug("Creating NVIDIA kmod macro file...")

        with open(macro_file, "w", encoding="utf-8") as f:
            f.write("%_with_kmod_nvidia_open 1\n")

        current_kernel = os.uname().release
        self.logger.debug(
            "Rebuilding NVIDIA modules for kernel %s...", current_kernel
        )

        result = subprocess.run(
            ["akmods", "--kernels", current_kernel, "--rebuild"],
            check=False,
        )
        if result.returncode != 0:
            self.logger.warning(
                "Initial rebuild failed, attempting with --force..."
            )
            result = subprocess.run(
                [
                    "akmods",
                    "--kernels",
                    current_kernel,
                    "--rebuild",
                    "--force",
                ],
                check=False,
            )
            if result.returncode != 0:
                self.logger.error("Failed to rebuild NVIDIA modules")
                return False

        self.logger.debug(
            "Disabling RPMFusion non-free NVIDIA driver repository..."
        )
        run_privileged(
            ["dnf", "--disablerepo", "rpmfusion-nonfree-nvidia-driver"],
            check=False,
            capture_output=False,
        )

        self._log_open_driver_success_fedora()
        return True

    def _switch_to_open_arch(self) -> bool:
        """Switch to open driver on Arch.

        Returns:
            True if successful
        """
        self.logger.info("Installing NVIDIA open source drivers for Arch...")
        result = run_privileged(
            [
                "pacman",
                "-S",
                "--noconfirm",
                "nvidia-open-dkms",
                "nvidia-utils",
            ],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install NVIDIA open drivers")
            return False

        self._log_open_driver_success()
        return True

    def _switch_to_open_debian(self) -> bool:
        """Switch to open driver on Debian.

        Returns:
            True if successful
        """
        self.logger.info("Installing NVIDIA open source drivers for Debian...")

        # Check if contrib/non-free are enabled
        try:
            with open("/etc/apt/sources.list", encoding="utf-8") as f:
                sources = f.read()
                if "contrib" not in sources:
                    self.logger.warning(
                        "Enabling contrib and non-free repositories..."
                    )
                    run_privileged(
                        ["add-apt-repository", "-y", "contrib"],
                        check=False,
                        capture_output=False,
                    )
                    run_privileged(
                        ["add-apt-repository", "-y", "non-free"],
                        check=False,
                        capture_output=False,
                    )
                    run_privileged(
                        ["apt-get", "update"],
                        check=False,
                        capture_output=False,
                    )
        except FileNotFoundError:
            pass

        result = run_privileged(
            [
                "apt-get",
                "install",
                "-y",
                "nvidia-driver",
                "nvidia-kernel-open-dkms",
            ],
            check=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install NVIDIA open drivers")
            return False

        self._log_open_driver_success()
        return True

    def _log_open_driver_success(self) -> None:
        """Log success message for open driver installation."""
        self.logger.info("NVIDIA open source driver setup completed")
        self.logger.info("Please reboot for changes to take effect")
        self.logger.info("After reboot, verify installation with:")
        self.logger.info("  modinfo nvidia | grep license")

    def _log_open_driver_success_fedora(self) -> None:
        """Log success message for Fedora open driver installation."""
        self.logger.info("NVIDIA open source driver setup completed")
        self.logger.info(
            "Please wait 10-20 minutes for the NVIDIA modules to build, then reboot"
        )
        self.logger.info("After reboot, verify installation with:")
        self.logger.info(
            "1. 'modinfo nvidia | grep license' - should show 'Dual MIT/GPL'"
        )
        self.logger.info(
            "2. 'rpm -qa kmod-nvidia*' - should show kmod-nvidia-open package"
        )

    def setup_vaapi(self) -> bool:
        """Setup VA-API for NVIDIA RTX series (Fedora only).

        Returns:
            True if setup succeeds, False otherwise
        """
        self.logger.info("Setting up VA-API for NVIDIA RTX series...")

        if not self._has_nvidia_gpu():
            self.logger.error("No NVIDIA GPU detected in this system")
            return False

        if self.distro != "fedora":
            self.logger.error(
                "VA-API setup is currently only supported on Fedora"
            )
            return False

        packages = [
            "meson",
            "libva-devel",
            "gstreamer1-plugins-bad-freeworld",
            "nv-codec-headers",
            "nvidia-vaapi-driver",
            "gstreamer1-plugins-bad-free-devel",
        ]

        self.logger.debug("Installing VA-API related packages...")
        result = run_privileged(
            ["dnf", "install", "-y", *packages],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            self.logger.error("Failed to install VA-API packages")
            return False

        env_file = "/etc/environment"
        env_vars = [
            "MOZ_DISABLE_RDD_SANDBOX=1",
            "LIBVA_DRIVER_NAME=nvidia",
            "__GLX_VENDOR_LIBRARY_NAME=nvidia",
        ]

        self.logger.debug(
            "Setting up environment variables in %s...", env_file
        )

        # Check if variables already exist
        existing_content = ""
        if os.path.exists(env_file):
            with open(env_file, encoding="utf-8") as f:
                existing_content = f.read()

        need_append = any(var not in existing_content for var in env_vars)

        if need_append:
            with open(env_file, "a", encoding="utf-8") as f:
                for var in env_vars:
                    if var not in existing_content:
                        f.write(f"{var}\n")
        else:
            self.logger.debug(
                "Environment variables already set in %s", env_file
            )

        self.logger.info("VA-API setup completed successfully")
        self.logger.debug(
            "Note: You may need to reboot for changes to take effect"
        )
        return True

    def configure(self, **kwargs) -> bool:
        """Configure NVIDIA hardware.

        Supported operations via kwargs:
            - cuda: bool - Setup CUDA toolkit
            - open_driver: bool - Switch to open source driver
            - vaapi: bool - Setup VA-API for RTX series

        Args:
            **kwargs: Configuration options

        Returns:
            True if all requested operations succeed
        """
        success = True

        if kwargs.get("cuda", False):
            success = success and self.setup_cuda()

        if kwargs.get("open_driver", False):
            success = success and self.switch_to_open_driver()

        if kwargs.get("vaapi", False):
            success = success and self.setup_vaapi()

        return success
