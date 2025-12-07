"""Tests for CLI command parsing and execution."""

from argparse import Namespace

import pytest

from aps.cli import create_parser
from aps.cli.commands import cmd_list, cmd_status


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "aps"
        assert parser.description is not None
        assert "Auto Penguin Setup" in parser.description

    def test_parser_install_command(self):
        """Test install command parsing."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl", "wget"])
        assert args.command == "install"
        assert args.packages == ["curl", "wget"]
        assert not args.dry_run

    def test_parser_install_dry_run(self):
        """Test install with dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["install", "--dry-run", "@core"])
        assert args.command == "install"
        assert args.packages == ["@core"]
        assert args.dry_run

    def test_parser_remove_command(self):
        """Test remove command parsing."""
        parser = create_parser()
        args = parser.parse_args(["remove", "curl"])
        assert args.command == "remove"
        assert args.packages == ["curl"]

    def test_parser_list_command(self):
        """Test list command parsing."""
        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.source is None

    def test_parser_list_with_source(self):
        """Test list with source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "aur"])
        assert args.command == "list"
        assert args.source == "aur"

    def test_parser_sync_repos(self):
        """Test sync-repos command parsing."""
        parser = create_parser()
        parser.parse_args(["sync-repos"])
        # Just test that parsing doesn't fail

    def test_parser_sync_repos_auto(self):
        """Test sync-repos with auto flag."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos", "--auto"])
        assert args.command == "sync-repos"
        assert args.auto

    def test_parser_status_command(self):
        """Test status command parsing."""
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parser_no_command_error(self):
        """Test that parser requires a command."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestCLICommands:
    """Test CLI command execution."""

    def test_cmd_status(self, tmp_path, monkeypatch):
        """Test status command execution."""
        from unittest.mock import Mock, patch

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.version = "39"
        mock_distro.package_manager.value = "dnf"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []

        with (
            patch("aps.cli.commands.detect_distro", return_value=mock_distro),
            patch("aps.cli.commands.PackageTracker", return_value=mock_tracker),
            patch("builtins.print") as mock_print,
        ):
            args = Namespace()
            cmd_status(args)

            # Check that print was called with expected output
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert "Distribution: Fedora 39" in calls
            assert "Package Manager: dnf" in calls
            assert "Tracked Packages: 0" in calls

    def test_cmd_list_no_packages(self, tmp_path, monkeypatch):
        """Test list command with no packages."""
        from unittest.mock import Mock, patch

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []

        with (
            patch("aps.cli.commands.PackageTracker", return_value=mock_tracker),
            patch("builtins.print") as mock_print,
        ):
            args = Namespace(source=None)
            cmd_list(args)

            # Should not print anything for empty list
            assert mock_print.call_count == 0

    def test_cmd_list_with_packages(self, tmp_path, monkeypatch):
        """Test list command with packages."""
        from unittest.mock import Mock, patch

        mock_record = Mock()
        mock_record.name = "curl"
        mock_record.source = "official"
        mock_record.category = None
        mock_record.installed_at = "2025-12-06 17:24:50 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [mock_record]

        with (
            patch("aps.cli.commands.PackageTracker", return_value=mock_tracker),
            patch("builtins.print") as mock_print,
        ):
            args = Namespace(source=None)
            cmd_list(args)

            # Check that header, separator, column headers, dashes, and package info were printed
            assert mock_print.call_count == 5
            calls = mock_print.call_args_list
            assert calls[0][0][0] == "Tracked Packages:"
            assert calls[1][0][0] == "=" * 97  # 30+25+15+24+3
            assert "Name" in calls[2][0][0] and "Source" in calls[2][0][0]
            assert calls[3][0][0] == f"{'-' * 30} {'-' * 25} {'-' * 15} {'-' * 24}"
            assert "curl" in calls[4][0][0] and "official" in calls[4][0][0]

    def test_cmd_list_with_source_filter(self, tmp_path, monkeypatch):
        """Test list command with source filtering."""
        from unittest.mock import Mock, patch

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
            patch("aps.cli.commands.PackageTracker", return_value=mock_tracker),
            patch("builtins.print") as mock_print,
        ):
            args = Namespace(source="aur")
            cmd_list(args)

            # Check that header, separator, column headers, dashes, and filtered package were printed
            assert mock_print.call_count == 5
            calls = mock_print.call_args_list
            assert calls[0][0][0] == "Tracked Packages:"
            assert calls[1][0][0] == "=" * 97
            assert "Name" in calls[2][0][0] and "Source" in calls[2][0][0]
            assert calls[3][0][0] == f"{'-' * 30} {'-' * 25} {'-' * 15} {'-' * 24}"
            assert "neovim" in calls[4][0][0] and "aur" in calls[4][0][0]
