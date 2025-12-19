"""Tests for display manager configuration base class module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.display.base import BaseDisplayManager


class ConcreteDisplayManager(BaseDisplayManager):
    """Concrete implementation of BaseDisplayManager for testing."""

    def install(self) -> bool:
        """Concrete implementation of install method."""
        return True

    def configure_autologin(self, username: str, session: str) -> bool:
        """Concrete implementation of configure_autologin method."""
        return True


class TestBaseDisplayManagerInit:
    """Test BaseDisplayManager initialization."""

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
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

        dm = ConcreteDisplayManager()

        assert dm.distro == "fedora"
        assert dm.distro_info == fedora_distro
        assert dm.pm is not None
        mock_distro.assert_called_once()
        mock_pm.assert_called_once()

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
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

        dm = ConcreteDisplayManager()

        assert dm.distro == "arch"
        assert dm.distro_info.family == DistroFamily.ARCH

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_pm_initialized_from_distro_info(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that package manager is initialized with correct distro_info."""
        test_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = test_distro
        mock_pm_instance = MagicMock()
        mock_pm.return_value = mock_pm_instance

        dm = ConcreteDisplayManager()

        mock_pm.assert_called_once_with(test_distro)
        assert dm.pm == mock_pm_instance


class TestAbstractMethods:
    """Test that abstract methods must be implemented."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseDisplayManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseDisplayManager()  # type: ignore

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_concrete_class_must_implement_install(
        self, _mock_pm: Mock, _mock_distro: Mock
    ) -> None:
        """Test that concrete class must implement install method."""

        class IncompleteDisplayManager(BaseDisplayManager):
            def configure_autologin(self, username: str, session: str) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteDisplayManager()  # type: ignore

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_concrete_class_must_implement_configure_autologin(
        self, _mock_pm: Mock, _mock_distro: Mock
    ) -> None:
        """Test that concrete class must implement configure_autologin method."""

        class IncompleteDisplayManager(BaseDisplayManager):
            def install(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteDisplayManager()  # type: ignore

    @patch("aps.display.base.detect_distro")
    @patch("aps.display.base.get_package_manager")
    def test_concrete_implementation_succeeds(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that proper concrete implementation works."""
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

        dm = ConcreteDisplayManager()

        assert dm is not None
        assert isinstance(dm, BaseDisplayManager)
