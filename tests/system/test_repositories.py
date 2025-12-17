"""Tests for repository configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.repositories import RepositoryConfig


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
    def test_configure_arch(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
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
