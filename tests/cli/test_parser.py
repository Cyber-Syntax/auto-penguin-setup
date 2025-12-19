"""Tests for CLI argument parser construction and parsing."""

import pytest

from aps.cli.parser import create_parser


class TestParserCreation:
    """Test parser creation and basic properties."""

    def test_create_parser_returns_parser(self) -> None:
        """Test that create_parser returns a valid ArgumentParser."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "aps"

    def test_parser_description(self) -> None:
        """Test parser has correct description."""
        parser = create_parser()
        assert parser.description is not None
        assert "Auto Penguin Setup" in parser.description
        assert "Cross-distro" in parser.description

    def test_parser_version_flag(self) -> None:
        """Test that parser supports --version flag."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_version_short_flag(self) -> None:
        """Test that parser supports -v flag for version."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-v"])


class TestGlobalFlags:
    """Test global flags available to all commands."""

    def test_global_verbose_flag_on_main_parser(self) -> None:
        """Test that verbose flag is defined on main parser."""
        parser = create_parser()
        # Global flags are defined on main parser
        assert (
            parser.parse_args(["install", "--verbose", "curl"]).verbose is True
        )

    def test_global_noconfirm_flag_on_main_parser(self) -> None:
        """Test that noconfirm flag is defined on main parser."""
        parser = create_parser()
        # Global flags are defined on main parser, subcommands can use them
        # when inherited properly
        args = parser.parse_args(["remove", "curl"])
        assert args.noconfirm is False

    def test_verbose_flag_default_false(self) -> None:
        """Test that verbose flag defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl"])
        assert args.verbose is False

    def test_noconfirm_flag_default_false(self) -> None:
        """Test that noconfirm flag defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl"])
        assert args.noconfirm is False


class TestInstallCommand:
    """Test install command parsing."""

    def test_install_single_package(self) -> None:
        """Test parsing single package install."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl"])
        assert args.command == "install"
        assert args.packages == ["curl"]

    def test_install_multiple_packages(self) -> None:
        """Test parsing multiple packages install."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl", "wget", "git"])
        assert args.command == "install"
        assert args.packages == ["curl", "wget", "git"]

    def test_install_with_category(self) -> None:
        """Test parsing install with category."""
        parser = create_parser()
        args = parser.parse_args(["install", "@core"])
        assert args.command == "install"
        assert args.packages == ["@core"]

    def test_install_with_mixed_packages_and_categories(self) -> None:
        """Test parsing install with both packages and categories."""
        parser = create_parser()
        args = parser.parse_args(["install", "@core", "vim", "@dev"])
        assert args.command == "install"
        assert args.packages == ["@core", "vim", "@dev"]

    def test_install_with_dry_run(self) -> None:
        """Test install command with --dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["install", "--dry-run", "curl"])
        assert args.command == "install"
        assert args.dry_run is True
        assert args.packages == ["curl"]

    def test_install_dry_run_with_multiple_packages(self) -> None:
        """Test install --dry-run with multiple packages."""
        parser = create_parser()
        args = parser.parse_args(
            ["install", "--dry-run", "curl", "wget", "@core"]
        )
        assert args.dry_run is True
        assert args.packages == ["curl", "wget", "@core"]

    def test_install_verbose_flag(self) -> None:
        """Test install command with verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["install", "--verbose", "curl"])
        assert args.verbose is True
        assert args.packages == ["curl"]

    def test_install_combined_flags(self) -> None:
        """Test install with multiple flags."""
        parser = create_parser()
        args = parser.parse_args(
            ["install", "--dry-run", "--verbose", "curl", "wget"]
        )
        assert args.dry_run is True
        assert args.verbose is True
        assert args.packages == ["curl", "wget"]

    def test_install_requires_packages(self) -> None:
        """Test that install command requires at least one package."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["install"])

    def test_install_dry_run_default_false(self) -> None:
        """Test that dry_run defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["install", "curl"])
        assert args.dry_run is False


class TestRemoveCommand:
    """Test remove command parsing."""

    def test_remove_single_package(self) -> None:
        """Test parsing single package removal."""
        parser = create_parser()
        args = parser.parse_args(["remove", "curl"])
        assert args.command == "remove"
        assert args.packages == ["curl"]

    def test_remove_multiple_packages(self) -> None:
        """Test parsing multiple packages removal."""
        parser = create_parser()
        args = parser.parse_args(["remove", "curl", "wget", "git"])
        assert args.command == "remove"
        assert args.packages == ["curl", "wget", "git"]

    def test_remove_with_dry_run(self) -> None:
        """Test remove command with --dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["remove", "--dry-run", "curl"])
        assert args.command == "remove"
        assert args.dry_run is True

    def test_remove_with_verbose(self) -> None:
        """Test remove command with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["remove", "--verbose", "curl"])
        assert args.verbose is True
        assert args.command == "remove"

    def test_remove_requires_packages(self) -> None:
        """Test that remove command requires at least one package."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["remove"])

    def test_remove_dry_run_default_false(self) -> None:
        """Test that dry_run defaults to False for remove."""
        parser = create_parser()
        args = parser.parse_args(["remove", "curl"])
        assert args.dry_run is False


