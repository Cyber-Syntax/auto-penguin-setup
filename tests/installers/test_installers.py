"""Tests for application installers."""

from unittest.mock import MagicMock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.installers.brave import BraveInstaller
from aps.installers.vscode import VSCodeInstaller
