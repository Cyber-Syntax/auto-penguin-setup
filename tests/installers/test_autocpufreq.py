"""Tests for auto-cpufreq installer module."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.installers.autocpufreq import AutoCPUFreqInstaller


class TestAutoCPUFreqInstallerInit:
    """Test AutoCPUFreqInstaller initialization."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = AutoCPUFreqInstaller()
        assert installer.distro == "fedora"


class TestAutoCPUFreqInstall:
    """Test AutoCPUFreqInstaller install method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("shutil.which")
    def test_install_git_not_installed(
        self, mock_which: Mock, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test install fails when git is not installed."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = None

        installer = AutoCPUFreqInstaller()
        result = installer.install()

        assert result is False
        assert "git is not installed" in caplog.text

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("aps.installers.autocpufreq.run_privileged")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_install_success(
        self,
        mock_which: Mock,
        mock_subprocess: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test successful installation."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = "/usr/bin/git"
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_run_priv.return_value = MagicMock(returncode=0)

        installer = AutoCPUFreqInstaller()

        with patch("tempfile.TemporaryDirectory"):
            with patch("pathlib.Path.exists", return_value=True):
                result = installer.install()
                assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_install_git_clone_fails(
        self,
        mock_which: Mock,
        mock_subprocess: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install fails when git clone fails."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = "/usr/bin/git"
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git")

        installer = AutoCPUFreqInstaller()

        result = installer.install()
        assert result is False


class TestAutoCPUFreqIsInstalled:
    """Test AutoCPUFreqInstaller is_installed method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("shutil.which")
    def test_is_installed_true(self, mock_which: Mock, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test is_installed returns True when installed."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = "/usr/bin/auto-cpufreq"

        installer = AutoCPUFreqInstaller()
        result = installer.is_installed()

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    @patch("shutil.which")
    def test_is_installed_false(self, mock_which: Mock, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test is_installed returns False when not installed."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_which.return_value = None

        installer = AutoCPUFreqInstaller()
        result = installer.is_installed()

        assert result is False
