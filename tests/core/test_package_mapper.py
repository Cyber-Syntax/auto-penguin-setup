"""Tests for package mapper module."""

from pathlib import Path

from aps.core.distro import DistroInfo
from aps.core.package_mapper import PackageMapper, PackageMapping


class TestPackageMapping:
    """Test PackageMapping dataclass."""

    def test_is_official(self) -> None:
        """Test official package detection."""
        mapping = PackageMapping(original_name="git", mapped_name="git", source="official")
        assert mapping.is_official
        assert not mapping.is_copr
        assert not mapping.is_aur
        assert not mapping.is_ppa

    def test_is_copr(self) -> None:
        """Test COPR package detection."""
        mapping = PackageMapping(
            original_name="lazygit", mapped_name="lazygit", source="COPR:atim/lazygit"
        )
        assert mapping.is_copr
        assert not mapping.is_official
        assert not mapping.is_aur

    def test_is_aur(self) -> None:
        """Test AUR package detection."""
        mapping = PackageMapping(
            original_name="brave", mapped_name="brave-bin", source="AUR:brave-bin"
        )
        assert mapping.is_aur
        assert not mapping.is_official
        assert not mapping.is_copr

    def test_is_ppa(self) -> None:
        """Test PPA package detection."""
        mapping = PackageMapping(
            original_name="test", mapped_name="test-pkg", source="PPA:user/repo"
        )
        assert mapping.is_ppa
        assert not mapping.is_official

    def test_get_repo_name_copr(self) -> None:
        """Test extracting COPR repo name."""
        mapping = PackageMapping(original_name="test", mapped_name="test", source="COPR:user/repo")
        assert mapping.get_repo_name() == "user/repo"

    def test_get_repo_name_ppa(self) -> None:
        """Test extracting PPA repo name."""
        mapping = PackageMapping(original_name="test", mapped_name="test", source="PPA:user/repo")
        assert mapping.get_repo_name() == "user/repo"

    def test_get_repo_name_official(self) -> None:
        """Test repo name for official packages."""
        mapping = PackageMapping(original_name="git", mapped_name="git", source="official")
        assert mapping.get_repo_name() is None

    def test_get_repo_name_flatpak(self) -> None:
        """Test extracting Flatpak remote name."""
        mapping = PackageMapping(original_name="test", mapped_name="test", source="flatpak:flathub")
        assert mapping.get_repo_name() == "flathub"


class TestPackageMapper:
    """Test PackageMapper functionality."""

    def test_load_fedora_mappings(self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo) -> None:
        """Test loading Fedora package mappings."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        assert "brave-browser" in mapper.mappings
        assert "lazygit" in mapper.mappings

    def test_load_arch_mappings(self, sample_pkgmap_ini: Path, arch_distro: DistroInfo) -> None:
        """Test loading Arch package mappings."""
        mapper = PackageMapper(sample_pkgmap_ini, arch_distro)

        assert "brave-browser" in mapper.mappings
        brave = mapper.mappings["brave-browser"]
        assert brave.mapped_name == "brave-bin"
        assert brave.is_aur

    def test_load_debian_mappings(self, sample_pkgmap_ini: Path, debian_distro: DistroInfo) -> None:
        """Test loading Debian package mappings."""
        mapper = PackageMapper(sample_pkgmap_ini, debian_distro)

        assert "brave-browser" in mapper.mappings

    def test_map_package_with_mapping(
        self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo
    ) -> None:
        """Test mapping package with defined mapping."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        mapping = mapper.map_package("lazygit")
        assert mapping.original_name == "lazygit"
        assert mapping.mapped_name == "lazygit"
        assert mapping.source == "COPR:atim/lazygit"

    def test_map_package_without_mapping(
        self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo
    ) -> None:
        """Test mapping package without defined mapping."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        mapping = mapper.map_package("unknown-package")
        assert mapping.original_name == "unknown-package"
        assert mapping.mapped_name == "unknown-package"
        assert mapping.source == "official"

    def test_map_package_with_category(
        self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo
    ) -> None:
        """Test mapping package with category."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        mapping = mapper.map_package("lazygit", category="development")
        assert mapping.category == "development"

    def test_parse_copr_mapping(self, tmp_path: Path, fedora_distro: DistroInfo) -> None:
        """Test parsing COPR mapping format."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, fedora_distro)

        mapping = mapper._parse_mapping("test", "COPR:user/repo:package")
        assert mapping.source == "COPR:user/repo"
        assert mapping.mapped_name == "package"

    def test_parse_copr_mapping_without_package(
        self, tmp_path: Path, fedora_distro: DistroInfo
    ) -> None:
        """Test parsing COPR mapping without explicit package name - uses original_name."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, fedora_distro)

        # When COPR mapping is just "COPR:user/repo", it should use original_name
        mapping = mapper._parse_mapping("lazygit", "COPR:dejan/lazygit")
        assert mapping.source == "COPR:dejan/lazygit"
        assert mapping.mapped_name == "lazygit"
        assert mapping.original_name == "lazygit"

    def test_parse_aur_mapping(self, tmp_path: Path, arch_distro: DistroInfo) -> None:
        """Test parsing AUR mapping format."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, arch_distro)

        mapping = mapper._parse_mapping("test", "AUR:package-bin")
        assert mapping.source == "AUR:package-bin"
        assert mapping.mapped_name == "package-bin"

    def test_parse_ppa_mapping(self, tmp_path: Path, debian_distro: DistroInfo) -> None:
        """Test parsing PPA mapping format."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, debian_distro)

        mapping = mapper._parse_mapping("test", "PPA:user/repo:package")
        assert mapping.source == "PPA:user/repo"
        assert mapping.mapped_name == "package"

    def test_parse_flatpak_mapping(self, tmp_path: Path, fedora_distro: DistroInfo) -> None:
        """Test parsing Flatpak mapping format."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, fedora_distro)

        mapping = mapper._parse_mapping("test", "flatpak:flathub:package")
        assert mapping.source == "flatpak:flathub"
        assert mapping.mapped_name == "package"

    def test_parse_official_mapping(self, tmp_path: Path, fedora_distro: DistroInfo) -> None:
        """Test parsing official package mapping."""
        # Create empty pkgmap for mapper initialization
        empty_pkgmap = tmp_path / "empty.ini"
        empty_pkgmap.write_text("")

        mapper = PackageMapper(empty_pkgmap, fedora_distro)

        mapping = mapper._parse_mapping("test", "package-name")
        assert mapping.source == "official"
        assert mapping.mapped_name == "package-name"

    def test_has_mapping(self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo) -> None:
        """Test checking if package has mapping."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        assert mapper.has_mapping("lazygit")
        assert not mapper.has_mapping("unknown-package")

    def test_get_packages_by_source(
        self, sample_pkgmap_ini: Path, fedora_distro: DistroInfo
    ) -> None:
        """Test getting packages by source."""
        mapper = PackageMapper(sample_pkgmap_ini, fedora_distro)

        copr_packages = mapper.get_packages_by_source("COPR:")
        assert len(copr_packages) == 2  # brave-browser and lazygit
        assert all(p.is_copr for p in copr_packages)

        official_packages = mapper.get_packages_by_source("official")
        assert len(official_packages) >= 0  # May have official packages
        assert all(p.is_official for p in official_packages)

    def test_nonexistent_config(self, tmp_path: Path, fedora_distro: DistroInfo) -> None:
        """Test handling nonexistent pkgmap file."""
        mapper = PackageMapper(tmp_path / "nonexistent.ini", fedora_distro)
        assert len(mapper.mappings) == 0
