"""Display manager configuration modules for Auto Penguin Setup."""

from .base import BaseDisplayManager
from .lightdm import LightDMConfig
from .sddm import SDDMConfig

__all__ = [
    "BaseDisplayManager",
    "LightDMConfig",
    "SDDMConfig",
]
