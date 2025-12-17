"""Tests for official repository priority checking."""

from unittest.mock import Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.core.package_manager import AptManager, DnfManager, PacmanManager


class TestOfficialReposPriority:
    """Test that package managers can check official repository availability."""

    def test_dnf_is_available_in_official_repos_found(self) -> None:
        """Test DnfManager finds package in official repos."""
        distro = DistroInfo(
            name="Fedora",
            version="40",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        pm = DnfManager(distro)

        with patch("subprocess.run") as mock_run:
            # Mock dnf repoquery returning success
            mock_repoquery = Mock(returncode=0, stdout="git-2.43.0-1.fc40.x86_64\n")
            # Mock dnf list showing official repo (not copr)
            mock_list = Mock(returncode=0, stdout="git.x86_64 2.43.0-1.fc40 updates\n")

            mock_run.side_effect = [mock_repoquery, mock_list]
            result = pm.is_available_in_official_repos("git")

        assert result is True
        assert mock_run.call_count == 2
        # Check first call was dnf repoquery
        cmd1 = mock_run.call_args_list[0][0][0]
        assert cmd1 == ["dnf", "repoquery", "git"]
        # Check second call was dnf list
        cmd2 = mock_run.call_args_list[1][0][0]
        assert cmd2 == ["dnf", "list", "git"]

    def test_dnf_is_available_in_official_repos_not_found(self) -> None:
        """Test DnfManager doesn't find package in official repos."""
        distro = DistroInfo(
            name="Fedora",
            version="40",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        pm = DnfManager(distro)

        with patch("subprocess.run") as mock_run:
            # Mock dnf repoquery returning failure (package not found)
            mock_run.return_value = Mock(returncode=1, stdout="")
            result = pm.is_available_in_official_repos("nonexistent-package")

        assert result is False
        # Only one call should be made (repoquery fails, so list is not called)
        assert mock_run.call_count == 1

    def test_dnf_is_available_in_official_repos_copr_package(self) -> None:
        """Test DnfManager rejects packages from COPR repos."""
        distro = DistroInfo(
            name="Fedora",
            version="40",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        pm = DnfManager(distro)

        with patch("subprocess.run") as mock_run:
            # Mock dnf repoquery returning success
            mock_repoquery = Mock(returncode=0, stdout="lazygit-0.57.0-1.fc42.x86_64\n")
            # Mock dnf list showing COPR repo
            mock_list = Mock(
                returncode=0,
                stdout="lazygit.x86_64 0.57.0-1.fc42 copr:copr.fedorainfracloud.org:dejan:lazygit\n",
            )

            mock_run.side_effect = [mock_repoquery, mock_list]
            result = pm.is_available_in_official_repos("lazygit")

        assert result is False
        assert mock_run.call_count == 2

    def test_pacman_is_available_in_official_repos_found(self) -> None:
        """Test PacmanManager finds package in official repos."""
        distro = DistroInfo(
            name="Arch",
            version="rolling",
            id="arch",
            id_like=[],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        pm = PacmanManager(distro)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="extra/git 2.43.0-1\n    The fast distributed version control system\n",
            )
            result = pm.is_available_in_official_repos("git")

        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "pacman" in cmd
        assert "-Ss" in cmd

    def test_pacman_is_available_in_official_repos_aur_only(self) -> None:
        """Test PacmanManager rejects AUR-only packages."""
        distro = DistroInfo(
            name="Arch",
            version="rolling",
            id="arch",
            id_like=[],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        pm = PacmanManager(distro)

        with patch("subprocess.run") as mock_run:
            # Simulate package only in AUR (not in official repos)
            mock_run.return_value = Mock(
                returncode=0, stdout="aur/package 1.0.0-1\n    AUR package\n"
            )
            result = pm.is_available_in_official_repos("package")

        assert result is False

    def test_pacman_is_available_in_official_repos_core(self) -> None:
        """Test PacmanManager finds package in core repo."""
        distro = DistroInfo(
            name="Arch",
            version="rolling",
            id="arch",
            id_like=[],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        pm = PacmanManager(distro)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="core/linux 6.6.8-1\n    The Linux kernel and modules\n"
            )
            result = pm.is_available_in_official_repos("linux")

        assert result is True

    def test_apt_is_available_in_official_repos_found(self) -> None:
        """Test AptManager finds package in official repos."""
        distro = DistroInfo(
            name="Ubuntu",
            version="22.04",
            id="ubuntu",
            id_like=["debian"],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        pm = AptManager(distro)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="git:\n  Installed: (none)\n  Candidate: 1:2.34.1-1ubuntu1.10\n",
            )
            result = pm.is_available_in_official_repos("git")

        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "apt-cache" in cmd
        assert "policy" in cmd
        assert "git" in cmd

    def test_apt_is_available_in_official_repos_not_found(self) -> None:
        """Test AptManager doesn't find package."""
        distro = DistroInfo(
            name="Ubuntu",
            version="22.04",
            id="ubuntu",
            id_like=["debian"],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        pm = AptManager(distro)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="nonexistent:\n  Installed: (none)\n  Candidate: (none)\n"
            )
            result = pm.is_available_in_official_repos("nonexistent")

        assert result is False

    def test_apt_is_available_in_official_repos_error(self) -> None:
        """Test AptManager handles errors gracefully."""
        distro = DistroInfo(
            name="Ubuntu",
            version="22.04",
            id="ubuntu",
            id_like=["debian"],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        pm = AptManager(distro)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            result = pm.is_available_in_official_repos("test")

        assert result is False
