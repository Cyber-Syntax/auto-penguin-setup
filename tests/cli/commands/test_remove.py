"""Tests for remove command functionality.

Covers dry-run, successful removal, error handling, and Flatpak source-aware
removal.
"""

from argparse import Namespace
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.cli.commands.remove import cmd_remove
from aps.core.tracking import PackageRecord


class TestRemoveCommand:
    """Test remove command with various scenarios."""

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_single_package(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test removing a single package."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim"], setup=None, dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        mock_pm.remove.assert_called_once_with(["vim"], assume_yes=False)
        mock_tracker.remove_package.assert_called_once_with("vim")

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_multiple_packages(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test removing multiple packages."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim", "git", "curl"],
            setup=None,
            dry_run=False,
            noconfirm=False,
        )
        cmd_remove(args)

        # Each package should be removed individually
        assert mock_pm.remove.call_count == 3
        assert mock_tracker.remove_package.call_count == 3

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_dry_run(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test dry run mode doesn't actually remove."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        caplog.set_level("INFO")
        args = Namespace(
            packages=["vim"], setup=None, dry_run=True, noconfirm=False
        )
        cmd_remove(args)

        # Should not actually remove
        mock_pm.remove.assert_not_called()
        mock_tracker.remove_package.assert_not_called()
        assert "Would remove: vim" in caplog.text

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_with_noconfirm_flag(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test remove with --noconfirm flag."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim"], setup=None, dry_run=False, noconfirm=True
        )
        cmd_remove(args)

        # Should pass noconfirm=True to package manager
        call_args = mock_pm.remove.call_args
        assert call_args[1]["assume_yes"] is True

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_failure_no_tracking(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test that failed removal does not update tracking."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (False, "Package not found")
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim"], setup=None, dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        # Should not track if removal failed
        mock_tracker.remove_package.assert_not_called()

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_partial_success(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test removing multiple packages with partial success."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        # First succeeds, second fails, third succeeds
        mock_pm.remove.side_effect = [
            (True, None),
            (False, "Package not found"),
            (True, None),
        ]
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim", "git", "curl"],
            setup=None,
            dry_run=False,
            noconfirm=False,
        )
        cmd_remove(args)

        # Only successful removals should be tracked
        assert mock_tracker.remove_package.call_count == 2
        mock_tracker.remove_package.assert_any_call("vim")
        mock_tracker.remove_package.assert_any_call("curl")

    @patch("aps.cli.commands.remove.subprocess")
    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_flatpak_package(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test that Flatpak packages are removed via flatpak uninstall."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_get_pm.return_value = mock_pm

        flatpak_record = PackageRecord.create(
            name="signal",
            source="flatpak:flathub",
            mapped_name="org.signal.Signal",
        )

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = flatpak_record
        mock_tracker_cls.return_value = mock_tracker

        mock_subprocess.run.return_value = Mock(returncode=0)

        args = Namespace(
            packages=["signal"], setup=None, dry_run=False, noconfirm=True
        )
        cmd_remove(args)

        mock_subprocess.run.assert_called_once_with(
            ["flatpak", "uninstall", "org.signal.Signal", "--assumeyes"],
            check=False,
        )
        mock_tracker.remove_package.assert_called_once_with("signal")
        # Package manager remove should not be called for flatpak packages
        mock_pm.remove.assert_not_called()

    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_system_package(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
    ) -> None:
        """Test that system packages still use pm.remove()."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        system_record = PackageRecord.create(
            name="vim",
            source="official",
        )

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = system_record
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["vim"], setup=None, dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        mock_pm.remove.assert_called_once_with(["vim"], assume_yes=False)
        mock_tracker.remove_package.assert_called_once_with("vim")

    @patch("aps.cli.commands.remove.subprocess")
    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_mixed_sources(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test handling mixed source types in one command."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        system_record = PackageRecord.create(name="vim", source="official")
        flatpak_record = PackageRecord.create(
            name="signal",
            source="flatpak:flathub",
            mapped_name="org.signal.Signal",
        )

        mock_tracker = Mock()
        mock_tracker.get_package.side_effect = [system_record, flatpak_record]
        mock_tracker_cls.return_value = mock_tracker

        mock_subprocess.run.return_value = Mock(returncode=0)

        args = Namespace(
            packages=["vim", "signal"],
            setup=None,
            dry_run=False,
            noconfirm=False,
        )
        cmd_remove(args)

        # vim should use pm.remove
        mock_pm.remove.assert_called_once_with(["vim"], assume_yes=False)

        # signal should use flatpak uninstall
        mock_subprocess.run.assert_called_once_with(
            ["flatpak", "uninstall", "org.signal.Signal"],
            check=False,
        )

        # Both should be removed from tracking
        assert mock_tracker.remove_package.call_count == 2
        mock_tracker.remove_package.assert_any_call("vim")
        mock_tracker.remove_package.assert_any_call("signal")

    @patch("aps.cli.commands.remove.subprocess")
    @patch("aps.cli.commands.remove.PackageTracker")
    @patch("aps.cli.commands.remove.get_package_manager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_untracked_package(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test graceful handling of untracked packages."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.remove.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_tracker = Mock()
        mock_tracker.get_package.return_value = None
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(
            packages=["unknown-pkg"],
            setup=None,
            dry_run=False,
            noconfirm=False,
        )
        cmd_remove(args)

        # Untracked packages should fallback to pm.remove
        mock_pm.remove.assert_called_once_with(
            ["unknown-pkg"], assume_yes=False
        )
        # flatpak should not be invoked
        mock_subprocess.run.assert_not_called()
        # If removal succeeds, should be tracked
        mock_tracker.remove_package.assert_called_once_with("unknown-pkg")

    @patch("aps.cli.commands.remove.SetupManager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_setup_ollama(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_setup_manager_cls: Mock,
    ) -> None:
        """Test removing a setup component (ollama)."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_setup_manager = Mock()
        mock_setup_manager_cls.return_value = mock_setup_manager

        args = Namespace(
            packages=[], setup="ollama", dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        # SetupManager should be instantiated with correct distro
        mock_setup_manager_cls.assert_called_once_with(mock_distro)
        # remove_component should be called with the setup name
        mock_setup_manager.remove_component.assert_called_once_with("ollama")

    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_setup_dry_run(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test dry run for setup component removal."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        caplog.set_level("INFO")
        args = Namespace(
            packages=[], setup="ollama", dry_run=True, noconfirm=False
        )
        cmd_remove(args)

        # Should log dry-run message
        assert "Would remove setup component: ollama" in caplog.text
        # Should not instantiate SetupManager for dry-run
        mock_detect_distro.assert_not_called()

    @patch("aps.cli.commands.remove.SetupManager")
    @patch("aps.cli.commands.remove.detect_distro")
    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_setup_failure(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_setup_manager_cls: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test error handling when setup component removal fails."""
        from aps.core.setup import SetupError

        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_detect_distro.return_value = mock_distro

        mock_setup_manager = Mock()
        mock_setup_manager.remove_component.side_effect = SetupError(
            "Unknown component: ollama"
        )
        mock_setup_manager_cls.return_value = mock_setup_manager

        caplog.set_level("ERROR")
        args = Namespace(
            packages=[], setup="ollama", dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        # Should log the error message
        assert "Failed to remove setup component ollama" in caplog.text
        assert "Unknown component: ollama" in caplog.text

    @patch("aps.cli.commands.remove.ensure_sudo")
    def test_remove_no_packages_or_setup(
        self,
        mock_ensure_sudo: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test error when neither packages nor setup component is specified."""
        caplog.set_level("ERROR")
        args = Namespace(
            packages=[], setup=None, dry_run=False, noconfirm=False
        )
        cmd_remove(args)

        # Should log error and return early
        assert "No packages or setup component specified" in caplog.text
