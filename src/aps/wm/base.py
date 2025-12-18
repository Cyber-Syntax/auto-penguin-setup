"""Base class for window manager configuration modules."""

import logging
from abc import ABC, abstractmethod

from aps.core.distro import DistroInfo, detect_distro
from aps.core.package_manager import get_package_manager

logger = logging.getLogger(__name__)


class BaseWMConfig(ABC):
    """Base class for window manager configuration modules.

    Provides common functionality for window manager installation and
    configuration across different distributions.
    """

    def __init__(self) -> None:
        """Initialize the window manager configuration module."""
        self.distro_info: DistroInfo = detect_distro()
        self.distro = self.distro_info.id
        self.pm = get_package_manager(self.distro_info)

    @abstractmethod
    def install(self) -> bool:
        """Install the window manager and its dependencies.

        Returns:
            bool: True if installation was successful, False otherwise.

        """

    @abstractmethod
    def configure(self) -> bool:
        """Configure the window manager.

        Returns:
            bool: True if configuration was successful, False otherwise.

        """
