"""Tests for configuration parser module."""

from pathlib import Path

import pytest
from pytest import MonkeyPatch

from aps.core.config import APSConfigParser, ensure_config_files


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

        fedora_mappings = parser.get_package_mappings("pkgmap.fedora")
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

    def test_comma_separated_values(self, tmp_path: Path) -> None:
        """Test parsing comma-separated values."""
        content = """[packages]
packages=curl, wget, git
"""
        config_file = tmp_path / "comma.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget", "git"]

    def test_comma_separated_no_spaces(self, tmp_path: Path) -> None:
        """Test parsing comma-separated values without spaces."""
        content = """[packages]
packages=curl,wget,git
"""
        config_file = tmp_path / "comma_nospace.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget", "git"]

    def test_mixed_format_one_per_line_and_comma(self, tmp_path: Path) -> None:
        """Test mixed format with one package per line and comma-separated."""
        content = """[packages]
curl
wget, git
python3
"""
        config_file = tmp_path / "mixed.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget", "git", "python3"]

    def test_inline_comments_hash(self, tmp_path: Path) -> None:
        """Test inline comments with hash symbol."""
        content = """[packages]
packages=curl, wget  # download tools
"""
        config_file = tmp_path / "inline_hash.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget"]

    def test_inline_comments_semicolon(self, tmp_path: Path) -> None:
        """Test inline comments with semicolon."""
        content = """[packages]
packages=curl, wget ; download tools
"""
        config_file = tmp_path / "inline_semi.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget"]

    def test_inline_comment_contains_comma(self, tmp_path: Path) -> None:
        """Ensure commas inside inline comments are not parsed as packages."""
        content = """[packages]
packages=trash-cli # trashing tool, alternative to rm
"""
        config_file = tmp_path / "comment_comma.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["trash-cli"]

    def test_with_full_line_comments(self, tmp_path: Path) -> None:
        """Test with full line comments and mixed formats."""
        content = """[packages]
# download tools
curl, wget

# version control
git
# firewall
ufw
"""
        config_file = tmp_path / "comments.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget", "git", "ufw"]

    def test_complex_real_world_format(self, tmp_path: Path) -> None:
        """Test complex real-world format from task specification."""
        content = """[core]
packages=curl, wget
# firewall
packages2=ufw
packages3=trash-cli,syncthing
# backup tools
packages4=borgbackup
packages5=backintime
packages6=flatpak,jq

[dev]
# development dbus headers
dbus=dbus-devel
# tools for hardware monitoring
monitoring=lm_sensors,htop,btop
# git and github tools
git_tools=lazygit,git-credential-libsecret,gh
# shell utilities
shell=starship # prompt
"""
        config_file = tmp_path / "complex.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        core_packages = parser.get_section_packages("core")
        assert "curl" in core_packages
        assert "wget" in core_packages
        assert "ufw" in core_packages
        assert "trash-cli" in core_packages
        assert "syncthing" in core_packages
        assert "borgbackup" in core_packages
        assert "backintime" in core_packages
        assert "flatpak" in core_packages
        assert "jq" in core_packages

        dev_packages = parser.get_section_packages("dev")
        assert "dbus-devel" in dev_packages
        assert "lm_sensors" in dev_packages
        assert "htop" in dev_packages
        assert "btop" in dev_packages
        assert "lazygit" in dev_packages
        assert "starship" in dev_packages

    def test_empty_values_filtered(self, tmp_path: Path) -> None:
        """Test that empty values are filtered out."""
        content = """[packages]
packages=curl,,wget,  ,git
"""
        config_file = tmp_path / "empty.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        packages = parser.get_section_packages("packages")
        assert packages == ["curl", "wget", "git"]

    def test_multiple_sections(self, tmp_path: Path) -> None:
        """Test parsing multiple sections."""
        content = """[section1]
items=item1, item2

[section2]
items=item3
items2=item4
"""
        config_file = tmp_path / "multi.ini"
        config_file.write_text(content)

        parser = APSConfigParser()
        parser.load(config_file)

        sec1 = parser.get_section_packages("section1")
        sec2 = parser.get_section_packages("section2")

        assert sec1 == ["item1", "item2"]
        assert sec2 == ["item3", "item4"]


class TestEnsureConfigFiles:
    """Test ensure_config_files functionality."""

    def test_create_config_files(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test creating config files from examples."""
        config_dir = tmp_path / "config"

        # Create a mock default_aps_configs directory
        examples_dir = tmp_path / "default_aps_configs"
        examples_dir.mkdir()

        # Create example files
        (examples_dir / "packages.ini").write_text("[core]\npackages=test")
        (examples_dir / "pkgmap.ini").write_text("[pkgmap.arch]\ntest=test")
        (examples_dir / "variables.ini").write_text("[variables]\ntest=value")

        # Mock the get_default_configs_dir function
        monkeypatch.setattr("aps.core.config.get_default_configs_dir", lambda: examples_dir)

        results = ensure_config_files(config_dir)

        # All files should be created
        assert results["packages.ini"] is True
        assert results["pkgmap.ini"] is True
        assert results["variables.ini"] is True

        # Files should exist
        assert (config_dir / "packages.ini").exists()
        assert (config_dir / "pkgmap.ini").exists()
        assert (config_dir / "variables.ini").exists()

    def test_skip_existing_files(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test that existing files are not overwritten."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create a mock default_aps_configs directory
        examples_dir = tmp_path / "default_aps_configs"
        examples_dir.mkdir()

        # Create example files
        (examples_dir / "packages.ini").write_text("[core]\npackages=test")
        (examples_dir / "pkgmap.ini").write_text("[pkgmap.arch]\ntest=test")
        (examples_dir / "variables.ini").write_text("[variables]\ntest=value")

        # Create existing file with different content
        existing_content = "[core]\npackages=existing"
        (config_dir / "packages.ini").write_text(existing_content)

        # Mock the get_default_configs_dir function
        monkeypatch.setattr("aps.core.config.get_default_configs_dir", lambda: examples_dir)

        results = ensure_config_files(config_dir)

        # packages.ini should not be created (already exists)
        assert results["packages.ini"] is False
        # Other files should be created
        assert results["pkgmap.ini"] is True
        assert results["variables.ini"] is True

        # Existing file should not be overwritten
        assert (config_dir / "packages.ini").read_text() == existing_content

    def test_missing_examples_directory(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test error when examples directory is missing."""
        config_dir = tmp_path / "config"

        # Mock the get_default_configs_dir function to return non-existent directory
        nonexistent_dir = tmp_path / "nonexistent"
        monkeypatch.setattr("aps.core.config.get_default_configs_dir", lambda: nonexistent_dir)

        with pytest.raises(FileNotFoundError, match="Config examples directory"):
            ensure_config_files(config_dir)
