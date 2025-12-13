"""Test fixtures for pytest."""

from pathlib import Path

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType


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
def debian_distro() -> DistroInfo:
    """Debian distribution fixture."""
    return DistroInfo(
        name="Debian GNU/Linux",
        version="12",
        id="debian",
        id_like=[],
        package_manager=PackageManagerType.APT,
        family=DistroFamily.DEBIAN,
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
def sample_os_release_debian(tmp_path: Path) -> Path:
    """Sample /etc/os-release for Debian."""
    content = """
NAME="Debian GNU/Linux"
VERSION="12 (bookworm)"
ID=debian
VERSION_ID=12
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
"""
    os_release = tmp_path / "os-release-debian"
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

[pkgmap.debian]
brave-browser=brave-browser
visual-studio-code=code
lazygit=lazygit
"""
    pkgmap_ini = tmp_path / "pkgmap.ini"
    pkgmap_ini.write_text(content)
    return pkgmap_ini
