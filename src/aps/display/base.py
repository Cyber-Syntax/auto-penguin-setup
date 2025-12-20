"""Base class for display manager configuration modules."""

from abc import ABC, abstractmethod

from aps.core.distro import DistroInfo, detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import get_package_manager

logger = get_logger(__name__)


class BaseDisplayManager(ABC):
    """Base class for display manager configuration modules.

    Provides common functionality for display manager installation and
    configuration across different distributions.
    """

    def __init__(self) -> None:
        """Initialize the display manager configuration module."""
        self.distro_info: DistroInfo = detect_distro()
        self.distro = self.distro_info.id
        self.pm = get_package_manager(self.distro_info)

    @abstractmethod
    def install(self) -> bool:
        """Install the display manager.

        Returns:
            bool: True if installation was successful, False otherwise.

        """

    @abstractmethod
    def configure_autologin(self, username: str, session: str) -> bool:
        """Configure autologin for the display manager.

        Args:
            username: Username to autologin
            session: Session name to start

        Returns:
            bool: True if configuration was successful, False otherwise.

        """
