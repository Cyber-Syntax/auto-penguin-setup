"""Tests for configuration parser module."""

from pathlib import Path

import pytest

from aps.core.config_parser import APSConfigParser


class TestAPSConfigParser:
    """Test APSConfigParser functionality."""

    def test_load_config(self, sample_packages_ini: Path) -> None:
        """Test loading configuration from file."""
        parser = APSConfigParser(sample_packages_ini)

        assert parser.has_section("development")
        assert parser.has_section("multimedia")

    def test_get_section_packages(self, sample_packages_ini: Path) -> None:
        """Test retrieving packages from section."""
        parser = APSConfigParser(sample_packages_ini)

        dev_packages = parser.get_section_packages("development")
        assert dev_packages == ["git", "vim", "python3"]

        multimedia_packages = parser.get_section_packages("multimedia")
        assert multimedia_packages == ["ffmpeg", "vlc", "gimp"]

    def test_get_section_packages_nonexistent(self, sample_packages_ini: Path) -> None:
        """Test retrieving packages from nonexistent section."""
        parser = APSConfigParser(sample_packages_ini)

        packages = parser.get_section_packages("nonexistent")
        assert packages == []

    def test_get_package_mappings(self, sample_pkgmap_ini: Path) -> None:
        """Test retrieving package mappings."""
        parser = APSConfigParser(sample_pkgmap_ini)

        fedora_mappings = parser.get_package_mappings("fedora")
        assert "brave-browser" in fedora_mappings
        assert fedora_mappings["brave-browser"] == "COPR:lecramyajiv/brave-browser:brave-browser"

    def test_get_variables(self, tmp_path: Path) -> None:
        """Test retrieving variables from config."""
        content = """
[variables]
python_version=3.12
install_path=/opt/myapp
"""
        config_file = tmp_path / "variables.ini"
        config_file.write_text(content)

        parser = APSConfigParser(config_file)
        variables = parser.get_variables()

        assert variables["python_version"] == "3.12"
        assert variables["install_path"] == "/opt/myapp"

    def test_get_single_value(self, sample_packages_ini: Path) -> None:
        """Test getting single configuration value."""
        parser = APSConfigParser(sample_packages_ini)

        value = parser.get("development", "1")
        assert value == "git"

    def test_get_with_fallback(self, sample_packages_ini: Path) -> None:
        """Test getting value with fallback."""
        parser = APSConfigParser(sample_packages_ini)

        value = parser.get("nonexistent", "key", fallback="default")
        assert value == "default"

    def test_sections_list(self, sample_packages_ini: Path) -> None:
        """Test listing all sections."""
        parser = APSConfigParser(sample_packages_ini)

        sections = parser.sections()
        assert "development" in sections
        assert "multimedia" in sections

    def test_empty_config(self, tmp_path: Path) -> None:
        """Test handling empty configuration file."""
        empty_config = tmp_path / "empty.ini"
        empty_config.write_text("")

        parser = APSConfigParser(empty_config)
        assert parser.sections() == []

    def test_missing_config_file(self, tmp_path: Path) -> None:
        """Test handling missing configuration file."""
        with pytest.raises(FileNotFoundError):
            parser = APSConfigParser()
            parser.load(tmp_path / "nonexistent.ini")

    def test_load_method_with_valid_file(self, tmp_path: Path) -> None:
        """Test load method with a valid file."""
        content = """
[section1]
key1=value1
"""
        config_file = tmp_path / "test.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        assert parser.has_section("section1")
        assert parser.get("section1", "key1") == "value1"

    def test_preprocess_bare_lines(self, tmp_path: Path) -> None:
        """Test preprocessing bare lines in config."""
        content = """[packages]
git
vim
python3
"""
        config_file = tmp_path / "bare.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["git", "vim", "python3"]

    def test_preprocess_mixed_format(self, tmp_path: Path) -> None:
        """Test preprocessing mixed bare lines and key=value pairs."""
        content = """[packages]
git
2=vim
python3
"""
        config_file = tmp_path / "mixed.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        # get_section_packages only returns numeric keys
        assert "git" in packages
        assert "vim" in packages
        assert "python3" in packages

    def test_preprocess_with_comments(self, tmp_path: Path) -> None:
        """Test preprocessing with comments and empty lines."""
        content = """[packages]
# This is a comment
git

; This is also a comment
vim
"""
        config_file = tmp_path / "comments.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["git", "vim"]

    def test_preprocess_multiple_sections(self, tmp_path: Path) -> None:
        """Test preprocessing with multiple sections."""
        content = """[section1]
item1
item2

[section2]
item3
item4
"""
        config_file = tmp_path / "multi.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        sec1 = parser.get_section_packages("section1")
        sec2 = parser.get_section_packages("section2")

        assert sec1 == ["item1", "item2"]
        assert sec2 == ["item3", "item4"]
