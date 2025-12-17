"""Tests for default applications configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.defaults import DefaultAppsConfig


class TestDefaultAppsConfig:
    """Tests for default applications configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test default apps configuration (placeholder)."""
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

        defaults = DefaultAppsConfig()
        result = defaults.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.defaults.Path.write_text")
    @patch("aps.system.defaults.Path.exists", return_value=False)
    def test_set_defaults(
        self, _mock_exists: Mock, mock_write: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test setting default applications."""
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

        defaults = DefaultAppsConfig()
        result = defaults.set_defaults(browser="brave", terminal="alacritty")

        assert result is True
        mock_write.assert_called_once()
