"""Placeholder test for hardware.intel module."""

"""Tests for Intel graphics configuration module."""

from pathlib import Path
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

from aps.hardware import intel


class TestIntelConfigSetupXorg:
    """Test Xorg setup functionality."""

    @patch("shutil.copy2")
    def test_setup_xorg_success(
        self, mock_copy: Mock, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test successful Xorg setup."""
        caplog.set_level("INFO")
        # Create config file
        config_file = tmp_path / "20-intel.conf"
        config_file.write_text(
            'Section "Device"\n  Driver "intel"\nEndSection\n'
        )

        # Create destination directory
        dest_dir = tmp_path / "xorg.conf.d"
        dest_dir.mkdir()

        # Mock resolve_config_file to return our test config
        with patch(
            "aps.hardware.intel.resolve_config_file", return_value=config_file
        ):
            result = intel.setup_xorg(str(config_file))

        assert result is True
        assert "Xorg configuration completed" in caplog.text

    def test_setup_xorg_config_not_found(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test setup fails when config file not found."""
        caplog.set_level("ERROR")
        result = intel.setup_xorg("/nonexistent/20-intel.conf")

        assert result is False
        assert "not found" in caplog.text

    def test_setup_xorg_with_default_config(self, tmp_path: Path) -> None:
        """Test setup with default config file."""
        # Create config file in temp location
        config_file = tmp_path / "20-intel.conf"
        config_file.write_text("test config")

        with (
            patch(
                "aps.hardware.intel.resolve_config_file",
                return_value=config_file,
            ),
            patch(
                "aps.hardware.intel.copy_config_file", return_value=True
            ) as mock_copy,
        ):
            result = intel.setup_xorg()

            assert result is True
            mock_copy.assert_called_once()


class TestIntelConfigConfigure:
    """Test configure method."""

    def test_configure_with_xorg_true(self, tmp_path: Path) -> None:
        """Test configure with xorg=True."""
        config_file = tmp_path / "20-intel.conf"
        config_file.write_text("config")

        with (
            patch(
                "aps.hardware.intel.resolve_config_file",
                return_value=config_file,
            ),
            patch(
                "aps.hardware.intel.setup_xorg", return_value=True
            ) as mock_setup,
        ):
            result = intel.configure(
                "fedora", xorg=True, config_source=str(config_file)
            )

            assert result is True
            mock_setup.assert_called_once()

    def test_configure_with_xorg_false(self) -> None:
        """Test configure with xorg=False."""
        result = intel.configure("fedora", xorg=False)

        assert result is True

    def test_configure_default(self) -> None:
        """Test configure with no arguments."""
        result = intel.configure(
            "fedora",
        )

        assert result is True
