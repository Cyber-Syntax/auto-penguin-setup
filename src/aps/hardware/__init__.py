"""Hardware configuration modules."""

from aps.hardware.amd import AMDConfig
from aps.hardware.hostname import HostnameConfig
from aps.hardware.intel import IntelConfig
from aps.hardware.nvidia import NvidiaConfig
from aps.hardware.touchpad import TouchpadConfig

__all__ = [
    "AMDConfig",
    "HostnameConfig",
    "IntelConfig",
    "NvidiaConfig",
    "TouchpadConfig",
]
