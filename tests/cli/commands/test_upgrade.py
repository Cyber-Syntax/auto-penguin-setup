"""Tests for upgrade command functionality.

Verifies UV availability checking and os.execvp execution for self-updating.
"""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from aps.cli.commands.upgrade import cmd_upgrade


class TestUpgradeCommand:
    """Test upgrade command with various scenarios."""

    @patch("aps.cli.commands.upgrade.os.execvp")
    @patch("aps.cli.commands.upgrade.shutil.which")
    def test_upgrade_executes_with_uv_available(
        self,
        mock_which: Mock,
        mock_execvp: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test upgrade command executes when UV is available."""
        mock_which.return_value = "/usr/bin/uv"

        caplog.set_level("INFO")
        args = Namespace()

        cmd_upgrade(args)

        assert "Checking for UV availability" in caplog.text
        assert "Upgrading auto-penguin-setup to latest version" in caplog.text
        assert "Running: uv tool upgrade auto-penguin-setup" in caplog.text

        mock_which.assert_called_once_with("uv")
        mock_execvp.assert_called_once_with(
            "uv", ["uv", "tool", "upgrade", "auto-penguin-setup"]
        )

    @patch("aps.cli.commands.upgrade.shutil.which")
    def test_upgrade_fails_when_uv_not_found(
        self,
        mock_which: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test upgrade command exits with error when UV not found."""
        mock_which.return_value = None

        caplog.set_level("ERROR")
        args = Namespace()

        with pytest.raises(SystemExit) as exc_info:
            cmd_upgrade(args)

        assert exc_info.value.code == 1
        assert "UV not found" in caplog.text
        assert "Please install UV first" in caplog.text
        assert "https://docs.astral.sh/uv/" in caplog.text

    @patch("aps.cli.commands.upgrade.os.execvp")
    @patch("aps.cli.commands.upgrade.shutil.which")
    def test_upgrade_handles_execvp_oserror(
        self,
        mock_which: Mock,
        mock_execvp: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test upgrade command handles OSError from execvp."""
        mock_which.return_value = "/usr/bin/uv"
        mock_execvp.side_effect = OSError("Command not found")

        caplog.set_level("ERROR")
        args = Namespace()

        with pytest.raises(SystemExit) as exc_info:
            cmd_upgrade(args)

        assert exc_info.value.code == 1
        assert "Failed to execute upgrade command" in caplog.text
        assert "Command not found" in caplog.text

    @patch("aps.cli.commands.upgrade.os.execvp")
    @patch("aps.cli.commands.upgrade.shutil.which")
    def test_upgrade_with_different_uv_path(
        self,
        mock_which: Mock,
        mock_execvp: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test upgrade works with UV in different path."""
        mock_which.return_value = "/home/user/.cargo/bin/uv"

        caplog.set_level("INFO")
        args = Namespace()

        cmd_upgrade(args)

        assert "Upgrading auto-penguin-setup" in caplog.text
        mock_which.assert_called_once_with("uv")
        mock_execvp.assert_called_once_with(
            "uv", ["uv", "tool", "upgrade", "auto-penguin-setup"]
        )

    @patch("aps.cli.commands.upgrade.os.execvp")
    @patch("aps.cli.commands.upgrade.shutil.which")
    def test_upgrade_checks_uv_before_execvp(
        self,
        mock_which: Mock,
        mock_execvp: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test upgrade checks UV availability before attempting execvp."""
        mock_which.return_value = "/usr/bin/uv"

        caplog.set_level("INFO")
        args = Namespace()

        cmd_upgrade(args)

        call_order = []
        for record in caplog.records:
            if "Checking for UV availability" in record.message:
                call_order.append("check_uv")
            elif "Upgrading auto-penguin-setup" in record.message:
                call_order.append("upgrade")

        assert call_order == ["check_uv", "upgrade"]
        assert mock_which.called
        assert mock_execvp.called
