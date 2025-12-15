"""Tests for aps.main module."""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from aps.core.logger import setup_logging
from aps.main import main


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_log_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that setup_logging creates the log directory."""
        log_dir = tmp_path / ".config" / "auto-penguin-setup" / "logs"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        setup_logging()

        assert log_dir.exists()
        assert (log_dir / "aps.log").exists()

    def test_setup_logging_configures_handlers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that setup_logging configures both file and stream handlers."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        setup_logging()

        root_logger = logging.getLogger()
        handlers = root_logger.handlers

        # Should have exactly 2 handlers: RotatingFileHandler and StreamHandler
        assert len(handlers) == 2

        # Check that there's a StreamHandler with INFO level (default non-verbose)
        stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
        assert any(h.level == logging.INFO for h in stream_handlers)


class TestMain:
    """Tests for main function."""

    def test_main_install_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with install command."""
        mock_cmd_install = Mock()
        monkeypatch.setattr("aps.main.cmd_install", mock_cmd_install)
        monkeypatch.setattr(sys, "argv", ["aps", "install", "package"])

        result = main()

        assert result == 0
        mock_cmd_install.assert_called_once()

    def test_main_remove_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with remove command."""
        mock_cmd_remove = Mock()
        monkeypatch.setattr("aps.main.cmd_remove", mock_cmd_remove)
        monkeypatch.setattr(sys, "argv", ["aps", "remove", "package"])

        result = main()

        assert result == 0
        mock_cmd_remove.assert_called_once()

    def test_main_list_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with list command."""
        mock_cmd_list = Mock()
        monkeypatch.setattr("aps.main.cmd_list", mock_cmd_list)
        monkeypatch.setattr(sys, "argv", ["aps", "list"])

        result = main()

        assert result == 0
        mock_cmd_list.assert_called_once()

    def test_main_sync_repos_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with sync-repos command."""
        mock_cmd_sync_repos = Mock()
        monkeypatch.setattr("aps.main.cmd_sync_repos", mock_cmd_sync_repos)
        monkeypatch.setattr(sys, "argv", ["aps", "sync-repos"])

        result = main()

        assert result == 0
        mock_cmd_sync_repos.assert_called_once()

    def test_main_status_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with status command."""
        mock_cmd_status = Mock()
        monkeypatch.setattr("aps.main.cmd_status", mock_cmd_status)
        monkeypatch.setattr(sys, "argv", ["aps", "status"])

        result = main()

        assert result == 0
        mock_cmd_status.assert_called_once()

    def test_main_setup_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with setup command."""
        mock_cmd_setup = Mock()
        monkeypatch.setattr("aps.main.cmd_setup", mock_cmd_setup)
        monkeypatch.setattr(sys, "argv", ["aps", "setup", "aur-helper"])

        result = main()

        assert result == 0
        mock_cmd_setup.assert_called_once()

    def test_main_no_command(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main without a command shows help and exits with 2."""
        monkeypatch.setattr(sys, "argv", ["aps"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "usage:" in captured.err

    def test_main_invalid_command(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main with invalid command shows help and exits with 2."""
        monkeypatch.setattr(sys, "argv", ["aps", "invalid"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "usage:" in captured.err
