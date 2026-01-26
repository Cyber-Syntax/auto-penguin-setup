"""Tests for sudoers configuration module."""

from pathlib import Path
from unittest.mock import Mock, patch

from aps.system import sudoers

EXPECTED_RUN_PRIVILEGED_CALLS = 2


class TestSudoersConfig:
    """Tests for Sudoers configuration."""

    def test_sudoers_file_constant(self) -> None:
        """Test SUDOERS_FILE constant."""
        assert Path("/etc/sudoers") == sudoers.SUDOERS_FILE

    @patch("aps.system.sudoers.configure_terminal_timeout")
    def test_configure_success(
        self,
        mock_configure_timeout: Mock,
    ) -> None:
        """Test successful configuration."""
        mock_configure_timeout.return_value = True

        result = sudoers.configure(distro="fedora")

        assert result is True
        mock_configure_timeout.assert_called_once()

    @patch("aps.system.sudoers.configure_terminal_timeout")
    def test_configure_failure(
        self,
        mock_configure_timeout: Mock,
    ) -> None:
        """Test configuration failure."""
        mock_configure_timeout.return_value = False

        result = sudoers.configure(distro="fedora")

        assert result is False
        mock_configure_timeout.assert_called_once()

    @patch("aps.system.sudoers._create_backup")
    @patch("aps.system.sudoers._update_sudoers_section")
    def test_configure_terminal_timeout_success(
        self,
        mock_update_section: Mock,
        mock_create_backup: Mock,
    ) -> None:
        """Test successful terminal timeout configuration."""
        mock_create_backup.return_value = True
        mock_update_section.return_value = True

        result = sudoers.configure_terminal_timeout()

        assert result is True
        mock_create_backup.assert_called_once()
        mock_update_section.assert_called_once()

    @patch("aps.system.sudoers._create_backup")
    def test_configure_terminal_timeout_backup_failure(
        self,
        mock_create_backup: Mock,
    ) -> None:
        """Test terminal timeout configuration when backup fails."""
        mock_create_backup.return_value = False

        result = sudoers.configure_terminal_timeout()

        assert result is False
        mock_create_backup.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    @patch("aps.system.sudoers._create_backup")
    @patch("aps.system.sudoers.Path.read_text")
    @patch("aps.system.sudoers._restore_latest_backup")
    def test_configure_terminal_timeout_validation_failure(
        self,
        mock_restore: Mock,
        mock_read_text: Mock,
        mock_create_backup: Mock,
        mock_run_privileged: Mock,
    ) -> None:
        """Test terminal timeout configuration when validation fails."""
        mock_create_backup.return_value = True
        mock_read_text.return_value = "existing content"
        mock_restore.return_value = True

        # Mock tee success, visudo failure
        mock_run_privileged.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # tee
            Mock(returncode=1, stdout="", stderr=""),  # visudo
        ]

        result = sudoers.configure_terminal_timeout()

        assert result is False
        mock_create_backup.assert_called_once()
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS

    @patch("aps.system.sudoers.run_privileged")
    @patch("aps.system.sudoers.Path.read_text")
    @patch("aps.system.sudoers._validate_sudoers")
    def test_update_sudoers_section_existing(
        self,
        mock_validate: Mock,
        mock_read_text: Mock,
        mock_run_privileged: Mock,
    ) -> None:
        """Test updating sudoers section when existing section present."""
        mock_read_text.return_value = (
            "existing content\n# START\nold config\n# END\nmore content"
        )
        mock_run_privileged.return_value = Mock(returncode=0)
        mock_validate.return_value = True

        result = sudoers._update_sudoers_section(
            "# START", "# END", "new config"
        )

        assert result is True
        mock_run_privileged.assert_called()

    @patch("aps.system.sudoers.Path.read_text")
    def test_update_sudoers_section_exception(
        self,
        mock_read_text: Mock,
    ) -> None:
        """Test updating sudoers section when read_text raises exception."""
        mock_read_text.side_effect = OSError("Permission denied")

        result = sudoers._update_sudoers_section(
            "# START", "# END", "new config"
        )

        assert result is False

    @patch("aps.system.sudoers.run_privileged")
    def test_create_backup_success(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test successful backup creation."""
        mock_run_privileged.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )

        result = sudoers._create_backup()

        assert result is True
        mock_run_privileged.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    def test_create_backup_failure(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test backup creation failure."""
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        result = sudoers._create_backup()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    def test_validate_sudoers_success(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test successful sudoers validation."""
        mock_run_privileged.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )

        result = sudoers._validate_sudoers()

        assert result is True
        mock_run_privileged.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    def test_validate_sudoers_failure(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test sudoers validation failure."""
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        result = sudoers._validate_sudoers()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_success(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test successful backup restoration."""
        mock_run_privileged.side_effect = [
            Mock(
                returncode=0,
                stdout="/etc/sudoers.bak.20231218120000\n/etc/sudoers.bak.20231218110000",
                stderr="",
            ),
            Mock(returncode=0, stdout="", stderr=""),
        ]

        result = sudoers._restore_latest_backup()

        assert result is True
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS

    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_no_backups(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test backup restoration when no backups exist."""
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        result = sudoers._restore_latest_backup()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_restore_failure(
        self,
        mock_run_privileged: Mock,
    ) -> None:
        """Test backup restoration when restore command fails."""
        mock_run_privileged.side_effect = [
            Mock(
                returncode=0,
                stdout="/etc/sudoers.bak.20231218120000",
                stderr="",
            ),
            Mock(returncode=1, stdout="", stderr=""),
        ]

        result = sudoers._restore_latest_backup()

        assert result is False
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS
