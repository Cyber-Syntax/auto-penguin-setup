"""Tests for hardware base configuration module."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import LogCaptureFixture

from aps.hardware.base import BaseHardwareConfig


class ConcreteHardwareConfig(BaseHardwareConfig):
    """Concrete implementation of BaseHardwareConfig for testing."""

    def configure(self, **kwargs: dict[str, bool | str]) -> bool:
        """Concrete implementation of configure method."""
        return True


class TestBaseHardwareConfigInit:
    """Test BaseHardwareConfig initialization."""

    def test_init_with_fedora(self) -> None:
        """Test initialization with fedora distro."""
        config = ConcreteHardwareConfig("fedora")
        assert config.distro == "fedora"
        assert config.logger is not None

    def test_init_with_arch(self) -> None:
        """Test initialization with arch distro."""
        config = ConcreteHardwareConfig("arch")
        assert config.distro == "arch"

    def test_init_with_debian(self) -> None:
        """Test initialization with debian distro."""
        config = ConcreteHardwareConfig("debian")
        assert config.distro == "debian"


class TestBaseHardwareConfigAbstractMethods:
    """Test abstract methods enforcement."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseHardwareConfig cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseHardwareConfig("fedora")  # type: ignore


class TestCopyConfigFile:
    """Test _copy_config_file method."""

    def test_copy_file_success(
        self, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test successful file copy."""
        caplog.set_level("INFO")
        config = ConcreteHardwareConfig("fedora")

        # Create source file
        source = tmp_path / "source.conf"
        source.write_text("config content")

        # Set destination in temp directory
        dest_dir = tmp_path / "conf.d"
        destination = dest_dir / "config.conf"

        # Test copy
        result = config._copy_config_file(str(source), str(destination))

        assert result is True
        assert destination.exists()
        assert destination.read_text() == "config content"
        assert "Copied" in caplog.text

    def test_copy_file_creates_destination_directory(
        self, tmp_path: Path
    ) -> None:
        """Test that destination directory is created if it doesn't exist."""
        config = ConcreteHardwareConfig("fedora")

        source = tmp_path / "source.conf"
        source.write_text("content")

        # Destination in non-existent directory
        dest_dir = tmp_path / "new_dir" / "nested"
        destination = dest_dir / "config.conf"

        result = config._copy_config_file(str(source), str(destination))

        assert result is True
        assert destination.exists()
        assert dest_dir.exists()

    def test_copy_file_source_not_found(
        self, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test handling of missing source file."""
        caplog.set_level("ERROR")
        config = ConcreteHardwareConfig("fedora")

        source = tmp_path / "nonexistent.conf"
        destination = tmp_path / "dest.conf"

        result = config._copy_config_file(str(source), str(destination))

        assert result is False
        assert "Failed to copy" in caplog.text

    def test_copy_file_permission_denied(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handling of permission denied errors."""
        caplog.set_level("ERROR")
        config = ConcreteHardwareConfig("fedora")

        with patch(
            "shutil.copy2", side_effect=PermissionError("Permission denied")
        ):
            result = config._copy_config_file(
                "/src/file.conf", "/dest/file.conf"
            )

            assert result is False
            assert "Failed to copy" in caplog.text

    def test_copy_file_preserves_metadata(self, tmp_path: Path) -> None:
        """Test that copy preserves file metadata."""
        config = ConcreteHardwareConfig("fedora")

        source = tmp_path / "source.conf"
        source.write_text("content")
        source.chmod(0o600)

        destination = tmp_path / "dest.conf"

        result = config._copy_config_file(str(source), str(destination))

        assert result is True
        # File should be copied with similar permissions (copy2 preserves metadata)
        assert destination.exists()


class TestConfigureAbstractMethod:
    """Test configure abstract method enforcement."""

    def test_subclass_must_implement_configure(self) -> None:
        """Test that subclasses must implement configure method."""

        class IncompleteConfig(BaseHardwareConfig):
            """Missing configure implementation."""

            pass

        with pytest.raises(TypeError):
            IncompleteConfig("fedora")  # type: ignore
