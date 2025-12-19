"""Tests for TLP installer module."""

from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.tlp import TLPInstaller


class TestTLPInstallerInit:
    """Test TLPInstaller initialization."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = TLPInstaller()
        assert installer.distro == "fedora"


class TestTLPInstall:
    """Test TLPInstaller install method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Fedora."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm_instance.remove.return_value = (True, None)
        mock_pm_instance.is_installed.return_value = False
        mock_pm.return_value = mock_pm_instance

        installer = TLPInstaller()
        with patch.object(installer, "try_official_first", return_value=True):
            with patch("shutil.which", return_value="/usr/bin/tlp"):
                with patch("shutil.copy2"):
                    with patch("pathlib.Path.exists", return_value=True):
                        result = installer.install()
                        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Arch."""
        mock_distro.return_value = MagicMock(id="arch")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm_instance.remove.return_value = (True, None)
        mock_pm_instance.is_installed.return_value = False
        mock_pm.return_value = mock_pm_instance

        installer = TLPInstaller()
        with patch.object(installer, "try_official_first", return_value=True):
            with patch("shutil.which", return_value="/usr/bin/tlp"):
                with patch("shutil.copy2"):
                    with patch("pathlib.Path.exists", return_value=True):
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
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Unsupported")
        mock_pm_instance.remove.return_value = (False, "Unsupported")
        mock_pm_instance.is_installed.return_value = False
        mock_pm.return_value = mock_pm_instance

        installer = TLPInstaller()

        result = installer.install()
        assert result is False
