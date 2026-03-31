"""Tests for Ollama installer module."""

from unittest.mock import Mock, patch

from aps.installers import ollama


class TestOllamaInstaller:
    """Tests for Ollama installer."""

    def test_install_already_installed(self) -> None:
        """Test install when Ollama is already installed."""
        with (
            patch(
                "aps.installers.ollama.shutil.which",
                return_value="/usr/bin/ollama",
            ),
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):
            mock_subprocess.return_value = Mock(returncode=0)
            result = ollama.install()

        assert result is True

    def test_install_arch_nvidia_success(self) -> None:
        """Test Ollama installation on Arch with NVIDIA GPU."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.run_privileged") as mock_run_priv,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "nvidia-smi":
                    return "/usr/bin/nvidia-smi"
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            mock_run_priv.return_value = Mock(returncode=0, stderr="")

            result = ollama.install(distro="arch")

            assert result is True
            # Verify ollama-cuda was installed
            calls_str = str(mock_run_priv.call_args_list)
            assert "ollama-cuda" in calls_str

    def test_install_arch_amd_success(self) -> None:
        """Test Ollama installation on Arch with AMD GPU."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_lspci,
            patch("aps.installers.ollama.run_privileged") as mock_run_priv,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "nvidia-smi":
                    return None
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            mock_lspci.return_value = Mock(
                returncode=0,
                stdout="VGA compatible: AMD/ATI Device",
                stderr="",
            )
            mock_run_priv.return_value = Mock(returncode=0, stderr="")

            result = ollama.install(distro="arch")

            assert result is True
            # Verify ollama-rocm was installed
            calls_str = str(mock_run_priv.call_args_list)
            assert "ollama-rocm" in calls_str

    def test_install_arch_no_gpu_success(self) -> None:
        """Test Ollama installation on Arch without specific GPU."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_lspci,
            patch("aps.installers.ollama.run_privileged") as mock_run_priv,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            mock_lspci.return_value = Mock(returncode=0, stdout="", stderr="")
            mock_run_priv.return_value = Mock(returncode=0, stderr="")

            result = ollama.install(distro="arch")

            assert result is True
            # Verify plain 'ollama' package was attempted
            calls_str = str(mock_run_priv.call_args_list)
            assert "ollama" in calls_str

    def test_install_arch_pacman_fails_fallback_to_official(
        self,
    ) -> None:
        """Test Arch installation falls back on pacman failure."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
            patch("aps.installers.ollama.run_privileged") as mock_run_priv,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            def subprocess_side_effect(
                *args: object, **kwargs: object
            ) -> Mock:
                # lspci call returns empty (no GPU)
                return Mock(returncode=0, stdout="", stderr="")

            mock_which.side_effect = which_side_effect
            # pacman fails
            mock_run_priv.return_value = Mock(
                returncode=1, stderr="Error", stdout=""
            )
            # Both subprocess calls succeed (lspci and official installer)
            mock_subprocess.side_effect = subprocess_side_effect

            result = ollama.install(distro="arch")

            assert result is True
            # Verify both pacman and official installer were tried
            assert mock_run_priv.called
            assert mock_subprocess.called
            # Check that shell=True was used in at least one call
            # (the official installer)
            shell_calls = [
                call
                for call in mock_subprocess.call_args_list
                if call.kwargs.get("shell") is True
            ]
            assert len(shell_calls) > 0

    def test_install_fedora_official_installer(self) -> None:
        """Test Ollama installation on Fedora using official installer."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            mock_subprocess.return_value = Mock(returncode=0)

            result = ollama.install(distro="fedora")

            assert result is True
            # Verify official installer was called
            assert mock_subprocess.called
            call_args = mock_subprocess.call_args
            assert call_args.kwargs.get("shell") is True
            assert "https://ollama.com/install.sh" in call_args[0][0]

    def test_install_other_distro_official_installer(self) -> None:
        """Test Ollama installation on other distros using official installer."""  # noqa: E501
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            mock_subprocess.return_value = Mock(returncode=0)

            result = ollama.install(distro="ubuntu")

            assert result is True
            assert mock_subprocess.called

    def test_install_verification_failure_arch(self) -> None:
        """Test installation fails if ollama binary doesn't exist after install."""  # noqa: E501
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
            patch("aps.installers.ollama.run_privileged") as mock_run_priv,
        ):
            # ollama never becomes available
            mock_which.return_value = None
            mock_run_priv.return_value = Mock(returncode=0, stderr="")
            mock_subprocess.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            result = ollama.install(distro="arch")

            assert result is False

    def test_install_verification_failure_fedora(self) -> None:
        """Test install fails if ollama doesn't exist after install (Fedora)."""  # noqa: E501
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):
            # First check: not installed. After install: still not available
            mock_which.return_value = None
            mock_subprocess.return_value = Mock(returncode=0)

            result = ollama.install(distro="fedora")

            assert result is False

    def test_install_official_installer_command_failure(self) -> None:
        """Test installation fails when official installer command fails."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):
            # Not initially installed, remains not installed
            mock_which.return_value = None
            # Installer command fails
            mock_subprocess.return_value = Mock(returncode=1)

            result = ollama.install(distro="fedora")

            assert result is False

    def test_detect_gpu_vendor_nvidia(self) -> None:
        """Test GPU vendor detection for NVIDIA."""
        with patch(
            "aps.installers.ollama.shutil.which",
            return_value="/usr/bin/nvidia-smi",
        ):
            vendor = ollama._detect_gpu_vendor()  # noqa: SLF001
            assert vendor == "nvidia"

    def test_detect_gpu_vendor_amd(self) -> None:
        """Test GPU vendor detection for AMD via lspci."""
        with (
            patch("aps.installers.ollama.shutil.which", return_value=None),
            patch("aps.installers.ollama.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="VGA compatible: AMD/ATI Device",
                stderr="",
            )
            vendor = ollama._detect_gpu_vendor()  # noqa: SLF001
            assert vendor == "amd"

    def test_detect_gpu_vendor_amd_display(self) -> None:
        """Test GPU vendor detection for AMD with 'display' keyword."""
        with (
            patch("aps.installers.ollama.shutil.which", return_value=None),
            patch("aps.installers.ollama.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Display controller: AMD/ATI Device",
                stderr="",
            )
            vendor = ollama._detect_gpu_vendor()  # noqa: SLF001
            assert vendor == "amd"

    def test_detect_gpu_vendor_unknown(self) -> None:
        """Test GPU vendor detection when no GPU is detected."""
        with (
            patch("aps.installers.ollama.shutil.which", return_value=None),
            patch("aps.installers.ollama.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Intel integrated graphics",
                stderr="",
            )
            vendor = ollama._detect_gpu_vendor()  # noqa: SLF001
            assert vendor == "unknown"

    def test_detect_gpu_vendor_lspci_fails(self) -> None:
        """Test GPU vendor detection when lspci fails."""
        with (
            patch("aps.installers.ollama.shutil.which", return_value=None),
            patch("aps.installers.ollama.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="")
            vendor = ollama._detect_gpu_vendor()  # noqa: SLF001
            assert vendor == "unknown"

    def test_uninstall_not_installed(self) -> None:
        """Test uninstall when Ollama is not installed."""
        with patch(
            "aps.installers.ollama.shutil.which",
            return_value=None,
        ):
            result = ollama.uninstall()

        assert result is True

    def test_uninstall_arch_pacman_plus_cleanup(
        self, mock_run_privileged: Mock
    ) -> None:
        """Test uninstall on Arch: pacman removal + cleanup."""
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            # pacman -Qo returns the package
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout="community/ollama 0.1.0-1\n",
                stderr="",
            )
            # All privileged commands succeed
            mock_run_privileged.return_value = Mock(returncode=0, stderr="")

            result = ollama.uninstall(distro="arch")

            assert result is True
            # Verify pacman -Qo was called (to check ownership)
            assert any(
                "pacman" in str(call) and "-Qo" in str(call)
                for call in mock_subprocess.call_args_list
            )
            # Verify cleanup was called (systemctl stop, etc.)
            systemctl_calls = [
                call
                for call in mock_run_privileged.call_args_list
                if len(call[0]) > 0 and "systemctl" in str(call[0][0])
            ]
            assert len(systemctl_calls) > 0

    def test_uninstall_arch_pacman_not_owner_manual_only(
        self, mock_run_privileged: Mock
    ) -> None:
        """Test uninstall on Arch: pacman doesn't own binary, manual cleanup.

        Cleanup is still performed even when pacman doesn't own the binary.
        """
        with (
            patch("aps.installers.ollama.shutil.which") as mock_which,
            patch("aps.installers.ollama.subprocess.run") as mock_subprocess,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            # pacman -Qo returns error (pacman doesn't own it)
            mock_subprocess.return_value = Mock(
                returncode=1, stdout="", stderr=""
            )
            # All privileged commands succeed
            mock_run_privileged.return_value = Mock(returncode=0, stderr="")

            result = ollama.uninstall(distro="arch")

            assert result is True
            # Verify cleanup was called even though pacman doesn't own it
            systemctl_calls = [
                call
                for call in mock_run_privileged.call_args_list
                if len(call[0]) > 0 and "systemctl" in str(call[0][0])
            ]
            assert len(systemctl_calls) > 0

    def test_uninstall_manual_full_procedure(
        self, mock_run_privileged: Mock
    ) -> None:
        """Test uninstall on non-Arch: full manual procedure."""
        with patch(
            "aps.installers.ollama.shutil.which",
            return_value="/usr/bin/ollama",
        ):
            mock_run_privileged.return_value = Mock(returncode=0, stderr="")

            result = ollama.uninstall(distro="fedora")

            assert result is True
            # Verify all cleanup steps were called
            mock_run_privileged.assert_called()
            calls_str = str(mock_run_privileged.call_args_list)
            # Should have systemctl, rm, userdel, groupdel calls
            assert "systemctl" in calls_str
            rm_check = "rm" in calls_str or "/usr/bin/rm" in calls_str.replace(
                "'", ""
            )
            assert rm_check
            userdel_in_calls = (
                "userdel" in calls_str or "/usr/sbin/userdel" in calls_str
            )
            assert userdel_in_calls
            groupdel_in_calls = (
                "groupdel" in calls_str or "/usr/sbin/groupdel" in calls_str
            )
            assert groupdel_in_calls

    def test_uninstall_service_cleanup(
        self, mock_run_privileged: Mock
    ) -> None:
        """Test uninstall: service cleanup is called correctly."""
        with patch(
            "aps.installers.ollama.shutil.which",
            return_value="/usr/bin/ollama",
        ):
            mock_run_privileged.return_value = Mock(returncode=0, stderr="")

            result = ollama.uninstall()

            assert result is True
            # Verify systemctl commands were called
            systemctl_calls = [
                call
                for call in mock_run_privileged.call_args_list
                if len(call[0]) > 0 and "systemctl" in str(call[0][0])
            ]
            assert len(systemctl_calls) >= 2  # stop and disable
            # Should have both stop and disable
            calls_str = str(mock_run_privileged.call_args_list)
            assert "stop" in calls_str
            assert "disable" in calls_str
