"""Tests for LightDM display manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.display.lightdm import LightDMConfig


class TestLightDMConfigInit:
    """Test LightDMConfig initialization."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_init_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test LightDMConfig initialization on Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = fedora_distro
        mock_pm.return_value = MagicMock()

        config = LightDMConfig()

        assert config.distro == "fedora"
        assert config.distro_info == fedora_distro


class TestLightDMConfigInstall:
    """Test LightDMConfig install method."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_install_success(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test successful LightDM installation."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, "Success")
        mock_pm.return_value = mock_pm_instance

        config = LightDMConfig()
        result = config.install()

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["lightdm"])

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_install_failure(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test LightDM installation failure."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Installation failed")
        mock_pm.return_value = mock_pm_instance

        config = LightDMConfig()
        result = config.install()

        assert result is False


class TestLightDMConfigConfigureAutologin:
    """Test LightDMConfig configure_autologin method."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.utils.privilege.run_privileged")
    def test_configure_autologin_success(
        self, mock_run_priv: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test successful autologin configuration."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        # Mock the file read and write operations
        mock_run_priv.return_value = MagicMock(
            returncode=0,
            stdout="[General]\n",
            stderr="",
        )

        config = LightDMConfig()
        result = config.configure_autologin("testuser", "qtile")

        assert result is True
