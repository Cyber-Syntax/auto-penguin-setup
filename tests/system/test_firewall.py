"""Tests for firewall configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.firewall import UFWConfig


class TestUFWConfig:
    """Tests for UFW firewall configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful UFW configuration."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(ufw, "_configure_default_policies", return_value=True),
            patch.object(ufw, "_configure_syncthing_rules", return_value=True),
            patch.object(ufw, "_enable_ufw", return_value=True),
        ):
            result = ufw.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_ufw_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful UFW disabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()
        result = ufw._disable_ufw()  # noqa: SLF001

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_enable_ufw_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful UFW enabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()
        result = ufw._enable_ufw()  # noqa: SLF001

        assert result is True
