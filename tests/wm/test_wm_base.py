"""Tests for window manager configuration base class module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.wm.base import BaseWMConfig


class ConcreteWMConfig(BaseWMConfig):
    """Concrete implementation of BaseWMConfig for testing."""

    def install(self) -> bool:
        """Concrete implementation of install method."""
        return True

    def configure(self) -> bool:
        """Concrete implementation of configure method."""
        return True


class TestBaseWMConfigInit:
    """Test BaseWMConfig initialization."""

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
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

        config = ConcreteWMConfig()

        assert config.distro == "fedora"
        assert config.distro_info == fedora_distro
        assert config.pm is not None
        mock_distro.assert_called_once()
        mock_pm.assert_called_once()

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
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

        config = ConcreteWMConfig()

        assert config.distro == "arch"
        assert config.distro_info.family == DistroFamily.ARCH

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_with_debian(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization with Debian."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_distro.return_value = debian_distro
        mock_pm.return_value = MagicMock()

        config = ConcreteWMConfig()

        assert config.distro == "debian"
        assert config.distro_info.family == DistroFamily.DEBIAN

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_init_with_ubuntu(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization with Ubuntu."""
        ubuntu_distro = DistroInfo(
            name="Ubuntu",
            version="23.10",
            id="ubuntu",
            id_like=["debian"],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_distro.return_value = ubuntu_distro
        mock_pm.return_value = MagicMock()

        config = ConcreteWMConfig()

        assert config.distro == "ubuntu"
        assert config.distro_info.family == DistroFamily.DEBIAN

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
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

        config = ConcreteWMConfig()

        mock_pm.assert_called_once_with(test_distro)
        assert config.pm == mock_pm_instance


class TestAbstractMethods:
    """Test that abstract methods must be implemented."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseWMConfig cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseWMConfig()  # type: ignore

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_concrete_class_must_implement_install(
        self, _mock_pm: Mock, _mock_distro: Mock
    ) -> None:
        """Test that concrete class must implement install method."""

        class IncompleteWMConfig(BaseWMConfig):
            def configure(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteWMConfig()  # type: ignore

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
    def test_concrete_class_must_implement_configure(
        self, _mock_pm: Mock, _mock_distro: Mock
    ) -> None:
        """Test that concrete class must implement configure method."""

        class IncompleteWMConfig(BaseWMConfig):
            def install(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteWMConfig()  # type: ignore

    @patch("aps.wm.base.detect_distro")
    @patch("aps.wm.base.get_package_manager")
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

        config = ConcreteWMConfig()

        assert config is not None
        assert isinstance(config, BaseWMConfig)
