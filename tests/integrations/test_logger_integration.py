"""Integration tests for logging system."""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from aps.core.logger import get_logger, setup_logging


@pytest.mark.integration
class TestLoggingIntegration:
    def test_no_duplicate_messages_normal_mode(self, tmp_path: Path) -> None:
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=False)
            logger = get_logger("test")
            logger.info("Single message")
        output = stderr_capture.getvalue()
        assert output.count("Single message") == 1

    def test_no_duplicate_messages_verbose_mode(self, tmp_path: Path) -> None:
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=True)
            logger = get_logger("test")
            logger.debug("Debug message")
        output = stderr_capture.getvalue()
        assert output.count("Debug message") == 1

    def test_multiple_loggers_use_same_configuration(
        self, tmp_path: Path
    ) -> None:
        stderr_capture = StringIO()
        with patch.object(sys, "stderr", stderr_capture):
            setup_logging(verbose=False)
            logger1 = get_logger("module1")
            logger2 = get_logger("module2")
            logger1.info("Message from module1")
            logger2.info("Message from module2")
        output = stderr_capture.getvalue()
        assert "Message from module1" in output
        assert "Message from module2" in output
