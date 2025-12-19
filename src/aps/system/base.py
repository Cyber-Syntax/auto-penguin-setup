"""Base class for system configuration modules."""

import logging
from abc import ABC, abstractmethod

from ..core.distro import DistroInfo, detect_distro
from ..core.package_manager import get_package_manager

logger = logging.getLogger(__name__)


class BaseSystemConfig(ABC):
    """Base class for system configuration modules.

    Provides common functionality for system configuration tasks across
    different distributions.
    """

    def __init__(self) -> None:
        """Initialize the system configuration module."""
        self.distro_info: DistroInfo = detect_distro()
        self.distro = self.distro_info.id
        self.pm = get_package_manager(self.distro_info)

    @abstractmethod
    def configure(self) -> bool:
        """Configure the system component.

        Returns:
            bool: True if configuration was successful, False otherwise.

        """
