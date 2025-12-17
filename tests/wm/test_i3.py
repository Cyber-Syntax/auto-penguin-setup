"""Tests for i3 window manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.wm.i3 import I3Config


class TestI3ConfigInit:
    """Test I3Config initialization."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test I3Config initialization on Fedora."""
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

        config = I3Config()

        assert config.distro == "fedora"
        assert config.distro_info == fedora_distro

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test I3Config initialization on Arch Linux."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_distro.return_value = arch_distro
        mock_pm.return_value = MagicMock()

        config = I3Config()

        assert config.distro == "arch"


class TestI3ConfigInstall:
    """Test I3Config install method."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_with_packages(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install with packages provided."""
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

        config = I3Config()
        result = config.install(packages=["i3", "i3status"])

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["i3", "i3status"])

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_without_packages(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install without packages (empty list)."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm.return_value = mock_pm_instance

        config = I3Config()
        result = config.install()

        assert result is True
        mock_pm_instance.install.assert_not_called()

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_failure(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install failure."""
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

        config = I3Config()
        result = config.install(packages=["i3"])

        assert result is False

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_exception_handling(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install exception handling."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.side_effect = Exception("Install error")
        mock_pm.return_value = mock_pm_instance

        config = I3Config()
        result = config.install(packages=["i3"])

        assert result is False


class TestI3ConfigConfigure:
    """Test I3Config configure method."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_configure_returns_true(self, _mock_pm: Mock, _mock_distro: Mock) -> None:
        """Test that configure always returns True."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        _mock_distro.return_value = fedora_distro
        _mock_pm.return_value = MagicMock()

        config = I3Config()
        result = config.configure()

        assert result is True
