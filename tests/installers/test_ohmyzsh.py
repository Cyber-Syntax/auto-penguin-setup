"""Tests for Oh-My-Zsh installer module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.ohmyzsh import OhMyZshInstaller


class TestOhMyZshInstallerInit:
    """Test OhMyZshInstaller initialization."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = OhMyZshInstaller()
        assert installer.distro == "fedora"


class TestOhMyZshInstall:
    """Test OhMyZshInstaller install method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("shutil.which")
    def test_install_zsh_not_installed(
        self,
        mock_which: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install fails when zsh is not installed."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = None

        installer = OhMyZshInstaller()
        result = installer.install()

        assert result is False
        assert "Zsh is not installed" in caplog.text

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("shutil.which", return_value="/usr/bin/zsh")
    @patch.object(OhMyZshInstaller, "_get_zshrc_path")
    def test_install_already_installed(
        self,
        mock_zshrc: Mock,
        mock_which: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install when already installed."""
        caplog.set_level("INFO")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm_instance = MagicMock()
        mock_pm.return_value = mock_pm_instance
        mock_zshrc.return_value = Path.home() / ".zshrc"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("shutil.copy2"),
        ):
            with patch.object(
                OhMyZshInstaller, "_update_zshrc", return_value=True
            ):
                installer = OhMyZshInstaller()
                result = installer.install()

                assert result is True
                assert (
                    "updating configuration" in caplog.text
                    or "already installed" in caplog.text
                )


class TestOhMyZshGetZshrcPath:
    """Test OhMyZshInstaller _get_zshrc_path method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch.object(OhMyZshInstaller, "_get_zshrc_path")
    def test_get_zshrc_path(
        self, mock_zshrc: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test _get_zshrc_path returns valid path."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_zshrc.return_value = Path.home() / ".zshrc"

        installer = OhMyZshInstaller()
        result = installer._get_zshrc_path()

        assert result is not None
        assert isinstance(result, Path)
