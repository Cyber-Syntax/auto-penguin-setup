"""Tests for system configuration modules."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.bootloader import BootloaderConfig
from aps.system.defaults import DefaultAppsConfig
from aps.system.firewall import UFWConfig
from aps.system.multimedia import MultimediaConfig
from aps.system.network import NetworkConfig
from aps.system.pm_optimizer import PackageManagerOptimizer
from aps.system.repositories import RepositoryConfig
from aps.system.ssh import SSHConfig
from aps.system.sudoers import SudoersConfig


class TestPackageManagerOptimizer:
    """Tests for package manager optimizer."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_fedora(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test optimization for Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        optimizer = PackageManagerOptimizer()

        with patch.object(optimizer, "_optimize_dnf", return_value=True):
            result = optimizer.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_arch(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test optimization for Arch."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_get_pm.return_value = MagicMock()

        optimizer = PackageManagerOptimizer()

        with patch.object(optimizer, "_optimize_pacman", return_value=True):
            result = optimizer.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_unsupported(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test optimization for unsupported distro."""
        unsupported_distro = DistroInfo(
            name="Unknown",
            version="1.0",
            id="unknown",
            id_like=[],
            package_manager=PackageManagerType.UNKNOWN,
            family=DistroFamily.UNKNOWN,
        )
        mock_detect_distro.return_value = unsupported_distro
        mock_get_pm.return_value = MagicMock()

        optimizer = PackageManagerOptimizer()
        result = optimizer.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.pm_optimizer.run_privileged")
    def test_create_backup_success(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful backup creation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0)

        optimizer = PackageManagerOptimizer()

        with patch("aps.system.pm_optimizer.Path.exists", return_value=False):
            result = optimizer._create_backup(Path("/etc/dnf/dnf.conf"))

        assert result is True
        mock_run.assert_called_once()


class TestUFWConfig:
    """Tests for UFW firewall configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW configuration."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=True
            ),
            patch.object(ufw, "_configure_syncthing_rules", return_value=True),
            patch.object(ufw, "_enable_ufw", return_value=True),
        ):
            result = ufw.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.firewall.run_privileged")
    def test_disable_ufw_success(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW disabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0)

        ufw = UFWConfig()
        result = ufw._disable_ufw()

        assert result is True
        mock_run.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.firewall.run_privileged")
    def test_enable_ufw_success(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW enabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0)

        ufw = UFWConfig()
        result = ufw._enable_ufw()

        assert result is True
        mock_run.assert_called_once()


