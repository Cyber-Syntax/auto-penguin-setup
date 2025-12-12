"""Auto-cpufreq installer for automatic CPU speed and power optimization."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseInstaller

logger = logging.getLogger(__name__)


class AutoCPUFreqInstaller(BaseInstaller):
    """Installer for auto-cpufreq from GitHub repository.

    Available in AUR, snap, and auto-cpufreq-installer from GitHub.
    Using GitHub installer for consistency across all distributions.
    """

    def install(self) -> bool:
        """Install auto-cpufreq from GitHub repository.

        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Installing auto-cpufreq...")

        # Check if git is available
        if not shutil.which("git"):
            logger.error("git is not installed. Please install git first.")
            return False

        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Clone repository
            logger.info("Cloning auto-cpufreq repository...")
            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/AdnanHodzic/auto-cpufreq.git",
                        str(repo_path / "auto-cpufreq"),
                    ],
                    check=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Failed to clone auto-cpufreq repository (exit code %s). See output above.",
                    e.returncode,
                )
                return False

            installer_dir = repo_path / "auto-cpufreq"
            installer_script = installer_dir / "auto-cpufreq-installer"

            if not installer_script.exists():
                logger.error("Installer script not found in cloned repository")
                return False

            # Run installer with automatic "Install" option
            logger.info("Running auto-cpufreq installer...")
            logger.info("NOTE: The installer will ask for confirmation during installation.")
            logger.info("Please respond to the prompts as needed (typically 'y' to proceed).")
            logger.info("Installer output will be streamed directly from the script.")

            try:
                # Pipe "I" into installer to automatically select Install option
                subprocess.run(
                    ["sudo", str(installer_script)],
                    input="I\n",
                    cwd=installer_dir,
                    check=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    "auto-cpufreq installation failed (exit code %s). See installer output above.",
                    e.returncode,
                )
                return False

        logger.info("auto-cpufreq installation completed")
        return True

    def is_installed(self) -> bool:
        """Check if auto-cpufreq is installed.

        Returns:
            True if installed, False otherwise
        """
        return shutil.which("auto-cpufreq") is not None
