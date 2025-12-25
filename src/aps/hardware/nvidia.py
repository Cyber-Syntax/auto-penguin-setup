"""NVIDIA GPU configuration and driver management."""

import os
import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def has_nvidia_gpu() -> bool:
    """Check if system has NVIDIA GPU.

    Returns:
        True if NVIDIA GPU is detected

    """
    try:
        result = subprocess.run(
            ["/usr/bin/lspci"], capture_output=True, text=True, check=False
        )
        return "nvidia" in result.stdout.lower()
    except FileNotFoundError:
        logger.warning("lspci command not found, cannot detect NVIDIA GPU")
        return False


def setup_cuda(distro: str) -> bool:
    """Install NVIDIA CUDA toolkit.

    Args:
        distro: Distribution name (fedora, arch)

    Returns:
        True if installation succeeds, False otherwise

    """
    logger.info("Setting up NVIDIA CUDA...")

    if not has_nvidia_gpu():
        logger.error("No NVIDIA GPU detected in this system")
        return False

    try:
        arch = os.uname().machine

        if distro == "fedora":
            return _setup_cuda_fedora(arch)
        if distro == "arch":
            return _setup_cuda_arch()
        logger.error("Unsupported distribution: %s", distro)
        return False
    except Exception:
        logger.exception("Failed to setup CUDA")
        return False


def _setup_cuda_fedora(arch: str) -> bool:
    """Setup CUDA on Fedora.

    Args:
        arch: System architecture

    Returns:
        True if successful

    """
    try:
        with open("/etc/fedora-release", encoding="utf-8") as f:
            version = f.read().split()[-2]
    except (FileNotFoundError, IndexError):
        logger.error("Failed to detect Fedora version")
        return False

    cuda_repo = (
        f"https://developer.download.nvidia.com/compute/cuda/repos/"
        f"fedora{version}/{arch}/cuda-fedora{version}.repo"
    )

    logger.debug("Adding CUDA repository for Fedora %s...", version)
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
        logger.error("Failed to add CUDA repository")
        return False

    logger.debug("Cleaning DNF cache...")
    run_privileged(
        ["/usr/bin/dnf", "clean", "all"], check=False, capture_output=False
    )

    logger.debug("Disabling nvidia-driver module...")
    run_privileged(
        ["/usr/bin/dnf", "module", "disable", "-y", "nvidia-driver"],
        check=False,
        capture_output=False,
    )

    logger.debug("Setting package exclusions...")
    exclude_pkgs = (
        "nvidia-driver,nvidia-modprobe,nvidia-persistenced,"
        "nvidia-settings,nvidia-libXNVCtrl,nvidia-xconfig"
    )
    run_privileged(
        [
            "/usr/bin/dnf",
            "config-manager",
            "setopt",
            f"cuda-fedora{version}-{arch}.exclude={exclude_pkgs}",
        ],
        check=False,
        capture_output=False,
    )

    logger.debug("Installing CUDA toolkit...")
    result = run_privileged(
        ["/usr/bin/dnf", "install", "-y", "cuda-toolkit"],
        check=False,
        capture_output=False,
    )
    if result.returncode != 0:
        logger.error("Failed to install CUDA toolkit")
        return False

    return _verify_cuda_installation()


def _setup_cuda_arch() -> bool:
    """Setup CUDA on Arch Linux.

    Returns:
        True if successful

    """
    logger.debug("Installing CUDA from official repositories...")
    result = run_privileged(
        ["/usr/bin/pacman", "-S", "--noconfirm", "cuda", "cuda-tools"],
        check=False,
        capture_output=False,
    )
    if result.returncode != 0:
        logger.error("Failed to install CUDA toolkit")
        return False

    return _verify_cuda_installation()


def _verify_cuda_installation() -> bool:
    """Verify CUDA installation.

    Returns:
        True if nvcc is available

    """
    try:
        subprocess.run(
            ["nvcc", "--version"], capture_output=True, check=True
        )
        logger.info("CUDA setup completed successfully")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.error(
            "CUDA toolkit installation failed - nvcc not found"
        )
        logger.info(
            "You may need to add CUDA to your PATH: "
            "export PATH=/usr/local/cuda/bin:$PATH"
        )
        return False


def switch_to_open_driver(distro: str) -> bool:
    """Switch to NVIDIA open source drivers.

    Args:
        distro: Distribution name (fedora, arch)

    Returns:
        True if switch succeeds, False otherwise

    """
    logger.info("Switching to NVIDIA open source drivers...")

    if not has_nvidia_gpu():
        logger.error("No NVIDIA GPU detected in this system")
        return False

    if os.geteuid() != 0:
        logger.error(
            "This function must be run as root or with sudo privileges"
        )
        return False

    try:
        if distro == "fedora":
            return _switch_to_open_fedora()
        if distro == "arch":
            return _switch_to_open_arch()
        logger.error("Unsupported distribution: %s", distro)
        return False
    except Exception:
        logger.exception("Failed to switch to open driver")
        return False


