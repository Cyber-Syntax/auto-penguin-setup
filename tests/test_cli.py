"""Tests for CLI command parsing and execution."""

from argparse import Namespace

import pytest
from pytest import CaptureFixture

from aps.cli.commands import cmd_install, cmd_list, cmd_remove, cmd_status
from aps.cli.parser import create_parser


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_create_parser_basic(self) -> None:
        """Test basic parser creation."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "aps"
        assert parser.description is not None
        assert "Auto Penguin Setup" in parser.description

    def test_parser_install_command(self) -> None:
        """Test install command parsing."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl", "wget"])
        assert args.command == "install"
        assert args.packages == ["curl", "wget"]
        assert not args.dry_run

    def test_parser_install_dry_run(self) -> None:
        """Test install with dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["install", "--dry-run", "@core"])
        assert args.command == "install"
        assert args.packages == ["@core"]
        assert args.dry_run

    def test_parser_remove_command(self) -> None:
        """Test remove command parsing."""
        parser = create_parser()
        args = parser.parse_args(["remove", "curl"])
        assert args.command == "remove"
        assert args.packages == ["curl"]

    def test_parser_list_command(self) -> None:
        """Test list command parsing."""
        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.source is None

    def test_parser_list_with_source(self) -> None:
        """Test list with source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "aur"])
        assert args.command == "list"
        assert args.source == "aur"

    def test_parser_sync_repos(self) -> None:
        """Test sync-repos command parsing."""
        parser = create_parser()
        parser.parse_args(["sync-repos"])
        # Just test that parsing doesn't fail

    def test_parser_sync_repos_auto(self) -> None:
        """Test sync-repos with auto flag."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos", "--auto"])
        assert args.command == "sync-repos"
        assert args.auto

    def test_parser_status_command(self) -> None:
        """Test status command parsing."""
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parser_no_command_error(self) -> None:
        """Test that parser requires a command."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestCLICommands:
    """Test CLI command execution."""

    def test_cmd_status(self, capsys: CaptureFixture[str]) -> None:
        """Test status command execution."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.version = "39"
        mock_distro.package_manager.value = "dnf"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []

        with (
            patch("aps.cli.commands.status.detect_distro", return_value=mock_distro),
            patch("aps.cli.commands.status.PackageTracker", return_value=mock_tracker),
        ):
            args = Namespace()
            cmd_status(args)

            # Check that logger output to stderr contains expected messages
            captured = capsys.readouterr()
            assert "Distribution: Fedora 39" in captured.err
            assert "Package Manager: dnf" in captured.err
            assert "Tracked Packages: 0" in captured.err

    def test_cmd_list_no_packages(self, capsys: CaptureFixture[str]) -> None:
        """Test list command with no packages."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []

        with (
            patch("aps.cli.commands.list.PackageTracker", return_value=mock_tracker),
        ):
            args = Namespace(source=None)
            cmd_list(args)

            # Should not log anything for empty list
            captured = capsys.readouterr()
            assert "Tracked Packages:" not in captured.err

    def test_cmd_list_with_packages(self, capsys: CaptureFixture[str]) -> None:
        """Test list command with packages."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_record = Mock()
        mock_record.name = "curl"
        mock_record.source = "official"
        mock_record.category = None
        mock_record.installed_at = "2025-12-06 17:24:50 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [mock_record]

        with (
            patch("aps.cli.commands.list.PackageTracker", return_value=mock_tracker),
        ):
            args = Namespace(source=None)
            cmd_list(args)

            # Check that logger output contains expected content
            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "curl" in captured.err
            assert "official" in captured.err

    def test_cmd_list_with_source_filter(self, capsys: CaptureFixture[str]) -> None:
        """Test list command with source filtering."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_record1 = Mock()
        mock_record1.name = "curl"
        mock_record1.source = "official"
        mock_record1.category = None
        mock_record1.installed_at = "2025-12-06 17:24:50 +0000"

        mock_record2 = Mock()
        mock_record2.name = "neovim"
        mock_record2.source = "aur"
        mock_record2.category = None
        mock_record2.installed_at = "2025-12-06 17:24:50 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [mock_record1, mock_record2]

        with (
            patch("aps.cli.commands.list.PackageTracker", return_value=mock_tracker),
        ):
            args = Namespace(source="aur")
            cmd_list(args)

            # Check that logger output contains filtered package
            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "neovim" in captured.err
            assert "aur" in captured.err

    def test_cmd_install_dry_run(self, capsys: CaptureFixture[str]) -> None:
        """Test install command with dry run."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.version = "39"
        mock_distro.family = "fedora"

        mock_pm = Mock()
        mock_repo_mgr = Mock()
        mock_tracker = Mock()
        mock_mapper = Mock()
        mock_mapper.mappings = {}

        # Mock package mapping
        mock_mapping = Mock()
        mock_mapping.original_name = "neovim"
        mock_mapping.mapped_name = "neovim"
        mock_mapping.source = "official"
        mock_mapping.category = None
        mock_mapping.is_official = True
        mock_mapping.is_copr = False
        mock_mapping.is_aur = False
        mock_mapping.is_ppa = False
        mock_mapping.is_flatpak = False

        mock_repo_mgr.check_official_before_enabling.return_value = mock_mapping
        mock_mapper.map_package.return_value = mock_mapping

        with (
            patch("aps.cli.commands.install.detect_distro", return_value=mock_distro),
            patch("aps.cli.commands.install.get_package_manager", return_value=mock_pm),
            patch("aps.cli.commands.install.RepositoryManager", return_value=mock_repo_mgr),
            patch("aps.cli.commands.install.PackageTracker", return_value=mock_tracker),
            patch("aps.cli.commands.install.PackageMapper", return_value=mock_mapper),
            patch("aps.cli.commands.install.load_category_packages", return_value=[]),
        ):
            args = Namespace(packages=["neovim"], dry_run=True)
            cmd_install(args)

            # Check that logger output contains dry run message
            captured = capsys.readouterr()
            assert "Would install: neovim" in captured.err

    def test_cmd_remove_dry_run(self, capsys: CaptureFixture[str]) -> None:
        """Test remove command with dry run."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.version = "39"

        mock_pm = Mock()
        mock_tracker = Mock()

        with (
            patch("aps.cli.commands.remove.detect_distro", return_value=mock_distro),
            patch("aps.cli.commands.remove.get_package_manager", return_value=mock_pm),
            patch("aps.cli.commands.remove.PackageTracker", return_value=mock_tracker),
        ):
            args = Namespace(packages=["neovim"], dry_run=True)
            cmd_remove(args)

            # Check that logger output contains dry run message
            captured = capsys.readouterr()
            assert "Would remove: neovim" in captured.err
