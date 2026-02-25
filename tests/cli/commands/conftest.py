"""Test fixtures for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_config_validation():
    """Mock APSConfigParser validation to skip file loading in install tests.

    This allows existing tests to run without needing real config files.
    Tests that specifically test the validation behavior will override this
    mock with their own @patch decorators.

    """
    patcher = patch("aps.cli.commands.install.APSConfigParser")
    mock_parser_cls = patcher.start()
    mock_instance = MagicMock()
    mock_instance.validate_no_flatpak_category.return_value = None
    mock_parser_cls.return_value = mock_instance

    yield

    patcher.stop()
