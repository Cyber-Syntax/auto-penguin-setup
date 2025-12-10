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
                check=False,
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
                check=False,
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
            mock_run.assert_called_once_with(
                ["dnf", "repolist", "--enabled"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_is_copr_enabled_false(self, fedora_distro: DistroInfo) -> None:
        """Test checking if COPR is enabled returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = repo_mgr.is_copr_enabled("user/repo")

            assert result is False
            mock_run.assert_called_once_with(
                ["dnf", "repolist", "--enabled"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_is_copr_enabled_non_fedora(self, arch_distro: DistroInfo) -> None:
        """Test checking COPR on non-Fedora returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        result = repo_mgr.is_copr_enabled("user/repo")
        assert result is False

    def test_is_copr_enabled_command_failure(self, fedora_distro: DistroInfo) -> None:
        """Test that command failure returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
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
                check=False,
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
                check=False,
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

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak already installed
            mock_which.return_value = "/usr/bin/flatpak"
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
                check=False,
            )

    def test_enable_flatpak_remote_custom(self, fedora_distro: DistroInfo) -> None:
        """Test enabling custom Flatpak remote."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak already installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.enable_flatpak_remote(
                "custom", "https://example.com/repo.flatpakrepo"
            )

            assert result is True

    def test_enable_flatpak_remote_no_url(self, fedora_distro: DistroInfo) -> None:
        """Test enabling Flatpak remote without URL raises error."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with patch("shutil.which") as mock_which:
            # Simulate flatpak already installed
            mock_which.return_value = "/usr/bin/flatpak"
            with pytest.raises(ValueError, match="remote_url is required"):
                repo_mgr.enable_flatpak_remote("custom")

    def test_is_flatpak_remote_enabled_true(self, fedora_distro: DistroInfo) -> None:
        """Test checking if Flatpak remote is enabled returns True."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=0, stdout="flathub\n")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is True

    def test_is_flatpak_remote_enabled_false(self, fedora_distro: DistroInfo) -> None:
        """Test checking if Flatpak remote is enabled returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=0, stdout="")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is False

    def test_is_flatpak_remote_enabled_command_failed(self, fedora_distro: DistroInfo) -> None:
        """Test checking Flatpak remote when command fails."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=1, stdout="")
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is False

    def test_install_flatpak_success(self, fedora_distro: DistroInfo) -> None:
        """Test installing Flatpak package successfully."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak already installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.install_flatpak("org.mozilla.firefox")

            assert result is True
            # No -y flag - installation is interactive
            mock_run.assert_called_once_with(
                ["sudo", "flatpak", "install", "flathub", "org.mozilla.firefox"],
                check=False,
            )

    def test_install_flatpak_custom_remote(self, fedora_distro: DistroInfo) -> None:
        """Test installing Flatpak package from custom remote."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(fedora_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Simulate flatpak already installed
            mock_which.return_value = "/usr/bin/flatpak"
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.install_flatpak("org.mozilla.firefox", remote="fedora")

            assert result is True
            # No -y flag - installation is interactive
            mock_run.assert_called_once_with(
                ["sudo", "flatpak", "install", "fedora", "org.mozilla.firefox"],
                check=False,
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
                check=False,
            )

    def test_is_flatpak_installed_true(self, arch_distro: DistroInfo) -> None:
        """Test checking if flatpak is installed returns True."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/flatpak"
            result = repo_mgr.is_flatpak_installed()

            assert result is True
            mock_which.assert_called_once_with("flatpak")

    def test_is_flatpak_installed_false(self, arch_distro: DistroInfo) -> None:
        """Test checking if flatpak is installed returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = repo_mgr.is_flatpak_installed()

            assert result is False
            mock_which.assert_called_once_with("flatpak")

    def test_is_flatpak_remote_enabled_not_installed(self, arch_distro: DistroInfo) -> None:
        """Test checking remote when flatpak is not installed returns False."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = repo_mgr.is_flatpak_remote_enabled("flathub")

            assert result is False
            mock_which.assert_called_once_with("flatpak")

    def test_ensure_flatpak_installed_already_installed(self, arch_distro: DistroInfo) -> None:
        """Test ensuring flatpak is installed when already present."""
        pm = Mock(spec=PackageManager)
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/flatpak"
            result = repo_mgr.ensure_flatpak_installed()

            assert result is True
            mock_which.assert_called_once_with("flatpak")
            # Should not call install since it's already installed
            pm.install.assert_not_called()

    def test_ensure_flatpak_installed_success(self, arch_distro: DistroInfo) -> None:
        """Test installing flatpak successfully when not present."""
        pm = Mock(spec=PackageManager)
        pm.install.return_value = (True, "")
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            # First call: flatpak not installed, second call: flatpak installed
            mock_which.side_effect = [None, "/usr/bin/flatpak"]
            result = repo_mgr.ensure_flatpak_installed()

            assert result is True
            pm.install.assert_called_once_with(["flatpak"], assume_yes=True)

    def test_ensure_flatpak_installed_install_fails(self, arch_distro: DistroInfo) -> None:
        """Test handling installation failure."""
        pm = Mock(spec=PackageManager)
        pm.install.return_value = (False, "Installation failed")
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(
                PackageManagerError, match="Failed to install flatpak: Installation failed"
            ):
                repo_mgr.ensure_flatpak_installed()

    def test_ensure_flatpak_installed_verification_fails(self, arch_distro: DistroInfo) -> None:
        """Test handling verification failure after installation."""
        pm = Mock(spec=PackageManager)
        pm.install.return_value = (True, "")
        repo_mgr = RepositoryManager(arch_distro, pm)

        with patch("shutil.which") as mock_which:
            # Always return None to simulate verification failure
            mock_which.return_value = None
            with pytest.raises(
                PackageManagerError, match="flatpak installation verification failed"
            ):
                repo_mgr.ensure_flatpak_installed()

    def test_enable_flatpak_remote_installs_flatpak_first(self, arch_distro: DistroInfo) -> None:
        """Test that enabling remote installs flatpak if needed."""
        pm = Mock(spec=PackageManager)
        pm.install.return_value = (True, "")
        repo_mgr = RepositoryManager(arch_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # First call: not installed, second call: installed
            mock_which.side_effect = [None, "/usr/bin/flatpak"]
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.enable_flatpak_remote("flathub")

            assert result is True
            pm.install.assert_called_once_with(["flatpak"], assume_yes=True)

    def test_install_flatpak_installs_flatpak_first(self, arch_distro: DistroInfo) -> None:
        """Test that installing flatpak package installs flatpak command if needed."""
        pm = Mock(spec=PackageManager)
        pm.install.return_value = (True, "")
        repo_mgr = RepositoryManager(arch_distro, pm)

        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # First call: not installed, second call: installed
            mock_which.side_effect = [None, "/usr/bin/flatpak"]
            mock_run.return_value = Mock(returncode=0)
            result = repo_mgr.install_flatpak("org.mozilla.firefox")

            assert result is True
            pm.install.assert_called_once_with(["flatpak"], assume_yes=True)
