"""System configuration modules for Auto Penguin Setup."""

from .base import BaseSystemConfig
from .firewall import UFWConfig
from .multimedia import MultimediaConfig
from .pm_optimizer import PackageManagerOptimizer
from .repositories import RepositoryConfig
from .ssh import SSHConfig
from .sudoers import SudoersConfig

__all__ = [
    "BaseSystemConfig",
    "MultimediaConfig",
    "PackageManagerOptimizer",
    "RepositoryConfig",
    "SSHConfig",
    "SudoersConfig",
    "UFWConfig",
]
