"""System configuration modules for Auto Penguin Setup."""

from .base import BaseSystemConfig
from .bootloader import BootloaderConfig
from .defaults import DefaultAppsConfig
from .firewall import UFWConfig
from .multimedia import MultimediaConfig
from .network import NetworkConfig
from .pm_optimizer import PackageManagerOptimizer
from .repositories import RepositoryConfig
from .ssh import SSHConfig
from .sudoers import SudoersConfig

__all__ = [
    "BaseSystemConfig",
    "BootloaderConfig",
    "DefaultAppsConfig",
    "MultimediaConfig",
    "NetworkConfig",
    "PackageManagerOptimizer",
    "RepositoryConfig",
    "SSHConfig",
    "SudoersConfig",
    "UFWConfig",
]
