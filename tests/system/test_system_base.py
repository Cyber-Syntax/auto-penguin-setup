"""Tests for system configuration base class module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.base import BaseSystemConfig


class ConcreteSystemConfig(BaseSystemConfig):
    """Concrete implementation of BaseSystemConfig for testing."""

    def configure(self) -> bool:
        """Concrete implementation of configure method."""
        return True


class TestBaseSystemConfigInit:
    """Test BaseSystemConfig initialization."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_init_initializes_attributes(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that __init__ properly initializes attributes."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = fedora_distro
        mock_pm.return_value = MagicMock()

        config = ConcreteSystemConfig()

        assert config.distro == "fedora"
        assert config.distro_info == fedora_distro
        assert config.pm is not None
        mock_distro.assert_called_once()
        mock_pm.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_init_with_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization with Arch Linux."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_distro.return_value = arch_distro
        mock_pm.return_value = MagicMock()

        config = ConcreteSystemConfig()

        assert config.distro == "arch"
        assert config.distro_info.family == DistroFamily.ARCH


class TestBaseSystemConfigAbstractMethods:
    """Test abstract methods enforcement."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseSystemConfig cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSystemConfig()  # type: ignore

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_concrete_implementation_must_implement_configure(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that concrete implementations must provide configure method."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm.return_value = MagicMock()

        # This should work because ConcreteSystemConfig implements configure
        config = ConcreteSystemConfig()
        assert config.configure() is True


class TestBaseSystemConfigPackageManager:
    """Test package manager integration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_package_manager_fedora(
        self, mock_get_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that package manager is correctly initialized for Fedora."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = fedora_distro
        mock_pm_instance = MagicMock()
        mock_get_pm.return_value = mock_pm_instance

        config = ConcreteSystemConfig()

        assert config.pm == mock_pm_instance
        mock_get_pm.assert_called_once_with(fedora_distro)

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_package_manager_arch(
        self, mock_get_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that package manager is correctly initialized for Arch."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_distro.return_value = arch_distro
        mock_pm_instance = MagicMock()
        mock_get_pm.return_value = mock_pm_instance

        config = ConcreteSystemConfig()

        assert config.pm == mock_pm_instance
        mock_get_pm.assert_called_once_with(arch_distro)
