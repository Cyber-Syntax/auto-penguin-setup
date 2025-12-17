"""Tests for setup command functionality.

Covers successful setup and SetupError handling.
"""

from argparse import Namespace
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.cli.commands.setup import cmd_setup
from aps.core.setup import SetupError


class TestSetupCommand:
    """Test setup command with various scenarios."""

    @patch("aps.cli.commands.setup.SetupManager")
    @patch("aps.cli.commands.setup.detect_distro")
    @patch("aps.cli.commands.setup.ensure_sudo")
    def test_setup_success(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_manager_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test successful component setup."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        manager = Mock()
        mock_manager_cls.return_value = manager

        caplog.set_level("INFO")
        args = Namespace(component="ohmyzsh")
        cmd_setup(args)

        manager.setup_component.assert_called_once_with("ohmyzsh")
        assert "setup completed successfully" in caplog.text

    @patch("aps.cli.commands.setup.SetupManager")
    @patch("aps.cli.commands.setup.detect_distro")
    @patch("aps.cli.commands.setup.ensure_sudo")
    def test_setup_error_handling(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_manager_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test setup error is caught and logged."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        manager = Mock()
        manager.setup_component.side_effect = SetupError("Component not available")
        mock_manager_cls.return_value = manager

        caplog.set_level("ERROR")
        args = Namespace(component="aur-helper")
        cmd_setup(args)

        assert "Setup failed" in caplog.text
        assert "Component not available" in caplog.text

    @patch("aps.cli.commands.setup.SetupManager")
    @patch("aps.cli.commands.setup.detect_distro")
    @patch("aps.cli.commands.setup.ensure_sudo")
    def test_setup_various_components(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_manager_cls: Mock,
    ) -> None:
        """Test setup with various component names."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        manager = Mock()
        mock_manager_cls.return_value = manager

        # Test multiple components
        components = ["ohmyzsh", "ollama", "aur-helper"]
        for component in components:
            args = Namespace(component=component)
            cmd_setup(args)

        assert manager.setup_component.call_count == 3
        for component in components:
            manager.setup_component.assert_any_call(component)

    @patch("aps.cli.commands.setup.SetupManager")
    @patch("aps.cli.commands.setup.detect_distro")
    @patch("aps.cli.commands.setup.ensure_sudo")
    def test_setup_detects_distro(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_manager_cls: Mock,
    ) -> None:
        """Test that setup detects the current distro."""
        mock_distro = Mock()
        mock_distro.name = "Arch Linux"
        mock_detect_distro.return_value = mock_distro

        manager = Mock()
        mock_manager_cls.return_value = manager

        args = Namespace(component="ohmyzsh")
        cmd_setup(args)

        # Verify distro was detected
        mock_detect_distro.assert_called_once()
        # Verify SetupManager was initialized with distro info
        mock_manager_cls.assert_called_once_with(mock_distro)
