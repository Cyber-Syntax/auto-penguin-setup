"""Tests for network configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.network import NetworkConfig


class TestNetworkConfig:
    """Tests for network configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.network.Path.exists", return_value=True)
    @patch("aps.system.network.shutil.copy2")
    def test_configure_success(
        self,
        mock_copy: Mock,
        _mock_exists: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful TCP BBR configuration."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        network = NetworkConfig()
        result = network.configure()

        assert result is True
        mock_copy.assert_called_once()
