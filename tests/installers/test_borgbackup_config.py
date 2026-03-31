"""Tests for borgbackup configuration, tracking, and utilities."""

from unittest.mock import MagicMock, patch

from aps.installers.borgbackup import is_installed, uninstall
from aps.utils.paths import resolve_config_file


class TestBorgbackupIsInstalled:
    """Test borgbackup is_installed function."""

    def test_is_installed_true(self) -> None:
        """Test is_installed returns True when timer is enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_installed() is True

    def test_is_installed_false(self) -> None:
        """Test is_installed returns False when timer is not enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_installed() is False

    def test_is_installed_user_mode_checks_user_timer(self) -> None:
        """User mode checks is-enabled borg.timer (system scope, not user)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_installed() is True
            cmd = mock_run.call_args[0][0]
            assert "--user" not in cmd
            assert "borg.timer" in cmd

    def test_is_installed_root_mode_checks_system_timer(self) -> None:
        """Root mode checks systemctl is-enabled borg.timer (system scope)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_installed() is True
            cmd = mock_run.call_args[0][0]
            assert "--user" not in cmd
            assert "borg.timer" in cmd

    def test_is_installed_false_user_mode(self) -> None:
        """Test is_installed returns False for user mode when disabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_installed() is False

    def test_is_installed_false_root_mode(self) -> None:
        """Test is_installed returns False for root mode when disabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_installed() is False


class TestBorgbackupUninstall:
    """Test borgbackup uninstall function."""

    def test_uninstall_user_mode_disables_user_timer(
        self, mock_run_privileged: MagicMock
    ) -> None:
        """User uninstall disables borg.timer (system scope, not --user)."""
        uninstall()

        disable_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "disable" in str(call)
        ]
        assert len(disable_calls) > 0
        disable_cmd = str(disable_calls[0])
        assert "borg.timer" in disable_cmd
        assert "--user" not in disable_cmd

    def test_uninstall_user_mode_removes_user_files(
        self, mock_run_privileged: MagicMock
    ) -> None:
        """Remove files from /usr/local/sbin/ and /etc/systemd/system/."""
        uninstall()

        rm_calls = [
            str(call)
            for call in mock_run_privileged.call_args_list
            if "rm" in str(call)
        ]
        removed = " ".join(rm_calls)
        assert "/usr/local/sbin/borg.sh" in removed
        assert "/etc/systemd/system/borg.service" in removed
        assert "/etc/systemd/system/borg.timer" in removed

    @patch("subprocess.run")
    def test_uninstall_root_mode_disables_system_timer(
        self, mock_run: MagicMock, mock_run_privileged: MagicMock
    ) -> None:
        """Root uninstall should disable system timer."""
        mock_run.return_value = MagicMock(returncode=0)
        uninstall()

        disable_call = [
            call
            for call in mock_run_privileged.call_args_list
            if "disable" in str(call)
        ]
        assert len(disable_call) > 0
        assert "borg.timer" in str(disable_call[0])

    @patch("subprocess.run")
    def test_uninstall_root_mode_removes_root_files(
        self, mock_run: MagicMock, mock_run_privileged: MagicMock
    ) -> None:
        """Remove files from /opt/borg/ and /etc/systemd/system/."""
        mock_run.return_value = MagicMock(returncode=0)
        uninstall()

        rm_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "/usr/bin/rm" in str(call)
        ]
        assert len(rm_calls) >= 4

    @patch("subprocess.run")
    @patch("pathlib.Path.unlink")
    def test_uninstall_user_mode_returns_true_on_success(
        self, mock_unlink: MagicMock, mock_run: MagicMock
    ) -> None:
        """User uninstall should return True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        result = uninstall()
        assert result is True

    @patch("subprocess.run")
    def test_uninstall_root_mode_returns_true_on_success(
        self, mock_run: MagicMock, mock_run_privileged: MagicMock
    ) -> None:
        """Root uninstall should return True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        result = uninstall()
        assert result is True


class TestBorgbackupSystemdFiles:
    """Test borgbackup systemd unit files exist with correct content."""

    def test_service_file_has_correct_exec_start(self) -> None:
        """System service should use absolute path."""
        service = resolve_config_file("borg-scripts/borg.service")
        content = service.read_text()
        assert "ExecStart=/usr/local/sbin/borg.sh" in content
        assert "Type=oneshot" in content

    def test_timer_file_has_daily_schedule(self) -> None:
        """Timer file should have daily schedule with persistence."""
        timer = resolve_config_file("borg-scripts/borg.timer")
        content = timer.read_text()
        assert "OnCalendar=*-*-* 07:00:00" in content
        assert "Persistent=true" in content


class TestBorgbackupConfigFiles:
    """Test user-mode and root-mode borgbackup config files."""

    def test_user_service_has_borg_user_and_capabilities(self) -> None:
        """System service needs User=borg and AmbientCapabilities."""
        service = resolve_config_file("borg-scripts/borg.service")
        content = service.read_text()
        assert "User=borg" in content
        assert "AmbientCapabilities=CAP_DAC_READ_SEARCH" in content

    def test_user_service_exec_start_uses_sbin(self) -> None:
        """System service ExecStart should use /usr/local/sbin/borg.sh."""
        service = resolve_config_file("borg-scripts/borg.service")
        content = service.read_text()
        assert "ExecStart=/usr/local/sbin/borg.sh" in content

    def test_user_script_uses_plain_borg(self) -> None:
        """System script should use plain 'borg' commands (no sudo)."""
        script = resolve_config_file("borg-scripts/borg.sh")
        content = script.read_text()
        # Check for plain borg commands without sudo
        assert "borg create" in content
        assert "borg prune" in content
        assert "borg check" in content
        assert "borg compact" in content
        # Ensure no sudo borg commands
        assert "sudo borg" not in content

    def test_user_script_excludes_path_uses_sbin(self) -> None:
        """System script should reference excludes.txt from /usr/local/sbin."""
        script = resolve_config_file("borg-scripts/borg.sh")
        content = script.read_text()
        # Script should reference excludes.txt file
        assert "excludes.txt" in content
        assert "/usr/local/sbin" in content
