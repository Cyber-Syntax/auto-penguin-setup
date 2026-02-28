"""Ollama installer module."""

import shutil
import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:
    """Install or update Ollama.

    On Arch, uses package manager with GPU-specific packages.
    On other distributions, uses official install script.

    Args:
        distro: Distribution ID (e.g., 'arch', 'fedora'). If None, uses
            official installer.

    Returns:
        bool: True if installation was successful, False otherwise.

    """
    action = "Updating" if shutil.which("ollama") else "Installing"
    logger.info("%s Ollama...", action)

    if distro == "arch":
        success = _install_ollama_arch()
    else:
        success = _install_ollama_official()

    if not success:
        logger.error("Failed to %s Ollama", action.lower())
        return False

    # Verify installation
    if not shutil.which("ollama"):
        logger.error("Ollama binary not found after %s", action.lower())
        return False

    logger.info("Ollama %s completed successfully", action.lower())
    return True


def _install_ollama_arch() -> bool:
    """Install Ollama on Arch Linux using package manager.

    Returns:
        bool: True if installation succeeded, False otherwise.

    """
    gpu_vendor = _detect_gpu_vendor()
    logger.info("Detected GPU vendor: %s", gpu_vendor)

    # Select appropriate package
    pkg_map = {
        "nvidia": "ollama-cuda",
        "amd": "ollama-rocm",
    }
    pkg = pkg_map.get(gpu_vendor, "ollama")

    logger.info("Attempting to install Ollama package: %s", pkg)

    # Try package manager installation
    result = run_privileged(
        ["pacman", "-S", "--needed", "--noconfirm", pkg],
        capture_output=False,
        text=True,
        check=False,
    )

    if result.returncode == 0 and shutil.which("ollama"):
        logger.info("Ollama installed successfully via package manager")
        return True

    # Fallback to official installer
    logger.warning(
        "Package installation failed, falling back to official installer"
    )
    return _install_ollama_official()


def _install_ollama_official() -> bool:
    """Install Ollama using official install script.

    Returns:
        bool: True if installation succeeded, False otherwise.

    """
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
        logger.error("Failed to install Ollama via official installer")
        return False

    return True


def _detect_gpu_vendor() -> str:
    """Detect GPU vendor for Ollama package selection.

    Returns:
        str: GPU vendor: "nvidia", "amd", or "unknown".

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
