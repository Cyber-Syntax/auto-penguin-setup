"""Ollama installer module."""

import shutil
import subprocess
from pathlib import Path

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


def uninstall(distro: str | None = None) -> bool:
    """Uninstall Ollama.

    On Arch, attempts pacman removal then always runs cleanup.
    On other distributions, runs manual cleanup directly.

    Args:
        distro: Distribution ID (e.g., 'arch', 'fedora'). If None, uses
            manual cleanup only.

    Returns:
        bool: True if uninstallation was successful, False otherwise.

    """
    binary_path = shutil.which("ollama")
    if not binary_path:
        logger.warning("Ollama is not installed")
        return True

    logger.info("Uninstalling Ollama from %s", binary_path)

    if distro == "arch":
        _uninstall_via_pacman()
        # Always cleanup regardless of pacman result
        success = _cleanup_ollama_artifacts()
    else:
        success = _cleanup_ollama_artifacts()

    if success:
        logger.info("Ollama uninstallation completed successfully")
    else:
        logger.warning("Ollama uninstallation had some errors but completed")

    return True


def _uninstall_via_pacman() -> bool:
    """Remove Ollama via pacman on Arch Linux.

    Returns:
        bool: True if pacman removal succeeded or wasn't applicable, False on
            failure.

    """
    binary_path = shutil.which("ollama")
    if not binary_path:
        return True

    # Check if pacman owns the binary
    result = subprocess.run(  # noqa: S603
        ["pacman", "-Qo", binary_path],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.info(
            "Pacman does not own Ollama binary, skipping pacman removal"
        )
        return True

    # Extract package name from pacman output (format: "repo/package version")
    output_parts = result.stdout.split()
    min_parts = 2
    if len(output_parts) < min_parts:
        logger.warning("Could not parse pacman output")
        return False

    pkg_name = output_parts[1]
    logger.info("Removing Ollama package via pacman: %s", pkg_name)

    removal_result = run_privileged(
        ["/usr/bin/pacman", "-R", "--noconfirm", pkg_name],
        capture_output=False,
        text=True,
        check=False,
    )

    if removal_result.returncode == 0:
        logger.info("Successfully removed Ollama via pacman")
        return True

    logger.warning("Pacman removal failed, will continue with manual cleanup")
    return False


def _cleanup_ollama_artifacts() -> bool:
    """Remove Ollama artifacts (best effort cleanup).

    Removes systemd service, library directories, binary, user/group, and
    data directories.

    Returns:
        bool: True (always succeeds with best effort approach).

    """
    binary_path = shutil.which("ollama")
    if not binary_path:
        return True

    # Stop and disable systemd service
    logger.info("Stopping Ollama service...")
    stop_result = run_privileged(
        ["/usr/bin/systemctl", "stop", "ollama"],
        capture_output=True,
        text=True,
        check=False,
    )
    if stop_result.returncode != 0:
        logger.warning("Failed to stop Ollama service (may not exist)")

    logger.info("Disabling Ollama service...")
    disable_result = run_privileged(
        ["/usr/bin/systemctl", "disable", "ollama"],
        capture_output=True,
        text=True,
        check=False,
    )
    if disable_result.returncode != 0:
        logger.warning("Failed to disable Ollama service (may not exist)")

    # Remove service file
    logger.info("Removing Ollama service file...")
    service_file = "/etc/systemd/system/ollama.service"
    rm_service_result = run_privileged(
        ["/usr/bin/rm", "-f", service_file],
        capture_output=True,
        text=True,
        check=False,
    )
    if rm_service_result.returncode != 0:
        logger.warning("Failed to remove service file %s", service_file)

    # Determine and remove lib directory
    # Get the directory containing the binary and replace 'bin' with 'lib'
    bin_dir = Path(binary_path).parent
    lib_dir = bin_dir.parent / "lib" / "ollama"
    logger.info("Removing Ollama library directory: %s", lib_dir)
    rm_lib_result = run_privileged(
        ["/usr/bin/rm", "-rf", str(lib_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if rm_lib_result.returncode != 0:
        logger.warning("Failed to remove library directory %s", lib_dir)

    # Remove binary
    logger.info("Removing Ollama binary: %s", binary_path)
    rm_binary_result = run_privileged(
        ["/usr/bin/rm", "-f", binary_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if rm_binary_result.returncode != 0:
        logger.warning("Failed to remove binary %s", binary_path)

    # Remove user
    logger.info("Removing Ollama user...")
    userdel_result = run_privileged(
        ["/usr/sbin/userdel", "ollama"],
        capture_output=True,
        text=True,
        check=False,
    )
    if userdel_result.returncode != 0:
        logger.warning("Failed to remove user 'ollama' (may not exist)")

    # Remove group
    logger.info("Removing Ollama group...")
    groupdel_result = run_privileged(
        ["/usr/sbin/groupdel", "ollama"],
        capture_output=True,
        text=True,
        check=False,
    )
    if groupdel_result.returncode != 0:
        logger.warning("Failed to remove group 'ollama' (may not exist)")

    # Remove data directory
    logger.info("Removing Ollama data directory...")
    data_dir = "/usr/share/ollama"
    rm_data_result = run_privileged(
        ["/usr/bin/rm", "-rf", data_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    if rm_data_result.returncode != 0:
        logger.warning("Failed to remove data directory %s", data_dir)

    logger.info("Ollama cleanup completed")
    return True
