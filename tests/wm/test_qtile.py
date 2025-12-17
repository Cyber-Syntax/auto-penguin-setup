"""Tests for Qtile window manager configuration module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.wm.qtile import QtileConfig


class TestQtileConfigInit:
    """Test QtileConfig initialization."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test QtileConfig initialization on Fedora."""
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

        config = QtileConfig()

        assert config.distro == "fedora"
        assert config.distro_info == fedora_distro

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test QtileConfig initialization on Arch Linux."""
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

        config = QtileConfig()

        assert config.distro == "arch"


class TestQtileConfigInstall:
    """Test QtileConfig install method."""

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

        config = QtileConfig()
        result = config.install(packages=["qtile"])

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["qtile"])

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

        config = QtileConfig()
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

        config = QtileConfig()
        result = config.install(packages=["qtile"])

        assert result is False


class TestQtileConfigSetupBacklightRules:
    """Test QtileConfig setup_backlight_rules method."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    @patch("aps.utils.privilege.run_privileged")
    def test_setup_backlight_rules_success(
        self, mock_run_priv: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test successful backlight rules setup."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        config = QtileConfig()
        result = config.setup_backlight_rules(Path("/tmp/qtile.rules"), Path("/tmp/backlight.conf"))

        assert result is True


class TestQtileConfigConfigure:
    """Test QtileConfig configure method."""

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

        config = QtileConfig()
        result = config.configure()

        assert result is True
