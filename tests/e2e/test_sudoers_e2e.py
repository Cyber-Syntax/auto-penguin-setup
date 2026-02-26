"""E2E tests for sudoers configuration."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import aps.system.sudoers as sudoers_module
from aps.system.sudoers import configure_terminal_timeout


class TestSudoersE2E:
    """E2E tests for sudoers configuration."""

    def test_configure_terminal_timeout_e2e(
        self,
        sudoers_e2e_tmp_root: Path,
        mock_sudoers_filesystem: Path,
        mock_sudoers_commands: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test full terminal timeout configuration workflow.

        Verifies:
        - Backup file is created
        - Sudoers file contains the marker section
        - Configuration values are correct
        - Original content is preserved

        Args:
            sudoers_e2e_tmp_root: Temp root for sudoers tests
            mock_sudoers_filesystem: Mock sudoers filesystem
            mock_sudoers_commands: Mock system commands
            monkeypatch: pytest monkeypatch fixture
        """
        sudoers_file = sudoers_e2e_tmp_root / "etc" / "sudoers"
        monkeypatch.setattr(sudoers_module, "SUDOERS_FILE", sudoers_file)

        result = configure_terminal_timeout()
        assert result is True

        # Verify backup file was created
        backup_files = list(sudoers_e2e_tmp_root.glob("etc/sudoers.bak.*"))
        assert len(backup_files) > 0

        # Verify marker section is in the sudoers file
        sudoers_content = sudoers_file.read_text()
        marker_start = "# BEGIN auto-penguin-setup: terminal-timeout"
        marker_end = "# END auto-penguin-setup: terminal-timeout"
        assert marker_start in sudoers_content
        assert marker_end in sudoers_content
        assert "Defaults timestamp_type=global" in sudoers_content
        assert "Defaults env_reset,timestamp_timeout=20" in sudoers_content

    def test_configure_terminal_timeout_idempotent_e2e(
        self,
        sudoers_e2e_tmp_root: Path,
        mock_sudoers_filesystem: Path,
        mock_sudoers_commands: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test running configuration twice doesn't duplicate section.

        Verifies:
        - Marker section appears exactly once after second run
        - Content is correct after both runs

        Args:
            sudoers_e2e_tmp_root: Temp root for sudoers tests
            mock_sudoers_filesystem: Mock sudoers filesystem
            mock_sudoers_commands: Mock system commands
            monkeypatch: pytest monkeypatch fixture
        """
        sudoers_file = sudoers_e2e_tmp_root / "etc" / "sudoers"
        monkeypatch.setattr(sudoers_module, "SUDOERS_FILE", sudoers_file)

        result1 = configure_terminal_timeout()
        result2 = configure_terminal_timeout()

        assert result1 is True
        assert result2 is True

        # Verify marker section appears exactly once
        sudoers_content = sudoers_file.read_text()
        marker = "# BEGIN auto-penguin-setup: terminal-timeout"
        marker_count = sudoers_content.count(marker)
        assert marker_count == 1

    def test_configure_terminal_timeout_backup_preserved_e2e(
        self,
        sudoers_e2e_tmp_root: Path,
        mock_sudoers_filesystem: Path,
        mock_sudoers_commands: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test backup file contains original sudoers content.

        Verifies:
        - Backup file exists
        - Backup content matches original fixture content

        Args:
            sudoers_e2e_tmp_root: Temp root for sudoers tests
            mock_sudoers_filesystem: Mock sudoers filesystem
            mock_sudoers_commands: Mock system commands
            monkeypatch: pytest monkeypatch fixture
        """
        sudoers_file = sudoers_e2e_tmp_root / "etc" / "sudoers"
        monkeypatch.setattr(sudoers_module, "SUDOERS_FILE", sudoers_file)

        original_content = sudoers_file.read_text()
        result = configure_terminal_timeout()
        assert result is True

        # Verify backup file exists and contains original content
        backup_files = list(sudoers_e2e_tmp_root.glob("etc/sudoers.bak.*"))
        assert len(backup_files) > 0
        backup_content = backup_files[0].read_text()
        assert backup_content == original_content

    def test_configure_terminal_timeout_validation_failure_restores_e2e(
        self,
        sudoers_e2e_tmp_root: Path,
        mock_sudoers_filesystem: Path,
        mock_sudoers_commands: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test backup is restored when visudo validation fails.

        Verifies:
        - When visudo returns failure, backup is restored
        - Sudoers file content matches original after restore

        Args:
            sudoers_e2e_tmp_root: Temp root for sudoers tests
            mock_sudoers_filesystem: Mock sudoers filesystem
            mock_sudoers_commands: Mock system commands
            monkeypatch: pytest monkeypatch fixture
        """
        sudoers_file = sudoers_e2e_tmp_root / "etc" / "sudoers"
        monkeypatch.setattr(sudoers_module, "SUDOERS_FILE", sudoers_file)

        original_content = sudoers_file.read_text()

        # Wrap the existing handler to intercept visudo
        original_handler = mock_sudoers_commands.side_effect

        def visudo_failure_handler(
            cmd: list[str], **kwargs: object
        ) -> MagicMock:
            """Delegate to conftest handler but fail visudo."""
            name = cmd[0].split("/")[-1] if cmd and "/" in cmd[0] else cmd[0]
            if name == "visudo":
                return MagicMock(
                    returncode=1,
                    stdout="",
                    stderr="Syntax error",
                )
            return original_handler(cmd, **kwargs)

        mock_sudoers_commands.side_effect = visudo_failure_handler

        result = configure_terminal_timeout()
        assert result is False

        # Verify backup was actually created
        backup_files = list(sudoers_e2e_tmp_root.glob("etc/sudoers.bak.*"))
        assert len(backup_files) > 0

        # Verify sudoers file was restored to original content
        restored_content = sudoers_file.read_text()
        assert restored_content == original_content
