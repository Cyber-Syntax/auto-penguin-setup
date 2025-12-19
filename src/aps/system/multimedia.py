"""Multimedia package configuration for Fedora systems."""

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

from .base import BaseSystemConfig

logger = get_logger(__name__)


class MultimediaConfig(BaseSystemConfig):
    """Configure multimedia packages like FFmpeg."""

    def configure(self) -> bool:
        """Swap ffmpeg-free with full ffmpeg on Fedora."""
        if self.distro != "fedora":
            logger.info("FFmpeg swap only applies to Fedora, skipping")
            return True

        logger.info("Checking for ffmpeg-free package...")

        # Check if ffmpeg-free is installed
        check_result = run_privileged(
            ["dnf", "list", "installed", "ffmpeg-free"],
            capture_output=True,
            text=True,
            check=False,
        )

        if check_result.returncode != 0:
            logger.info("ffmpeg-free is not installed, skipping swap")
            return True

        logger.info("Swapping ffmpeg-free with ffmpeg...")

        result = run_privileged(
            ["dnf", "swap", "ffmpeg-free", "ffmpeg", "--allowerasing", "-y"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to swap ffmpeg packages")
            return False

        logger.info("FFmpeg swap completed successfully")
        return True
