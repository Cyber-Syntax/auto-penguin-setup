"""Tests for install command functionality."""

from argparse import Namespace
from unittest.mock import Mock, patch

from _pytest.logging import LogCaptureFixture

from aps.cli.commands.install import cmd_install
from aps.core.distro import DistroFamily


class TestInstallCommand:
    """Test install command with various scenarios."""

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_single_official_package(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test installing a single official package."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.version = "41"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "vim"
        mapping.mapped_name = "vim"
        mapping.source = "official"
        mapping.is_official = True
        mapping.is_copr = False
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["vim"], dry_run=False, noconfirm=False)
        cmd_install(args)

        mock_pm.install.assert_called_once()
        mock_tracker.track_install.assert_called_once()

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_dry_run(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test dry run mode doesn't actually install."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "vim"
        mapping.mapped_name = "vim"
        mapping.source = "official"
        mapping.is_official = True
        mapping.is_copr = False
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        caplog.set_level("INFO")
        args = Namespace(packages=["vim"], dry_run=True, noconfirm=False)
        cmd_install(args)

        # In dry-run, should not actually install
        mock_pm.install.assert_not_called()
        mock_tracker.track_install.assert_not_called()
        assert "Would install: vim" in caplog.text

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_multiple_packages(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test installing multiple packages."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()

        def create_mapping(name: str) -> Mock:
            mapping = Mock()
            mapping.original_name = name
            mapping.mapped_name = name
            mapping.source = "official"
            mapping.is_official = True
            mapping.is_copr = False
            mapping.is_aur = False
            mapping.is_ppa = False
            mapping.is_flatpak = False
            mapping.category = None
            return mapping

        mappings = [create_mapping("vim"), create_mapping("git"), create_mapping("curl")]
        mock_mapper.mappings = mappings
        mock_mapper.map_package.side_effect = [mappings[0], mappings[1], mappings[2]]
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.side_effect = [
            mappings[0],
            mappings[1],
            mappings[2],
        ]
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["vim", "git", "curl"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # Should install all three packages
        call_args = mock_pm.install.call_args
        installed_packages = call_args[0][0]
        assert len(installed_packages) == 3
        assert "vim" in installed_packages
        assert "git" in installed_packages
        assert "curl" in installed_packages

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.load_category_packages")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_from_category(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_load_category: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test installing from a category."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        # Category contains vim and neovim
        mock_load_category.return_value = ["vim", "neovim"]

        mock_mapper = Mock()

        def create_mapping(name: str) -> Mock:
            mapping = Mock()
            mapping.original_name = name
            mapping.mapped_name = name
            mapping.source = "official"
            mapping.is_official = True
            mapping.is_copr = False
            mapping.is_aur = False
            mapping.is_ppa = False
            mapping.is_flatpak = False
            mapping.category = "editors"
            return mapping

        mappings = [create_mapping("vim"), create_mapping("neovim")]
        mock_mapper.mappings = mappings
        mock_mapper.map_package.side_effect = mappings
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.side_effect = mappings
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["@editors"], dry_run=False, noconfirm=False)
        cmd_install(args)

        mock_load_category.assert_called_once_with("editors")
        assert mock_pm.install.called

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_failure_returns_early(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test that installation failure returns early without tracking."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (False, "Installation failed")
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "vim"
        mapping.mapped_name = "vim"
        mapping.source = "official"
        mapping.is_official = True
        mapping.is_copr = False
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["vim"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # Should not track if install failed
        mock_tracker.track_install.assert_not_called()

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_install_with_noconfirm_flag(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test install with --noconfirm flag."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "vim"
        mapping.mapped_name = "vim"
        mapping.source = "official"
        mapping.is_official = True
        mapping.is_copr = False
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["vim"], dry_run=False, noconfirm=True)
        cmd_install(args)

        # Should pass noconfirm=True to package manager
        call_args = mock_pm.install.call_args
        assert call_args[1]["assume_yes"] is True

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_copr_repo_enablement_fedora(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test COPR repo is enabled on Fedora."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "lazygit"
        mapping.mapped_name = "lazygit"
        mapping.source = "COPR:user/repo"
        mapping.is_official = False
        mapping.is_copr = True
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mapping.get_repo_name.return_value = "user/repo"
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.is_copr_enabled.return_value = False
        mock_repo_mgr.enable_copr.return_value = True
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["lazygit"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # COPR repo should be enabled
        mock_repo_mgr.enable_copr.assert_called_once_with("user/repo")

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_aur_package_installation_arch(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test AUR package installation on Arch."""
        mock_distro = Mock()
        mock_distro.name = "Arch"
        mock_distro.family = DistroFamily.ARCH
        mock_detect_distro.return_value = mock_distro

        from aps.core.package_manager import PacmanManager

        mock_pm = Mock(spec=PacmanManager)
        mock_pm.install_aur.return_value = True
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "lazygit"
        mapping.mapped_name = "lazygit"
        mapping.source = "AUR:lazygit"
        mapping.is_official = False
        mapping.is_copr = False
        mapping.is_aur = True
        mapping.is_ppa = False
        mapping.is_flatpak = False
        mapping.category = None
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["lazygit"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # AUR package should be installed
        mock_pm.install_aur.assert_called_once()

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_flatpak_package_installation(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test flatpak package installation."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()
        mapping = Mock()
        mapping.original_name = "discord"
        mapping.mapped_name = "com.discord.Discord"
        mapping.source = "flatpak:flathub"
        mapping.is_official = False
        mapping.is_copr = False
        mapping.is_aur = False
        mapping.is_ppa = False
        mapping.is_flatpak = True
        mapping.category = "flatpak"
        mapping.get_repo_name.return_value = "flathub"
        mock_mapper.mappings = [mapping]
        mock_mapper.map_package.return_value = mapping
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.is_flatpak_remote_enabled.return_value = True
        mock_repo_mgr.check_official_before_enabling.return_value = mapping
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        mock_subprocess.return_value = Mock(returncode=0)

        args = Namespace(packages=["discord"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # Flatpak should be installed via subprocess
        assert mock_subprocess.called

    @patch("aps.cli.commands.install.subprocess.run")
    @patch("aps.cli.commands.install.PackageTracker")
    @patch("aps.cli.commands.install.RepositoryManager")
    @patch("aps.cli.commands.install.PackageMapper")
    @patch("aps.cli.commands.install.get_package_manager")
    @patch("aps.cli.commands.install.detect_distro")
    @patch("aps.cli.commands.install.ensure_sudo")
    def test_mixed_package_sources(
        self,
        mock_ensure_sudo: Mock,
        mock_detect_distro: Mock,
        mock_get_pm: Mock,
        mock_mapper_cls: Mock,
        mock_repo_mgr_cls: Mock,
        mock_tracker_cls: Mock,
        mock_subprocess: Mock,
    ) -> None:
        """Test installing packages from mixed sources."""
        mock_distro = Mock()
        mock_distro.name = "Fedora"
        mock_distro.family = DistroFamily.FEDORA
        mock_detect_distro.return_value = mock_distro

        mock_pm = Mock()
        mock_pm.install.return_value = (True, None)
        mock_get_pm.return_value = mock_pm

        mock_mapper = Mock()

        def create_mapping(name: str, source: str, is_official: bool, is_copr: bool) -> Mock:
            mapping = Mock()
            mapping.original_name = name
            mapping.mapped_name = name
            mapping.source = source
            mapping.is_official = is_official
            mapping.is_copr = is_copr
            mapping.is_aur = False
            mapping.is_ppa = False
            mapping.is_flatpak = False
            mapping.category = None
            if is_copr:
                mapping.get_repo_name.return_value = "user/repo"
            return mapping

        mappings = [
            create_mapping("vim", "official", True, False),
            create_mapping("lazygit", "COPR:user/repo", False, True),
        ]
        mock_mapper.mappings = mappings
        mock_mapper.map_package.side_effect = mappings
        mock_mapper_cls.return_value = mock_mapper

        mock_repo_mgr = Mock()
        mock_repo_mgr.is_copr_enabled.return_value = False
        mock_repo_mgr.enable_copr.return_value = True
        mock_repo_mgr.check_official_before_enabling.side_effect = mappings
        mock_repo_mgr_cls.return_value = mock_repo_mgr

        mock_tracker = Mock()
        mock_tracker_cls.return_value = mock_tracker

        args = Namespace(packages=["vim", "lazygit"], dry_run=False, noconfirm=False)
        cmd_install(args)

        # Both official and COPR should be processed
        mock_repo_mgr.enable_copr.assert_called_once()
        mock_pm.install.assert_called_once()
