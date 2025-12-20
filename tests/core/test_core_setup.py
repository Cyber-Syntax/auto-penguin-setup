"""Tests for setup manager module."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.core.setup import SetupError, SetupManager


@pytest.fixture
def arch_distro() -> DistroInfo:
    """Create Arch Linux distro info."""
    return DistroInfo(
        name="Arch Linux",
        version="rolling",
        id="arch",
        id_like=[],
        package_manager=PackageManagerType.PACMAN,
        family=DistroFamily.ARCH,
    )


@pytest.fixture
def fedora_distro() -> DistroInfo:
    """Create Fedora distro info."""
    return DistroInfo(
        name="Fedora",
        version="39",
        id="fedora",
        id_like=["rhel", "fedora"],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )


@pytest.fixture
def setup_manager_arch(arch_distro: DistroInfo) -> SetupManager:
    """Create SetupManager for Arch Linux."""
    return SetupManager(arch_distro)


@pytest.fixture
def setup_manager_fedora(fedora_distro: DistroInfo) -> SetupManager:
    """Create SetupManager for Fedora."""
    return SetupManager(fedora_distro)


class TestSetupManagerAURHelper:
    """Tests for AUR helper setup."""

    def test_aur_helper_already_installed_paru(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test that setup skips if paru is already installed."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/paru"
            setup_manager_arch.setup_aur_helper()
            # Should not raise, just skip installation

    def test_aur_helper_already_installed_yay(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test that setup skips if yay is already installed."""
        with patch("shutil.which") as mock_which:
            # First call for paru returns None, second for yay returns path
            mock_which.side_effect = [None, "/usr/bin/yay"]
            setup_manager_arch.setup_aur_helper()
            # Should not raise, just skip installation

    def test_aur_helper_not_available_on_non_arch(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test that AUR helper setup raises error on non-Arch distros."""
        with pytest.raises(SetupError, match="only available for Arch-based"):
            setup_manager_fedora.setup_aur_helper()

    def test_aur_helper_installation_success(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test successful paru installation."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
            patch("pathlib.Path.home") as mock_home,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            # Setup mocks
            mock_home.return_value = Path("/home/testuser")
            mock_exists.return_value = False  # GPG keyring does not exist

            # Mock which() calls: not installed initially, then installed after build
            mock_which.side_effect = [
                None,  # paru not installed initially
                None,  # yay not installed
                "/usr/bin/paru",  # paru installed after build
            ]

            # Mock successful subprocess calls for non-privileged operations
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            setup_manager_arch.setup_aur_helper()

            # Verify pacman was called for build deps via run_privileged
            calls_str = str(mock_run_privileged.call_args_list)
            assert "base-devel" in calls_str

    def test_aur_helper_build_deps_failure(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test that build dependency installation failure raises error."""
        with (
            patch("subprocess.run"),
            patch("shutil.which") as mock_which,
            patch("pathlib.Path.home") as mock_home,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_home.return_value = Path("/home/testuser")
            mock_exists.return_value = True
            mock_which.side_effect = [None, None]  # Not installed

            # Mock failed pacman call via run_privileged
            mock_run_privileged.return_value = Mock(
                returncode=1, stdout="", stderr="Permission denied"
            )

            with pytest.raises(
                SetupError, match="Failed to install build dependencies"
            ):
                setup_manager_arch.setup_aur_helper()

    def test_aur_helper_clone_failure(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test that git clone failure raises error."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
            patch("pathlib.Path.home") as mock_home,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_home.return_value = Path("/home/testuser")
            mock_exists.return_value = True
            # Always return None for which() - no helper installed
            mock_which.return_value = None

            # Mock run_privileged to fail for git clone, succeed for others
            def priv_side_effect(cmd: list[str], **kwargs: Any) -> Mock:
                if "git" in cmd and "clone" in cmd:
                    return Mock(returncode=1, stdout="", stderr="Clone failed")
                return Mock(returncode=0, stdout="", stderr="")

            mock_run_privileged.side_effect = priv_side_effect

            # Mock subprocess.run for makepkg
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with pytest.raises(
                SetupError, match="Failed to clone paru-bin repository"
            ):
                setup_manager_arch.setup_aur_helper()

    def test_aur_helper_verification_failure(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test that verification failure after build raises error."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
            patch("pathlib.Path.home") as mock_home,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_home.return_value = Path("/home/testuser")
            mock_exists.return_value = True

            # paru never becomes available
            mock_which.return_value = None

            # All subprocess commands succeed
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            # run_privileged also succeeds
            mock_run_privileged.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )

            with pytest.raises(
                SetupError, match="paru installation verification failed"
            ):
                setup_manager_arch.setup_aur_helper()


class TestSetupManagerOllama:
    """Tests for Ollama setup."""

    def test_ollama_arch_nvidia_success(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test Ollama installation on Arch with NVIDIA GPU."""
        with patch("shutil.which") as mock_which:
            # Mock nvidia-smi available (NVIDIA GPU)
            def which_side_effect(cmd: str) -> str | None:
                if cmd == "nvidia-smi":
                    return "/usr/bin/nvidia-smi"
                if cmd == "ollama":
                    return "/usr/bin/ollama"  # Installed after pacman
                return None

            mock_which.side_effect = which_side_effect

            setup_manager_arch.setup_ollama()

            # Verify ollama-cuda was installed via run_privileged
            calls_str = str(mock_run_privileged.call_args_list)
            assert "ollama-cuda" in calls_str

    def test_ollama_arch_amd_success(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test Ollama installation on Arch with AMD GPU."""
        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_lspci,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "nvidia-smi":
                    return None
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect

            # Mock lspci output for AMD GPU
            mock_lspci.return_value = Mock(
                returncode=0,
                stdout="VGA compatible: AMD/ATI Device",
                stderr="",
            )

            setup_manager_arch.setup_ollama()

            # Verify ollama-rocm was installed via run_privileged
            calls_str = str(mock_run_privileged.call_args_list)
            assert "ollama-rocm" in calls_str

    def test_ollama_arch_no_gpu(
        self, setup_manager_arch: SetupManager, mock_run_privileged: Any
    ) -> None:
        """Test Ollama installation on Arch without specific GPU."""
        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_lspci,
        ):

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "ollama":
                    return "/usr/bin/ollama"
                return None

            mock_which.side_effect = which_side_effect
            # Mock lspci with no GPU info
            mock_lspci.return_value = Mock(returncode=0, stdout="", stderr="")

            setup_manager_arch.setup_ollama()

            # Verify generic ollama package was installed via run_privileged
            calls_str = str(mock_run_privileged.call_args_list)
            # Should install plain 'ollama' package, not ollama-cuda or ollama-rocm
            assert "pacman" in calls_str
            assert ("ollama-cuda" not in calls_str) and (
                "ollama-rocm" not in calls_str
            )

    def test_ollama_fedora_official_installer(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test Ollama installation on Fedora using official installer."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
            mock_which.side_effect = [
                None,
                "/usr/bin/ollama",
            ]  # Not installed, then installed
            mock_run.return_value = Mock(returncode=0)

            setup_manager_fedora.setup_ollama()

            # Verify the shell command was called
            assert mock_run.called
            call_args = mock_run.call_args
            assert (
                "shell=True" in str(call_args)
                or call_args.kwargs.get("shell") is True
            )

    def test_ollama_installation_verification_failure(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test that verification failure after install raises error."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
            mock_which.return_value = None  # Never becomes available
            mock_run.return_value = Mock(returncode=0)

            with pytest.raises(
                SetupError, match="Ollama binary not found after"
            ):
                setup_manager_fedora.setup_ollama()

    def test_ollama_official_installer_execution_failure(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test that installer execution failure raises error."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
            mock_which.return_value = None
            mock_run.return_value = Mock(returncode=1)

            with pytest.raises(SetupError, match="Failed to install Ollama"):
                setup_manager_fedora.setup_ollama()

    def test_ollama_already_installed(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test that Ollama update succeeds when already installed."""
        with (
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            mock_which.return_value = "/usr/bin/ollama"  # Already installed
            mock_run.return_value = Mock(returncode=0)
            setup_manager_fedora.setup_ollama()
            # Should complete without error


class TestDetectGPUVendor:
    """Tests for GPU vendor detection."""

    def test_detect_nvidia_gpu(self, setup_manager_arch: SetupManager) -> None:
        """Test NVIDIA GPU detection."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/nvidia-smi"
            vendor = setup_manager_arch._detect_gpu_vendor()
            assert vendor == "nvidia"

    def test_detect_amd_gpu(self, setup_manager_arch: SetupManager) -> None:
        """Test AMD GPU detection."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
            mock_which.return_value = None  # No nvidia-smi
            mock_run.return_value = Mock(
                returncode=0,
                stdout="01:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Display",
                stderr="",
            )

            vendor = setup_manager_arch._detect_gpu_vendor()
            assert vendor == "amd"

    def test_detect_unknown_gpu(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test unknown GPU detection."""
        with (
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
            mock_which.return_value = None
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            vendor = setup_manager_arch._detect_gpu_vendor()
            assert vendor == "unknown"


class TestComponentRegistry:
    """Tests for component registry and setup_component method."""

    def test_get_available_components(self) -> None:
        """Test that get_available_components returns all registered components."""
        components = SetupManager.get_available_components()

        # Verify all expected components are present
        expected_components = [
            "aur-helper",
            "ollama",
            "ohmyzsh",
            "brave",
            "protonvpn",
            "thinkfan",
            "tlp",
            "autocpufreq",
            "nfancurve",
            "syncthing",
            "trashcli",
            "ueberzugpp",
            "virtmanager",
            "vscode",
            # Hardware configuration components
            "amd",
            "intel",
            "nvidia",
            "touchpad",
            # System configuration components
            "firewall",
            "multimedia",
            "pm-optimizer",
            "repositories",
            "ssh",
            "sudoers",
            # Window manager configuration components
            "qtile",
        ]

        for component in expected_components:
            assert component in components
            assert isinstance(components[component], str)
            assert len(components[component]) > 0  # Has description

    def test_setup_component_aur_helper(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component delegates to setup_aur_helper."""
        with patch.object(
            setup_manager_arch, "setup_aur_helper"
        ) as mock_setup:
            setup_manager_arch.setup_component("aur-helper")
            mock_setup.assert_called_once()

    def test_setup_component_ollama(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component delegates to setup_ollama."""
        with patch.object(setup_manager_arch, "setup_ollama") as mock_setup:
            setup_manager_arch.setup_component("ollama")
            mock_setup.assert_called_once()

    def test_setup_component_ohmyzsh(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component instantiates and calls installer for ohmyzsh."""
        mock_installer = Mock()
        mock_installer.install.return_value = True
        mock_installer_class = Mock(return_value=mock_installer)

        # Temporarily replace the installer class in the registry
        original_installer = SetupManager.COMPONENT_REGISTRY["ohmyzsh"][
            "installer"
        ]
        try:
            SetupManager.COMPONENT_REGISTRY["ohmyzsh"]["installer"] = (
                mock_installer_class
            )
            setup_manager_arch.setup_component("ohmyzsh")
            mock_installer_class.assert_called_once()
            mock_installer.install.assert_called_once()
        finally:
            SetupManager.COMPONENT_REGISTRY["ohmyzsh"]["installer"] = (
                original_installer
            )

    def test_setup_component_brave(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component instantiates and calls installer for brave."""
        mock_installer = Mock()
        mock_installer.install.return_value = True
        mock_installer_class = Mock(return_value=mock_installer)

        # Temporarily replace the installer class in the registry
        original_installer = SetupManager.COMPONENT_REGISTRY["brave"][
            "installer"
        ]
        try:
            SetupManager.COMPONENT_REGISTRY["brave"]["installer"] = (
                mock_installer_class
            )
            setup_manager_arch.setup_component("brave")
            mock_installer_class.assert_called_once()
            mock_installer.install.assert_called_once()
        finally:
            SetupManager.COMPONENT_REGISTRY["brave"]["installer"] = (
                original_installer
            )

    def test_setup_component_unknown(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component raises error for unknown component."""
        with pytest.raises(SetupError, match="Unknown component"):
            setup_manager_arch.setup_component("nonexistent-component")

    def test_setup_component_installer_failure(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component raises error when installer returns False."""
        mock_installer = Mock()
        mock_installer.install.return_value = False
        mock_installer_class = Mock(return_value=mock_installer)

        # Temporarily replace the installer class in the registry
        original_installer = SetupManager.COMPONENT_REGISTRY["tlp"][
            "installer"
        ]
        try:
            SetupManager.COMPONENT_REGISTRY["tlp"]["installer"] = (
                mock_installer_class
            )
            with pytest.raises(SetupError, match="Failed to setup tlp"):
                setup_manager_arch.setup_component("tlp")
        finally:
            SetupManager.COMPONENT_REGISTRY["tlp"]["installer"] = (
                original_installer
            )

    def test_setup_component_installer_exception(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component raises error when installer raises exception."""
        mock_installer = Mock()
        mock_installer.install.side_effect = Exception("Installation error")
        mock_installer_class = Mock(return_value=mock_installer)

        # Temporarily replace the installer class in the registry
        original_installer = SetupManager.COMPONENT_REGISTRY["thinkfan"][
            "installer"
        ]
        try:
            SetupManager.COMPONENT_REGISTRY["thinkfan"]["installer"] = (
                mock_installer_class
            )
            with pytest.raises(
                SetupError, match="Error during thinkfan setup"
            ):
                setup_manager_arch.setup_component("thinkfan")
        finally:
            SetupManager.COMPONENT_REGISTRY["thinkfan"]["installer"] = (
                original_installer
            )
