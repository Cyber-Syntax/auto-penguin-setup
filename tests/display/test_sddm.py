"""Tests for SDDM display manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.display import sddm


class TestSDDMInstall:
    """Test SDDM install function."""

    @patch("aps.display.sddm.get_package_manager")
    @patch("aps.core.distro.detect_distro")
    @patch("subprocess.run")
    def test_install_already_installed(
        self, mock_subprocess: Mock, mock_distro: Mock, mock_pm: Mock
    ) -> None:
        """Test install when SDDM is already installed."""
        mock_distro.return_value = MagicMock()
        mock_pm.return_value = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = sddm.install("fedora")

        assert result is True

    @patch("aps.display.sddm.get_package_manager")
    @patch("aps.core.distro.detect_distro")
    @patch("subprocess.run")
    def test_install_success(
        self, mock_subprocess: Mock, mock_distro: Mock, mock_pm: Mock
    ) -> None:
        """Test successful SDDM installation."""
        mock_distro.return_value = MagicMock()
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, "Success")
        mock_pm.return_value = mock_pm_instance
        mock_subprocess.return_value = MagicMock(returncode=1)

        result = sddm.install("fedora")

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["sddm"])

    @patch("aps.display.sddm.get_package_manager")
    @patch("aps.core.distro.detect_distro")
    @patch("subprocess.run")
    def test_install_failure(
        self, mock_subprocess: Mock, mock_distro: Mock, mock_pm: Mock
    ) -> None:
        """Test SDDM installation failure."""
        mock_distro.return_value = MagicMock()
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Installation failed")
        mock_pm.return_value = mock_pm_instance
        mock_subprocess.return_value = MagicMock(returncode=1)

        result = sddm.install("fedora")

        assert result is False


class TestSDDMConfigureAutologin:
    """Test SDDM configure_autologin function."""

    @patch("aps.utils.privilege.run_privileged")
    def test_configure_autologin_success(self, mock_run_priv: Mock) -> None:
        """Test successful autologin configuration."""
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        result = sddm.configure_autologin("fedora", "testuser", "plasma")

        assert result is True

    @patch("aps.utils.privilege.run_privileged")
    def test_configure_autologin_with_different_session(
        self, mock_run_priv: Mock
    ) -> None:
        """Test autologin configuration with different session."""
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        result = sddm.configure_autologin("arch", "myuser", "qtile")

        assert result is True