class TestListCommand:
    """Test list command parsing."""

    def test_list_no_arguments(self) -> None:
        """Test list command with no arguments."""
        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.source is None

    def test_list_with_source_official(self) -> None:
        """Test list with official source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "official"])
        assert args.command == "list"
        assert args.source == "official"

    def test_list_with_source_copr(self) -> None:
        """Test list with COPR source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "copr"])
        assert args.source == "copr"

    def test_list_with_source_aur(self) -> None:
        """Test list with AUR source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "aur"])
        assert args.source == "aur"

    def test_list_with_source_ppa(self) -> None:
        """Test list with PPA source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "ppa"])
        assert args.source == "ppa"

    def test_list_with_source_flatpak(self) -> None:
        """Test list with flatpak source filter."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "flatpak"])
        assert args.source == "flatpak"

    def test_list_with_verbose(self) -> None:
        """Test list command with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["list", "--verbose"])
        assert args.verbose is True
        assert args.command == "list"

    def test_list_with_source_and_verbose(self) -> None:
        """Test list with both source and verbose flags."""
        parser = create_parser()
        args = parser.parse_args(["list", "--source", "aur", "--verbose"])
        assert args.source == "aur"
        assert args.verbose is True

    def test_list_invalid_source(self) -> None:
        """Test list with invalid source raises error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["list", "--source", "invalid"])


class TestSyncReposCommand:
    """Test sync-repos command parsing."""

    def test_sync_repos_no_flags(self) -> None:
        """Test sync-repos command without flags."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos"])
        assert args.command == "sync-repos"
        assert args.auto is False

    def test_sync_repos_with_auto_flag(self) -> None:
        """Test sync-repos command with --auto flag."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos", "--auto"])
        assert args.command == "sync-repos"
        assert args.auto is True

    def test_sync_repos_with_verbose(self) -> None:
        """Test sync-repos with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos", "--verbose"])
        assert args.verbose is True
        assert args.command == "sync-repos"

    def test_sync_repos_auto_default_false(self) -> None:
        """Test that auto flag defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["sync-repos"])
        assert args.auto is False


class TestStatusCommand:
    """Test status command parsing."""

    def test_status_no_arguments(self) -> None:
        """Test status command without arguments."""
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_status_with_verbose(self) -> None:
        """Test status command with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["status", "--verbose"])
        assert args.verbose is True
        assert args.command == "status"


class TestSetupCommand:
    """Test setup command parsing."""

    def test_setup_with_component(self) -> None:
        """Test setup command with a component."""
        parser = create_parser()
        args = parser.parse_args(["setup", "aur-helper"])
        assert args.command == "setup"
        assert args.component == "aur-helper"

    def test_setup_available_components(self) -> None:
        """Test setup command recognizes available components."""
        parser = create_parser()
        # Test with known components
        args = parser.parse_args(["setup", "aur-helper"])
        assert args.component == "aur-helper"

        args = parser.parse_args(["setup", "ollama"])
        assert args.component == "ollama"

    def test_setup_with_verbose(self) -> None:
        """Test setup command with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["setup", "aur-helper", "--verbose"])
        assert args.verbose is True
        assert args.component == "aur-helper"

    def test_setup_requires_component(self) -> None:
        """Test that setup command requires a component."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["setup"])

    def test_setup_invalid_component(self) -> None:
        """Test setup command with invalid component."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["setup", "invalid-component"])


class TestCommandRequirement:
    """Test that commands are required."""

    def test_no_command_raises_error(self) -> None:
        """Test that parser requires a command."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_no_command_with_verbose_raises_error(self) -> None:
        """Test that parser requires command even with global flags."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--verbose"])

    def test_no_command_with_noconfirm_raises_error(self) -> None:
        """Test that parser requires command with --noconfirm."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--noconfirm"])


class TestFlagPositioning:
    """Test flag positioning and order flexibility."""

    def test_command_specific_flags_after_command(self) -> None:
        """Test that command-specific flags come after command."""
        parser = create_parser()
        args = parser.parse_args(["install", "--dry-run", "curl"])
        assert args.dry_run is True

    def test_packages_after_command_and_flags(self) -> None:
        """Test package specification after command and flags."""
        parser = create_parser()
        args = parser.parse_args(
            ["install", "--dry-run", "--verbose", "curl", "wget"]
        )
        assert args.packages == ["curl", "wget"]
        assert args.dry_run is True
        assert args.verbose is True

    def test_flag_order_flexibility_within_command(self) -> None:
        """Test that flag order is flexible within command scope."""
        parser = create_parser()
        args1 = parser.parse_args(
            ["install", "--verbose", "--dry-run", "curl"]
        )
        args2 = parser.parse_args(
            ["install", "--dry-run", "--verbose", "curl"]
        )

        assert args1.verbose == args2.verbose
        assert args1.dry_run == args2.dry_run
        assert args1.packages == args2.packages
