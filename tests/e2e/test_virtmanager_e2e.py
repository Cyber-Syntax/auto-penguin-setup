"""E2E tests for virtmanager path redirection and filesystem operations."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import aps.installers.virtmanager as virtmanager_module
from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.core.package_manager import PacmanManager
from aps.utils.privilege import run_privileged


def test_path_redirection(redirect_paths: tuple[Path, Path]) -> None:
    """Validate that Path('/etc/libvirt/foo') resolves to tmp_path.

    Tests that the redirect_paths fixture properly intercepts /etc/libvirt/*
    paths and redirects them to tmp_path/etc/libvirt/*.

    Args:
        redirect_paths: Tuple of (tmp_path, redirected_tmp_path)

    """
    _tmp_path, redirected_tmp = redirect_paths

    # Get the patched Path from the virtmanager module
    patched_path = virtmanager_module.Path

    # Test Path creation and redirection
    test_file = patched_path("/etc/libvirt/test.conf")
    assert str(test_file.resolve()).startswith(str(redirected_tmp))

    # Test write_text method
    test_file.write_text("test content")
    assert test_file.exists()
    assert test_file.read_text() == "test content"

    # Test mkdir method
    test_dir = patched_path("/etc/libvirt/subdir")
    test_dir.mkdir(parents=True, exist_ok=True)
    assert test_dir.exists()
    assert test_dir.is_dir()

    # Test that files are actually in the redirected tmp path
    expected_file = redirected_tmp / "test.conf"
    assert expected_file.exists()
    assert expected_file.read_text() == "test content"

    expected_dir = redirected_tmp / "subdir"
    assert expected_dir.exists()


def test_run_privileged_with_path_redirection(
    redirect_paths: tuple[Path, Path], mock_system_commands: MagicMock
) -> None:
    """Validate tee and cp operations write/copy to redirected filesystem.

    Tests that run_privileged with tee and cp commands perform actual
    file operations on the redirected filesystem paths.

    Args:
        redirect_paths: Tuple of (tmp_path, redirected_tmp_path)
        mock_system_commands: Configured mock for system commands
    """
    _tmp_path, redirected_tmp = redirect_paths

    # Test tee command writes stdin_input to target file
    tee_target = "/etc/libvirt/tee_test.conf"
    tee_content = "test tee content\nline 2\n"

    result = run_privileged(
        ["/usr/bin/tee", tee_target],
        stdin_input=tee_content,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    # Verify file was written to the redirected filesystem
    tee_file = redirected_tmp / "tee_test.conf"
    assert tee_file.exists()
    assert tee_file.read_text() == tee_content

    # Test cp command copies source file to destination
    # First create a source file
    source_file = redirected_tmp / "source.conf"
    source_content = "source file content"
    source_file.write_text(source_content)

    cp_dest = "/etc/libvirt/dest.conf"
    result = run_privileged(
        ["/usr/bin/cp", str(source_file), cp_dest],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    # Verify destination file was created in the redirected filesystem
    dest_file = redirected_tmp / "dest.conf"
    assert dest_file.exists()
    assert dest_file.read_text() == source_content


def test_install_fedora_e2e(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test complete virtmanager installation workflow for Fedora.

    Verifies that install("fedora") correctly:
    - Calls dnf install commands
    - Checks and creates libvirt group
    - Adds user to libvirt group
    - Uncomments and configures libvirtd.conf
    - Uncomments and configures qemu.conf with username
    - Enables libvirtd.socket
    - Configures network.conf
    - Creates backup files
    - Returns True on success

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, libvirt_dir = redirect_paths

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        # (group doesn't exist) so groupadd will be called
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install
        result = virtmanager_module.install("fedora")

        # Assert install returned True
        assert result is True

        # Verify getent was called to check libvirt group
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0] == [
            "/usr/bin/getent",
            "group",
            "libvirt",
        ]

    # Verify dnf install commands were called
    assert mock_run_privileged.called
    dnf_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/bin/dnf"
    ]
    assert len(dnf_calls) >= 2

    # Verify first dnf call for @virtualization group
    assert dnf_calls[0][0][0] == [
        "/usr/bin/dnf",
        "install",
        "-y",
        "@virtualization",
    ]

    # Verify second dnf call for optional packages
    assert dnf_calls[1][0][0] == [
        "/usr/bin/dnf",
        "group",
        "install",
        "-y",
        "--with-optional",
        "virtualization",
    ]

    # Verify groupadd was called
    groupadd_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/groupadd"
    ]
    assert len(groupadd_calls) > 0

    # Verify usermod was called to add user to libvirt group
    usermod_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/usermod"
    ]
    assert len(usermod_calls) > 0
    assert "testuser" in str(usermod_calls)

    # Verify systemctl enable was called
    systemctl_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/bin/systemctl"
    ]
    assert len(systemctl_calls) > 0
    assert any("libvirtd.socket" in str(call) for call in systemctl_calls)

    # Verify libvirtd.conf backup exists
    libvirtd_backup = libvirt_dir / "libvirtd.conf.bak"
    assert libvirtd_backup.exists()

    # Verify libvirtd.conf was modified
    libvirtd_conf = libvirt_dir / "libvirtd.conf"
    libvirtd_content = libvirtd_conf.read_text()
    # Should have uncommented unix_sock_group and unix_sock_rw_perms
    assert "unix_sock_group" in libvirtd_content
    assert "unix_sock_rw_perms" in libvirtd_content
    # These lines should not be commented out
    assert not any(
        line.lstrip().startswith("#") and "unix_sock_group" in line
        for line in libvirtd_content.split("\n")
    )

    # Verify qemu.conf backup exists
    qemu_backup = libvirt_dir / "qemu.conf.bak"
    assert qemu_backup.exists()

    # Verify qemu.conf has user and group set to "testuser"
    qemu_conf = libvirt_dir / "qemu.conf"
    qemu_content = qemu_conf.read_text()
    assert 'user = "testuser"' in qemu_content
    assert 'group = "testuser"' in qemu_content

    # Verify network.conf backup exists
    network_backup = libvirt_dir / "network.conf.bak"
    assert network_backup.exists()

    # Verify network.conf has firewall_backend = "iptables"
    network_conf = libvirt_dir / "network.conf"
    network_content = network_conf.read_text()
    assert 'firewall_backend = "iptables"' in network_content


def test_install_arch_e2e(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test complete virtmanager installation workflow for Arch.

    Verifies that install("arch") correctly:
    - Calls PacmanManager.install with correct packages
    - Checks and creates libvirt group
    - Adds user to libvirt group
    - Uncomments and configures libvirtd.conf
    - Uncomments and configures qemu.conf with username
    - Enables libvirtd.socket
    - Configures network.conf
    - Creates backup files
    - Returns True on success

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, libvirt_dir = redirect_paths

    # Create DistroInfo for Arch
    arch_info = DistroInfo(
        name="Arch",
        version="rolling",
        id="arch",
        id_like=["arch"],
        package_manager=PackageManagerType.PACMAN,
        family=DistroFamily.ARCH,
    )

    # Create a mock PacmanManager with spec to pass isinstance check
    mock_pm = MagicMock(spec=PacmanManager)
    mock_pm.install.return_value = (True, None)

    # Mock detect_distro, get_package_manager, getpass.getuser,
    # and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=arch_info,
        ),
        patch(
            "aps.installers.virtmanager.get_package_manager",
            return_value=mock_pm,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        # (group doesn't exist) so groupadd will be called
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install
        result = virtmanager_module.install("arch")

        # Assert install returned True
        assert result is True

        # Verify getent was called to check libvirt group
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0] == [
            "/usr/bin/getent",
            "group",
            "libvirt",
        ]

    # Verify PacmanManager.install was called with correct packages
    mock_pm.install.assert_called_once()
    install_call = mock_pm.install.call_args
    # Check the packages argument
    expected_packages = [
        "libvirt",
        "qemu-base",
        "virt-manager",
        "virt-install",
    ]
    assert install_call[0][0] == expected_packages
    # Check assume_yes=True keyword argument
    assert install_call[1]["assume_yes"] is True

    # Verify groupadd was called
    groupadd_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/groupadd"
    ]
    assert len(groupadd_calls) > 0

    # Verify usermod was called to add user to libvirt group
    usermod_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/usermod"
    ]
    assert len(usermod_calls) > 0
    assert "testuser" in str(usermod_calls)

    # Verify systemctl enable was called
    systemctl_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/bin/systemctl"
    ]
    assert len(systemctl_calls) > 0
    assert any("libvirtd.socket" in str(call) for call in systemctl_calls)

    # Verify libvirtd.conf backup exists
    libvirtd_backup = libvirt_dir / "libvirtd.conf.bak"
    assert libvirtd_backup.exists()

    # Verify libvirtd.conf was modified
    libvirtd_conf = libvirt_dir / "libvirtd.conf"
    libvirtd_content = libvirtd_conf.read_text()
    # Should have uncommented unix_sock_group and unix_sock_rw_perms
    assert "unix_sock_group" in libvirtd_content
    assert "unix_sock_rw_perms" in libvirtd_content
    # These lines should not be commented out
    assert not any(
        line.lstrip().startswith("#") and "unix_sock_group" in line
        for line in libvirtd_content.split("\n")
    )

    # Verify qemu.conf backup exists
    qemu_backup = libvirt_dir / "qemu.conf.bak"
    assert qemu_backup.exists()

    # Verify qemu.conf has user and group set to "testuser"
    qemu_conf = libvirt_dir / "qemu.conf"
    qemu_content = qemu_conf.read_text()
    assert 'user = "testuser"' in qemu_content
    assert 'group = "testuser"' in qemu_content

    # Verify network.conf backup exists
    network_backup = libvirt_dir / "network.conf.bak"
    assert network_backup.exists()

    # Verify network.conf has firewall_backend = "iptables"
    network_conf = libvirt_dir / "network.conf"
    network_content = network_conf.read_text()
    assert 'firewall_backend = "iptables"' in network_content


def test_install_idempotent(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test that running install twice doesn't break anything.

    Verifies that install("fedora") can be called twice in the same test
    and both calls return True without errors or side effects.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, _libvirt_dir = redirect_paths

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install first time
        result1 = virtmanager_module.install("fedora")
        assert result1 is True

        # Reset mock to prepare for second call
        mock_run_privileged.reset_mock()
        mock_subprocess_run.reset_mock()
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install second time
        result2 = virtmanager_module.install("fedora")
        assert result2 is True


def test_install_with_existing_group(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test install when libvirt group already exists.

    Verifies that when getent reports the libvirt group exists
    (returncode=0), groupadd is NOT called but usermod IS called,
    and install returns True.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, _libvirt_dir = redirect_paths

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return 0 (group exists)
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Call install
        result = virtmanager_module.install("fedora")
        assert result is True

        # Verify getent was called
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args
        assert call_args[0][0] == [
            "/usr/bin/getent",
            "group",
            "libvirt",
        ]

    # Verify groupadd was NOT called (group already exists)
    groupadd_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/groupadd"
    ]
    assert len(groupadd_calls) == 0

    # Verify usermod WAS called to add user to libvirt group
    usermod_calls = [
        call
        for call in mock_run_privileged.call_args_list
        if call[0][0][0] == "/usr/sbin/usermod"
    ]
    assert len(usermod_calls) > 0


def test_install_with_existing_backups(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test install when backup files already exist.

    Verifies that if .bak files already exist, install doesn't error
    and returns True.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, libvirt_dir = redirect_paths

    # Pre-create backup files to simulate they already exist
    (libvirt_dir / "libvirtd.conf.bak").write_text("old backup")
    (libvirt_dir / "qemu.conf.bak").write_text("old backup")
    (libvirt_dir / "network.conf.bak").write_text("old backup")

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install
        result = virtmanager_module.install("fedora")
        assert result is True

        # Verify backup files still exist
        assert (libvirt_dir / "libvirtd.conf.bak").exists()
        assert (libvirt_dir / "qemu.conf.bak").exists()
        assert (libvirt_dir / "network.conf.bak").exists()


def test_install_network_conf_missing(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test install when network.conf is missing.

    Verifies that if network.conf doesn't exist, _setup_network_config
    returns False and install returns False.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, libvirt_dir = redirect_paths

    # Remove network.conf from the redirected filesystem
    network_conf_path = libvirt_dir / "network.conf"
    if network_conf_path.exists():
        network_conf_path.unlink()

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install - should return False because network.conf is missing
        result = virtmanager_module.install("fedora")
        assert result is False


def test_install_command_failure(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_run_privileged: MagicMock,
) -> None:
    """Test install when dnf command fails.

    Verifies that when run_privileged raises CalledProcessError
    for the dnf install command, _install_fedora catches it,
    logs the error, and returns False.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir) for
            path redirection
        mock_libvirt_filesystem: Path to mock libvirt directory with
            fixture files
        mock_run_privileged: Global mock of run_privileged
    """
    _tmp_path, _libvirt_dir = redirect_paths

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Make run_privileged raise CalledProcessError for dnf
        mock_run_privileged.side_effect = subprocess.CalledProcessError(
            1, "dnf"
        )

        # Call install - should return False due to dnf failure
        result = virtmanager_module.install("fedora")
        assert result is False


def _run_fedora_install_and_return_libvirt_dir(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> Path:
    """Helper to run Fedora install and return libvirt_dir.

    Avoids duplicating mocking boilerplate across multiple content tests.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir)
        mock_libvirt_filesystem: Mock libvirt directory with fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged

    Returns:
        Path to the libvirt directory after installation
    """
    _tmp_path, libvirt_dir = redirect_paths

    # Create DistroInfo for Fedora
    fedora_info = DistroInfo(
        name="Fedora",
        version="41",
        id="fedora",
        id_like=["rhel"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )

    # Mock detect_distro, getpass.getuser, and subprocess.run
    with (
        patch(
            "aps.installers.virtmanager.detect_distro",
            return_value=fedora_info,
        ),
        patch(
            "aps.installers.virtmanager.getpass.getuser",
            return_value="testuser",
        ),
        patch(
            "aps.installers.virtmanager.subprocess.run"
        ) as mock_subprocess_run,
    ):
        # Mock subprocess.run for getent to return non-zero
        # (group doesn't exist) so groupadd will be called
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        # Call install
        result = virtmanager_module.install("fedora")

        # Assert install returned True
        assert result is True

    return libvirt_dir


def test_libvirtd_conf_content_after_install(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test that libvirtd.conf has correct content after install.

    Verifies that unix_sock_group and unix_sock_rw_perms are properly
    uncommented and have the correct values after installation.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir)
        mock_libvirt_filesystem: Mock libvirt directory with fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    libvirt_dir = _run_fedora_install_and_return_libvirt_dir(
        redirect_paths,
        mock_libvirt_filesystem,
        mock_system_commands,
        mock_run_privileged,
    )

    # Read the modified libvirtd.conf
    libvirtd_conf = libvirt_dir / "libvirtd.conf"
    content = libvirtd_conf.read_text()

    # Verify unix_sock_group is uncommented with correct value
    assert 'unix_sock_group = "libvirt"' in content

    # Verify unix_sock_rw_perms is uncommented with correct value
    assert 'unix_sock_rw_perms = "0770"' in content

    # Verify the line is NOT commented out (no setting line with # prefix)
    lines = content.split("\n")
    uncommented_unix_group = any(
        line.strip() == 'unix_sock_group = "libvirt"' for line in lines
    )
    assert uncommented_unix_group

    uncommented_unix_perms = any(
        line.strip() == 'unix_sock_rw_perms = "0770"' for line in lines
    )
    assert uncommented_unix_perms

    # Verify that original comment blocks are still present
    assert "# Set the UNIX domain socket group ownership" in content, (
        "Original comment block for unix_sock_group should be preserved"
    )
    assert "# Set the UNIX socket permissions for the R/W socket" in content, (
        "Original comment block for unix_sock_rw_perms should be preserved"
    )


def test_qemu_conf_content_after_install(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test that qemu.conf has correct content after install.

    Verifies that user and group settings are properly replaced
    with the current username after installation.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir)
        mock_libvirt_filesystem: Mock libvirt directory with fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    libvirt_dir = _run_fedora_install_and_return_libvirt_dir(
        redirect_paths,
        mock_libvirt_filesystem,
        mock_system_commands,
        mock_run_privileged,
    )

    # Read the modified qemu.conf
    qemu_conf = libvirt_dir / "qemu.conf"
    content = qemu_conf.read_text()

    # Verify user is set to testuser
    assert 'user = "testuser"' in content

    # Verify group is set to testuser
    assert 'group = "testuser"' in content

    # Verify the old commented values are NOT present
    assert '#user = "libvirt-qemu"' not in content
    assert '#group = "libvirt-qemu"' not in content

    # Verify the lines are uncommented and not commented versions
    lines = content.split("\n")
    user_line_uncommented = any(
        line.strip() == 'user = "testuser"' for line in lines
    )
    assert user_line_uncommented

    group_line_uncommented = any(
        line.strip() == 'group = "testuser"' for line in lines
    )
    assert group_line_uncommented

    # Verify that example lines with indentation remain present (not replaced)
    # Example format in qemu.conf: "user = qemu" with 7+ spaces of indentation
    assert '#       user = "qemu"' in content
    assert '#       user = "+0"' in content
    assert '#       user = "100"' in content

    # Verify group examples are also preserved
    # The fixture file has similar example patterns for group settings
    # Verify the structure is intact by finding the comment about examples
    assert "# Some examples of valid values are:" in content


def test_network_conf_content_after_install(
    redirect_paths: tuple[Path, Path],
    mock_libvirt_filesystem: Path,
    mock_system_commands: MagicMock,
    mock_run_privileged: MagicMock,
) -> None:
    """Test that network.conf has correct content after install.

    Verifies that firewall_backend is properly set to iptables
    and the original configuration is preserved after installation.

    Args:
        redirect_paths: Tuple of (e2e_tmp_root, libvirt_dir)
        mock_libvirt_filesystem: Mock libvirt directory with fixture files
        mock_system_commands: Configured mock for system commands
        mock_run_privileged: Global mock of run_privileged
    """
    libvirt_dir = _run_fedora_install_and_return_libvirt_dir(
        redirect_paths,
        mock_libvirt_filesystem,
        mock_system_commands,
        mock_run_privileged,
    )

    # Read the modified network.conf
    network_conf = libvirt_dir / "network.conf"
    content = network_conf.read_text()

    # Verify firewall_backend is set to iptables
    assert 'firewall_backend = "iptables"' in content

    # Verify the original commented nftables setting is still present
    assert '#firewall_backend = "nftables"' in content

    # Verify the comment block at the top is preserved
    assert "# Master configuration file for the network driver" in content
    assert "# All settings described here are optional" in content

    # Verify the descriptive comments about firewall_backend are preserved
    assert "# firewall_backend:" in content
    assert (
        "iptables - use iptables commands to construct the firewall" in content
    )
