"""Tests for ProtonVPN installer module."""

from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.protonvpn import ProtonVPNInstaller


class TestProtonVPNInstallerInit:
    """Test ProtonVPNInstaller initialization."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ProtonVPNInstaller()
        assert installer.distro == "fedora"


class TestProtonVPNInstall:
    """Test ProtonVPNInstaller install method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Fedora."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        installer = ProtonVPNInstaller()
        with patch.object(installer, "_install_fedora", return_value=True):
            result = installer.install()
            assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Arch."""
        mock_distro.return_value = MagicMock(id="arch")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        installer = ProtonVPNInstaller()
        with patch.object(installer, "_install_arch", return_value=True):
            result = installer.install()
            assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_unsupported_distro(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install on unsupported distribution."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="unknown")
        installer = ProtonVPNInstaller()

        result = installer.install()
        assert result is False
        assert "Unsupported" in caplog.text or "distro" in caplog.text.lower()
