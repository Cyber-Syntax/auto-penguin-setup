"""Tests for E2E fixtures."""

from pathlib import Path


def test_mock_libvirt_filesystem_fixture(
    mock_libvirt_filesystem: Path,
) -> None:
    """Validates fixture creates correct directory structure under tmp_root."""
    # Verify the fixture returns a path
    assert mock_libvirt_filesystem is not None
    assert isinstance(mock_libvirt_filesystem, Path)

    # Verify the libvirt directory structure exists
    assert mock_libvirt_filesystem.exists()
    assert mock_libvirt_filesystem.is_dir()

    # Verify the standard libvirt subdirectories are created
    expected_dirs = [
        "qemu",
        "qemu-kvm",
        "networks",
        "storage",
        "hooks",
    ]
    for subdir in expected_dirs:
        subdir_path = mock_libvirt_filesystem / subdir
        assert subdir_path.exists(), (
            f"Directory {subdir} not found in {mock_libvirt_filesystem}"
        )
        assert subdir_path.is_dir()

    # Verify fixture config files were copied (if they exist in test fixtures)
    fixture_virt_dir = Path(__file__).parent.parent / "fixtures" / "virt"
    if fixture_virt_dir.exists():
        for config_file in fixture_virt_dir.glob("*.conf"):
            copied_file = mock_libvirt_filesystem / config_file.name
            assert copied_file.exists(), (
                f"Config file {config_file.name} not copied"
            )
            assert copied_file.is_file()
