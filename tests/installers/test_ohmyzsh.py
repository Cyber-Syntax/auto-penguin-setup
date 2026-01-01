"""Tests for Oh-My-Zsh installer module."""

from pathlib import Path
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.ohmyzsh import _get_zshrc_path, install


class TestOhMyZshInstall:
    """Test Oh-My-Zsh install function."""

    @patch("shutil.which")
    def test_install_zsh_not_installed(
        self,
        mock_which: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install fails when zsh is not installed."""
        caplog.set_level("ERROR")
        mock_which.return_value = None

        result = install()

        assert result is False
        assert "Zsh is not installed" in caplog.text

    @patch("shutil.which", return_value="/usr/bin/zsh")
    @patch("aps.installers.ohmyzsh._get_zshrc_path")
    def test_install_already_installed(
        self,
        mock_zshrc: Mock,
        mock_which: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install when already installed."""
        caplog.set_level("INFO")
        mock_zshrc.return_value = Path.home() / ".zshrc"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("shutil.copy2"),
            patch("aps.installers.ohmyzsh._update_zshrc", return_value=True),
        ):
            result = install()

            assert result is True
            assert (
                "updating configuration" in caplog.text
                or "already installed" in caplog.text
            )


class TestOhMyZshGetZshrcPath:
    """Test _get_zshrc_path function."""

    @patch("aps.installers.ohmyzsh._get_zshrc_path")
    def test_get_zshrc_path(self, mock_zshrc: Mock) -> None:
        """Test _get_zshrc_path returns valid path."""
        mock_zshrc.return_value = Path.home() / ".zshrc"

        result = _get_zshrc_path()

        assert result is not None
        assert isinstance(result, Path)
