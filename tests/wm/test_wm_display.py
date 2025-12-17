"""Tests for window manager and display manager configuration modules."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.display.lightdm import LightDMConfig
from aps.display.sddm import SDDMConfig
from aps.wm.i3 import I3Config
from aps.wm.qtile import QtileConfig


class TestQtileConfig:
    """Tests for Qtile window manager configuration."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful Qtile installation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm

        qtile = QtileConfig()
        result = qtile.install(["qtile", "python3-qtile"])

        assert result is True
        mock_pm.install.assert_called_once_with(["qtile", "python3-qtile"])

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    def test_setup_backlight_rules(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test backlight rules setup."""
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
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        qtile = QtileConfig()

        with patch.object(Path, "exists", return_value=True):
            result = qtile.setup_backlight_rules("/tmp/qtile.rules", "/tmp/backlight.conf")

        assert result is True

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_configure(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test Qtile configuration."""
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

        qtile = QtileConfig()
        result = qtile.configure()

        assert result is True


class TestI3Config:
    """Tests for i3 window manager configuration."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_install_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful i3 installation."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm

        i3 = I3Config()
        result = i3.install(["i3-wm", "i3status"])

        assert result is True
        mock_pm.install.assert_called_once_with(["i3-wm", "i3status"])

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_configure(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test i3 configuration."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_get_pm.return_value = MagicMock()

        i3 = I3Config()
        result = i3.configure()

        assert result is True


class TestSDDMConfig:
    """Tests for SDDM display manager configuration."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.display.sddm.subprocess.run")
    def test_install_already_installed(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test SDDM installation when already installed."""
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
        mock_run.return_value = Mock(returncode=0, stdout="sddm-1.0", stderr="")

        sddm = SDDMConfig()
        result = sddm.install()

        assert result is True

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.display.sddm.subprocess.run")
    def test_switch_to_sddm(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test switching to SDDM."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm

        # First call checks if installed (returns non-zero, not installed)
        # Subsequent calls for systemctl commands
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr=""),  # rpm -q sddm (not installed)
            Mock(returncode=0, stdout="gdm.service", stderr=""),  # list-units
            Mock(returncode=0, stdout="", stderr=""),  # disable gdm
            Mock(returncode=0, stdout="", stderr=""),  # enable sddm
        ]

        sddm = SDDMConfig()
        result = sddm.switch_to_sddm()

        assert result is True

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.display.sddm.subprocess.run")
    @patch("aps.display.sddm.Path.exists", return_value=False)
    def test_configure_autologin(
        self, mock_exists: Mock, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test SDDM autologin configuration."""
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
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        sddm = SDDMConfig()
        result = sddm.configure_autologin("testuser", "qtile")

        assert result is True


class TestLightDMConfig:
    """Tests for LightDM display manager configuration."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_install_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test successful LightDM installation."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm

        lightdm = LightDMConfig()
        result = lightdm.install()

        assert result is True
        mock_pm.install.assert_called_once_with(["lightdm"])

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.display.lightdm.run_privileged")
    def test_switch_to_lightdm(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test switching to LightDM."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        lightdm = LightDMConfig()
        result = lightdm.switch_to_lightdm()

        assert result is True

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.display.lightdm.run_privileged")
    @patch("aps.display.lightdm.Path.exists", return_value=True)
    def test_configure_autologin(
        self, mock_exists: Mock, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test LightDM autologin configuration."""
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

        # Mock config file content
        config_content = """[LightDM]
run-directory=/run/lightdm

[Seat:*]
#autologin-user=
#autologin-session=
"""

        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # cp (backup)
            Mock(returncode=0, stdout=config_content, stderr=""),  # cat
            Mock(returncode=0, stdout="", stderr=""),  # tee
        ]

        lightdm = LightDMConfig()
        result = lightdm.configure_autologin("testuser", "qtile")

        assert result is True
