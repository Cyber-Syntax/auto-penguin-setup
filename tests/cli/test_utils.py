"""Tests for CLI utilities module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aps.cli.utils import get_tracking_db_path, load_category_packages


class TestGetTrackingDbPath:
    """Test tracking database path resolution."""

    @patch("aps.cli.utils.Path.home")
    def test_returns_correct_path(self, mock_home: Mock) -> None:
        """Test that tracking db path is correct."""
        mock_home.return_value = Path("/home/testuser")

        path = get_tracking_db_path()

        assert path == Path(
            "/home/testuser/.config/auto-penguin-setup/metadata.jsonl"
        )

    @patch("aps.cli.utils.Path.home")
    def test_returns_pathlib_path_object(self, mock_home: Mock) -> None:
        """Test that return type is Path object."""
        mock_home.return_value = Path("/home/testuser")

        path = get_tracking_db_path()

        assert isinstance(path, Path)

    @patch("aps.cli.utils.Path.home")
    def test_different_home_directories(self, mock_home: Mock) -> None:
        """Test with different home directories."""
        mock_home.return_value = Path("/root")
        path = get_tracking_db_path()
        assert path == Path("/root/.config/auto-penguin-setup/metadata.jsonl")

        mock_home.return_value = Path("/home/anotheruser")
        path = get_tracking_db_path()
        assert path == Path(
            "/home/anotheruser/.config/auto-penguin-setup/metadata.jsonl"
        )


class TestLoadCategoryPackages:
    """Test loading packages from categories."""

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_load_existing_category(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test loading packages from existing category."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_section_packages.return_value = [
            "vim",
            "emacs",
            "neovim",
        ]
        mock_parser_cls.return_value = mock_parser

        packages = load_category_packages("editors")

        assert packages == ["vim", "emacs", "neovim"]
        mock_ensure.assert_called_once()
        mock_parser.load.assert_called_once()

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_load_nonexistent_category_raises_error(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test loading nonexistent category raises ValueError."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = False
        mock_parser_cls.return_value = mock_parser

        with pytest.raises(ValueError, match="Category 'invalid' not found"):
            load_category_packages("invalid")

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_load_empty_category(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test loading empty category returns empty list."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_section_packages.return_value = []
        mock_parser_cls.return_value = mock_parser

        packages = load_category_packages("empty")

        assert packages == []

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_load_large_category(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test loading category with many packages."""
        mock_home.return_value = Path("/home/testuser")

        large_list = [f"package{i}" for i in range(50)]
        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_section_packages.return_value = large_list
        mock_parser_cls.return_value = mock_parser

        packages = load_category_packages("large")

        assert len(packages) == 50
        assert packages == large_list

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_ensure_config_called_before_load(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test that ensure_config_files is called before loading."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_section_packages.return_value = ["vim"]
        mock_parser_cls.return_value = mock_parser

        load_category_packages("test")

        # Ensure called before parser operations
        mock_ensure.assert_called_once_with(
            Path("/home/testuser/.config/auto-penguin-setup")
        )
        mock_parser.load.assert_called_once()

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_load_different_categories(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test loading multiple different categories."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = True

        # Different categories return different packages
        def get_packages_side_effect(category: str) -> list[str]:
            categories = {
                "core": ["bash", "zsh"],
                "dev": ["git", "gcc"],
                "editors": ["vim", "emacs"],
            }
            return categories.get(category, [])

        mock_parser.get_section_packages.side_effect = get_packages_side_effect
        mock_parser_cls.return_value = mock_parser

        assert load_category_packages("core") == ["bash", "zsh"]
        assert load_category_packages("dev") == ["git", "gcc"]
        assert load_category_packages("editors") == ["vim", "emacs"]

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_config_dir_resolved_correctly(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test that config directory is resolved correctly."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_section_packages.return_value = ["vim"]
        mock_parser_cls.return_value = mock_parser

        load_category_packages("test")

        expected_config_dir = Path("/home/testuser/.config/auto-penguin-setup")
        mock_ensure.assert_called_once_with(expected_config_dir)

        # Parser should load from correct path
        expected_file = expected_config_dir / "packages.ini"
        mock_parser.load.assert_called_once_with(expected_file)

    @patch("aps.cli.utils.APSConfigParser")
    @patch("aps.cli.utils.ensure_config_files")
    @patch("aps.cli.utils.Path.home")
    def test_case_sensitive_category_name(
        self, mock_home: Mock, mock_ensure: Mock, mock_parser_cls: Mock
    ) -> None:
        """Test that category names are case-sensitive."""
        mock_home.return_value = Path("/home/testuser")

        mock_parser = Mock()
        mock_parser.has_section.side_effect = lambda cat: cat == "Dev"
        mock_parser.get_section_packages.return_value = ["git", "gcc"]
        mock_parser_cls.return_value = mock_parser

        # 'Dev' should work
        packages = load_category_packages("Dev")
        assert packages == ["git", "gcc"]

        # 'dev' should fail (different case)
        mock_parser.has_section.return_value = False
        with pytest.raises(ValueError):
            load_category_packages("dev")
