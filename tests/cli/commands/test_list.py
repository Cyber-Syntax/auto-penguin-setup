"""Tests for list command functionality.

Verifies printing of tracked packages and source filtering.
"""

from argparse import Namespace
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.cli.commands.list import cmd_list


def _pkg(name: str, source: str, category: str | None, installed_at: str) -> Mock:
    """Create a mock package object."""
    p = Mock()
    p.name = name
    p.source = source
    p.category = category
    p.installed_at = installed_at
    return p


class TestListCommand:
    """Test list command with various scenarios."""

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_all_packages(self, mock_tracker_cls: Mock, caplog: LogCaptureFixture) -> None:
        """Test listing all tracked packages."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("lazygit", "COPR:user/repo", "dev", "2025-12-02"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source=None)
        cmd_list(args)

        assert "Tracked Packages:" in caplog.text
        assert "vim" in caplog.text
        assert "lazygit" in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_empty_packages(self, mock_tracker_cls: Mock, caplog: LogCaptureFixture) -> None:
        """Test listing when no packages are tracked."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = []
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source=None)
        cmd_list(args)

        # When no packages, should still initialize but not print package rows
        # The function returns early if packages list is empty

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_filtered_by_source_official(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering packages by official source."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("lazygit", "COPR:user/repo", "dev", "2025-12-02"),
            _pkg("curl", "official", "core", "2025-12-03"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="official")
        cmd_list(args)

        # Should include official packages but not COPR
        assert "vim" in caplog.text
        assert "curl" in caplog.text
        assert "lazygit" not in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_filtered_by_source_copr(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering packages by COPR source."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("lazygit", "COPR:user/repo", "dev", "2025-12-02"),
            _pkg("neovim", "COPR:another/repo", "dev", "2025-12-03"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="COPR")
        cmd_list(args)

        # Should include COPR packages but not official
        assert "lazygit" in caplog.text
        assert "neovim" in caplog.text
        # Verify official is not in the package list (only in headers)
        lines = [line for line in caplog.text.split("\n") if "official" in line]
        assert len(lines) == 0

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_case_insensitive_source_filter(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test that source filtering is case-insensitive."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("lazygit", "COPR:user/repo", "dev", "2025-12-02"),
            _pkg("vim", "official", None, "2025-12-01"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        # Try lowercase 'copr'
        args = Namespace(source="copr")
        cmd_list(args)

        # Should still match COPR packages (case-insensitive)
        assert "lazygit" in caplog.text
        assert "vim" not in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_filtered_by_source_aur(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering packages by AUR source."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("lazygit", "AUR:lazygit", "dev", "2025-12-02"),
            _pkg("paru-bin", "AUR:paru-bin", "system", "2025-12-03"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="AUR")
        cmd_list(args)

        # Should include AUR packages only
        assert "lazygit" in caplog.text
        assert "paru-bin" in caplog.text
        assert "vim" not in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_filtered_by_source_ppa(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering packages by PPA source."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("neovim", "PPA:user/repo", "dev", "2025-12-02"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="PPA")
        cmd_list(args)

        # Should include PPA packages only
        assert "neovim" in caplog.text
        # Verify official is not in the package list
        lines = [line for line in caplog.text.split("\n") if "official" in line]
        assert len(lines) == 0

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_filtered_by_source_flatpak(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering packages by flatpak source."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("discord", "flatpak:flathub", "flatpak", "2025-12-02"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="flatpak")
        cmd_list(args)

        # Should include flatpak packages only
        assert "discord" in caplog.text
        assert "vim" not in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_no_matching_filter(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test filtering when no packages match the filter."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
            _pkg("curl", "official", None, "2025-12-02"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source="COPR")
        cmd_list(args)

        # When no packages match filter, function returns early
        # No output is generated

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_with_categories(self, mock_tracker_cls: Mock, caplog: LogCaptureFixture) -> None:
        """Test listing packages with various categories."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", "editors", "2025-12-01"),
            _pkg("curl", "official", "core", "2025-12-02"),
            _pkg("lazygit", "COPR:user/repo", "dev", "2025-12-03"),
            _pkg("discord", "flatpak:flathub", "flatpak", "2025-12-04"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source=None)
        cmd_list(args)

        # All packages should be listed
        assert "vim" in caplog.text
        assert "editors" in caplog.text
        assert "curl" in caplog.text
        assert "core" in caplog.text
        assert "lazygit" in caplog.text
        assert "dev" in caplog.text
        assert "discord" in caplog.text
        assert "flatpak" in caplog.text

    @patch("aps.cli.commands.list.PackageTracker")
    def test_list_with_none_category(
        self, mock_tracker_cls: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test listing packages with None category displays N/A."""
        tracker = Mock()
        tracker.get_tracked_packages.return_value = [
            _pkg("vim", "official", None, "2025-12-01"),
        ]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace(source=None)
        cmd_list(args)

        # N/A should be shown for None category
        assert "N/A" in caplog.text
