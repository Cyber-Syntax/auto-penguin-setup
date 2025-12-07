"""Tests for distribution detection module."""

import pytest

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType


class TestDistroInfo:
    """Test DistroInfo class and detection."""

    def test_from_os_release_fedora(self, sample_os_release_fedora):
        """Test parsing Fedora os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_fedora)

        assert distro.id == "fedora"
        assert distro.name == "Fedora Linux"
        assert distro.version == "39"
        assert distro.package_manager == PackageManagerType.DNF
        assert distro.family == DistroFamily.FEDORA

    def test_from_os_release_arch(self, sample_os_release_arch):
        """Test parsing Arch os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_arch)

        assert distro.id == "arch"
        assert distro.name == "Arch Linux"
        assert distro.package_manager == PackageManagerType.PACMAN
        assert distro.family == DistroFamily.ARCH

    def test_from_os_release_debian(self, sample_os_release_debian):
        """Test parsing Debian os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_debian)

        assert distro.id == "debian"
        assert distro.name == "Debian GNU/Linux"
        assert distro.version == "12"
        assert distro.package_manager == PackageManagerType.APT
        assert distro.family == DistroFamily.DEBIAN

    def test_from_os_release_missing_file(self, tmp_path):
        """Test handling of missing os-release file."""
        with pytest.raises(FileNotFoundError):
            DistroInfo.from_os_release(tmp_path / "nonexistent")

    def test_derivative_distro_nobara(self, tmp_path):
        """Test detection of Nobara (Fedora derivative)."""
        content = """
NAME="Nobara Linux"
ID=nobara
ID_LIKE=fedora
VERSION_ID=39
"""
        os_release = tmp_path / "os-release-nobara"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.FEDORA
        assert distro.package_manager == PackageManagerType.DNF

    def test_derivative_distro_cachyos(self, tmp_path):
        """Test detection of CachyOS (Arch derivative)."""
        content = """
NAME="CachyOS"
ID=cachyos
ID_LIKE=arch
"""
        os_release = tmp_path / "os-release-cachyos"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.ARCH
        assert distro.package_manager == PackageManagerType.PACMAN

    def test_derivative_distro_ubuntu(self, tmp_path):
        """Test detection of Ubuntu (Debian derivative)."""
        content = """
NAME="Ubuntu"
ID=ubuntu
ID_LIKE=debian
VERSION_ID=22.04
"""
        os_release = tmp_path / "os-release-ubuntu"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.DEBIAN
        assert distro.package_manager == PackageManagerType.APT

    def test_rolling_version_default(self, tmp_path):
        """Test default version for rolling release."""
        content = """
NAME="Arch Linux"
ID=arch
"""
        os_release = tmp_path / "os-release-arch-rolling"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.version == "rolling"

    def test_parse_os_release_quoted_values(self, tmp_path):
        """Test parsing os-release with quoted values."""
        content = """
NAME="Test Distribution"
ID="test"
VERSION="1.0"
"""
        os_release = tmp_path / "os-release-quoted"
        os_release.write_text(content)

        data = DistroInfo._parse_os_release(os_release)
        assert data["NAME"] == "Test Distribution"
        assert data["ID"] == "test"
        assert data["VERSION"] == "1.0"

    def test_parse_os_release_unquoted_values(self, tmp_path):
        """Test parsing os-release with unquoted values."""
        content = """
NAME=TestDistro
ID=test
"""
        os_release = tmp_path / "os-release-unquoted"
        os_release.write_text(content)

        data = DistroInfo._parse_os_release(os_release)
        assert data["NAME"] == "TestDistro"
        assert data["ID"] == "test"
