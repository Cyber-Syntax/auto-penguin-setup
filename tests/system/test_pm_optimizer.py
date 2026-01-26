"""Tests for package manager optimizer module."""

from pathlib import Path
from unittest.mock import Mock, patch

from aps.system import pm_optimizer


class TestPackageManagerOptimizer:
    """Tests for package manager optimizer."""

    @patch("aps.system.pm_optimizer._optimize_dnf")
    def test_configure_fedora(self, mock_optimize_dnf: Mock) -> None:
        """Test optimization for Fedora."""
        mock_optimize_dnf.return_value = True

        result = pm_optimizer.configure(distro="fedora")

        assert result is True
        mock_optimize_dnf.assert_called_once()

    @patch("aps.system.pm_optimizer._optimize_pacman")
    def test_configure_arch(self, mock_optimize_pacman: Mock) -> None:
        """Test optimization for Arch."""
        mock_optimize_pacman.return_value = True

        result = pm_optimizer.configure(distro="arch")

        assert result is True
        mock_optimize_pacman.assert_called_once()

    def test_configure_unsupported(self) -> None:
        """Test optimization for unsupported distro."""
        result = pm_optimizer.configure(distro="unknown")

        assert result is False

    def test_create_backup_success(self) -> None:
        """Test successful backup creation."""
        with patch("aps.system.pm_optimizer.Path.exists", return_value=False):
            result = pm_optimizer._create_backup(Path("/etc/dnf/dnf.conf"))

        assert result is True
