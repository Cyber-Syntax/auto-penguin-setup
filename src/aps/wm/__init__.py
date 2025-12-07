"""Window manager configuration modules for Auto Penguin Setup."""

from .base import BaseWMConfig
from .i3 import I3Config
from .qtile import QtileConfig

__all__ = [
    "BaseWMConfig",
    "I3Config",
    "QtileConfig",
]
