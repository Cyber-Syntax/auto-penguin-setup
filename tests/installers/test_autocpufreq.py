"""Tests for auto-cpufreq installer module."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.autocpufreq import install, is_installed


class TestAutoCPUFreqInstall:
    """Test auto-cpufreq install function."""

    @patch("shutil.which")
    def test_install_git_not_installed(
        self,
        mock_which: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install fails when git is not installed."""
        caplog.set_level("ERROR")
        mock_which.return_value = None

        result = install()

        assert result is False
        assert "git is not installed" in caplog.text

    @patch("aps.installers.autocpufreq.run_privileged")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_install_success(
        self,
        mock_which: Mock,
        mock_subprocess: Mock,
        mock_run_priv: Mock,
    ) -> None:
        """Test successful installation."""
        mock_which.return_value = "/usr/bin/git"
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_run_priv.return_value = MagicMock(returncode=0)

        with (
            patch("tempfile.TemporaryDirectory"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = install()
            assert result is True

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_install_git_clone_fails(
        self,
        mock_which: Mock,
        mock_subprocess: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install fails when git clone fails."""
        caplog.set_level("ERROR")
        mock_which.return_value = "/usr/bin/git"
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git")

        result = install()
        assert result is False


class TestAutoCPUFreqIsInstalled:
    """Test auto-cpufreq is_installed function."""

    @patch("shutil.which")
    def test_is_installed_true(self, mock_which: Mock) -> None:
        """Test is_installed returns True when installed."""
        mock_which.return_value = "/usr/bin/auto-cpufreq"

        result = is_installed()

        assert result is True

    @patch("shutil.which")
    def test_is_installed_false(self, mock_which: Mock) -> None:
        """Test is_installed returns False when not installed."""
        mock_which.return_value = None

        result = is_installed()

        assert result is False
