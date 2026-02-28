"""Tests for setup manager module."""

from unittest.mock import patch

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
def cachyos_distro() -> DistroInfo:
    """Create CachyOS distro info (Arch derivative)."""
    return DistroInfo(
        name="CachyOS",
        version="rolling",
        id="cachyos",
        id_like=["arch"],
        package_manager=PackageManagerType.PACMAN,
        family=DistroFamily.ARCH,
    )


@pytest.fixture
def setup_manager_arch(arch_distro: DistroInfo) -> SetupManager:
    """Create SetupManager for Arch Linux."""
    return SetupManager(arch_distro)


@pytest.fixture
def setup_manager_fedora(fedora_distro: DistroInfo) -> SetupManager:
    """Create SetupManager for Fedora."""
    return SetupManager(fedora_distro)


class TestSetupManagerDistroNormalization:
    """Tests for distro key normalization in SetupManager."""

    def test_setup_component_passes_family_key_for_arch_derivative(
        self, cachyos_distro: DistroInfo
    ) -> None:
        """Ensure Arch derivatives pass 'arch' to installer modules."""
        manager = SetupManager(cachyos_distro)

        with patch("aps.core.setup.virtmanager.install") as mock_install:
            mock_install.return_value = True
            manager.setup_component("virtmanager")

            mock_install.assert_called_once()
            _, kwargs = mock_install.call_args
            assert kwargs["distro"] == "arch"


class TestSetupManagerAURHelper:
    """Tests for AUR helper setup."""

    def test_aur_helper_not_available_on_non_arch(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test that AUR helper setup raises error on non-Arch distros."""
        with patch("aps.core.setup.paru.install") as mock_paru_install:
            mock_paru_install.return_value = False
            with pytest.raises(SetupError, match="Failed to install paru"):
                setup_manager_fedora.setup_aur_helper()
            # Verify paru.install was called with fedora distro
            mock_paru_install.assert_called_once_with(distro="fedora")

    def test_aur_helper_already_installed(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test that setup succeeds if paru/yay is already installed."""
        with patch("aps.core.setup.paru.install") as mock_paru_install:
            mock_paru_install.return_value = True
            setup_manager_arch.setup_aur_helper()
            # Verify paru.install was called with arch distro
            mock_paru_install.assert_called_once_with(distro="arch")

    def test_aur_helper_installation_success(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test successful paru installation delegates to paru.install."""
        with patch("aps.core.setup.paru.install") as mock_paru_install:
            mock_paru_install.return_value = True
            setup_manager_arch.setup_aur_helper()
            # Verify paru.install was called
            mock_paru_install.assert_called_once_with(distro="arch")

    def test_aur_helper_installation_failure(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test that installation failure raises error."""
        with patch("aps.core.setup.paru.install") as mock_paru_install:
            mock_paru_install.return_value = False
            with pytest.raises(SetupError, match="Failed to install paru"):
                setup_manager_arch.setup_aur_helper()


class TestSetupManagerOllama:
    """Tests for Ollama setup."""

    def test_ollama_installation_success_arch(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test Ollama installation delegates to ollama.install with arch."""
        with patch("aps.core.setup.ollama.install") as mock_ollama_install:
            mock_ollama_install.return_value = True
            setup_manager_arch.setup_ollama()
            # Verify ollama.install was called with arch distro
            mock_ollama_install.assert_called_once_with(distro="arch")

    def test_ollama_installation_success_fedora(
        self, setup_manager_fedora: SetupManager
    ) -> None:
        """Test Ollama installation delegates to ollama.install with fedora."""
        with patch("aps.core.setup.ollama.install") as mock_ollama_install:
            mock_ollama_install.return_value = True
            setup_manager_fedora.setup_ollama()
            # Verify ollama.install was called with fedora distro
            mock_ollama_install.assert_called_once_with(distro="fedora")

    def test_ollama_installation_failure(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test that installation failure raises error."""
        with patch("aps.core.setup.ollama.install") as mock_ollama_install:
            mock_ollama_install.return_value = False
            with pytest.raises(SetupError, match="Failed to install Ollama"):
                setup_manager_arch.setup_ollama()


class TestComponentRegistry:
    """Tests for component registry and setup_component method."""

    def test_get_available_components(self) -> None:
        """Test that get_available_components returns all components."""
        components = SetupManager.get_available_components()

        # Verify all expected components are present
        expected_components = [
            "aur-helper",
            "ollama",
            "ohmyzsh",
            "brave",
            "thinkfan",
            "tlp",
            "autocpufreq",
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
        """Test setup_component delegates to paru installer module."""
        with patch("aps.installers.paru.install") as mock_install:
            mock_install.return_value = True
            setup_manager_arch.setup_component("aur-helper")
            mock_install.assert_called_once_with(distro="arch")

    def test_setup_component_ollama(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component calls ollama installer for ollama component."""
        with patch("aps.installers.ollama.install") as mock_install:
            mock_install.return_value = True
            setup_manager_arch.setup_component("ollama")
            mock_install.assert_called_once_with(distro="arch")

    def test_setup_component_ohmyzsh(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component calls installer module for ohmyzsh."""
        # Mock the ohmyzsh module's install function
        with patch("aps.installers.ohmyzsh.install") as mock_install:
            mock_install.return_value = True
            setup_manager_arch.setup_component("ohmyzsh")
            mock_install.assert_called_once_with(
                distro=setup_manager_arch.distro.id
            )

    def test_setup_component_brave(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component calls installer module for brave."""
        # Mock the brave module's install function
        with patch("aps.installers.brave.install") as mock_install:
            mock_install.return_value = True
            setup_manager_arch.setup_component("brave")
            mock_install.assert_called_once()

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
        # Mock the tlp module's install function to return False
        with patch("aps.installers.tlp.install") as mock_install:
            mock_install.return_value = False
            with pytest.raises(SetupError, match="Failed to setup tlp"):
                setup_manager_arch.setup_component("tlp")

    def test_setup_component_installer_exception(
        self, setup_manager_arch: SetupManager
    ) -> None:
        """Test setup_component raises error when installer raises error."""
        # Mock the thinkfan module's install function to raise exception
        with patch("aps.installers.thinkfan.install") as mock_install:
            mock_install.side_effect = Exception("Installation error")
            with pytest.raises(
                SetupError, match="Error during thinkfan setup"
            ):
                setup_manager_arch.setup_component("thinkfan")
