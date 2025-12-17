"""Placeholder test for hardware.touchpad module."""

"""Tests for touchpad configuration module."""

from pathlib import Path
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

from aps.hardware.touchpad import TouchpadConfig


class TestTouchpadConfigInit:
    """Test TouchpadConfig initialization."""

    def test_init_fedora(self) -> None:
        """Test initialization with fedora distro."""
        config = TouchpadConfig("fedora")
        assert config.distro == "fedora"

    def test_init_arch(self) -> None:
        """Test initialization with arch distro."""
        config = TouchpadConfig("arch")
        assert config.distro == "arch"

    def test_init_debian(self) -> None:
        """Test initialization with debian distro."""
        config = TouchpadConfig("debian")
        assert config.distro == "debian"


class TestTouchpadConfigSetup:
    """Test touchpad setup functionality."""

    @patch("shutil.copy2")
    def test_setup_success(
        self, mock_copy: Mock, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test successful touchpad setup."""
        caplog.set_level("INFO")
        config = TouchpadConfig("fedora")

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
            result = config.setup(str(config_file))

        assert result is True
        assert "Touchpad configuration completed" in caplog.text

    def test_setup_config_not_found(self, caplog: LogCaptureFixture) -> None:
        """Test setup fails when config file not found."""
        caplog.set_level("ERROR")
        config = TouchpadConfig("fedora")

        result = config.setup("/nonexistent/99-touchpad.conf")

        assert result is False
        assert "not found" in caplog.text

    def test_setup_with_default_config(self, tmp_path: Path) -> None:
        """Test setup with default config file."""
        config = TouchpadConfig("fedora")

        # Create config file in temp location
        config_file = tmp_path / "99-touchpad.conf"
        config_file.write_text("test config")

        with (
            patch(
                "aps.hardware.touchpad.resolve_config_file",
                return_value=config_file,
            ),
            patch.object(
                config, "_copy_config_file", return_value=True
            ) as mock_copy,
        ):
            result = config.setup()

            assert result is True
            mock_copy.assert_called_once()


class TestTouchpadConfigConfigure:
    """Test configure method."""

    def test_configure_with_setup_true(self, tmp_path: Path) -> None:
        """Test configure with setup=True."""
        config = TouchpadConfig("fedora")

        config_file = tmp_path / "99-touchpad.conf"
        config_file.write_text("config")

        with (
            patch(
                "aps.hardware.touchpad.resolve_config_file",
                return_value=config_file,
            ),
            patch.object(config, "setup", return_value=True) as mock_setup,
        ):
            result = config.configure(
                setup=True, config_source=str(config_file)
            )

            assert result is True
            mock_setup.assert_called_once()

    def test_configure_with_setup_false(self) -> None:
        """Test configure with setup=False."""
        config = TouchpadConfig("fedora")

        result = config.configure(setup=False)

        assert result is True

    def test_configure_default(self) -> None:
        """Test configure with no arguments."""
        config = TouchpadConfig("fedora")

        result = config.configure()

        assert result is True
