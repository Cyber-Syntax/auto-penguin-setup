"""Tests for status command functionality.

Verifies distribution info and package counts by source.
"""

from argparse import Namespace
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.cli.commands.status import cmd_status


class TestStatusCommand:
    """Test status command with various scenarios."""

    @patch("aps.cli.commands.status.PackageTracker")
    @patch("aps.cli.commands.status.detect_distro")
    def test_status_reports_distro_info(
        self,
        mock_detect_distro: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that status reports distribution information."""
        distro = Mock()
        distro.name = "Fedora"
        distro.version = "41"
        pkgmgr = Mock()
        pkgmgr.value = "dnf"
        distro.package_manager = pkgmgr
        mock_detect_distro.return_value = distro

        tracker = Mock()
        tracker.get_tracked_packages.return_value = []
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace()
        cmd_status(args)

        assert "Distribution: Fedora 41" in caplog.text
        assert "Package Manager: dnf" in caplog.text

    @patch("aps.cli.commands.status.PackageTracker")
    @patch("aps.cli.commands.status.detect_distro")
    def test_status_counts_packages(
        self,
        mock_detect_distro: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that status counts tracked packages."""
        distro = Mock()
        distro.name = "Fedora"
        distro.version = "41"
        pkgmgr = Mock()
        pkgmgr.value = "dnf"
        distro.package_manager = pkgmgr
        mock_detect_distro.return_value = distro

        # Create mock packages
        pkg1 = Mock()
        pkg1.name = "vim"
        pkg1.source = "official"
        pkg1.installed_at = "2025-12-01"

        pkg2 = Mock()
        pkg2.name = "lazygit"
        pkg2.source = "COPR:user/repo"
        pkg2.installed_at = "2025-12-02"

        pkg3 = Mock()
        pkg3.name = "discord"
        pkg3.source = "flatpak:flathub"
        pkg3.installed_at = "2025-12-03"

        tracker = Mock()
        tracker.get_tracked_packages.return_value = [pkg1, pkg2, pkg3]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace()
        cmd_status(args)

        assert "Tracked Packages: 3" in caplog.text
        assert "By Source:" in caplog.text

    @patch("aps.cli.commands.status.PackageTracker")
    @patch("aps.cli.commands.status.detect_distro")
    def test_status_sources_breakdown(
        self,
        mock_detect_distro: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that status breaks down packages by source."""
        distro = Mock()
        distro.name = "Fedora"
        distro.version = "41"
        pkgmgr = Mock()
        pkgmgr.value = "dnf"
        distro.package_manager = pkgmgr
        mock_detect_distro.return_value = distro

        # Multiple packages per source
        pkg1 = Mock()
        pkg1.source = "official"

        pkg2 = Mock()
        pkg2.source = "COPR:user/repo"

        pkg3 = Mock()
        pkg3.source = "COPR:another/repo"

        pkg4 = Mock()
        pkg4.source = "official"

        tracker = Mock()
        tracker.get_tracked_packages.return_value = [pkg1, pkg2, pkg3, pkg4]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace()
        cmd_status(args)

        # Should show count for each source prefix
        assert "official: 2" in caplog.text
        assert "COPR: 2" in caplog.text

    @patch("aps.cli.commands.status.PackageTracker")
    @patch("aps.cli.commands.status.detect_distro")
    def test_status_no_tracked_packages(
        self,
        mock_detect_distro: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test status when no packages are tracked."""
        distro = Mock()
        distro.name = "Arch"
        distro.version = "rolling"
        pkgmgr = Mock()
        pkgmgr.value = "pacman"
        distro.package_manager = pkgmgr
        mock_detect_distro.return_value = distro

        tracker = Mock()
        tracker.get_tracked_packages.return_value = []
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace()
        cmd_status(args)

        assert "Tracked Packages: 0" in caplog.text

    @patch("aps.cli.commands.status.PackageTracker")
    @patch("aps.cli.commands.status.detect_distro")
    def test_status_compound_sources(
        self,
        mock_detect_distro: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test status correctly extracts source prefix from compound sources."""
        distro = Mock()
        distro.name = "Debian"
        distro.version = "bookworm"
        pkgmgr = Mock()
        pkgmgr.value = "apt"
        distro.package_manager = pkgmgr
        mock_detect_distro.return_value = distro

        pkg1 = Mock()
        pkg1.source = "PPA:user/repo"

        pkg2 = Mock()
        pkg2.source = "PPA:another/repo"

        pkg3 = Mock()
        pkg3.source = "official"

        tracker = Mock()
        tracker.get_tracked_packages.return_value = [pkg1, pkg2, pkg3]
        mock_tracker_cls.return_value = tracker

        caplog.set_level("INFO")
        args = Namespace()
        cmd_status(args)

        # Should correctly count PPA sources
        assert "PPA: 2" in caplog.text
        assert "official: 1" in caplog.text
