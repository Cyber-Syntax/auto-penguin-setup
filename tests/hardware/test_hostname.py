"""Placeholder test for hardware.hostname module."""

"""Tests for hostname configuration module."""

from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

from aps.hardware.hostname import HostnameConfig


class TestHostnameConfigInit:
    """Test HostnameConfig initialization."""

    def test_init_fedora(self) -> None:
        """Test initialization with fedora distro."""
        config = HostnameConfig("fedora")
        assert config.distro == "fedora"

    def test_init_arch(self) -> None:
        """Test initialization with arch distro."""
        config = HostnameConfig("arch")
        assert config.distro == "arch"

    def test_init_debian(self) -> None:
        """Test initialization with debian distro."""
        config = HostnameConfig("debian")
        assert config.distro == "debian"


class TestHostnameConfigSetHostname:
    """Test set_hostname functionality."""

    @patch("subprocess.run")
    def test_set_hostname_success(self, mock_run: Mock, caplog: LogCaptureFixture) -> None:
        """Test successful hostname change."""
        caplog.set_level("INFO")
        mock_run.return_value = Mock(returncode=0)
        config = HostnameConfig("fedora")

        result = config.set_hostname("myhostname")

        assert result is True
        assert "Hostname changed" in caplog.text
        mock_run.assert_called_once_with(["hostnamectl", "set-hostname", "myhostname"], check=False)

    @patch("subprocess.run")
    def test_set_hostname_failure(self, mock_run: Mock, caplog: LogCaptureFixture) -> None:
        """Test hostname change failure."""
        caplog.set_level("ERROR")
        mock_run.return_value = Mock(returncode=1)
        config = HostnameConfig("fedora")

        result = config.set_hostname("myhostname")

        assert result is False
        assert "Failed to change hostname" in caplog.text

    def test_set_hostname_empty(self, caplog: LogCaptureFixture) -> None:
        """Test hostname change with empty hostname."""
        caplog.set_level("ERROR")
        config = HostnameConfig("fedora")

        result = config.set_hostname("")

        assert result is False
        assert "cannot be empty" in caplog.text

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_set_hostname_hostnamectl_not_found(
        self, mock_run: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test hostname change when hostnamectl is not found."""
        caplog.set_level("ERROR")
        config = HostnameConfig("fedora")

        result = config.set_hostname("myhostname")

        assert result is False
        assert "hostnamectl command not found" in caplog.text

    @patch("subprocess.run", side_effect=Exception("Test error"))
    def test_set_hostname_exception(self, mock_run: Mock, caplog: LogCaptureFixture) -> None:
        """Test hostname change with exception."""
        caplog.set_level("ERROR")
        config = HostnameConfig("fedora")

        result = config.set_hostname("myhostname")

        assert result is False
        assert "Failed to set hostname" in caplog.text


class TestHostnameConfigConfigure:
    """Test configure method."""

    @patch("aps.hardware.hostname.HostnameConfig.set_hostname")
    def test_configure_with_hostname(self, mock_set: Mock) -> None:
        """Test configure with hostname parameter."""
        mock_set.return_value = True
        config = HostnameConfig("fedora")

        result = config.configure(hostname="myhostname")

        assert result is True
        mock_set.assert_called_once_with("myhostname")

    def test_configure_without_hostname(self, caplog: LogCaptureFixture) -> None:
        """Test configure without hostname parameter."""
        caplog.set_level("ERROR")
        config = HostnameConfig("fedora")

        result = config.configure()

        assert result is False
        assert "No hostname provided" in caplog.text
