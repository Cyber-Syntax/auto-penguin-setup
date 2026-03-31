"""Tests for borgbackup install function."""

import subprocess
from unittest.mock import MagicMock, patch

from aps.installers.borgbackup import (
    _init_borg_repo,
    _set_backup_dir_permissions,
    _uninstall_user,
    install,
    is_installed,
)


class TestBorgbackupInstall:
    """Test borgbackup install function."""

    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_success_fedora(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
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
        mock_pm.install.assert_called_once_with(
            ["borgbackup"], assume_yes=True
        )
        # mkdir, 4x cp, chmod, daemon-reload, enable timer = 8 calls minimum
        assert mock_run_privileged.call_count >= 6

    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_success_arch(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
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
        mock_pm.install.assert_called_once_with(["borg"], assume_yes=True)
        assert mock_run_privileged.call_count >= 6

    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_root_mode_no_useradd(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Root-mode install should not call useradd."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
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


class TestBorgbackupUserModeInstall:
    """Test user-mode borgbackup installation."""

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_mode_copies_system_paths(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode copies files to system paths."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        # Verify run_privileged was called for cp operations with correct paths
        cp_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/cp"
        ]
        assert len(cp_calls) == 4
        cp_dests = [str(call.args[0][2]) for call in cp_calls]
        assert "/usr/local/sbin/borg.sh" in cp_dests
        assert "/usr/local/sbin/excludes.txt" in cp_dests
        assert "/etc/systemd/system/borg.service" in cp_dests
        assert "/etc/systemd/system/borg.timer" in cp_dests

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_mode_no_opt_borg_mkdir(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode should not create /opt/borg directory."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        # Verify mkdir /opt/borg was NOT called
        assert not any(
            "/opt/borg" in str(call.args)
            for call in mock_run_privileged.call_args_list
        )

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=False)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_mode_creates_borg_user(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode still needs borg user for service User=borg capability."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        # Verify useradd was called since user didn't exist
        assert any(
            call.args[0][0].endswith("useradd")
            for call in mock_run_privileged.call_args_list
        )

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_mode_enables_system_timer(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode enables system timer without --user."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        # Verify systemctl enable --now borg.timer was called (no --user flag)
        enable_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if (
                "/usr/bin/systemctl" in str(call.args[0])
                and "enable" in str(call.args[0])
            )
        ]
        assert len(enable_calls) > 0
        assert "borg.timer" in str(enable_calls[0])
        assert "--user" not in str(enable_calls[0])

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_copies_script_to_sbin(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode should copy script to /usr/local/sbin/borg.sh."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        cp_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/cp"
        ]
        cp_dests = [str(call.args[0][2]) for call in cp_calls]
        assert "/usr/local/sbin/borg.sh" in cp_dests

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_copies_excludes_to_sbin(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode should copy excludes to /usr/local/sbin/excludes.txt."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        cp_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/cp"
        ]
        cp_dests = [str(call.args[0][2]) for call in cp_calls]
        assert "/usr/local/sbin/excludes.txt" in cp_dests

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_copies_service_to_etc_systemd(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode copies service to /etc/systemd/system/."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        cp_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/cp"
        ]
        cp_dests = [str(call.args[0][2]) for call in cp_calls]
        assert "/etc/systemd/system/borg.service" in cp_dests

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_copies_timer_to_etc_systemd(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode should copy timer to /etc/systemd/system/borg.timer."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        cp_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/cp"
        ]
        cp_dests = [str(call.args[0][2]) for call in cp_calls]
        assert "/etc/systemd/system/borg.timer" in cp_dests

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_makes_script_executable(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode should make script executable via run_privileged."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        chmod_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if call.args[0][0] == "/usr/bin/chmod"
        ]
        assert len(chmod_calls) > 0
        assert any(
            (
                "+x" in str(call.args[0])
                and "/usr/local/sbin/borg.sh" in str(call.args[0])
            )
            for call in chmod_calls
        )

    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_daemon_reload_before_enable(
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User mode daemon-reload should be called before enable --now."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        result = install()

        assert result is True
        daemon_reload_idx = None
        enable_idx = None

        for idx, call in enumerate(mock_run_privileged.call_args_list):
            call_args = str(call.args[0])
            if "daemon-reload" in call_args:
                daemon_reload_idx = idx
            if "enable" in call_args and "borg.timer" in call_args:
                enable_idx = idx

        assert daemon_reload_idx is not None
        assert enable_idx is not None
        msg = "daemon-reload must be called before enable"
        assert daemon_reload_idx < enable_idx, msg

    @patch("aps.installers.borgbackup._init_borg_repo")
    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_calls_repo_init(  # noqa: PLR0913
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_init_repo: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode install should call _init_borg_repo."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm
        mock_init_repo.return_value = True

        result = install()

        assert result is True
        mock_init_repo.assert_called_once_with("/mnt/backups/borgbackup/home")

    @patch("aps.installers.borgbackup._set_backup_dir_permissions")
    @patch("aps.installers.borgbackup._init_borg_repo")
    @patch("aps.installers.borgbackup._borg_user_exists", return_value=True)
    @patch("aps.installers.borgbackup.get_package_manager")
    @patch("aps.installers.borgbackup.detect_distro")
    @patch("aps.installers.borgbackup.resolve_config_file")
    def test_install_user_calls_set_permissions(  # noqa: PLR0913
        self,
        mock_resolve: MagicMock,
        mock_detect: MagicMock,
        mock_get_pm: MagicMock,
        mock_user_exists: MagicMock,
        mock_init_repo: MagicMock,
        mock_set_perms: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User-mode install should call _set_backup_dir_permissions."""
        mock_resolve.return_value = "/fake/path/to/config"
        mock_detect.return_value.family.name = "FEDORA"
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm
        mock_init_repo.return_value = True
        mock_set_perms.return_value = True

        result = install()

        assert result is True
        mock_set_perms.assert_called_once_with("/mnt/backups/borgbackup/home")

    @patch("subprocess.run")
    def test_is_installed_user_checks_borg_timer(
        self,
        mock_subprocess_run: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """is_installed user mode checks borg.timer without --user."""
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        result = is_installed()

        assert result is True
        # Verify the command used
        call_args = mock_subprocess_run.call_args_list[0]
        cmd = call_args.args[0] if call_args.args else call_args[0]
        assert cmd == ["/usr/bin/systemctl", "is-enabled", "borg.timer"]
        assert "--user" not in cmd


class TestBorgbackupRepoInit:
    """Test borg repository initialization helper."""

    @patch("aps.installers.borgbackup.subprocess.run")
    @patch("aps.installers.borgbackup.Path")
    def test_init_borg_repo_calls_borg_init(
        self,
        mock_path_cls: MagicMock,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Test _init_borg_repo calls borg init directly (no sudo)."""
        # First Path(repo_path)/"data" check → not initialised
        mock_data = MagicMock()
        mock_data.exists.return_value = False
        # Second Path(repo_path) check → directory exists
        mock_repo = MagicMock()
        mock_repo.exists.return_value = True
        mock_repo.__truediv__ = MagicMock(return_value=mock_data)
        mock_path_cls.return_value = mock_repo

        result = _init_borg_repo("/mnt/backups/borgbackup/home")

        assert result is True
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args[1] == "init"
        assert "--encryption=none" in call_args
        assert "/mnt/backups/borgbackup/home" in call_args

    @patch("aps.installers.borgbackup.subprocess.run")
    @patch("aps.installers.borgbackup.Path")
    def test_init_borg_repo_skips_if_already_initialised(
        self,
        mock_path_cls: MagicMock,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Test that _init_borg_repo skips init when data subdir exists."""
        mock_data = MagicMock()
        mock_data.exists.return_value = True
        mock_repo = MagicMock()
        mock_repo.__truediv__ = MagicMock(return_value=mock_data)
        mock_path_cls.return_value = mock_repo

        result = _init_borg_repo("/mnt/backups/borgbackup/home")

        assert result is True
        mock_subprocess_run.assert_not_called()

    @patch("aps.installers.borgbackup.subprocess.run")
    @patch("aps.installers.borgbackup.Path")
    def test_init_borg_repo_returns_false_if_dir_missing(
        self,
        mock_path_cls: MagicMock,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Test _init_borg_repo returns False when backup dir is absent."""
        mock_data = MagicMock()
        mock_data.exists.return_value = False
        mock_repo = MagicMock()
        mock_repo.exists.return_value = False  # backup dir itself missing
        mock_repo.__truediv__ = MagicMock(return_value=mock_data)
        mock_path_cls.return_value = mock_repo

        result = _init_borg_repo("/mnt/backups/borgbackup/home")

        assert result is False
        mock_subprocess_run.assert_not_called()

    @patch("aps.installers.borgbackup.run_privileged")
    @patch("aps.installers.borgbackup.Path")
    def test_set_backup_dir_permissions_calls_chown_chmod(
        self,
        mock_path_cls: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Test _set_backup_dir_permissions calls chown and chmod."""
        mock_path_cls.return_value.exists.return_value = True

        result = _set_backup_dir_permissions("/mnt/backups/borgbackup/home")

        assert result is True
        assert mock_run_privileged.call_count == 2
        mock_run_privileged.assert_any_call(
            [
                "/usr/bin/chown",
                "-R",
                "borg:borg",
                "/mnt/backups/borgbackup/home",
            ]
        )
        mock_run_privileged.assert_any_call(
            ["/usr/bin/chmod", "755", "/mnt/backups/borgbackup/home"]
        )

    @patch("aps.installers.borgbackup.run_privileged")
    @patch("aps.installers.borgbackup.Path")
    def test_set_backup_dir_permissions_skips_if_dir_missing(
        self,
        mock_path_cls: MagicMock,
        mock_run_privileged: MagicMock,
    ) -> None:
        """Test _set_backup_dir_permissions skips if dir doesn't exist."""
        mock_path_cls.return_value.exists.return_value = False

        result = _set_backup_dir_permissions("/mnt/backups/borgbackup/home")

        assert result is True
        mock_run_privileged.assert_not_called()


class TestBorgbackupUserModeUninstall:
    """Test user-mode borgbackup uninstallation."""

    def test_uninstall_user_disables_borg_timer(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall disables borg.timer (system scope)."""
        result = _uninstall_user()

        assert result is True
        disable_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "disable" in str(call.args[0])
        ]
        assert len(disable_calls) > 0
        assert disable_calls[0].args[0] == [
            "/usr/bin/systemctl",
            "disable",
            "--now",
            "borg.timer",
        ]

    def test_uninstall_user_removes_script_from_sbin(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall removes borg.sh from /usr/local/sbin/."""
        result = _uninstall_user()

        assert result is True
        rm_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "/usr/bin/rm" in str(call.args[0])
        ]
        assert any(
            "/usr/local/sbin/borg.sh" in str(call.args[0]) for call in rm_calls
        )

    def test_uninstall_user_removes_excludes_from_sbin(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall removes excludes.txt from /usr/local/sbin/."""
        result = _uninstall_user()

        assert result is True
        rm_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "/usr/bin/rm" in str(call.args[0])
        ]
        assert any(
            "/usr/local/sbin/excludes.txt" in str(call.args[0])
            for call in rm_calls
        )

    def test_uninstall_user_removes_service_from_systemd(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall removes borg.service from /etc/systemd/system/."""
        result = _uninstall_user()

        assert result is True
        rm_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "/usr/bin/rm" in str(call.args[0])
        ]
        assert any(
            "/etc/systemd/system/borg.service" in str(call.args[0])
            for call in rm_calls
        )

    def test_uninstall_user_removes_timer_from_systemd(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall removes borg.timer from /etc/systemd/system/."""
        result = _uninstall_user()

        assert result is True
        rm_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "/usr/bin/rm" in str(call.args[0])
        ]
        assert any(
            "/etc/systemd/system/borg.timer" in str(call.args[0])
            for call in rm_calls
        )

    def test_uninstall_user_reloads_daemon_after_remove(
        self,
        mock_run_privileged: MagicMock,
    ) -> None:
        """User uninstall reloads systemd daemon after file removal."""
        result = _uninstall_user()

        assert result is True
        daemon_reload_calls = [
            call
            for call in mock_run_privileged.call_args_list
            if "daemon-reload" in str(call.args[0])
        ]
        assert len(daemon_reload_calls) > 0
