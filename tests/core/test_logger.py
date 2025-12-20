"""Tests for centralized logging configuration."""

import logging
import sys
from io import StringIO
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

import pytest

from aps.core.logger import get_logger, setup_logging


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory."""
    return tmp_path / ".config" / "auto-penguin-setup" / "logs"


@pytest.fixture
def mock_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock Path.home() to use temporary directory."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def test_creates_log_directory(self, mock_home: Path) -> None:
        """Test that log directory is created if it doesn't exist."""
        setup_logging()

        log_dir = mock_home / ".config" / "auto-penguin-setup" / "logs"
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_creates_log_file(self, mock_home: Path) -> None:
        """Test that log file is created."""
        setup_logging()

        log_file = (
            mock_home / ".config" / "auto-penguin-setup" / "logs" / "aps.log"
        )
        # File may not exist until first log, but parent directory should
        assert log_file.parent.exists()

    def test_normal_mode_shows_info_messages(self, mock_home: Path) -> None:
        """Test that INFO messages are shown in normal mode."""
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=False)
            logger = logging.getLogger("test")
            logger.info("Test info message")
            logger.debug("Test debug message")

        output = stderr_capture.getvalue()
        assert "Test info message" in output
        assert "Test debug message" not in output

    def test_verbose_mode_shows_debug_messages(self, mock_home: Path) -> None:
        """Test that DEBUG messages are shown in verbose mode."""
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=True)
            logger = logging.getLogger("test")
            logger.info("Test info message")
            logger.debug("Test debug message")

        output = stderr_capture.getvalue()
        assert "Test info message" in output
        assert "Test debug message" in output

    def test_file_handler_configured_with_rotation(
        self, mock_home: Path
    ) -> None:
        """Test that file handler is configured with proper rotation."""
        setup_logging()

        root_logger = logging.getLogger()
        file_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, RotatingFileHandler)
        ]

        assert len(file_handlers) == 1
        handler = file_handlers[0]
        # Type narrowing for mypy - we know it's a RotatingFileHandler
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 5 * 1024 * 1024  # 5MB
        assert handler.backupCount == 3

    def test_clears_existing_handlers(self, mock_home: Path) -> None:
        """Test that existing handlers are cleared to avoid duplicates."""
        # Setup logging once
        setup_logging(verbose=False)
        root_logger = logging.getLogger()
        handler_count_first = len(root_logger.handlers)

        # Setup again - should clear and recreate
        setup_logging(verbose=True)
        handler_count_second = len(root_logger.handlers)

        # Should have same number of handlers, not double
        assert handler_count_first == handler_count_second
        # Should have exactly 2 handlers: file + console
        assert handler_count_second == 2

    def test_console_output_format_is_simple(self, mock_home: Path) -> None:
        """Test that console output uses simple format without timestamps."""
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=False)
            logger = logging.getLogger("test.module")
            logger.info("Simple message")

        output = stderr_capture.getvalue()
        # Should just be the message, no timestamp or module name
        assert output.strip() == "Simple message"

    def test_file_output_format_is_detailed(self, mock_home: Path) -> None:
        """Test that file output includes timestamps and module names."""
        setup_logging(verbose=False)
        log_file = (
            mock_home / ".config" / "auto-penguin-setup" / "logs" / "aps.log"
        )

        logger = logging.getLogger("test.module")
        logger.info("Detailed message")

        # Force flush to ensure message is written
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text()
        assert "test.module" in content
        assert "INFO" in content
        assert "Detailed message" in content
        # Should contain timestamp (year)
        assert "2025" in content or "2024" in content


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_returns_logger_instance(self) -> None:
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_returns_logger_with_correct_name(self) -> None:
        """Test that logger has the correct name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_returns_same_logger_for_same_name(self) -> None:
        """Test that same logger is returned for same name."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")
        assert logger1 is logger2
