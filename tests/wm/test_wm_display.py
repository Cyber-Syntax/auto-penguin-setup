"""Tests for window manager configuration modules."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.wm import qtile


class TestQtileConfig:
    """Tests for Qtile window manager configuration."""

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    def test_install_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful Qtile installation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "Success")
        mock_get_pm.return_value = mock_pm

        result = qtile.install("fedora", ["qtile", "python3-qtile"])

        assert result is True
        mock_pm.install.assert_called_once_with(["qtile", "python3-qtile"])

    @patch("aps.wm.qtile.run_privileged")
    def test_setup_backlight_rules(self, mock_run: Mock) -> None:
        """Test backlight rules setup."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=True):
            result = qtile.setup_backlight_rules()

        assert result is True

    def test_configure(self) -> None:
        """Test Qtile configuration."""
        with patch.object(qtile, "setup_backlight_rules", return_value=True):
            result = qtile.configure("fedora")

        assert result is True
