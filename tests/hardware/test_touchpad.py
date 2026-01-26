"""Placeholder test for hardware.touchpad module."""

"""Tests for touchpad configuration module."""

from pathlib import Path
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

from aps.hardware import touchpad


class TestTouchpadConfigSetup:
    """Test touchpad setup functionality."""

    @patch("shutil.copy2")
    def test_setup_success(
        self, mock_copy: Mock, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test successful touchpad setup."""
        caplog.set_level("INFO")
        # Create config file
        config_file = tmp_path / "99-touchpad.conf"
        config_file.write_text('Section "InputClass"\nEndSection\n')

        # Create destination directory
        dest_dir = tmp_path / "xorg.conf.d"
        dest_dir.mkdir()

        # Mock resolve_config_file to return our test config
        with patch(
            "aps.hardware.touchpad.resolve_config_file",
            return_value=config_file,
        ):
            result = touchpad.setup(str(config_file))

        assert result is True
        assert "Touchpad configuration completed" in caplog.text

    def test_setup_config_not_found(self, caplog: LogCaptureFixture) -> None:
        """Test setup fails when config file not found."""
        caplog.set_level("ERROR")
        result = touchpad.setup("/nonexistent/99-touchpad.conf")

        assert result is False
        assert "not found" in caplog.text

    def test_setup_with_default_config(self, tmp_path: Path) -> None:
        """Test setup with default config file."""
        # Create config file in temp location
        config_file = tmp_path / "99-touchpad.conf"
        config_file.write_text("test config")

        with (
            patch(
                "aps.hardware.touchpad.resolve_config_file",
                return_value=config_file,
            ),
            patch(
                "aps.hardware.touchpad.copy_config_file", return_value=True
            ) as mock_copy,
        ):
            result = touchpad.setup()

            assert result is True
            mock_copy.assert_called_once()


class TestTouchpadConfigConfigure:
    """Test configure method."""

    def test_configure_with_setup_true(self, tmp_path: Path) -> None:
        """Test configure with setup=True."""
        config_file = tmp_path / "99-touchpad.conf"
        config_file.write_text("config")

        with (
            patch(
                "aps.hardware.touchpad.resolve_config_file",
                return_value=config_file,
            ),
            patch(
                "aps.hardware.touchpad.setup", return_value=True
            ) as mock_setup,
        ):
            result = touchpad.configure(
                "fedora", setup=True, config_source=str(config_file)
            )

            assert result is True
            mock_setup.assert_called_once()

    def test_configure_with_setup_false(self) -> None:
        """Test configure with setup=False."""
        result = touchpad.configure("fedora", setup=False)

        assert result is True

    def test_configure_default(self) -> None:
        """Test configure with no arguments."""
        result = touchpad.configure(
            "fedora",
        )

        assert result is True
