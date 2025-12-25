"""Tests for repository configuration module."""

from unittest.mock import Mock, patch

from aps.system import repositories


class TestRepositoryConfig:
    """Tests for repository configuration."""

    @patch("aps.system.repositories.subprocess.run")
    @patch("aps.system.repositories.run_privileged")
    def test_configure_fedora(
        self, mock_run_priv: Mock, mock_run: Mock
    ) -> None:
        """Test RPM Fusion repository setup on Fedora."""
        mock_run.return_value = Mock(returncode=0, stdout="39")
        mock_run_priv.return_value = Mock(returncode=0)

        result = repositories.configure(distro="fedora")

        assert result is True

    def test_configure_arch(self) -> None:
        """Test repository config on Arch (should return True)."""
        result = repositories.configure(distro="arch")

        assert result is True
