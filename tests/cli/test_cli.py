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
        mock_tracker.get_tracked_packages.return_value = [
            Mock(name="git", source="official"),
            Mock(name="lazygit", source="COPR:atim/lazygit"),
            Mock(name="vscode", source="AUR:vscode"),
        ]

        with (
            patch(
                "aps.cli.commands.status.detect_distro",
                return_value=mock_distro,
            ),
            patch(
                "aps.cli.commands.status.PackageTracker",
                return_value=mock_tracker,
            ),
        ):
            args = Namespace()
            cmd_status(args)

            # Check that logger output to stderr contains expected messages
            captured = capsys.readouterr()
            assert "Distribution: Fedora 39" in captured.err
            assert "Package Manager: dnf" in captured.err
            assert "Tracked Packages: 3" in captured.err
            assert "By Source:" in captured.err
            assert "official: 1" in captured.err
            assert "COPR: 1" in captured.err
            assert "AUR: 1" in captured.err

    def test_cmd_list_no_packages(self, capsys: CaptureFixture[str]) -> None:
        """Test list command with no packages."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()  # Configure logger to output to stderr

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []

        with (
            patch(
                "aps.cli.commands.list.PackageTracker",
                return_value=mock_tracker,
            ),
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
            patch(
                "aps.cli.commands.list.PackageTracker",
                return_value=mock_tracker,
            ),
        ):
            args = Namespace(source=None)
            cmd_list(args)

            # Check that logger output contains expected content
            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "curl" in captured.err
            assert "official" in captured.err

    def test_cmd_list_with_source_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
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
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
        ]

        with (
            patch(
                "aps.cli.commands.list.PackageTracker",
                return_value=mock_tracker,
            ),
        ):
            args = Namespace(source="aur")
            cmd_list(args)

            # Check that logger output contains filtered package
            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "neovim" in captured.err
            assert "aur" in captured.err

    def test_cmd_list_with_case_insensitive_source_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command with case-insensitive source filtering."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        # Create mock records with various source formats
        mock_record1 = Mock()
        mock_record1.name = "lazygit"
        mock_record1.source = "COPR:atim/lazygit"
        mock_record1.category = "dev"
        mock_record1.installed_at = "2025-12-06 17:24:50 +0000"

        mock_record2 = Mock()
        mock_record2.name = "starship"
        mock_record2.source = "COPR:atim/starship"
        mock_record2.category = "shell"
        mock_record2.installed_at = "2025-12-06 17:25:00 +0000"

        mock_record3 = Mock()
        mock_record3.name = "obsidian"
        mock_record3.source = "flatpak:flathub"
        mock_record3.category = "apps"
        mock_record3.installed_at = "2025-12-06 17:26:00 +0000"

        mock_record4 = Mock()
        mock_record4.name = "curl"
        mock_record4.source = "official"
        mock_record4.category = None
        mock_record4.installed_at = "2025-12-06 17:27:00 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
            mock_record3,
            mock_record4,
        ]

        # Test lowercase "copr" matches "COPR:..." sources
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="copr")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "lazygit" in captured.err
            assert "starship" in captured.err
            assert "COPR:atim/lazygit" in captured.err
            assert "COPR:atim/starship" in captured.err
            # Should NOT include flatpak or official packages
            assert "obsidian" not in captured.err
            assert "curl" not in captured.err

    def test_cmd_list_with_uppercase_source_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command with uppercase source filter."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        mock_record1 = Mock()
        mock_record1.name = "obsidian"
        mock_record1.source = "flatpak:flathub"
        mock_record1.category = "apps"
        mock_record1.installed_at = "2025-12-06 17:26:00 +0000"

        mock_record2 = Mock()
        mock_record2.name = "signal"
        mock_record2.source = "flatpak:flathub"
        mock_record2.category = "apps"
        mock_record2.installed_at = "2025-12-06 17:26:30 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
        ]

        # Test uppercase "FLATPAK" matches "flatpak:..." sources
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="FLATPAK")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "obsidian" in captured.err
            assert "signal" in captured.err
            assert "flatpak:flathub" in captured.err

    def test_cmd_list_with_official_source_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command filtering official packages (no colon in source)."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        mock_record1 = Mock()
        mock_record1.name = "curl"
        mock_record1.source = "official"
        mock_record1.category = None
        mock_record1.installed_at = "2025-12-06 17:27:00 +0000"

        mock_record2 = Mock()
        mock_record2.name = "git"
        mock_record2.source = "official"
        mock_record2.category = None
        mock_record2.installed_at = "2025-12-06 17:27:30 +0000"

        mock_record3 = Mock()
        mock_record3.name = "lazygit"
        mock_record3.source = "COPR:atim/lazygit"
        mock_record3.category = "dev"
        mock_record3.installed_at = "2025-12-06 17:24:50 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
            mock_record3,
        ]

        # Test "official" or "OFFICIAL" matches "official" sources
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="OFFICIAL")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "curl" in captured.err
            assert "git" in captured.err
            # Should NOT include COPR package
            assert "lazygit" not in captured.err

    def test_cmd_list_with_aur_lowercase_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command with lowercase 'aur' filter matching AUR packages."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        mock_record1 = Mock()
        mock_record1.name = "lazygit"
        mock_record1.source = "AUR:lazygit"
        mock_record1.category = "dev"
        mock_record1.installed_at = "2025-12-06 17:24:50 +0000"

        mock_record2 = Mock()
        mock_record2.name = "thinkfan"
        mock_record2.source = "AUR:thinkfan"
        mock_record2.category = "laptop"
        mock_record2.installed_at = "2025-12-06 17:25:00 +0000"

        mock_record3 = Mock()
        mock_record3.name = "qtile-extras"
        mock_record3.source = "AUR:qtile-extras"
        mock_record3.category = "wm-common"
        mock_record3.installed_at = "2025-12-06 17:25:30 +0000"

        mock_record4 = Mock()
        mock_record4.name = "curl"
        mock_record4.source = "official"
        mock_record4.category = None
        mock_record4.installed_at = "2025-12-06 17:27:00 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
            mock_record3,
            mock_record4,
        ]

        # Test lowercase "aur" matches "AUR:..." sources
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="aur")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "lazygit" in captured.err
            assert "thinkfan" in captured.err
            assert "qtile-extras" in captured.err
            assert "AUR:lazygit" in captured.err
            assert "AUR:thinkfan" in captured.err
            assert "AUR:qtile-extras" in captured.err
            # Should NOT include official package
            assert "curl" not in captured.err
            assert "official" not in captured.err

    def test_cmd_list_with_aur_uppercase_filter(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command with uppercase 'AUR' filter matching AUR packages."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        mock_record1 = Mock()
        mock_record1.name = "xautolock"
        mock_record1.source = "AUR:xautolock"
        mock_record1.category = "desktop"
        mock_record1.installed_at = "2025-12-06 17:26:00 +0000"

        mock_record2 = Mock()
        mock_record2.name = "starship"
        mock_record2.source = "COPR:atim/starship"
        mock_record2.category = "shell"
        mock_record2.installed_at = "2025-12-06 17:26:30 +0000"

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            mock_record1,
            mock_record2,
        ]

        # Test uppercase "AUR" matches "AUR:..." sources
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="AUR")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "Tracked Packages:" in captured.err
            assert "xautolock" in captured.err
            assert "AUR:xautolock" in captured.err
            # Should NOT include COPR package
            assert "starship" not in captured.err
            assert "COPR:atim/starship" not in captured.err

    def test_cmd_list_with_mixed_sources(
        self, capsys: CaptureFixture[str]
    ) -> None:
        """Test list command correctly filters among mixed source types."""
        from unittest.mock import Mock, patch

        from aps.core.logger import setup_logging

        setup_logging()

        # Create a diverse set of packages from different sources
        mock_records = [
            Mock(
                name="curl",
                source="official",
                category=None,
                installed_at="2025-12-06 17:27:00 +0000",
            ),
            Mock(
                name="lazygit",
                source="AUR:lazygit",
                category="dev",
                installed_at="2025-12-06 17:24:50 +0000",
            ),
            Mock(
                name="starship",
                source="COPR:atim/starship",
                category="shell",
                installed_at="2025-12-06 17:25:00 +0000",
            ),
            Mock(
                name="obsidian",
                source="flatpak:flathub",
                category="apps",
                installed_at="2025-12-06 17:26:00 +0000",
            ),
            Mock(
                name="thinkfan",
                source="AUR:thinkfan",
                category="laptop",
                installed_at="2025-12-06 17:25:30 +0000",
            ),
        ]

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = mock_records

        # Test filtering by "aur" - should only show AUR packages
        with patch(
            "aps.cli.commands.list.PackageTracker", return_value=mock_tracker
        ):
            args = Namespace(source="aur")
            cmd_list(args)

            captured = capsys.readouterr()
            assert "lazygit" in captured.err
            assert "thinkfan" in captured.err
            # Should NOT include other source types
            assert "curl" not in captured.err
            assert "starship" not in captured.err
            assert "obsidian" not in captured.err

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
        mock_mapping.is_flatpak = False

        mock_repo_mgr.check_official_before_enabling.return_value = (
            mock_mapping
        )
        mock_mapper.map_package.return_value = mock_mapping

        with (
            patch("aps.utils.privilege.ensure_sudo"),  # Mock at the source
            patch(
                "aps.cli.commands.install.detect_distro",
                return_value=mock_distro,
            ),
            patch(
                "aps.cli.commands.install.get_package_manager",
                return_value=mock_pm,
            ),
            patch(
                "aps.cli.commands.install.RepositoryManager",
                return_value=mock_repo_mgr,
            ),
            patch(
                "aps.cli.commands.install.PackageTracker",
                return_value=mock_tracker,
            ),
            patch(
                "aps.cli.commands.install.PackageMapper",
                return_value=mock_mapper,
            ),
            patch(
                "aps.cli.commands.install.load_category_packages",
                return_value=[],
            ),
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
            patch("aps.utils.privilege.ensure_sudo"),  # Mock at the source
            patch(
                "aps.cli.commands.remove.detect_distro",
                return_value=mock_distro,
            ),
            patch(
                "aps.cli.commands.remove.get_package_manager",
                return_value=mock_pm,
            ),
            patch(
                "aps.cli.commands.remove.PackageTracker",
                return_value=mock_tracker,
            ),
        ):
            args = Namespace(packages=["neovim"], dry_run=True)
            cmd_remove(args)

            # Check that logger output contains dry run message
            captured = capsys.readouterr()
            assert "Would remove: neovim" in captured.err
