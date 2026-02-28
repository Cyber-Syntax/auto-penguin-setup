"""Tests for borgbackup installer module."""

import subprocess
from unittest.mock import MagicMock, patch

from aps.installers.borgbackup import install, is_installed
from aps.utils.paths import resolve_config_file


class TestBorgbackupInstall:
    """Test borgbackup install function."""

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=False)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_success_fedora(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Test successful borgbackup installation on Fedora."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        mock_user_exists.assert_called_once_with("borg")
        mock_pm.install.assert_called_once_with(
            ["borgbackup"], assume_yes=True
        )
        assert any(
            call.args[0][0].endswith("useradd")
            for call in mock_run_privileged.call_args_list
        )
        # mkdir, 4x cp, chmod, daemon-reload, enable timer
        assert mock_run_privileged.call_count >= 6

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=False)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_success_arch(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Test successful borgbackup installation on Arch."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "ARCH"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        mock_user_exists.assert_called_once_with("borg")
        mock_pm.install.assert_called_once_with(["borg"], assume_yes=True)
        assert any(
            call.args[0][0].endswith("useradd")
            for call in mock_run_privileged.call_args_list
        )
        assert mock_run_privileged.call_count >= 6

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_skips_user_creation_when_user_exists(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Install should not call useradd when borg user already exists."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        mock_user_exists.assert_called_once_with("borg")
        assert not any(
            call.args[0][0].endswith("useradd")
            for call in mock_run_privileged.call_args_list
        )

    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_copy_failure_returns_false(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Test install returns False when file copy fails."""
        mock_resolve.return_value = "/fake/path"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm
        mock_run_privileged.side_effect = subprocess.CalledProcessError(
            1, "cp"
        )

        result = install()

        assert result is False


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


class TestBorgbackupSystemdFiles:
    """Test borgbackup systemd unit files exist with correct content."""

    def test_service_file_has_correct_exec_start(self) -> None:
        """Service file should reference /opt/borg/home-borgbackup.sh."""
        service = resolve_config_file("borg-scripts/home-borgbackup.service")
        content = service.read_text()
        assert "ExecStart=/opt/borg/home-borgbackup.sh" in content
        assert "Type=oneshot" in content

    def test_timer_file_has_daily_schedule(self) -> None:
        """Timer file should have daily schedule with persistence."""
        timer = resolve_config_file("borg-scripts/home-borgbackup.timer")
        content = timer.read_text()
        assert "OnCalendar=*-*-* 07:00:00" in content
        assert "Persistent=true" in content
