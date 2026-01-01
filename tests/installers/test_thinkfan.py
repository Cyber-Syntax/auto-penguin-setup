"""Tests for ThinkFan installer module."""

from unittest.mock import MagicMock, Mock, mock_open, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.thinkfan import install


class TestThinkfanInstall:
    """Test thinkfan install function."""

    @patch("aps.core.distro.detect_distro")
    @patch("aps.core.package_manager.get_package_manager")
    @patch("shutil.which", return_value="/usr/bin/thinkfan")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_install_fedora(
        self,
        mock_open_file: Mock,
        mock_which: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test install on Fedora."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        with (
            patch("shutil.copy2"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = install()
            assert result is True

    @patch("aps.core.distro.detect_distro")
    @patch("aps.core.package_manager.get_package_manager")
    @patch("shutil.which", return_value="/usr/bin/thinkfan")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_install_arch(
        self,
        mock_open_file: Mock,
        mock_which: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test install on Arch."""
        mock_distro.return_value = MagicMock(id="arch")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, None)
        mock_pm.return_value = mock_pm_instance

        with (
            patch("shutil.copy2"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = install()
            assert result is True

    @patch("aps.core.distro.detect_distro")
    @patch("aps.core.package_manager.get_package_manager")
    def test_install_unsupported_distro(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install on unsupported distribution."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="unknown")
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Unsupported")
        mock_pm_instance.remove.return_value = (False, "Unsupported")
        mock_pm.return_value = mock_pm_instance

        result = install()
        assert result is False
