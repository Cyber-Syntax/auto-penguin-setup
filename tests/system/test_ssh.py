"""Tests for SSH configuration module."""

from pathlib import Path
from unittest.mock import Mock, patch

from aps.system import ssh


class TestSSHConfig:
    """Tests for SSH configuration."""

    def test_get_ssh_service_name_fedora(self) -> None:
        """Test SSH service name detection for Fedora."""
        service_name = ssh._get_ssh_service_name("fedora")

        assert service_name == "sshd"

    def test_parse_remote_host(self) -> None:
        """Test parsing remote host string."""
        user, ip, port = ssh._parse_remote_host("alice@192.168.1.10:22")

        assert user == "alice"
        assert ip == "192.168.1.10"
        assert port == 22

    def test_parse_remote_host_invalid(self) -> None:
        """Test parsing invalid remote host string."""
        try:
            ssh._parse_remote_host("invalid-format")
            raise AssertionError("Should have raised ValueError")  # noqa: EM101, TRY003
        except ValueError as e:
            assert "Invalid host format" in str(e)

    @patch("aps.system.ssh.subprocess.run")
    @patch("aps.system.ssh.Path.mkdir")
    @patch("aps.system.ssh.KEY_PATH")
    @patch("aps.system.ssh.PUB_KEY_PATH")
    def test_create_ssh_keys(
        self,
        mock_pub_key: Mock,
        mock_key: Mock,
        _mock_mkdir: Mock,
        mock_run: Mock,
    ) -> None:
        """Test SSH key creation."""
        # Mock path.exists to return False
        mock_key.exists.return_value = False
        mock_pub_key.exists.return_value = False

        mock_run.return_value = Mock(
            returncode=0, stdout="testhost\n", stderr=""
        )

        with patch.object(Path, "chmod"):
            result = ssh.create_ssh_keys()

        assert result is True
        # ssh-keygen should be called at least once
        assert any(
            "ssh-keygen" in str(call) for call in mock_run.call_args_list
        )

    @patch("aps.system.ssh.run_privileged")
    @patch("aps.system.ssh.Path.exists")
    def test_configure_sshd_security(
        self, mock_exists: Mock, mock_run_priv: Mock
    ) -> None:
        """Test SSH daemon security configuration."""
        mock_exists.return_value = True
        mock_run_priv.return_value = Mock(returncode=0)

        result = ssh.configure_sshd_security(port=2222, password_auth=False)

        assert result is True

    @patch("aps.system.ssh.subprocess.run")
    @patch("aps.system.ssh.CONFIG_FILE")
    def test_generate_ssh_config(
        self,
        mock_config_file: Mock,
        mock_run: Mock,
    ) -> None:
        """Test SSH client config generation."""
        mock_config_file.exists.return_value = False
        mock_config_file.write_text = Mock()
        mock_config_file.chmod = Mock()
        mock_run.return_value = Mock(
            returncode=0, stdout="testhost\n", stderr=""
        )

        devices = {
            "server1": "alice@192.168.1.10:22",
            "server2": "bob@192.168.1.20:2222",
        }

        with patch("aps.system.ssh.SSH_DIR") as mock_ssh_dir:
            mock_ssh_dir.mkdir = Mock()
            result = ssh.generate_ssh_config(devices)

        assert result is True
        mock_config_file.write_text.assert_called_once()
        config_content = mock_config_file.write_text.call_args[0][0]
        assert "Host server1" in config_content
        assert "Host server2" in config_content

    @patch("aps.system.ssh.subprocess.run")
    def test_test_ssh_connection(
        self,
        mock_run: Mock,
    ) -> None:
        """Test SSH connection testing."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = ssh.test_ssh_connection("alice", "192.168.1.10", 22)

        assert result is True
        assert any("ssh" in str(call) for call in mock_run.call_args_list)
