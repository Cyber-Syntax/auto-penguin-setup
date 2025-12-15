"""Tests for sync-repos command functionality."""

import logging
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest import LogCaptureFixture

from aps.cli.commands import _extract_package_name, _parse_package_source, cmd_sync_repos
from aps.core.tracking import PackageRecord


class TestParsePackageSource:
    """Test _parse_package_source helper function."""

    def test_official_package(self) -> None:
        """Test parsing official package (no prefix)."""
        assert _parse_package_source("vim") == "official"
        assert _parse_package_source("neovim") == "official"

    def test_aur_package(self) -> None:
        """Test parsing AUR package."""
        assert _parse_package_source("AUR:lazygit") == "AUR:lazygit"
        assert _parse_package_source("AUR:paru-bin") == "AUR:paru-bin"

    def test_copr_package(self) -> None:
        """Test parsing COPR package."""
        assert _parse_package_source("COPR:user/repo") == "COPR:user/repo"
        assert _parse_package_source("COPR:user/repo:package") == "COPR:user/repo"

    def test_ppa_package(self) -> None:
        """Test parsing PPA package."""
        assert _parse_package_source("PPA:user/repo") == "PPA:user/repo"
        assert _parse_package_source("PPA:user/repo:package") == "PPA:user/repo"


class TestExtractPackageName:
    """Test _extract_package_name helper function."""

    def test_official_package(self) -> None:
        """Test extracting name from official package."""
        assert _extract_package_name("vim") == "vim"
        assert _extract_package_name("neovim") == "neovim"

    def test_aur_package(self) -> None:
        """Test extracting name from AUR package."""
        assert _extract_package_name("AUR:lazygit") == "lazygit"
        assert _extract_package_name("AUR:paru-bin") == "paru-bin"

    def test_copr_with_explicit_name(self) -> None:
        """Test extracting name from COPR with explicit package name."""
        assert _extract_package_name("COPR:user/repo:mypackage") == "mypackage"

    def test_copr_without_explicit_name(self) -> None:
        """Test COPR without explicit name returns full value."""
        result = _extract_package_name("COPR:user/repo")
        assert result == "COPR:user/repo"  # Caller should handle this

    def test_ppa_with_explicit_name(self) -> None:
        """Test extracting name from PPA with explicit package name."""
        assert _extract_package_name("PPA:user/repo:mypackage") == "mypackage"

    def test_ppa_without_explicit_name(self) -> None:
        """Test PPA without explicit name returns full value."""
        result = _extract_package_name("PPA:user/repo")
        assert result == "PPA:user/repo"