def _switch_to_open_fedora() -> bool:
    """Switch to open driver on Fedora.

    Returns:
        True if successful

    """
    macro_file = "/etc/rpm/macros.nvidia-kmod"
    logger.debug("Creating NVIDIA kmod macro file...")

    with open(macro_file, "w", encoding="utf-8") as f:
        f.write("%_with_kmod_nvidia_open 1\n")

    current_kernel = os.uname().release
    logger.debug(
        "Rebuilding NVIDIA modules for kernel %s...", current_kernel
    )

    result = subprocess.run(
        ["akmods", "--kernels", current_kernel, "--rebuild"],
        check=False,
    )
    if result.returncode != 0:
        logger.warning(
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
            logger.error("Failed to rebuild NVIDIA modules")
            return False

    logger.debug(
        "Disabling RPMFusion non-free NVIDIA driver repository..."
    )
    run_privileged(
        ["dnf", "--disablerepo", "rpmfusion-nonfree-nvidia-driver"],
        check=False,
        capture_output=False,
    )

    _log_open_driver_success_fedora()
    return True


def _switch_to_open_arch() -> bool:
    """Switch to open driver on Arch.

    Returns:
        True if successful

    """
    logger.info("Installing NVIDIA open source drivers for Arch...")
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
        logger.error("Failed to install NVIDIA open drivers")
        return False

    _log_open_driver_success()
    return True


def _log_open_driver_success() -> None:
    """Log success message for open driver installation."""
    logger.info("NVIDIA open source driver setup completed")
    logger.info("Please reboot for changes to take effect")
    logger.info("After reboot, verify installation with:")
    logger.info("  modinfo nvidia | grep license")


def _log_open_driver_success_fedora() -> None:
    """Log success message for Fedora open driver installation."""
    logger.info("NVIDIA open source driver setup completed")
    logger.info(
        "Please wait 10-20 minutes for the NVIDIA modules to build, "
        "then reboot"
    )
    logger.info("After reboot, verify installation with:")
    logger.info(
        "1. 'modinfo nvidia | grep license' - should show 'Dual MIT/GPL'"
    )
    logger.info(
        "2. 'rpm -qa kmod-nvidia*' - should show kmod-nvidia-open package"
    )


def setup_vaapi(distro: str) -> bool:
    """Setup VA-API for NVIDIA RTX series (Fedora only).

    Args:
        distro: Distribution name (must be fedora)

    Returns:
        True if setup succeeds, False otherwise

    """
    logger.info("Setting up VA-API for NVIDIA RTX series...")

    if not has_nvidia_gpu():
        logger.error("No NVIDIA GPU detected in this system")
        return False

    if distro != "fedora":
        logger.error("VA-API setup is currently only supported on Fedora")
        return False

    packages = [
        "meson",
        "libva-devel",
        "gstreamer1-plugins-bad-freeworld",
        "nv-codec-headers",
        "nvidia-vaapi-driver",
        "gstreamer1-plugins-bad-free-devel",
    ]

    logger.debug("Installing VA-API related packages...")
    result = run_privileged(
        ["dnf", "install", "-y", *packages],
        check=False,
        capture_output=False,
    )
    if result.returncode != 0:
        logger.error("Failed to install VA-API packages")
        return False

    env_file = "/etc/environment"
    env_vars = [
        "MOZ_DISABLE_RDD_SANDBOX=1",
        "LIBVA_DRIVER_NAME=nvidia",
        "__GLX_VENDOR_LIBRARY_NAME=nvidia",
    ]

    logger.debug("Setting up environment variables in %s...", env_file)

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
        logger.debug("Environment variables already set in %s", env_file)

    logger.info("VA-API setup completed successfully")
    logger.debug("Note: You may need to reboot for changes to take effect")
    return True


def configure(distro: str, **kwargs) -> bool:
    """Configure NVIDIA hardware.

    Args:
        distro: Distribution name (fedora, arch)
        **kwargs: Configuration options
            - cuda: bool - Setup CUDA toolkit
            - open_driver: bool - Switch to open source driver
            - vaapi: bool - Setup VA-API for RTX series

    Returns:
        True if all requested operations succeed

    """
    success = True

    if kwargs.get("cuda", False):
        success = success and setup_cuda(distro)

    if kwargs.get("open_driver", False):
        success = success and switch_to_open_driver(distro)

    if kwargs.get("vaapi", False):
        success = success and setup_vaapi(distro)

    return success
