"""Tests for SDDM display manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.display.sddm import SDDMConfig


class TestSDDMConfigInit:
    """Test SDDMConfig initialization."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_init_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test SDDMConfig initialization on Arch Linux."""
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

        config = SDDMConfig()

        assert config.distro == "arch"
        assert config.distro_info == arch_distro

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_init_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test SDDMConfig initialization on Fedora."""
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

        config = SDDMConfig()

        assert config.distro == "fedora"


class TestSDDMConfigInstall:
    """Test SDDMConfig install method."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("subprocess.run")
    def test_install_already_installed(
        self, mock_subprocess: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test install when SDDM is already installed."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0)

        config = SDDMConfig()
        result = config.install()

        assert result is True

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("subprocess.run")
    def test_install_success(
        self, mock_subprocess: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test successful SDDM installation."""
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
        mock_subprocess.return_value = MagicMock(returncode=1)

        config = SDDMConfig()
        result = config.install()

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["sddm"])

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("subprocess.run")
    def test_install_failure(
        self, mock_subprocess: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test SDDM installation failure."""
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
        mock_subprocess.return_value = MagicMock(returncode=1)

        config = SDDMConfig()
        result = config.install()

        assert result is False


class TestSDDMConfigConfigureAutologin:
    """Test SDDMConfig configure_autologin method."""

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
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        config = SDDMConfig()
        result = config.configure_autologin("testuser", "plasma")

        assert result is True

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    @patch("aps.utils.privilege.run_privileged")
    def test_configure_autologin_with_different_session(
        self, mock_run_priv: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test autologin configuration with different session."""
        mock_distro.return_value = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_pm.return_value = MagicMock()
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        config = SDDMConfig()
        result = config.configure_autologin("myuser", "qtile")

        assert result is True
