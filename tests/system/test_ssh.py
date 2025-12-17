"""Tests for SSH configuration module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.ssh import SSHConfig


class TestSSHConfig:
    """Tests for SSH configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_get_ssh_service_name_fedora(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        service_name = ssh._get_ssh_service_name()  # noqa: SLF001

        assert service_name == "sshd"

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_get_ssh_service_name_debian(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        service_name = ssh._get_ssh_service_name()  # noqa: SLF001

        assert service_name == "ssh"

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_parse_remote_host(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        user, ip, port = ssh._parse_remote_host("alice@192.168.1.10:22")  # noqa: SLF001

        assert user == "alice"
        assert ip == "192.168.1.10"
        assert port == 22

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_parse_remote_host_invalid(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
            ssh._parse_remote_host("invalid-format")  # noqa: SLF001
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
        _mock_exists: Mock,
        _mock_mkdir: Mock,
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
        mock_run.return_value = Mock(returncode=0, stdout="testhost\n", stderr="")

        ssh = SSHConfig()

        with patch.object(Path, "chmod"):
            result = ssh.create_ssh_keys()

        assert result is True
        # ssh-keygen should be called at least once
        assert any("ssh-keygen" in str(call) for call in mock_run.call_args_list)

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_sshd_security(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
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

        ssh = SSHConfig()
        result = ssh.configure_sshd_security(port=2222, password_auth=False)

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.ssh.Path.write_text")
    def test_generate_ssh_config(
        self, mock_write: MagicMock, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
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

        with (
            patch("aps.system.ssh.subprocess.run") as mock_run,
            patch.object(Path, "chmod"),
            patch.object(Path, "exists", return_value=False),
        ):
            mock_run.return_value = Mock(returncode=0, stdout="testhost\n", stderr="")
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
        self, mock_run: MagicMock, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
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
