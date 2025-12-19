# Import DistroInfo for use in tests
from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType

"""Tests for Visual Studio Code installer module."""

from unittest.mock import MagicMock, patch

from aps.installers.vscode import VSCodeInstaller


class TestVSCodeInstaller:
    """Tests for VS Code installer."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora_success(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test successful VS Code installation on Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro

        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_pm.update_cache.return_value = True
        mock_pm.is_available_in_official_repos.return_value = (
            False  # Not in official repos
        )
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()

        with (
            patch.object(
                installer, "_import_microsoft_gpg_rpm", return_value=True
            ),
            patch.object(installer, "_create_fedora_repo", return_value=True),
        ):
            result = installer.install()

        assert result is True
        mock_pm.is_available_in_official_repos.assert_called_once_with(
            "vscode"
        )
        mock_pm.update_cache.assert_called_once()
        mock_pm.install.assert_called_once_with(["vscode"])

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora_gpg_import_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on Fedora when GPG import fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro

        mock_pm = MagicMock()
        mock_pm.is_available_in_official_repos.return_value = False
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()

        with patch.object(
            installer, "_import_microsoft_gpg_rpm", return_value=False
        ):
            result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora_repo_creation_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on Fedora when repo creation fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro

        mock_pm = MagicMock()
        mock_pm.is_available_in_official_repos.return_value = False
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()

        with (
            patch.object(
                installer, "_import_microsoft_gpg_rpm", return_value=True
            ),
            patch.object(installer, "_create_fedora_repo", return_value=False),
        ):
            result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora_update_cache_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on Fedora when cache update fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro

        mock_pm = MagicMock()
        mock_pm.install.return_value = (True, "")
        mock_pm.update_cache.return_value = False
        mock_pm.is_available_in_official_repos.return_value = False
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()

        with (
            patch.object(
                installer, "_import_microsoft_gpg_rpm", return_value=True
            ),
            patch.object(installer, "_create_fedora_repo", return_value=True),
        ):
            result = installer.install()

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_fedora_install_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on Fedora when package install fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro

        mock_pm = MagicMock()
        mock_pm.install.return_value = (False, "Install failed")
        mock_pm.update_cache.return_value = True
        mock_pm.is_available_in_official_repos.return_value = False
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()

        with (
            patch.object(
                installer, "_import_microsoft_gpg_rpm", return_value=True
            ),
            patch.object(installer, "_create_fedora_repo", return_value=True),
        ):
            result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_arch_install_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on Arch when package install fails."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro

        mock_pm = MagicMock()
        mock_pm.install.return_value = (False, "Install failed")
        mock_pm.is_available_in_official_repos.return_value = False
        mock_get_pm.return_value = mock_pm

        installer = VSCodeInstaller()
        result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_unsupported_distro(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test VS Code installation on unsupported distribution."""
        unsupported_distro = DistroInfo(
            name="Unknown Linux",
            version="1.0",
            id="unknown",
            id_like=[],
            package_manager=PackageManagerType.UNKNOWN,
            family=DistroFamily.UNKNOWN,
        )
        mock_detect_distro.return_value = unsupported_distro
        mock_get_pm.return_value = MagicMock()

        installer = VSCodeInstaller()
        result = installer.install()

        assert result is False
