"""Tests for Virtual Machine Manager installer module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.core.distro import DistroFamily
from aps.installers.virtmanager import (
    _append_or_update_libvirt_setting,
    _arch_virtualization_packages,
    _configure_libvirt,
    _configure_libvirtd_conf,
    _configure_qemu_conf,
    _create_backup,
    _install_fedora,
    _setup_libvirt_group_access,
    _setup_network_config,
    _uncomment_and_replace,
    _uncomment_line,
    install,
)


class TestVirtManagerInstall:
    """Test virt-manager install function."""

    @patch("aps.installers.virtmanager.detect_distro")
    @patch("aps.installers.virtmanager._install_fedora")
    def test_install_fedora(
        self, mock_install_fedora: Mock, mock_distro: Mock
    ) -> None:
        """Test install on Fedora."""
        mock_distro.return_value = MagicMock(
            id="fedora", family=DistroFamily.FEDORA
        )
        mock_install_fedora.return_value = True

        result = install()
        assert result is True
        mock_install_fedora.assert_called_once_with()

    @patch("aps.installers.virtmanager.detect_distro")
    @patch("aps.installers.virtmanager._install_arch")
    def test_install_arch(
        self, mock_install_arch: Mock, mock_distro: Mock
    ) -> None:
        """Test install on Arch."""
        mock_distro.return_value = MagicMock(
            id="arch", family=DistroFamily.ARCH
        )
        mock_install_arch.return_value = True

        result = install()
        assert result is True
        mock_install_arch.assert_called_once_with()

    @patch("aps.installers.virtmanager.detect_distro")
    @patch("aps.installers.virtmanager._install_arch")
    def test_install_arch_derivative_cachyos(
        self, mock_install_arch: Mock, mock_distro: Mock
    ) -> None:
        """Test install on CachyOS (Arch derivative)."""
        mock_distro.return_value = MagicMock(
            id="cachyos", family=DistroFamily.ARCH
        )
        mock_install_arch.return_value = True

        result = install()

        assert result is True
        mock_install_arch.assert_called_once_with()

    @patch("aps.installers.virtmanager.detect_distro")
    def test_install_unsupported_distro(
        self, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install on unsupported distribution."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(
            id="unknown", family=DistroFamily.UNKNOWN
        )

        result = install()
        assert result is False
        assert "Unsupported" in caplog.text or "distro" in caplog.text.lower()


class TestArchVirtualizationPackages:
    """Test _arch_virtualization_packages function."""

    def test_arch_virtualization_packages_simplified(self) -> None:
        """Test simplified package list is returned."""
        mock_pm = MagicMock()

        result = _arch_virtualization_packages(mock_pm)

        expected = [
            "libvirt",
            "qemu-base",
            "virt-manager",
            "virt-install",
        ]
        assert result == expected
        assert isinstance(result, list)

    def test_arch_virtualization_packages_returns_list_not_tuple(self) -> None:
        """Test that function returns list, not tuple."""
        mock_pm = MagicMock()

        result = _arch_virtualization_packages(mock_pm)

        assert not isinstance(result, tuple)
        assert isinstance(result, list)

    def test_arch_virtualization_packages_no_package_checks(self) -> None:
        """Test that function doesn't check for package availability."""
        mock_pm = MagicMock()
        mock_pm.is_available_in_official_repos = MagicMock(return_value=False)

        result = _arch_virtualization_packages(mock_pm)

        # Should return simplified list regardless of availability
        expected = [
            "libvirt",
            "qemu-base",
            "virt-manager",
            "virt-install",
        ]
        assert result == expected
        # Should not have called is_available_in_official_repos
        mock_pm.is_available_in_official_repos.assert_not_called()

    def test_arch_virtualization_packages_order(self) -> None:
        """Test that packages are in expected order."""
        mock_pm = MagicMock()

        result = _arch_virtualization_packages(mock_pm)

        assert result[0] == "libvirt"
        assert result[1] == "qemu-base"
        assert result[2] == "virt-manager"
        assert result[3] == "virt-install"

    def test_arch_virtualization_packages_exact_content(self) -> None:
        """Test that exactly these packages are returned, no more, no less."""
        mock_pm = MagicMock()

        result = _arch_virtualization_packages(mock_pm)

        assert len(result) == 4
        assert "libvirt" in result
        assert "qemu-base" in result
        assert "virt-manager" in result
        assert "virt-install" in result

    """Test _append_or_update_libvirt_setting function."""

    @patch("aps.installers.virtmanager.run_privileged")
    def test_append_new_setting(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test appending a new key=value to file."""
        config_file = tmp_path / "libvirt.conf"
        config_file.write_text("# Existing content\n")

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _append_or_update_libvirt_setting(
            config_file, "firewall_backend", "nftables"
        )

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0] == ["/usr/bin/tee", str(config_file)]
        assert 'firewall_backend = "nftables"' in call_args[1]["stdin_input"]

    @patch("aps.installers.virtmanager.run_privileged")
    def test_update_existing_setting(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test updating an existing key with new value."""
        config_file = tmp_path / "libvirt.conf"
        config_file.write_text('firewall_backend = "iptables"\n')

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _append_or_update_libvirt_setting(
            config_file, "firewall_backend", "nftables"
        )

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0] == ["/usr/bin/tee", str(config_file)]
        content = call_args[1]["stdin_input"]
        assert 'firewall_backend = "nftables"' in content
        assert "iptables" not in content

    @patch("aps.installers.virtmanager.run_privileged")
    def test_setting_already_correct(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test no-op when setting already has correct value."""
        config_file = tmp_path / "libvirt.conf"
        config_file.write_text('firewall_backend = "nftables"\n')

        result = _append_or_update_libvirt_setting(
            config_file, "firewall_backend", "nftables"
        )

        assert result is True
        mock_run_privileged.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_append_to_nonexistent_file(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test creating file if it doesn't exist."""
        config_file = tmp_path / "nonexistent.conf"

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _append_or_update_libvirt_setting(
            config_file, "test_key", "test_value"
        )

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0] == ["/usr/bin/tee", str(config_file)]
        assert 'test_key = "test_value"' in call_args[1]["stdin_input"]

    @patch("aps.installers.virtmanager.run_privileged")
    def test_handle_subprocess_error(
        self,
        mock_run_privileged: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test handling subprocess errors."""
        caplog.set_level("ERROR")
        config_file = tmp_path / "libvirt.conf"
        config_file.write_text("# Content\n")

        mock_run_privileged.return_value = MagicMock(returncode=1)

        result = _append_or_update_libvirt_setting(
            config_file, "firewall_backend", "nftables"
        )

        assert result is False
        text_lower = caplog.text.lower()
        assert "error" in text_lower or "failed" in text_lower


class TestInstallFedora:
    """Test _install_fedora function."""

    @patch("aps.installers.virtmanager._configure_libvirt")
    @patch("aps.installers.virtmanager.run_privileged")
    def test_install_fedora_uses_fully_qualified_dnf_path(
        self, mock_run_privileged: Mock, mock_configure_libvirt: Mock
    ) -> None:
        """Test that _install_fedora uses fully qualified /usr/bin/dnf path."""
        mock_run_privileged.return_value = MagicMock(returncode=0)
        mock_configure_libvirt.return_value = True

        result = _install_fedora()

        assert result is True
        # Verify dnf was called with fully qualified path
        assert mock_run_privileged.call_count >= 1
        # Check first call uses /usr/bin/dnf
        first_call = mock_run_privileged.call_args_list[0]
        assert first_call[0][0][0] == "/usr/bin/dnf"

    @patch("aps.installers.virtmanager._configure_libvirt")
    @patch("aps.installers.virtmanager.run_privileged")
    def test_install_fedora_dnf_group_install_path(
        self, mock_run_privileged: Mock, mock_configure_libvirt: Mock
    ) -> None:
        """Test that dnf group install also uses fully qualified path."""
        mock_run_privileged.return_value = MagicMock(returncode=0)
        mock_configure_libvirt.return_value = True

        _install_fedora()

        # Check that second call also uses /usr/bin/dnf
        if mock_run_privileged.call_count >= 2:
            second_call = mock_run_privileged.call_args_list[1]
            assert second_call[0][0][0] == "/usr/bin/dnf"


class TestSetupLibvirtGroupAccess:
    """Test _setup_libvirt_group_access function."""

    @patch("aps.installers.virtmanager.subprocess.run")
    @patch("aps.installers.virtmanager.run_privileged")
    @patch("aps.installers.virtmanager.getpass.getuser")
    def test_getent_uses_fully_qualified_path(
        self,
        mock_getuser: Mock,
        mock_run_privileged: Mock,
        mock_subprocess_run: Mock,
    ) -> None:
        """Test that getent command uses fully qualified path."""
        mock_subprocess_run.return_value = MagicMock(returncode=1)
        mock_run_privileged.return_value = MagicMock(returncode=0)
        mock_getuser.return_value = "testuser"

        result = _setup_libvirt_group_access()

        assert result is True
        # Verify subprocess.run was called with fully qualified getent path
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0][0] == "/usr/bin/getent"

    @patch("aps.installers.virtmanager.subprocess.run")
    @patch("aps.installers.virtmanager.run_privileged")
    @patch("aps.installers.virtmanager.getpass.getuser")
    def test_groupadd_uses_fully_qualified_path(
        self,
        mock_getuser: Mock,
        mock_run_privileged: Mock,
        mock_subprocess_run: Mock,
    ) -> None:
        """Test that groupadd command uses fully qualified path."""
        mock_subprocess_run.return_value = MagicMock(returncode=1)
        mock_run_privileged.return_value = MagicMock(returncode=0)
        mock_getuser.return_value = "testuser"

        _setup_libvirt_group_access()

        # Verify groupadd was called with fully qualified path
        groupadd_call = None
        for call in mock_run_privileged.call_args_list:
            if call[0][0][0] == "/usr/sbin/groupadd":
                groupadd_call = call
                break
        assert groupadd_call is not None, "groupadd call not found"

    @patch("aps.installers.virtmanager.subprocess.run")
    @patch("aps.installers.virtmanager.run_privileged")
    @patch("aps.installers.virtmanager.getpass.getuser")
    def test_usermod_uses_fully_qualified_path(
        self,
        mock_getuser: Mock,
        mock_run_privileged: Mock,
        mock_subprocess_run: Mock,
    ) -> None:
        """Test that usermod command uses fully qualified path."""
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_run_privileged.return_value = MagicMock(returncode=0)
        mock_getuser.return_value = "testuser"

        _setup_libvirt_group_access()

        # Verify usermod was called with fully qualified path
        usermod_call = None
        for call in mock_run_privileged.call_args_list:
            if call[0][0][0] == "/usr/sbin/usermod":
                usermod_call = call
                break
        assert usermod_call is not None, "usermod call not found"


class TestCreateBackup:
    """Test _create_backup function."""

    @patch("aps.installers.virtmanager.run_privileged")
    def test_create_backup_success(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test successful backup creation."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text("# Config content\n")

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _create_backup(config_file)

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0][0] == "/usr/bin/cp"
        assert str(config_file) in call_args[0][0]
        assert str(config_file) + ".bak" in call_args[0][0]

    def test_backup_already_exists(self, tmp_path: Path) -> None:
        """Test skip if backup already exists."""
        config_file = tmp_path / "libvirtd.conf"
        backup_file = tmp_path / "libvirtd.conf.bak"

        config_file.write_text("# Config content\n")
        backup_file.write_text("# Old backup\n")

        with patch("aps.installers.virtmanager.run_privileged") as mock_run:
            result = _create_backup(config_file)

            assert result is True
            mock_run.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_create_backup_failure(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test failure returns False."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text("# Config content\n")

        mock_run_privileged.return_value = MagicMock(returncode=1)

        result = _create_backup(config_file)

        assert result is False


class TestUncommentLine:
    """Test _uncomment_line function."""

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_line_success(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test successfully uncomment a commented line."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text(
            "# unix_sock_group = 'libvirt'\nother_setting = 'value'\n"
        )

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _uncomment_line(config_file, "unix_sock_group")

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0][0] == "/usr/bin/tee"
        content = call_args[1]["stdin_input"]
        assert "unix_sock_group" in content
        assert content.count("#") == 0  # All comments removed

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_line_already_uncommented(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test idempotent behavior when line already uncommented."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text(
            "unix_sock_group = 'libvirt'\nother_setting = 'value'\n"
        )

        result = _uncomment_line(config_file, "unix_sock_group")

        assert result is True
        mock_run_privileged.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_line_pattern_not_found(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test returns False when pattern not found."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text("other_setting = 'value'\n")

        result = _uncomment_line(config_file, "unix_sock_group")

        assert result is False
        mock_run_privileged.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_line_subprocess_error(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test handle subprocess errors."""
        config_file = tmp_path / "libvirtd.conf"
        config_file.write_text("# unix_sock_group = 'libvirt'\n")

        mock_run_privileged.return_value = MagicMock(returncode=1)

        result = _uncomment_line(config_file, "unix_sock_group")

        assert result is False


class TestUncommentAndReplace:
    """Test _uncomment_and_replace function."""

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_and_replace_success(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test uncomment and replace a value."""
        config_file = tmp_path / "qemu.conf"
        config_file.write_text(
            '# user = "libvirt-qemu"\nother_setting = "value"\n'
        )

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _uncomment_and_replace(
            config_file, "user", "libvirt-qemu", "testuser"
        )

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        assert call_args[0][0][0] == "/usr/bin/tee"
        content = call_args[1]["stdin_input"]
        assert 'user = "testuser"' in content
        assert "libvirt-qemu" not in content

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_and_replace_already_correct(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test idempotent when value already correct."""
        config_file = tmp_path / "qemu.conf"
        config_file.write_text('user = "testuser"\nother_setting = "value"\n')

        result = _uncomment_and_replace(
            config_file, "user", "libvirt-qemu", "testuser"
        )

        assert result is True
        mock_run_privileged.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_and_replace_pattern_not_found(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test returns False when pattern not found."""
        config_file = tmp_path / "qemu.conf"
        config_file.write_text('other_setting = "value"\n')

        result = _uncomment_and_replace(
            config_file, "user", "libvirt-qemu", "testuser"
        )

        assert result is False
        mock_run_privileged.assert_not_called()

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_and_replace_subprocess_error(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test handle subprocess errors."""
        config_file = tmp_path / "qemu.conf"
        config_file.write_text('# user = "libvirt-qemu"\n')

        mock_run_privileged.return_value = MagicMock(returncode=1)

        result = _uncomment_and_replace(
            config_file, "user", "libvirt-qemu", "testuser"
        )

        assert result is False

    @patch("aps.installers.virtmanager.run_privileged")
    def test_uncomment_and_replace_already_uncommented_different_value(
        self, mock_run_privileged: Mock, tmp_path: Path
    ) -> None:
        """Test replace when already uncommented but has different value."""
        config_file = tmp_path / "qemu.conf"
        config_file.write_text('user = "olduser"\nother_setting = "value"\n')

        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _uncomment_and_replace(
            config_file, "user", "olduser", "newuser"
        )

        assert result is True
        mock_run_privileged.assert_called_once()

        call_args = mock_run_privileged.call_args
        content = call_args[1]["stdin_input"]
        assert 'user = "newuser"' in content


class TestConfigureLibvirtdConf:
    """Test _configure_libvirtd_conf function."""

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_success(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test successful configuration of libvirtd.conf."""
        mock_create_backup.return_value = True
        mock_uncomment_line.return_value = True

        result = _configure_libvirtd_conf()

        assert result is True
        mock_create_backup.assert_called_once()
        assert mock_uncomment_line.call_count == 2

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_creates_backup(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test that backup is created before modifications."""
        mock_create_backup.return_value = True
        mock_uncomment_line.return_value = True

        _configure_libvirtd_conf()

        mock_create_backup.assert_called_once()
        call_args = mock_create_backup.call_args
        # Verify it's called with Path to /etc/libvirt/libvirtd.conf
        assert "libvirtd.conf" in str(call_args[0][0])

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_already_configured(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test handling when settings already uncommented."""
        mock_create_backup.return_value = True
        # Simulate already configured (both calls return True without changes)
        mock_uncomment_line.return_value = True

        result = _configure_libvirtd_conf()

        assert result is True
        # Both uncomment calls should still happen
        assert mock_uncomment_line.call_count == 2

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_backup_failure(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test failure when backup creation fails."""
        mock_create_backup.return_value = False

        result = _configure_libvirtd_conf()

        assert result is False
        mock_uncomment_line.assert_not_called()

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_uncomment_unix_sock_group(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test that unix_sock_group line is uncommented."""
        mock_create_backup.return_value = True
        mock_uncomment_line.return_value = True

        _configure_libvirtd_conf()

        # Check that _uncomment_line was called with unix_sock_group pattern
        calls = mock_uncomment_line.call_args_list
        patterns = [call[0][1] for call in calls]
        assert "unix_sock_group" in patterns

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_uncomment_unix_sock_rw_perms(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test that unix_sock_rw_perms line is uncommented."""
        mock_create_backup.return_value = True
        mock_uncomment_line.return_value = True

        _configure_libvirtd_conf()

        # Check that _uncomment_line was called with unix_sock_rw_perms pattern
        calls = mock_uncomment_line.call_args_list
        patterns = [call[0][1] for call in calls]
        assert "unix_sock_rw_perms" in patterns

    @patch("aps.installers.virtmanager._uncomment_line")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_libvirtd_conf_uncomment_failure(
        self, mock_create_backup: Mock, mock_uncomment_line: Mock
    ) -> None:
        """Test failure when uncomment fails."""
        mock_create_backup.return_value = True
        mock_uncomment_line.return_value = False

        result = _configure_libvirtd_conf()

        assert result is False


class TestConfigureQemuConf:
    """Test _configure_qemu_conf function."""

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_success(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test successful configuration of qemu.conf."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = True
        mock_getuser.return_value = "testuser"

        result = _configure_qemu_conf()

        assert result is True
        mock_create_backup.assert_called_once()
        assert mock_uncomment_and_replace.call_count == 2

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_creates_backup(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test that backup is created before modifications."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = True
        mock_getuser.return_value = "testuser"

        _configure_qemu_conf()

        mock_create_backup.assert_called_once()
        call_args = mock_create_backup.call_args
        # Verify it's called with Path to /etc/libvirt/qemu.conf
        assert "qemu.conf" in str(call_args[0][0])

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_with_correct_username(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test that username is correctly passed to uncomment_and_replace."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = True
        mock_getuser.return_value = "myusername"

        _configure_qemu_conf()

        # Verify getuser was called
        mock_getuser.assert_called()

        # Verify _uncomment_and_replace was called with correct username
        calls = mock_uncomment_and_replace.call_args_list
        values = [call[0][3] for call in calls]  # Get the new_value (4th arg)
        assert "myusername" in values
        # Should be called twice with same user
        assert values.count("myusername") == 2

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_backup_failure(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test failure when backup creation fails."""
        mock_create_backup.return_value = False
        mock_getuser.return_value = "testuser"

        result = _configure_qemu_conf()

        assert result is False
        mock_uncomment_and_replace.assert_not_called()

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_uncomment_user(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test that user setting is uncommented and replaced."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = True
        mock_getuser.return_value = "testuser"

        _configure_qemu_conf()

        # Check that _uncomment_and_replace was called for user
        calls = mock_uncomment_and_replace.call_args_list
        patterns = [call[0][1] for call in calls]  # Get the pattern (2nd arg)
        assert "user" in patterns

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_uncomment_group(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test that group setting is uncommented and replaced."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = True
        mock_getuser.return_value = "testuser"

        _configure_qemu_conf()

        # Check that _uncomment_and_replace was called for group
        calls = mock_uncomment_and_replace.call_args_list
        patterns = [call[0][1] for call in calls]  # Get the pattern (2nd arg)
        assert "group" in patterns

    @patch("aps.installers.virtmanager.getpass.getuser")
    @patch("aps.installers.virtmanager._uncomment_and_replace")
    @patch("aps.installers.virtmanager._create_backup")
    def test_configure_qemu_conf_uncomment_failure(
        self,
        mock_create_backup: Mock,
        mock_uncomment_and_replace: Mock,
        mock_getuser: Mock,
    ) -> None:
        """Test failure when uncomment_and_replace fails."""
        mock_create_backup.return_value = True
        mock_uncomment_and_replace.return_value = False
        mock_getuser.return_value = "testuser"

        result = _configure_qemu_conf()

        assert result is False


class TestSetupNetworkConfig:
    """Test _setup_network_config function."""

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_append(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
        tmp_path: Path,
    ) -> None:
        """Test appending firewall_backend if not present."""
        network_conf = tmp_path / "network.conf"
        network_conf.write_text("# Network config\n")

        with patch.object(Path, "exists", return_value=True):
            mock_create_backup.return_value = True
            mock_append_or_update.return_value = True

            result = _setup_network_config()

            assert result is True
            mock_create_backup.assert_called_once()
            mock_append_or_update.assert_called_once()

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_creates_backup(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
    ) -> None:
        """Test that backup is created before modifications."""
        mock_create_backup.return_value = True
        mock_append_or_update.return_value = True

        with patch.object(Path, "exists", return_value=True):
            _setup_network_config()

            mock_create_backup.assert_called_once()
            call_args = mock_create_backup.call_args
            # Verify it's called with Path to /etc/libvirt/network.conf
            assert "network.conf" in str(call_args[0][0])

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_already_exists(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
    ) -> None:
        """Test when firewall_backend already exists."""
        mock_create_backup.return_value = True
        # Return True when firewall_backend already exists
        mock_append_or_update.return_value = True

        with patch.object(Path, "exists", return_value=True):
            result = _setup_network_config()

            assert result is True
            # Backup and append still called
            mock_create_backup.assert_called_once()
            mock_append_or_update.assert_called_once()

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_file_not_exists(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
    ) -> None:
        """Test when network.conf does not exist."""
        with patch.object(Path, "exists", return_value=False):
            result = _setup_network_config()

            # Should return False when file doesn't exist
            assert result is False
            mock_create_backup.assert_not_called()
            mock_append_or_update.assert_not_called()

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_backup_failure(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
    ) -> None:
        """Test failure when backup creation fails."""
        mock_create_backup.return_value = False

        with patch.object(Path, "exists", return_value=True):
            result = _setup_network_config()

            assert result is False
            mock_append_or_update.assert_not_called()

    @patch("aps.installers.virtmanager._append_or_update_libvirt_setting")
    @patch("aps.installers.virtmanager._create_backup")
    def test_setup_network_config_append_failure(
        self,
        mock_create_backup: Mock,
        mock_append_or_update: Mock,
    ) -> None:
        """Test failure when append fails."""
        mock_create_backup.return_value = True
        mock_append_or_update.return_value = False

        with patch.object(Path, "exists", return_value=True):
            result = _setup_network_config()

            assert result is False
            mock_create_backup.assert_called_once()


class TestConfigureLibvirtIntegration:
    """Test _configure_libvirt integration with all configuration functions."""

    @patch("aps.installers.virtmanager.subprocess.run")
    @patch("aps.installers.virtmanager.run_privileged")
    @patch("aps.installers.virtmanager._setup_network_config")
    @patch("aps.installers.virtmanager._configure_qemu_conf")
    @patch("aps.installers.virtmanager._configure_libvirtd_conf")
    def test_full_non_root_setup(
        self,
        mock_libvirtd_conf: Mock,
        mock_qemu_conf: Mock,
        mock_network_config: Mock,
        mock_run_privileged: Mock,
        mock_subprocess_run: Mock,
    ) -> None:
        """Test full non-root setup calls all configuration functions."""
        mock_libvirtd_conf.return_value = True
        mock_qemu_conf.return_value = True
        mock_network_config.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _configure_libvirt()

        assert result is True
        # Verify libvirtd.conf configuration was called first
        mock_libvirtd_conf.assert_called_once()
        # Verify qemu.conf configuration was called
        mock_qemu_conf.assert_called_once()
        # Verify network configuration was called after socket enable
        mock_network_config.assert_called_once()

    @patch("aps.installers.virtmanager.subprocess.run")
    @patch("aps.installers.virtmanager.run_privileged")
    @patch("aps.installers.virtmanager._setup_network_config")
    @patch("aps.installers.virtmanager._configure_qemu_conf")
    @patch("aps.installers.virtmanager._configure_libvirtd_conf")
    def test_socket_mode_enabled(
        self,
        mock_libvirtd_conf: Mock,
        mock_qemu_conf: Mock,
        mock_network_config: Mock,
        mock_run_privileged: Mock,
        mock_subprocess_run: Mock,
    ) -> None:
        """Test that libvirtd.socket is enabled instead of libvirtd service."""
        mock_libvirtd_conf.return_value = True
        mock_qemu_conf.return_value = True
        mock_network_config.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_run_privileged.return_value = MagicMock(returncode=0)

        result = _configure_libvirt()

        assert result is True
        # Verify systemctl was called with libvirtd.socket using fully
        # qualified path
        socket_enable_call_found = False
        for call in mock_run_privileged.call_args_list:
            args = call[0][0] if call[0] else []
            if (
                isinstance(args, list)
                and len(args) > 0
                and args[0] == "/usr/bin/systemctl"
                and "libvirtd.socket" in args
            ):
                socket_enable_call_found = True
                # Verify enable and now flags
                assert "enable" in args
                assert "--now" in args
                break

        assert socket_enable_call_found, (
            "systemctl enable --now libvirtd.socket with "
            "fully qualified path not found"
        )
