"""Tests for bootloader configuration module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.bootloader import BootloaderConfig


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

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.bootloader.Path.exists", return_value=False)
    def test_configure_grub_not_found(
        self, mock_exists: Mock, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuration when GRUB is not installed."""
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

        bootloader = BootloaderConfig()
        result = bootloader.configure()

        assert result is True
