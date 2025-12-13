"""Tests for package tracking module."""

from datetime import UTC, datetime
from pathlib import Path

from aps.core.tracking import PackageRecord, PackageTracker


class TestPackageRecord:
    """Test PackageRecord dataclass."""

    def test_create_record(self) -> None:
        """Test creating package record with current timestamp."""
        record = PackageRecord.create("git", source="official")

        assert record.name == "git"
        assert record.source == "official"
        assert record.category is None
        assert record.mapped_name is None

        # Verify timestamp is recent (within last minute)
        timestamp = datetime.fromisoformat(record.installed_at)
        now = datetime.now(UTC)
        delta = (now - timestamp).total_seconds()
        assert delta < 60

    def test_create_record_with_all_fields(self) -> None:
        """Test creating record with all fields."""
        record = PackageRecord.create(
            name="lazygit",
            source="COPR:atim/lazygit",
            category="development",
            mapped_name="lazygit",
        )

        assert record.name == "lazygit"
        assert record.source == "COPR:atim/lazygit"
        assert record.category == "development"
        assert record.mapped_name == "lazygit"

    def test_to_dict(self) -> None:
        """Test converting record to dictionary."""
        record = PackageRecord.create("git", source="official", category="dev")
        data = record.to_dict()

        assert data["name"] == "git"
        assert data["source"] == "official"
        assert data["category"] == "dev"
        assert "installed_at" in data

    def test_from_dict(self) -> None:
        """Test creating record from dictionary."""
        data = {
            "name": "vim",
            "source": "official",
            "installed_at": "2025-01-21T10:00:00+00:00",
            "category": "editor",
            "mapped_name": None,
        }

        record = PackageRecord.from_dict(data)
        assert record.name == "vim"
        assert record.source == "official"
        assert record.category == "editor"


