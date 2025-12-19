"""Tests for utility modules."""

from pathlib import Path

from aps.utils.paths import (
    get_configs_dir,
    get_default_configs_dir,
    get_package_root,
    resolve_config_file,
    resolve_default_config_file,
)


class TestPaths:
    """Test path utility functions."""

    def test_get_package_root(self) -> None:
        """Test get_package_root returns correct path."""
        root = get_package_root()
        assert root.is_dir()
        # Should be the project root directory
        assert (root / "pyproject.toml").exists()
        assert (root / "src").exists()

    def test_get_configs_dir(self) -> None:
        """Test get_configs_dir returns correct path."""
        configs_dir = get_configs_dir()
        assert configs_dir.is_dir()
        # Should contain the config files
        assert (configs_dir / "01-mytlp.conf").exists()
        assert (configs_dir / "default_aps_configs").exists()

    def test_get_default_configs_dir(self) -> None:
        """Test get_default_configs_dir returns correct path."""
        default_dir = get_default_configs_dir()
        assert default_dir.is_dir()
        # Should contain the default config files
        assert (default_dir / "packages.ini").exists()
        assert (default_dir / "pkgmap.ini").exists()
        assert (default_dir / "variables.ini").exists()

    def test_resolve_config_file(self) -> None:
        """Test resolve_config_file resolves paths correctly."""
        # Test with a known config file
        config_file = resolve_config_file("01-mytlp.conf")
        assert config_file.is_file()
        assert config_file.name == "01-mytlp.conf"
        assert str(get_configs_dir()) in str(config_file)

        # Test with subdirectory
        mpv_file = resolve_config_file("mpv/mpv.conf")
        assert mpv_file.is_file()
        assert mpv_file.name == "mpv.conf"
        assert "mpv" in str(mpv_file)

    def test_resolve_default_config_file(self) -> None:
        """Test resolve_default_config_file resolves paths correctly."""
        # Test with a known default config file
        config_file = resolve_default_config_file("packages.ini")
        assert config_file.is_file()
        assert config_file.name == "packages.ini"
        assert str(get_default_configs_dir()) in str(config_file)

    def test_resolve_nonexistent_file(self) -> None:
        """Test resolving non-existent files.

        Should still return valid Path objects.
        """
        nonexistent = resolve_config_file("nonexistent.conf")
        assert isinstance(nonexistent, Path)
        assert not nonexistent.exists()
        # Should still be within configs directory
        assert str(get_configs_dir()) in str(nonexistent)
