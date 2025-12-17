"""Application installer modules for Auto Penguin Setup."""

from .autocpufreq import AutoCPUFreqInstaller
from .base import BaseInstaller
from .borgbackup import BorgbackupInstaller
from .brave import BraveInstaller
from .nfancurve import NfancurveInstaller
from .ohmyzsh import OhMyZshInstaller
from .protonvpn import ProtonVPNInstaller
from .syncthing import SyncthingInstaller
from .thinkfan import ThinkfanInstaller
from .tlp import TLPInstaller
from .trashcli import TrashCLIInstaller
from .ueberzugpp import UeberzugppInstaller
from .virtmanager import VirtManagerInstaller
from .vscode import VSCodeInstaller

__all__ = [
    "AutoCPUFreqInstaller",
    "BaseInstaller",
    "BorgbackupInstaller",
    "BraveInstaller",
    "NfancurveInstaller",
    "OhMyZshInstaller",
    "ProtonVPNInstaller",
    "SyncthingInstaller",
    "ThinkfanInstaller",
    "TLPInstaller",
    "TrashCLIInstaller",
    "UeberzugppInstaller",
    "VirtManagerInstaller",
    "VSCodeInstaller",
]
