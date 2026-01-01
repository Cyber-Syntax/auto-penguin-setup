"""Tests for Syncthing installer module."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.syncthing import install, is_installed


class TestSyncthingInstall:
    """Test Syncthing install function."""

    @patch("subprocess.run")
    def test_install_success(self, mock_run: Mock) -> None:
        """Test successful installation."""
        mock_run.return_value = MagicMock(returncode=0)

        result = install()

        assert result is True
        mock_run.assert_called_with(
            ["/usr/bin/systemctl", "--user", "enable", "--now", "syncthing"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_install_failure(
        self, mock_run: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install failure."""
        caplog.set_level("ERROR")
        mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")

        result = install()

        assert result is False


class TestSyncthingIsInstalled:
    """Test Syncthing is_installed function."""

    @patch("subprocess.run")
    def test_is_installed_true(self, mock_run: Mock) -> None:
        """Test is_installed returns True when enabled."""
        mock_run.return_value = MagicMock(returncode=0)

        result = is_installed()

        assert result is True

    @patch("subprocess.run")
    def test_is_installed_false(self, mock_run: Mock) -> None:
        """Test is_installed returns False when not enabled."""
        mock_run.return_value = MagicMock(returncode=1)

        result = is_installed()

        assert result is False
