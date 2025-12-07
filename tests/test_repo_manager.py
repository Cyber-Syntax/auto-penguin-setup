"""Tests for aps.core.repo_manager module."""

from unittest.mock import Mock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.core.package_manager import PackageManager, PackageManagerError, PacmanManager
from aps.core.repo_manager import RepositoryManager


class TestRepositoryManager:
    """Tests for RepositoryManager class."""

    @pytest.fixture
    def fedora_distro(self) -> DistroInfo:
        """Create a Fedora distro info instance."""
        return DistroInfo(
            name="fedora",
            version="40",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )

    @pytest.fixture
    def arch_distro(self) -> DistroInfo:
        """Create an Arch distro info instance."""
        return DistroInfo(
            name="arch",
            version="rolling",
            id="arch",
            id_like=[],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )

    @pytest.fixture
    def debian_distro(self) -> DistroInfo:
        """Create a Debian distro info instance."""
        return DistroInfo(
            name="ubuntu",
            version="22.04",
            id="ubuntu",
            id_like=["debian"],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )

    def test_init(self, fedora_distro: DistroInfo) -> None:
        """Test repository manager initialization."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        assert repo_mgr.distro == fedora_distro
        assert repo_mgr.pm == pm

    def test_enable_copr_success(self, fedora_distro: DistroInfo) -> None:
        """Test enabling COPR repository successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.enable_copr("user/repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "dnf", "copr", "enable", "-y", "user/repo"],
                capture_output=True,
            )

    def test_enable_copr_non_fedora(self, arch_distro: DistroInfo) -> None:
        """Test enabling COPR on non-Fedora raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with pytest.raises(PackageManagerError, match="COPR is only available on Fedora"):
            repo_mgr.enable_copr("user/repo")

    def test_disable_copr_success(self, fedora_distro: DistroInfo) -> None:
        """Test disabling COPR repository successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.disable_copr("user/repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "dnf", "copr", "disable", "-y", "user/repo"],
                capture_output=True,
            )

    def test_disable_copr_non_fedora(self, debian_distro: DistroInfo) -> None:
        """Test disabling COPR on non-Fedora raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(debian_distro, pm)

        with pytest.raises(PackageManagerError, match="COPR is only available on Fedora"):
            repo_mgr.disable_copr("user/repo")

    def test_is_copr_enabled_true(self, fedora_distro: DistroInfo) -> None:
        """Test checking if COPR is enabled returns True."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="copr:copr.fedorainfracloud.org:user:repo\n",
            )
            result = repo_mgr.is_copr_enabled("user/repo")

            assert result is True

    def test_is_copr_enabled_false(self, fedora_distro: DistroInfo) -> None:
        """Test checking if COPR is enabled returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = repo_mgr.is_copr_enabled("user/repo")

            assert result is False

    def test_is_copr_enabled_non_fedora(self, arch_distro: DistroInfo) -> None:
        """Test checking COPR on non-Fedora returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        result = repo_mgr.is_copr_enabled("user/repo")
        assert result is False

    def test_install_aur_package_success(self, arch_distro: DistroInfo) -> None:
        """Test installing AUR package successfully."""
        pm = Mock(spec=PacmanManager)
        pm.install_aur.return_value = True
        repo_mgr = RepositoryManager(arch_distro, pm)

        result = repo_mgr.install_aur_package("yay")

        assert result is True
        pm.install_aur.assert_called_once_with(["yay"])

    def test_install_aur_package_non_arch(self, fedora_distro: DistroInfo) -> None:
        """Test installing AUR on non-Arch raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with pytest.raises(PackageManagerError, match="AUR is only available on Arch"):
            repo_mgr.install_aur_package("yay")

    def test_install_aur_package_wrong_pm(self, arch_distro: DistroInfo) -> None:
        """Test installing AUR with wrong package manager raises error."""
        pm = Mock(spec=PackageManager)  # Not PacmanManager
        repo_mgr = RepositoryManager(arch_distro, pm)

        with pytest.raises(PackageManagerError, match="Package manager is not PacmanManager"):
            repo_mgr.install_aur_package("yay")

    def test_add_ppa_success(self, debian_distro: DistroInfo) -> None:
        """Test adding PPA successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(debian_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.add_ppa("user/repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "add-apt-repository", "-y", "ppa:user/repo"],
                capture_output=True,
            )
            pm.update_cache.assert_called_once()

    def test_add_ppa_failure(self, debian_distro: DistroInfo) -> None:
        """Test adding PPA failure."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(debian_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            result = repo_mgr.add_ppa("user/repo")

            assert result is False
            pm.update_cache.assert_not_called()

    def test_add_ppa_non_debian(self, fedora_distro: DistroInfo) -> None:
        """Test adding PPA on non-Debian raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with pytest.raises(PackageManagerError, match="PPA is only available on Debian/Ubuntu"):
            repo_mgr.add_ppa("user/repo")

    def test_remove_ppa_success(self, debian_distro: DistroInfo) -> None:
        """Test removing PPA successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(debian_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.remove_ppa("user/repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "add-apt-repository", "-y", "--remove", "ppa:user/repo"],
                capture_output=True,
            )

    def test_remove_ppa_non_debian(self, arch_distro: DistroInfo) -> None:
        """Test removing PPA on non-Debian raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with pytest.raises(PackageManagerError, match="PPA is only available on Debian/Ubuntu"):
            repo_mgr.remove_ppa("user/repo")

    def test_enable_flatpak_remote_flathub(self, fedora_distro: DistroInfo) -> None:
        """Test enabling Flathub remote."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.enable_flatpak_remote("flathub")

            assert result is True
            mock_run.assert_called_once_with(
                [
                    "sudo",
                    "flatpak",
                    "remote-add",
                    "--if-not-exists",
                    "flathub",
                    "https://flathub.org/repo/flathub.flatpakrepo",
                ],
                capture_output=True,
            )

    def test_enable_flatpak_remote_custom(self, fedora_distro: DistroInfo) -> None:
        """Test enabling custom Flatpak remote."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.enable_flatpak_remote(
                "custom", "https://example.com/repo.flatpakrepo"
            )

            assert result is True

    def test_enable_flatpak_remote_no_url(self, fedora_distro: DistroInfo) -> None:
        """Test enabling Flatpak remote without URL raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with pytest.raises(ValueError, match="remote_url is required"):
            repo_mgr.enable_flatpak_remote("custom")

    def test_is_flatpak_remote_enabled_true(self, fedora_distro: DistroInfo) -> None:
        """Test checking if Flatpak remote is enabled returns True."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="flathub\n")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is True

    def test_is_flatpak_remote_enabled_false(self, fedora_distro: DistroInfo) -> None:
        """Test checking if Flatpak remote is enabled returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is False

    def test_is_flatpak_remote_enabled_command_failed(self, fedora_distro: DistroInfo) -> None:
        """Test checking Flatpak remote when command fails."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is False

    def test_install_flatpak_success(self, fedora_distro: DistroInfo) -> None:
        """Test installing Flatpak package successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.install_flatpak("org.mozilla.firefox")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "flatpak", "install", "-y", "flathub", "org.mozilla.firefox"],
                capture_output=True,
            )

    def test_install_flatpak_custom_remote(self, fedora_distro: DistroInfo) -> None:
        """Test installing Flatpak package from custom remote."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.install_flatpak("org.mozilla.firefox", remote="fedora")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "flatpak", "install", "-y", "fedora", "org.mozilla.firefox"],
                capture_output=True,
            )

    def test_remove_flatpak_success(self, fedora_distro: DistroInfo) -> None:
        """Test removing Flatpak package successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.remove_flatpak("org.mozilla.firefox")

            assert result is True
            mock_run.assert_called_once_with(
                ["sudo", "flatpak", "uninstall", "-y", "org.mozilla.firefox"],
                capture_output=True,
            )
