"""Tests for Ueberzugpp installer module."""

from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.ueberzugpp import install


class TestUeberzugppInstall:
    """Test ueberzugpp install function."""

    @patch("aps.installers.ueberzugpp.detect_distro")
    @patch("aps.installers.ueberzugpp.get_package_manager")
    def test_install_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Fedora."""
        mock_distro.return_value = MagicMock()
        mock_distro.return_value.id = "fedora"
        mock_distro.return_value.name = "fedora"
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        result = install()
        assert result is True

    @patch("aps.installers.ueberzugpp.detect_distro")
    @patch("aps.installers.ueberzugpp.get_package_manager")
    def test_install_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install on Arch."""
        mock_distro.return_value = MagicMock()
        mock_distro.return_value.id = "arch"
        mock_distro.return_value.name = "arch"
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        result = install()
        assert result is True

    @patch("aps.installers.ueberzugpp.detect_distro")
    @patch("aps.core.package_manager.get_package_manager")
    def test_install_unsupported_distro(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install on unsupported distribution."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock()
        mock_distro.return_value.id = "unknown"
        mock_distro.return_value.name = "unknown"

        result = install()
        assert result is False