class TestCmdSyncRepos:
    """Test cmd_sync_repos command."""

    @pytest.fixture
    def mock_config_files(self, tmp_path: Path) -> Path:
        """Create mock configuration files."""
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)

        packages_ini = config_dir / "packages.ini"
        packages_ini.write_text("[dev]\nlazygit\nneovim\n")

        pkgmap_ini = config_dir / "pkgmap.ini"
        pkgmap_ini.write_text("[pkgmap.fedora]\nlazygit=COPR:dejan/lazygit\n")

        return config_dir

    @patch("aps.cli.commands.sync_repos.ensure_config_files")
    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    @patch("aps.cli.commands.sync_repos.APSConfigParser")
    def test_no_changes_detected(
        self,
        mock_parser_class: Mock,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        mock_ensure_config: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test when no repository changes are detected."""
        caplog.set_level(logging.INFO)
        # Setup mocks
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)
        (config_dir / "packages.ini").write_text("[dev]\nneovim\n")

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            PackageRecord(name="neovim", source="official", installed_at="2025-12-06")
        ]
        mock_tracker_class.return_value = mock_tracker

        mock_parser = Mock()
        mock_parser.has_section.return_value = False
        mock_parser.get_package_mappings.return_value = {}
        mock_parser_class.return_value = mock_parser

        # Execute
        args = Namespace()
        cmd_sync_repos(args)

        # Verify
        assert "No repository changes detected" in caplog.text
        assert "All tracked packages are in sync" in caplog.text

    @patch("aps.cli.commands.sync_repos.ensure_config_files")
    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    @patch("aps.cli.commands.sync_repos.APSConfigParser")
    def test_flatpak_packages_skipped(
        self,
        mock_parser_class: Mock,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        mock_ensure_config: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that Flatpak packages are skipped from migration."""
        caplog.set_level(logging.INFO)
        # Setup mocks
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)
        (config_dir / "packages.ini").write_text("[apps]\nobsidian\n")

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        # Flatpak package should be skipped
        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            PackageRecord(name="obsidian", source="flatpak:flathub", installed_at="2025-12-06")
        ]
        mock_tracker_class.return_value = mock_tracker

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_package_mappings.return_value = {"obsidian": "official"}
        mock_parser_class.return_value = mock_parser

        # Execute
        args = Namespace()
        cmd_sync_repos(args)

        # Verify - Flatpak should be skipped, so no changes
        assert "No repository changes detected" in caplog.text

    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    @patch("aps.cli.commands.sync_repos.APSConfigParser")
    @patch("builtins.input")
    def test_changes_detected_user_cancels(
        self,
        mock_input: Mock,
        mock_parser_class: Mock,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test when changes are detected but user cancels."""
        caplog.set_level(logging.INFO)
        # Setup mocks
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)
        (config_dir / "packages.ini").write_text("[dev]\nlazygit\n")
        (config_dir / "pkgmap.ini").write_text("[pkgmap.fedora]\nlazygit=COPR:dejan/lazygit\n")

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        # Package with different source
        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [
            PackageRecord(name="lazygit", source="COPR:atim/lazygit", installed_at="2025-12-06")
        ]
        mock_tracker_class.return_value = mock_tracker

        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_package_mappings.return_value = {"lazygit": "COPR:dejan/lazygit"}
        mock_parser_class.return_value = mock_parser

        # User cancels
        mock_input.return_value = "n"

        # Execute
        args = Namespace()
        cmd_sync_repos(args)

        # Verify
        assert "Repository Changes Detected" in caplog.text
        assert "lazygit" in caplog.text
        assert "COPR:atim/lazygit" in caplog.text
        assert "COPR:dejan/lazygit" in caplog.text
        assert "Migration cancelled" in caplog.text

    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    @patch("aps.cli.commands.sync_repos.APSConfigParser")
    @patch("aps.cli.commands.sync_repos.logging")
    def test_successful_migration_with_auto_flag(
        self,
        mock_logging: Mock,
        mock_parser_class: Mock,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test successful migration with --auto flag."""
        caplog.set_level(logging.INFO)
        # Setup mocks
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)
        (config_dir / "packages.ini").write_text("[dev]\nlazygit\n")
        (config_dir / "pkgmap.ini").write_text("[pkgmap.fedora]\nlazygit=COPR:dejan/lazygit\n")

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        # Package manager mock
        mock_pm = Mock()
        mock_pm.remove.return_value = (True, "")
        mock_pm.install.return_value = (True, "")
        mock_get_pm.return_value = mock_pm

        # Tracker mock
        old_record = PackageRecord(
            name="lazygit", source="COPR:atim/lazygit", installed_at="2025-12-06"
        )
        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [old_record]
        mock_tracker_class.return_value = mock_tracker

        # Parser mock
        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_package_mappings.return_value = {"lazygit": "COPR:dejan/lazygit"}
        mock_parser_class.return_value = mock_parser

        # Execute with --auto flag
        args = Namespace(auto=True)
        cmd_sync_repos(args)

        # Verify
        assert "Repository Changes Detected" in caplog.text
        assert "Migrating packages" in caplog.text
        assert "Successfully migrated" in caplog.text
        assert "Migration Summary" in caplog.text
        assert "Successful: 1" in caplog.text

        # Verify package manager calls
        mock_pm.remove.assert_called_once()
        mock_pm.install.assert_called_once()

        # Verify tracker updates
        mock_tracker.remove_package.assert_called_once_with("lazygit")
        mock_tracker.track_install.assert_called_once()

    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    @patch("aps.cli.commands.sync_repos.APSConfigParser")
    @patch("aps.cli.commands.sync_repos.logging")
    def test_migration_failure_with_rollback(
        self,
        mock_logging: Mock,
        mock_parser_class: Mock,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test migration failure with successful rollback."""
        caplog.set_level(logging.INFO)
        # Setup mocks
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        config_dir.mkdir(parents=True)
        (config_dir / "packages.ini").write_text("[dev]\nlazygit\n")
        (config_dir / "pkgmap.ini").write_text("[pkgmap.fedora]\nlazygit=COPR:dejan/lazygit\n")

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        # Package manager mock - removal succeeds, install fails, rollback succeeds
        mock_pm = Mock()
        mock_pm.remove.return_value = (True, "")
        mock_pm.install.side_effect = [
            (False, "Repository not found"),
            (True, ""),
        ]  # First install fails, rollback succeeds
        mock_get_pm.return_value = mock_pm

        # Tracker mock
        old_record = PackageRecord(
            name="lazygit", source="COPR:atim/lazygit", installed_at="2025-12-06"
        )
        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = [old_record]
        mock_tracker_class.return_value = mock_tracker

        # Parser mock
        mock_parser = Mock()
        mock_parser.has_section.return_value = True
        mock_parser.get_package_mappings.return_value = {"lazygit": "COPR:dejan/lazygit"}
        mock_parser_class.return_value = mock_parser

        # Execute with --auto flag
        args = Namespace(auto=True)
        cmd_sync_repos(args)

        # Verify
        assert "Failed to migrate lazygit" in caplog.text or "\u2717" in caplog.text
        assert "Migration Summary" in caplog.text
        assert "Failed: 1" in caplog.text
        assert "rolled back" in caplog.text or "rollback" in caplog.text.lower()

        # Verify rollback was attempted
        assert mock_pm.install.call_count == 2

    @patch("aps.cli.commands.sync_repos.Path.home")
    @patch("aps.cli.commands.sync_repos.get_package_manager")
    @patch("aps.cli.commands.sync_repos.detect_distro")
    @patch("aps.cli.commands.sync_repos.PackageTracker")
    def test_missing_config_file_auto_creation(
        self,
        mock_tracker_class: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_home: Mock,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that config files are auto-created when missing."""
        # Setup - no config files
        mock_home.return_value = tmp_path

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        # Mock the tracker to return empty list (no tracked packages)
        mock_tracker = Mock()
        mock_tracker.get_tracked_packages.return_value = []
        mock_tracker_class.return_value = mock_tracker

        # Execute
        args = Namespace()
        cmd_sync_repos(args)

        # Verify that config files were created
        config_dir = tmp_path / ".config" / "auto-penguin-setup"
        assert (config_dir / "packages.ini").exists()
        assert (config_dir / "pkgmap.ini").exists()
        assert (config_dir / "variables.ini").exists()
