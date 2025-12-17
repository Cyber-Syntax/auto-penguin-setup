"""Tests for sudoers configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.sudoers import SudoersConfig


class TestSudoersConfig:
    """Tests for sudoers configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.Path.read_text", return_value="# sudoers file\n")
    @patch("aps.utils.privilege.subprocess.run")
    @patch("aps.system.sudoers.subprocess.run")
    def test_configure_borgbackup(
        self,
        mock_subprocess_run: Mock,
        mock_privileged_run: Mock,
        _mock_read: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test borgbackup sudoers configuration."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        # Mock whoami command (direct subprocess.run call)
        mock_subprocess_run.return_value = Mock(returncode=0, stdout="testuser")

        # Mock privileged commands (via run_privileged): backup, tee, visudo
        # Adding extra returns in case there are more calls
        mock_privileged_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # backup via run_privileged
            Mock(returncode=0, stdout="", stderr=""),  # tee via run_privileged
            Mock(returncode=0, stdout="", stderr=""),  # visudo via run_privileged
            Mock(returncode=0, stdout="", stderr=""),  # extra just in case
            Mock(returncode=0, stdout="", stderr=""),  # extra just in case
        ]

        sudoers = SudoersConfig()
        result = sudoers.configure_borgbackup()

        assert result is True
