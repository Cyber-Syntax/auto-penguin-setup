"""Tests for firewall configuration module."""

from unittest.mock import Mock, patch

from aps.system import firewall


class TestFirewall:
    """Tests for UFW firewall configuration."""

    @patch("aps.system.firewall.run_privileged")
    def test_configure_success(self, mock_run: Mock) -> None:
        """Test successful firewall configuration."""
        mock_run.return_value = Mock(returncode=0)

        result = firewall.configure(distro="fedora")

        assert result is True

    @patch("aps.system.firewall.run_privileged")
    def test_configure_failure(self, mock_run: Mock) -> None:
        """Test firewall configuration failure."""
        mock_run.return_value = Mock(returncode=1)

        result = firewall.configure(distro="fedora")

        assert result is False