class TestPackageTracker:
    """Test PackageTracker functionality."""

    def test_create_tracker_default_path(self) -> None:
        """Test creating tracker with default path."""
        tracker = PackageTracker()
        assert tracker.db_path.name == "metadata.jsonl"
        assert "auto-penguin-setup" in str(tracker.db_path)

    def test_create_tracker_custom_path(self, tmp_path: Path) -> None:
        """Test creating tracker with custom path."""
        db_path = tmp_path / "custom.jsonl"
        tracker = PackageTracker(db_path)
        assert tracker.db_path == db_path

    def test_track_install(self, tmp_path: Path) -> None:
        """Test tracking package installation."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        record = PackageRecord.create("git", source="official")
        tracker.track_install(record)

        # Verify file was created and contains data
        assert db_path.exists()
        assert db_path.stat().st_size > 0

    def test_get_tracked_packages(self, tmp_path: Path) -> None:
        """Test retrieving tracked packages."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track multiple packages
        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))
        tracker.track_install(PackageRecord.create("lazygit", source="COPR:atim/lazygit"))

        # Retrieve and verify
        packages = tracker.get_tracked_packages()
        assert len(packages) == 3
        assert packages[0].name == "git"
        assert packages[1].name == "vim"
        assert packages[2].name == "lazygit"

    def test_get_package(self, tmp_path: Path) -> None:
        """Test getting specific package."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))

        package = tracker.get_package("vim")
        assert package is not None
        assert package.name == "vim"

        nonexistent = tracker.get_package("nonexistent")
        assert nonexistent is None

    def test_is_tracked(self, tmp_path: Path) -> None:
        """Test checking if package is tracked."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))

        assert tracker.is_tracked("git")
        assert not tracker.is_tracked("nonexistent")

    def test_remove_package(self, tmp_path: Path) -> None:
        """Test removing package from tracking."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))

        # Remove git
        success = tracker.remove_package("git")
        assert success

        # Verify git is removed but vim remains
        packages = tracker.get_tracked_packages()
        assert len(packages) == 1
        assert packages[0].name == "vim"

    def test_remove_nonexistent_package(self, tmp_path: Path) -> None:
        """Test removing package that doesn't exist."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        success = tracker.remove_package("nonexistent")
        assert not success

    def test_remove_multiple(self, tmp_path: Path) -> None:
        """Test removing multiple packages."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))
        tracker.track_install(PackageRecord.create("emacs", source="official"))

        removed = tracker.remove_multiple(["git", "emacs"])
        assert removed == 2

        packages = tracker.get_tracked_packages()
        assert len(packages) == 1
        assert packages[0].name == "vim"

    def test_get_packages_by_category(self, tmp_path: Path) -> None:
        """Test filtering packages by category."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official", category="dev"))
        tracker.track_install(PackageRecord.create("vim", source="official", category="editor"))
        tracker.track_install(PackageRecord.create("gcc", source="official", category="dev"))

        dev_packages = tracker.get_packages_by_category("dev")
        assert len(dev_packages) == 2
        assert all(p.category == "dev" for p in dev_packages)

    def test_get_packages_by_source(self, tmp_path: Path) -> None:
        """Test filtering packages by source."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("lazygit", source="COPR:atim/lazygit"))
        tracker.track_install(PackageRecord.create("brave", source="COPR:user/brave"))

        copr_packages = tracker.get_packages_by_source("COPR:")
        assert len(copr_packages) == 2

        official_packages = tracker.get_packages_by_source("official")
        assert len(official_packages) == 1

    def test_get_categories(self, tmp_path: Path) -> None:
        """Test getting unique categories."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official", category="dev"))
        tracker.track_install(PackageRecord.create("vim", source="official", category="editor"))
        tracker.track_install(PackageRecord.create("gcc", source="official", category="dev"))

        categories = tracker.get_categories()
        assert len(categories) == 2
        assert "dev" in categories
        assert "editor" in categories

    def test_count_packages(self, tmp_path: Path) -> None:
        """Test counting tracked packages."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        assert tracker.count_packages() == 0

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))

        assert tracker.count_packages() == 2

    def test_clear_all(self, tmp_path: Path) -> None:
        """Test clearing all tracked packages."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))
        tracker.track_install(PackageRecord.create("vim", source="official"))

        tracker.clear_all()

        assert tracker.count_packages() == 0
        assert db_path.stat().st_size == 0

    def test_backup_database(self, tmp_path: Path) -> None:
        """Test backing up tracking database."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        tracker.track_install(PackageRecord.create("git", source="official"))

        backup_path = tracker.backup_database()

        assert backup_path.exists()
        assert "backup" in backup_path.name
        assert backup_path.stat().st_size == db_path.stat().st_size

    def test_track_multiple(self, tmp_path: Path) -> None:
        """Test tracking multiple packages at once."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        records = [
            PackageRecord.create("git", source="official"),
            PackageRecord.create("vim", source="official"),
            PackageRecord.create("emacs", source="official"),
        ]

        tracker.track_multiple(records)

        assert tracker.count_packages() == 3

    def test_track_install_prevents_duplicates(self, tmp_path: Path) -> None:
        """Test that tracking same package twice doesn't create duplicates."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track package first time
        record1 = PackageRecord.create("git", source="official", category="dev")
        tracker.track_install(record1)

        # Track same package again
        record2 = PackageRecord.create("git", source="official", category="dev")
        tracker.track_install(record2)

        # Should only have one entry
        packages = tracker.get_tracked_packages()
        assert len(packages) == 1
        assert packages[0].name == "git"

    def test_track_install_updates_existing_package(self, tmp_path: Path) -> None:
        """Test that tracking existing package updates the record."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track package from official source
        record1 = PackageRecord.create("git", source="official", category="dev")
        tracker.track_install(record1)

        # Update to different source
        record2 = PackageRecord.create("git", source="COPR:test/git", category="tools")
        tracker.track_install(record2)

        # Should still have one entry with updated info
        packages = tracker.get_tracked_packages()
        assert len(packages) == 1
        assert packages[0].name == "git"
        assert packages[0].source == "COPR:test/git"
        assert packages[0].category == "tools"

    def test_track_multiple_prevents_duplicates(self, tmp_path: Path) -> None:
        """Test that tracking multiple packages prevents duplicates."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track initial packages
        records1 = [
            PackageRecord.create("git", source="official"),
            PackageRecord.create("vim", source="official"),
        ]
        tracker.track_multiple(records1)

        # Track again with some duplicates and new packages
        records2 = [
            PackageRecord.create("git", source="official"),  # duplicate
            PackageRecord.create("emacs", source="official"),  # new
            PackageRecord.create("vim", source="official"),  # duplicate
        ]
        tracker.track_multiple(records2)

        # Should have 3 unique packages
        packages = tracker.get_tracked_packages()
        assert len(packages) == 3
        names = {p.name for p in packages}
        assert names == {"git", "vim", "emacs"}

    def test_track_multiple_with_all_duplicates(self, tmp_path: Path) -> None:
        """Test tracking multiple packages that are all duplicates."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track initial packages
        records1 = [
            PackageRecord.create("git", source="official"),
            PackageRecord.create("vim", source="official"),
        ]
        tracker.track_multiple(records1)

        # Track same packages again
        records2 = [
            PackageRecord.create("git", source="official"),
            PackageRecord.create("vim", source="official"),
        ]
        tracker.track_multiple(records2)

        # Should still have only 2 packages
        packages = tracker.get_tracked_packages()
        assert len(packages) == 2

    def test_field_order_consistency(self, tmp_path: Path) -> None:
        """Test that JSONL field order is consistent."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        record = PackageRecord.create(
            "git", source="official", category="dev", mapped_name="git-core"
        )
        tracker.track_install(record)

        # Read raw JSONL and verify field order
        import orjson

        with open(db_path, encoding="utf-8") as f:
            line = f.readline().strip()
            data = orjson.loads(line)

        # Verify field order: name, mapped_name, source, category, installed_at
        keys = list(data.keys())
        assert keys[0] == "name"
        assert keys[1] == "mapped_name"
        assert keys[2] == "source"
        assert keys[3] == "category"
        assert keys[4] == "installed_at"

    def test_track_by_mapped_name_prevents_duplicates(self, tmp_path: Path) -> None:
        """Test that tracking by mapped_name also prevents duplicates."""
        db_path = tmp_path / "tracking.jsonl"
        tracker = PackageTracker(db_path)

        # Track package with mapped_name
        record1 = PackageRecord.create("git", source="official", mapped_name="git-core")
        tracker.track_install(record1)

        # Try to track by mapped_name (should update, not duplicate)
        record2 = PackageRecord.create("git-core", source="official")
        tracker.track_install(record2)

        # Should only have one entry
        packages = tracker.get_tracked_packages()
        assert len(packages) == 1
