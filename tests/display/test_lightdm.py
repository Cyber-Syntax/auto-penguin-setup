"""Tests for LightDM display manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.display import lightdm


class TestLightDMInstall:
    """Test LightDM install function."""

    @patch("aps.display.lightdm.get_package_manager")
    @patch("aps.core.distro.detect_distro")
    def test_install_success(self, mock_distro: Mock, mock_pm: Mock) -> None:
        """Test successful LightDM installation."""
        mock_distro.return_value = MagicMock()
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, "Success")
        mock_pm.return_value = mock_pm_instance

        result = lightdm.install("fedora")

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["lightdm"])

    @patch("aps.display.lightdm.get_package_manager")
    @patch("aps.core.distro.detect_distro")
    def test_install_failure(self, mock_distro: Mock, mock_pm: Mock) -> None:
        """Test LightDM installation failure."""
        mock_distro.return_value = MagicMock()
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Installation failed")
        mock_pm.return_value = mock_pm_instance

        result = lightdm.install("fedora")

        assert result is False


class TestLightDMConfigureAutologin:
    """Test LightDM configure_autologin function."""

    @patch("aps.utils.privilege.run_privileged")
    def test_configure_autologin_success(self, mock_run_priv: Mock) -> None:
        """Test successful autologin configuration."""
        # Mock the file read and write operations
        mock_run_priv.return_value = MagicMock(
            returncode=0,
            stdout="[General]\n",
            stderr="",
        )

        result = lightdm.configure_autologin("fedora", "testuser", "qtile")

        assert result is True
