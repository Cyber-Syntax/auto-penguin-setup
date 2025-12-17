"""Tests for package manager optimizer module."""

from pathlib import Path
from unittest.mock import Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.pm_optimizer import PackageManagerOptimizer


class TestPackageManagerOptimizer:
    """Tests for package manager optimizer."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_fedora(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        mock_get_pm.return_value = Mock()

        optimizer = PackageManagerOptimizer()

        with patch.object(optimizer, "_optimize_dnf", return_value=True):
            result = optimizer.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_arch(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        mock_get_pm.return_value = Mock()

        optimizer = PackageManagerOptimizer()

        with patch.object(optimizer, "_optimize_pacman", return_value=True):
            result = optimizer.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_unsupported(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        mock_get_pm.return_value = Mock()

        optimizer = PackageManagerOptimizer()
        result = optimizer.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_create_backup_success(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
        mock_get_pm.return_value = Mock()

        optimizer = PackageManagerOptimizer()

        with patch("aps.system.pm_optimizer.Path.exists", return_value=False):
            result = optimizer._create_backup(Path("/etc/dnf/dnf.conf"))  # noqa: SLF001

        assert result is True
