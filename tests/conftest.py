"""Test fixtures for pytest."""

import logging
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType

# Store global mock reference
_run_privileged_mock: MagicMock | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest to mock privileged operations."""
    global _run_privileged_mock

    # Patch run_privileged globally for all tests
    patcher = patch("aps.utils.privilege.run_privileged")
    _run_privileged_mock = patcher.start()
    _run_privileged_mock.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    # Configure logging to avoid "I/O operation on closed file" errors
    # Remove all handlers and use NullHandler for tests
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(logging.NullHandler())
    root_logger.setLevel(logging.DEBUG)


@pytest.fixture(autouse=True)
def mock_run_privileged() -> Generator[MagicMock, None, None]:
    """Global fixture to ensure run_privileged is mocked in tests and provides access to mock."""
    global _run_privileged_mock
    if _run_privileged_mock is None:
        raise RuntimeError("Global run_privileged mock not initialized")

    # Reset mock before each test - including side_effect
    _run_privileged_mock.reset_mock(side_effect=True)
    # Set default return value
    _run_privileged_mock.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )
    yield _run_privileged_mock


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def fedora_distro() -> DistroInfo:
    """Fedora distribution fixture."""
    return DistroInfo(
        name="Fedora Linux",
        version="39",
        id="fedora",
        id_like=[],
        package_manager=PackageManagerType.DNF,
        family=DistroFamily.FEDORA,
    )


@pytest.fixture
def arch_distro() -> DistroInfo:
    """Arch Linux distribution fixture."""
    return DistroInfo(
        name="Arch Linux",
        version="rolling",
        id="arch",
        id_like=["archlinux"],
        package_manager=PackageManagerType.PACMAN,
        family=DistroFamily.ARCH,
    )


@pytest.fixture
def sample_os_release_fedora(tmp_path: Path) -> Path:
    """Sample /etc/os-release for Fedora."""
    content = """
NAME="Fedora Linux"
VERSION="39 (Workstation Edition)"
ID=fedora
VERSION_ID=39
PRETTY_NAME="Fedora Linux 39 (Workstation Edition)"
ID_LIKE=""
"""
    os_release = tmp_path / "os-release-fedora"
    os_release.write_text(content)
    return os_release


@pytest.fixture
def sample_os_release_arch(tmp_path: Path) -> Path:
    """Sample /etc/os-release for Arch."""
    content = """
NAME="Arch Linux"
ID=arch
ID_LIKE=archlinux
PRETTY_NAME="Arch Linux"
"""
    os_release = tmp_path / "os-release-arch"
    os_release.write_text(content)
    return os_release


@pytest.fixture
def sample_packages_ini(tmp_path: Path) -> Path:
    """Sample packages.ini configuration."""
    content = """
[development]
git
vim
python3

[multimedia]
ffmpeg
vlc
gimp
"""
    packages_ini = tmp_path / "packages.ini"
    packages_ini.write_text(content)
    return packages_ini


@pytest.fixture
def sample_pkgmap_ini(tmp_path: Path) -> Path:
    """Sample pkgmap.ini configuration."""
    content = """
[pkgmap.fedora]
brave-browser=COPR:lecramyajiv/brave-browser:brave-browser
visual-studio-code=code
lazygit=COPR:atim/lazygit

[pkgmap.arch]
brave-browser=AUR:brave-bin
visual-studio-code=visual-studio-code-bin
lazygit=lazygit
"""
    pkgmap_ini = tmp_path / "pkgmap.ini"
    pkgmap_ini.write_text(content)
    return pkgmap_ini
