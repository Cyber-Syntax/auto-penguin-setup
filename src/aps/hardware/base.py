"""Base class for hardware configuration modules."""

from abc import ABC, abstractmethod

from aps.core.logger import get_logger

logger = get_logger(__name__)


class BaseHardwareConfig(ABC):
    """Base class for hardware configuration modules."""

    def __init__(self, distro: str):
        """Initialize hardware configuration.

        Args:
            distro: Distribution name (fedora, arch, debian)

        """
        self.distro = distro
        self.logger = logger

    @abstractmethod
    def configure(self, **kwargs) -> bool:
        """Configure hardware-specific settings.

        Args:
            **kwargs: Configuration-specific keyword arguments

        Returns:
            True if configuration succeeds, False otherwise

        """
        pass

    def _copy_config_file(self, source: str, destination: str) -> bool:
        """Copy configuration file to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if copy succeeds, False otherwise

        """
        import os
        import shutil

        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)

            # Copy file
            shutil.copy2(source, destination)
            self.logger.info("Copied %s to %s", source, destination)
            return True
        except OSError as e:
            self.logger.error(
                "Failed to copy %s to %s: %s", source, destination, e
            )
            return False
