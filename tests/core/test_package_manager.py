"""Tests for package manager abstraction module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pytest import LogCaptureFixture

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.core.package_manager import (
    AptManager,
    DnfManager,
    PackageManagerError,
    PacmanManager,
    get_package_manager,
)


class TestPackageManagerError:
    """Test PackageManagerError exception."""

    def test_error_is_exception(self) -> None:
        """Test that PackageManagerError is an Exception subclass."""
        error = PackageManagerError("Test error")
        assert isinstance(error, Exception)

    def test_error_message(self) -> None:
        """Test error message is preserved."""
        msg = "Package installation failed"
        error = PackageManagerError(msg)
        assert str(error) == msg


class TestDnfManager:
    """Test DnfManager for Fedora-based distributions."""

    @pytest.fixture
    def fedora_distro(self) -> DistroInfo:
        """Create a Fedora DistroInfo for testing."""
        return DistroInfo(
            id="fedora",
            id_like=[],
            name="Fedora Linux",
            version="39",
            family=DistroFamily.FEDORA,
            package_manager=PackageManagerType.DNF,
        )

    @pytest.fixture
    def dnf_manager(self, fedora_distro: DistroInfo) -> DnfManager:
        """Create a DnfManager instance for testing."""
        return DnfManager(fedora_distro)

    def test_init(
        self, dnf_manager: DnfManager, fedora_distro: DistroInfo
    ) -> None:
        """Test DnfManager initialization."""
        assert dnf_manager.distro == fedora_distro

    @patch("aps.core.package_manager.run_privileged")
    def test_install_single_package(
        self,
        mock_run: Mock,
        dnf_manager: DnfManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test installing a single package."""
        caplog.set_level("INFO")
        mock_run.return_value = Mock(returncode=0)

        success, error = dnf_manager.install(["vim"])

        assert success is True
        assert error == ""
        mock_run.assert_called_once()

    @patch("aps.core.package_manager.run_privileged")
    def test_install_multiple_packages(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test installing multiple packages."""
        mock_run.return_value = Mock(returncode=0)

        success, error = dnf_manager.install(["vim", "git", "neovim"])

        assert success is True
        assert error == ""
        call_args = mock_run.call_args[0][0]
        assert "vim" in call_args
        assert "git" in call_args
        assert "neovim" in call_args

    @patch("aps.core.package_manager.run_privileged")
    def test_install_with_assume_yes(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test install with assume_yes flag."""
        mock_run.return_value = Mock(returncode=0)

        dnf_manager.install(["vim"], assume_yes=True)

        call_args = mock_run.call_args[0][0]
        assert "-y" in call_args

    @patch("aps.core.package_manager.run_privileged")
    def test_install_failure(
        self,
        mock_run: Mock,
        dnf_manager: DnfManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test install failure handling."""
        mock_run.return_value = Mock(returncode=1)

        success, error = dnf_manager.install(["nonexistent"])

        assert success is False
        assert error != ""
        assert "Failed to install packages" in caplog.text

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_single_package(
        self,
        mock_run: Mock,
        dnf_manager: DnfManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test removing a single package."""
        mock_run.return_value = Mock(returncode=0)

        success, error = dnf_manager.remove(["vim"])

        assert success is True
        assert error == ""
        call_args = mock_run.call_args[0][0]
        assert "remove" in call_args
        assert "vim" in call_args

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_multiple_packages(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test removing multiple packages."""
        mock_run.return_value = Mock(returncode=0)

        success, error = dnf_manager.remove(["vim", "nano"])

        assert success is True
        call_args = mock_run.call_args[0][0]
        assert "vim" in call_args
        assert "nano" in call_args

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_failure(
        self,
        mock_run: Mock,
        dnf_manager: DnfManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test remove failure handling."""
        mock_run.return_value = Mock(returncode=1)

        success, error = dnf_manager.remove(["nonexistent"])

        assert success is False
        assert "Failed to remove packages" in caplog.text

    @patch("subprocess.run")
    def test_search_packages(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test searching for packages."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="vim.x86_64 : Highly configurable text editor\nnano.x86_64 : A small text editor",
        )

        results = dnf_manager.search("editor")

        assert len(results) == 2
        assert "vim.x86_64" in results
        assert "nano.x86_64" in results

    @patch("subprocess.run")
    def test_search_no_results(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test search with no results."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        results = dnf_manager.search("nonexistent-package-xyz")

        assert results == []

    @patch("subprocess.run")
    def test_is_installed_true(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test checking if installed package exists."""
        mock_run.return_value = Mock(returncode=0)

        assert dnf_manager.is_installed("vim") is True

    @patch("subprocess.run")
    def test_is_installed_false(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test checking if non-installed package exists."""
        mock_run.return_value = Mock(returncode=1)

        assert dnf_manager.is_installed("nonexistent") is False

    @patch("aps.core.package_manager.run_privileged")
    def test_update_cache(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test updating package manager cache."""
        mock_run.return_value = Mock(returncode=0)

        assert dnf_manager.update_cache() is True

    @patch("aps.core.package_manager.run_privileged")
    def test_update_cache_failure(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test update cache failure."""
        mock_run.return_value = Mock(returncode=1)

        assert dnf_manager.update_cache() is False

    @patch("subprocess.run")
    def test_is_available_in_official_repos_true(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test checking package availability in official repos."""
        # First call: dnf repoquery (found)
        # Second call: dnf list (official, no copr)
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="vim-1.0-1.fc39.x86_64\n",
                text="vim-1.0-1.fc39.x86_64",
            ),
            Mock(
                returncode=0,
                stdout="fedora     vim-1.0-1.fc39.x86_64",
                text="fedora     vim-1.0-1.fc39.x86_64",
            ),
        ]

        assert dnf_manager.is_available_in_official_repos("vim") is True

    @patch("subprocess.run")
    def test_is_available_in_official_repos_false_copr(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test checking package availability in official repos (in COPR)."""
        # First call: dnf repoquery (found)
        # Second call: dnf list (from COPR)
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="package-1.0-1.fc39.x86_64\n",
                text="package-1.0-1.fc39.x86_64",
            ),
            Mock(
                returncode=0,
                stdout="copr: package-1.0-1.fc39.x86_64",
                text="copr: package-1.0-1.fc39.x86_64",
            ),
        ]

        assert dnf_manager.is_available_in_official_repos("package") is False

    @patch("subprocess.run")
    def test_is_available_in_official_repos_not_found(
        self, mock_run: Mock, dnf_manager: DnfManager
    ) -> None:
        """Test checking package not available in any repos."""
        mock_run.return_value = Mock(returncode=1, stdout="", text="")

        assert (
            dnf_manager.is_available_in_official_repos("nonexistent") is False
        )


class TestPacmanManager:
    """Test PacmanManager for Arch-based distributions."""

    @pytest.fixture
    def arch_distro(self) -> DistroInfo:
        """Create an Arch DistroInfo for testing."""
        return DistroInfo(
            id="arch",
            id_like=[],
            name="Arch Linux",
            version="",
            family=DistroFamily.ARCH,
            package_manager=PackageManagerType.PACMAN,
        )

    @pytest.fixture
    def pacman_manager(self, arch_distro: DistroInfo) -> PacmanManager:
        """Create a PacmanManager instance for testing."""
        return PacmanManager(arch_distro)

    def test_init(
        self, pacman_manager: PacmanManager, arch_distro: DistroInfo
    ) -> None:
        """Test PacmanManager initialization."""
        assert pacman_manager.distro == arch_distro

    @patch("shutil.which")
    def test_detect_aur_helper_paru(self, mock_which: Mock) -> None:
        """Test AUR helper detection (paru found)."""
        mock_which.side_effect = (
            lambda cmd: "/usr/bin/paru" if cmd == "paru" else None
        )
        manager = PacmanManager(
            DistroInfo(
                id="arch",
                id_like=[],
                name="Arch Linux",
                version="",
                family=DistroFamily.ARCH,
                package_manager=PackageManagerType.PACMAN,
            )
        )
        assert manager.aur_helper == "paru"

    @patch("shutil.which")
    def test_detect_aur_helper_yay(self, mock_which: Mock) -> None:
        """Test AUR helper detection (yay found)."""
        mock_which.side_effect = (
            lambda cmd: "/usr/bin/yay" if cmd == "yay" else None
        )
        manager = PacmanManager(
            DistroInfo(
                id="arch",
                id_like=[],
                name="Arch Linux",
                version="",
                family=DistroFamily.ARCH,
                package_manager=PackageManagerType.PACMAN,
            )
        )
        assert manager.aur_helper == "yay"

    @patch("shutil.which")
    def test_detect_aur_helper_none(self, mock_which: Mock) -> None:
        """Test AUR helper detection (none found)."""
        mock_which.return_value = None
        manager = PacmanManager(
            DistroInfo(
                id="arch",
                id_like=[],
                name="Arch Linux",
                version="",
                family=DistroFamily.ARCH,
                package_manager=PackageManagerType.PACMAN,
            )
        )
        assert manager.aur_helper is None

    @patch("aps.core.package_manager.run_privileged")
    def test_install_single_package(
        self,
        mock_run: Mock,
        pacman_manager: PacmanManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test installing a single package."""
        caplog.set_level("INFO")
        mock_run.return_value = Mock(returncode=0)

        success, error = pacman_manager.install(["vim"])

        assert success is True
        assert error == ""

    @patch("aps.core.package_manager.run_privileged")
    def test_install_with_assume_yes(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test install with assume_yes flag."""
        mock_run.return_value = Mock(returncode=0)

        pacman_manager.install(["vim"], assume_yes=True)

        call_args = mock_run.call_args[0][0]
        assert "--noconfirm" in call_args

    @patch("subprocess.run")
    def test_install_aur_packages(
        self,
        mock_run: Mock,
        pacman_manager: PacmanManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test installing AUR packages."""
        caplog.set_level("INFO")
        pacman_manager.aur_helper = "paru"
        mock_run.return_value = Mock(returncode=0)

        result = pacman_manager.install_aur(["yay"])

        assert result is True

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_single_package(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test removing a single package."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        success, error = pacman_manager.remove(["vim"])

        assert success is True
        assert error == ""

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_with_assume_yes(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test remove with assume_yes flag."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        pacman_manager.remove(["vim"], assume_yes=True)

        call_args = mock_run.call_args[0][0]
        assert "--noconfirm" in call_args

    @patch("subprocess.run")
    def test_search_packages(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test searching for packages."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="extra/vim 9.0.1000-1\ncore/vi 4.0-1\n",
            text="extra/vim 9.0.1000-1\ncore/vi 4.0-1\n",
        )

        results = pacman_manager.search("vi")

        assert "vim" in results
        assert "vi" in results

    @patch("subprocess.run")
    def test_is_installed_true(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test checking if installed package exists."""
        mock_run.return_value = Mock(returncode=0)

        assert pacman_manager.is_installed("vim") is True

    @patch("subprocess.run")
    def test_is_installed_false(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test checking if non-installed package exists."""
        mock_run.return_value = Mock(returncode=1)

        assert pacman_manager.is_installed("nonexistent") is False

    @patch("aps.core.package_manager.run_privileged")
    def test_update_cache(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test updating package manager cache."""
        mock_run.return_value = Mock(returncode=0)

        assert pacman_manager.update_cache() is True

    @patch("subprocess.run")
    def test_is_available_in_official_repos_true(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test checking package availability in official repos."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="extra/vim 9.0.1000-1\n",
            text="extra/vim 9.0.1000-1\n",
        )

        assert pacman_manager.is_available_in_official_repos("vim") is True

    @patch("subprocess.run")
    def test_is_available_in_official_repos_false(
        self, mock_run: Mock, pacman_manager: PacmanManager
    ) -> None:
        """Test checking non-existent package."""
        mock_run.return_value = Mock(returncode=1, stdout="", text="")

        assert (
            pacman_manager.is_available_in_official_repos("nonexistent")
            is False
        )


class TestAptManager:
    """Test AptManager for Debian-based distributions."""

    @pytest.fixture
    def debian_distro(self) -> DistroInfo:
        """Create a Debian DistroInfo for testing."""
        return DistroInfo(
            id="debian",
            id_like=[],
            name="Debian GNU/Linux",
            version="12",
            family=DistroFamily.DEBIAN,
            package_manager=PackageManagerType.APT,
        )

    @pytest.fixture
    def apt_manager(self, debian_distro: DistroInfo) -> AptManager:
        """Create an AptManager instance for testing."""
        return AptManager(debian_distro)

    def test_init(
        self, apt_manager: AptManager, debian_distro: DistroInfo
    ) -> None:
        """Test AptManager initialization."""
        assert apt_manager.distro == debian_distro

    @patch("aps.core.package_manager.run_privileged")
    def test_install_single_package(
        self,
        mock_run: Mock,
        apt_manager: AptManager,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test installing a single package."""
        caplog.set_level("INFO")
        mock_run.return_value = Mock(returncode=0)

        success, error = apt_manager.install(["vim"])

        assert success is True
        assert error == ""

    @patch("aps.core.package_manager.run_privileged")
    def test_install_with_assume_yes(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test install with assume_yes flag."""
        mock_run.return_value = Mock(returncode=0)

        apt_manager.install(["vim"], assume_yes=True)

        call_args = mock_run.call_args[0][0]
        assert "-y" in call_args

    @patch("aps.core.package_manager.run_privileged")
    def test_remove_single_package(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test removing a single package."""
        mock_run.return_value = Mock(returncode=0)

        success, error = apt_manager.remove(["vim"])

        assert success is True
        assert error == ""

    @patch("subprocess.run")
    def test_search_packages(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test searching for packages."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="vim - Vi IMproved\nvim-common - Common files\n",
            text="vim - Vi IMproved\nvim-common - Common files\n",
        )

        results = apt_manager.search("vim")

        assert "vim" in results
        assert "vim-common" in results

    @patch("subprocess.run")
    def test_is_installed_true(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test checking if installed package exists."""
        mock_run.return_value = Mock(returncode=0)

        assert apt_manager.is_installed("vim") is True

    @patch("subprocess.run")
    def test_is_installed_false(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test checking if non-installed package exists."""
        mock_run.return_value = Mock(returncode=1)

        assert apt_manager.is_installed("nonexistent") is False

    @patch("aps.core.package_manager.run_privileged")
    def test_update_cache(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test updating package manager cache."""
        mock_run.return_value = Mock(returncode=0)

        assert apt_manager.update_cache() is True

    @patch("subprocess.run")
    def test_is_available_in_official_repos_true(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test checking package availability in official repos."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Candidate: 9.0.1000-1\n",
            text="Candidate: 9.0.1000-1\n",
        )

        assert apt_manager.is_available_in_official_repos("vim") is True

    @patch("subprocess.run")
    def test_is_available_in_official_repos_false(
        self, mock_run: Mock, apt_manager: AptManager
    ) -> None:
        """Test checking non-existent package."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Candidate: (none)\n",
            text="Candidate: (none)\n",
        )

        assert (
            apt_manager.is_available_in_official_repos("nonexistent") is False
        )


class TestGetPackageManager:
    """Test get_package_manager factory function."""

    def test_get_dnf_manager(self) -> None:
        """Test factory returns DnfManager for Fedora."""
        distro = DistroInfo(
            id="fedora",
            id_like=[],
            name="Fedora Linux",
            version="39",
            family=DistroFamily.FEDORA,
            package_manager=PackageManagerType.DNF,
        )

        manager = get_package_manager(distro)

        assert isinstance(manager, DnfManager)
        assert manager.distro == distro

    def test_get_pacman_manager(self) -> None:
        """Test factory returns PacmanManager for Arch."""
        distro = DistroInfo(
            id="arch",
            id_like=[],
            name="Arch Linux",
            version="",
            family=DistroFamily.ARCH,
            package_manager=PackageManagerType.PACMAN,
        )

        manager = get_package_manager(distro)

        assert isinstance(manager, PacmanManager)
        assert manager.distro == distro

    def test_get_apt_manager(self) -> None:
        """Test factory returns AptManager for Debian."""
        distro = DistroInfo(
            id="debian",
            id_like=[],
            name="Debian GNU/Linux",
            version="12",
            family=DistroFamily.DEBIAN,
            package_manager=PackageManagerType.APT,
        )

        manager = get_package_manager(distro)

        assert isinstance(manager, AptManager)
        assert manager.distro == distro

    def test_get_unsupported_distro(self) -> None:
        """Test factory raises error for unsupported distribution."""
        # Create a mock with an unsupported family
        distro = MagicMock(spec=DistroInfo)
        distro.family = "unsupported"

        with pytest.raises(
            ValueError, match="Unsupported distribution family"
        ):
            get_package_manager(distro)