class TestNetworkConfig:
    """Tests for network configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.network.resolve_config_file")
    @patch("aps.system.network.shutil.copy2")
    @patch("aps.system.network.run_privileged")
    def test_configure_success(
        self,
        mock_run: Mock,
        mock_copy: Mock,
        mock_resolve: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful TCP BBR configuration (uses run_privileged)."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_source = MagicMock()
        mock_source.exists.return_value = True
        mock_resolve.return_value = mock_source
        mock_run.return_value = Mock(returncode=0)

        network = NetworkConfig()
        result = network.configure()

        assert result is True
        mock_copy.assert_called_once()
        mock_run.assert_called_once()


class TestMultimediaConfig:
    """Tests for multimedia configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_non_fedora(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test multimedia config on non-Fedora (should skip)."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_get_pm.return_value = MagicMock()

        multimedia = MultimediaConfig()
        result = multimedia.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.utils.privilege.subprocess.run")
    def test_configure_fedora_no_ffmpeg_free(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test multimedia config when ffmpeg-free not installed (uses run_privileged)."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=1)  # Not installed

        multimedia = MultimediaConfig()
        result = multimedia.configure()

        assert result is True


class TestRepositoryConfig:
    """Tests for repository configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.repositories.subprocess.run")
    def test_configure_fedora(
        self, mock_run: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test RPM Fusion repository setup on Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0, stdout="39")

        repo = RepositoryConfig()
        result = repo.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_arch(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test repository config on Arch (should return True)."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_get_pm.return_value = MagicMock()

        repo = RepositoryConfig()
        result = repo.configure()

        assert result is True


class TestBootloaderConfig:
    """Tests for bootloader configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.bootloader.Path.exists", return_value=True)
    @patch("aps.system.bootloader.subprocess.run")
    @patch("aps.system.bootloader.subprocess.Popen")
    @patch("builtins.open", create=True)
    def test_set_timeout(
        self,
        mock_open: Mock,
        mock_popen: Mock,
        mock_run: Mock,
        mock_exists: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test GRUB timeout configuration."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0)
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (None, None)
        mock_popen.return_value.__enter__.return_value = mock_proc

        # Mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = "GRUB_TIMEOUT=5\n"
        mock_open.return_value.__enter__.return_value = mock_file

        bootloader = BootloaderConfig()
        with patch.object(Path, "read_text", return_value="GRUB_TIMEOUT=0\n"):
            result = bootloader.set_timeout(0)

        assert result is True


class TestSudoersConfig:
    """Tests for sudoers configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch(
        "aps.system.sudoers.Path.read_text", return_value="# sudoers file\n"
    )
    @patch("aps.utils.privilege.subprocess.run")
    @patch("aps.system.sudoers.subprocess.run")
    def test_configure_borgbackup(
        self,
        mock_subprocess_run: Mock,
        mock_privileged_run: Mock,
        mock_read: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test borgbackup sudoers configuration."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        # Mock whoami command (direct subprocess.run call)
        mock_subprocess_run.return_value = Mock(
            returncode=0, stdout="testuser"
        )

        # Mock privileged commands (via run_privileged): backup, tee, visudo
        # Adding extra returns in case there are more calls
        mock_privileged_run.side_effect = [
            Mock(
                returncode=0, stdout="", stderr=""
            ),  # backup via run_privileged
            Mock(returncode=0, stdout="", stderr=""),  # tee via run_privileged
            Mock(
                returncode=0, stdout="", stderr=""
            ),  # visudo via run_privileged
            Mock(returncode=0, stdout="", stderr=""),  # extra just in case
            Mock(returncode=0, stdout="", stderr=""),  # extra just in case
        ]

        sudoers = SudoersConfig()
        result = sudoers.configure_borgbackup()

        assert result is True


class TestDefaultAppsConfig:
    """Tests for default applications configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test default apps configuration (placeholder)."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        defaults = DefaultAppsConfig()
        result = defaults.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.defaults.Path.write_text")
    @patch("aps.system.defaults.Path.exists", return_value=False)
    def test_set_defaults(
        self,
        mock_exists: Mock,
        mock_write: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test setting default applications."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        defaults = DefaultAppsConfig()
        result = defaults.set_defaults(browser="brave", terminal="alacritty")

        assert result is True
        mock_write.assert_called_once()


class TestSSHConfig:
    """Tests for SSH configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_get_ssh_service_name_fedora(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test SSH service name detection for Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        ssh = SSHConfig()
        service_name = ssh._get_ssh_service_name()

        assert service_name == "sshd"

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_get_ssh_service_name_debian(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test SSH service name detection for Debian."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ssh = SSHConfig()
        service_name = ssh._get_ssh_service_name()

        assert service_name == "ssh"

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_parse_remote_host(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test parsing remote host string."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        ssh = SSHConfig()
        user, ip, port = ssh._parse_remote_host("alice@192.168.1.10:22")

        assert user == "alice"
        assert ip == "192.168.1.10"
        assert port == 22

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_parse_remote_host_invalid(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test parsing invalid remote host string."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        ssh = SSHConfig()

        try:
            ssh._parse_remote_host("invalid-format")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Invalid host format" in str(e)

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.ssh.subprocess.run")
    @patch("aps.system.ssh.Path.mkdir")
    @patch("aps.system.ssh.Path.exists", return_value=False)
    def test_create_ssh_keys(
        self,
        mock_exists: Mock,
        mock_mkdir: Mock,
        mock_run: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test SSH key creation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(
            returncode=0, stdout="testhost\n", stderr=""
        )

        ssh = SSHConfig()

        with patch.object(Path, "chmod"):
            result = ssh.create_ssh_keys()

        assert result is True
        # ssh-keygen should be called at least once
        assert any(
            "ssh-keygen" in str(call) for call in mock_run.call_args_list
        )

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.ssh.run_privileged")
    def test_configure_sshd_security(
        self,
        mock_run: MagicMock,
        mock_get_pm: MagicMock,
        mock_detect_distro: MagicMock,
    ) -> None:
        """Test SSH daemon security configuration."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        ssh = SSHConfig()
        result = ssh.configure_sshd_security(port=2222, password_auth=False)

        assert result is True
        assert any("tee" in str(call) for call in mock_run.call_args_list)

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.ssh.Path.write_text")
    def test_generate_ssh_config(
        self,
        mock_write: MagicMock,
        mock_get_pm: MagicMock,
        mock_detect_distro: MagicMock,
    ) -> None:
        """Test SSH client config generation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        ssh = SSHConfig()

        devices = {
            "server1": "alice@192.168.1.10:22",
            "server2": "bob@192.168.1.20:2222",
        }

        with patch("aps.system.ssh.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="testhost\n", stderr=""
            )
            with patch.object(Path, "chmod"):
                with patch.object(Path, "exists", return_value=False):
                    result = ssh.generate_ssh_config(devices)

        assert result is True
        mock_write.assert_called_once()
        config_content = mock_write.call_args[0][0]
        assert "Host server1" in config_content
        assert "Host server2" in config_content

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.ssh.subprocess.run")
    def test_test_ssh_connection(
        self,
        mock_run: MagicMock,
        mock_get_pm: MagicMock,
        mock_detect_distro: MagicMock,
    ) -> None:
        """Test SSH connection testing."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        ssh = SSHConfig()
        result = ssh.test_ssh_connection("alice", "192.168.1.10", 22)

        assert result is True
        assert any("ssh" in str(call) for call in mock_run.call_args_list)
