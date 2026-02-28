"""Tests for paru AUR helper installer module."""

from unittest.mock import MagicMock, Mock, patch

from aps.installers import paru


class TestParuInstaller:
    """Tests for paru AUR helper installer."""

    def test_install_skip_non_arch(self) -> None:
        """Test install returns False when distro is not Arch."""
        result = paru.install(distro="fedora")
        assert result is False

    def test_install_skip_paru_already_installed(self) -> None:
        """Test install returns True when paru is already found."""
        with patch("aps.installers.paru.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/paru"
            result = paru.install(distro="arch")
            assert result is True

    def test_install_skip_yay_already_installed(self) -> None:
        """Test install returns True when yay is already found."""
        with patch("aps.installers.paru.shutil.which") as mock_which:
            # First call for paru returns None, second for yay returns path
            mock_which.side_effect = [None, "/usr/bin/yay"]
            result = paru.install(distro="arch")
            assert result is True

    def test_install_success(self) -> None:
        """Test successful paru installation with all steps."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
        ):
            # Setup which() calls: not initially installed, then installed
            # First two calls: paru not installed, yay not installed
            # Last call: paru installed after build (verification)
            mock_which.side_effect = [
                None,  # paru check
                None,  # yay check
                "/usr/bin/paru",  # verification check
            ]

            # Mock successful subprocess calls
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            mock_run_priv.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            result = paru.install(distro="arch")

            assert result is True
            # Verify GPG keyring check was called
            mock_run.assert_called()
            # Verify build deps install was called
            calls_str = str(mock_run_priv.call_args_list)
            assert "base-devel" in calls_str

    def test_install_build_deps_failure(self) -> None:
        """Test install returns False when pacman fails."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
        ):
            # Not installed initially
            mock_which.side_effect = [None, None]

            # GPG check succeeds
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Build deps installation fails
            mock_run_priv.return_value = Mock(
                returncode=1, stdout="", stderr="Permission denied"
            )

            result = paru.install(distro="arch")

            assert result is False

    def test_install_clone_failure(self) -> None:
        """Test install returns False when git clone fails."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
        ):
            # Not installed initially
            mock_which.side_effect = [None, None]

            # GPG check succeeds
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Build deps succeeds, but clone fails
            def priv_side_effect(cmd: list[str], **kwargs: object) -> Mock:
                if "git" in cmd and "clone" in cmd:
                    return Mock(returncode=1, stdout="", stderr="Clone failed")
                return Mock(returncode=0, stdout="", stderr="")

            mock_run_priv.side_effect = priv_side_effect

            result = paru.install(distro="arch")

            assert result is False

    def test_install_makepkg_failure(self) -> None:
        """Test install returns False when makepkg fails."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
        ):
            # Not installed initially
            mock_which.side_effect = [None, None]

            # makepkg fails
            def subprocess_side_effect(
                cmd: list[str], **kwargs: object
            ) -> Mock:
                if cmd[0] == "makepkg":
                    return Mock(returncode=1, stdout="", stderr="Build failed")
                # GPG check succeeds
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = subprocess_side_effect

            # All privileged calls succeed
            mock_run_priv.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            result = paru.install(distro="arch")

            assert result is False

    def test_install_verification_failure(self) -> None:
        """Test install returns False when paru not found after build."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
        ):
            # paru never becomes available
            mock_which.return_value = None

            # All subprocess commands succeed
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            mock_run_priv.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            result = paru.install(distro="arch")

            assert result is False

    def test_install_cleanup_on_success(self) -> None:
        """Test install cleans up build dir after success."""
        with (
            patch("aps.installers.paru.shutil.which") as mock_which,
            patch("aps.installers.paru.subprocess.run") as mock_run,
            patch("aps.installers.paru.run_privileged") as mock_run_priv,
            patch("aps.installers.paru.Path") as mock_path_class,
        ):
            # Not installed initially, then installed after build
            mock_which.side_effect = [None, None, "/usr/bin/paru"]

            # All subprocess commands succeed
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Setup mock Path that tracks exists() calls and cleanup
            mock_build_dir = MagicMock()
            mock_build_dir.exists.return_value = True
            mock_path_class.return_value = mock_build_dir

            # Set up home path for GPG directories
            mock_home = MagicMock()
            mock_home.name = "testuser"
            mock_home.__truediv__ = MagicMock(
                return_value=MagicMock(
                    exists=MagicMock(return_value=False),
                    __truediv__=MagicMock(
                        return_value=MagicMock(
                            exists=MagicMock(return_value=False),
                            __truediv__=MagicMock(
                                return_value=MagicMock(
                                    exists=MagicMock(return_value=False)
                                )
                            ),
                        )
                    ),
                )
            )
            mock_path_class.home.return_value = mock_home

            # All privileged calls succeed
            mock_run_priv.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            result = paru.install(distro="arch")

            assert result is True
            # Verify cleanup was called in finally block
            cleanup_calls = [
                call
                for call in mock_run_priv.call_args_list
                if len(call[0][0]) > 0 and "rm" in call[0][0]
            ]
            assert len(cleanup_calls) > 0
