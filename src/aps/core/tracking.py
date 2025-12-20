"""Package tracking using JSONL database for fast, simple storage."""

import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

import orjson

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class PackageRecord:
    """Represents a tracked package installation."""

    name: str
    mapped_name: str | None = (
        None  # Actual installed name if different from 'name'
    )
    source: str = (
        "official"  # "official", "COPR:user/repo", "AUR:pkg", "flatpak:remote"
    )
    category: str | None = None
    installed_at: str = ""  # ISO 8601 timestamp - set in create()

    @classmethod
    def create(
        cls,
        name: str,
        source: str = "official",
        category: str | None = None,
        mapped_name: str | None = None,
    ) -> Self:
        """Create a new package record with current timestamp.

        Args:
            name: Package name (original/generic name)
            source: Package source (default: "official")
            category: Optional category for organization
            mapped_name: Actual installed package name if different

        Returns:
            New PackageRecord instance

        """
        timestamp = (
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
        )
        return cls(
            name=name,
            mapped_name=mapped_name,
            source=source,
            category=category,
            installed_at=timestamp,
        )

    def to_dict(self) -> dict[str, str | None]:
        """Convert record to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> Self:
        """Create record from dictionary."""
        return cls(**data)  # type: ignore[arg-type]


class PackageTracker:
    """Tracks installed packages using JSONL (JSON Lines) format.

    JSONL provides:
    - Simple append-only operations
    - Fast parsing with orjson (5-10x faster than stdlib json)
    - Easy backup and migration
    - Human-readable format
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize package tracker with database path.

        Args:
            db_path: Path to JSONL tracking database
                    (default: ~/.config/auto-penguin-setup/metadata.jsonl)

        """
        if db_path is None:
            config_dir = Path.home() / ".config" / "auto-penguin-setup"
            db_path = config_dir / "metadata.jsonl"

        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Create database file and parent directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self.db_path.touch()

    def track_install(self, record: PackageRecord) -> None:
        """Track a package installation, preventing duplicates.

        If package already tracked:
        - Same source → Update timestamp only
        - Different source → Update all fields (migration)
        If package doesn't exist → Add new record

        Args:
            record: PackageRecord to track

        """
        # Load all existing packages
        packages = self.get_tracked_packages()

        # Check if package exists (by name or mapped_name)
        existing_idx = None
        for idx, pkg in enumerate(packages):
            if pkg.name == record.name or (
                pkg.mapped_name and pkg.mapped_name == record.name
            ):
                existing_idx = idx
                break

        if existing_idx is not None:
            # Update existing record
            packages[existing_idx] = record
            logger.debug("Updated existing package: %s", record.name)
        else:
            # Add new record
            packages.append(record)
            logger.debug("Added new package: %s", record.name)

        # Write all packages back
        self._write_all_packages(packages)

    def track_multiple(self, records: list[PackageRecord]) -> None:
        """Track multiple package installations at once, preventing duplicates.

        For each record:
        - If package exists → Update existing record
        - If package doesn't exist → Add new record

        Args:
            records: List of PackageRecord objects to track

        """
        if not records:
            return

        # Load all existing packages
        packages = self.get_tracked_packages()

        # Create lookup for fast checking (name and mapped_name)
        pkg_lookup: dict[str, int] = {}
        for idx, pkg in enumerate(packages):
            pkg_lookup[pkg.name] = idx
            if pkg.mapped_name:
                pkg_lookup[pkg.mapped_name] = idx

        # Process each record
        added_count = 0
        updated_count = 0
        for record in records:
            if record.name in pkg_lookup:
                # Update existing
                idx = pkg_lookup[record.name]
                packages[idx] = record
                updated_count += 1
                logger.debug("Updated existing package: %s", record.name)
            else:
                # Add new
                packages.append(record)
                pkg_lookup[record.name] = len(packages) - 1
                if record.mapped_name:
                    pkg_lookup[record.mapped_name] = len(packages) - 1
                added_count += 1
                logger.debug("Added new package: %s", record.name)

        logger.info(
            "Tracked %d packages: %d added, %d updated",
            len(records),
            added_count,
            updated_count,
        )

        # Write all packages back
        self._write_all_packages(packages)

    def get_tracked_packages(self) -> list[PackageRecord]:
        """Load all tracked packages from JSONL database.

        Returns:
            List of all tracked PackageRecord objects

        """
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            return []

        packages: list[PackageRecord] = []
        with open(self.db_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = orjson.loads(line)
                packages.append(PackageRecord.from_dict(data))

        return packages

    def get_package(self, name: str) -> PackageRecord | None:
        """Get a specific package record by name.

        Returns the most recent record if multiple exist.

        Args:
            name: Package name to search for

        Returns:
            PackageRecord if found, None otherwise

        """
        packages = self.get_tracked_packages()

        # Return most recent record for this package
        for record in reversed(packages):
            if record.name == name or record.mapped_name == name:
                return record

        return None

    def is_tracked(self, name: str) -> bool:
        """Check if a package is currently tracked.

        Args:
            name: Package name to check

        Returns:
            True if package is tracked, False otherwise

        """
        return self.get_package(name) is not None

    def remove_package(self, name: str) -> bool:
        """Remove a package from tracking.

        Rewrites the entire JSONL file without the specified package.

        Args:
            name: Package name to remove

        Returns:
            True if package was found and removed, False otherwise

        """
        packages = self.get_tracked_packages()
        original_count = len(packages)

        # Filter out the package to remove
        filtered_packages = [
            p for p in packages if p.name != name and p.mapped_name != name
        ]

        if len(filtered_packages) == original_count:
            return False  # Package not found

        # Rewrite database without removed package
        self._write_all_packages(filtered_packages)
        return True

    def remove_multiple(self, names: list[str]) -> int:
        """Remove multiple packages from tracking.

        Args:
            names: List of package names to remove

        Returns:
            Number of packages actually removed

        """
        packages = self.get_tracked_packages()
        names_set = set(names)

        # Filter out packages to remove
        filtered_packages = [
            p
            for p in packages
            if p.name not in names_set
            and (p.mapped_name is None or p.mapped_name not in names_set)
        ]

        removed_count = len(packages) - len(filtered_packages)

        if removed_count > 0:
            self._write_all_packages(filtered_packages)

        return removed_count

    def get_packages_by_category(self, category: str) -> list[PackageRecord]:
        """Get all packages in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of PackageRecord objects in the category

        """
        packages = self.get_tracked_packages()
        return [p for p in packages if p.category == category]

    def get_packages_by_source(
        self, source_prefix: str
    ) -> list[PackageRecord]:
        """Get all packages from a specific source.

        Args:
            source_prefix: Source prefix to filter by (e.g., "COPR:", "AUR:", "official")

        Returns:
            List of PackageRecord objects matching the source

        """
        packages = self.get_tracked_packages()

        if source_prefix == "official":
            return [p for p in packages if p.source == "official"]

        return [p for p in packages if p.source.startswith(source_prefix)]

    def get_categories(self) -> set[str]:
        """Get all unique categories in tracked packages.

        Returns:
            Set of category names (excluding None)

        """
        packages = self.get_tracked_packages()
        return {p.category for p in packages if p.category is not None}

    def backup_database(self, backup_path: Path | None = None) -> Path:
        """Create a backup of the tracking database.

        Args:
            backup_path: Optional custom backup path
                        (default: metadata.jsonl.backup.<timestamp>)

        Returns:
            Path to created backup file

        """
        if backup_path is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_path = (
                self.db_path.parent / f"{self.db_path.name}.backup.{timestamp}"
            )

        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def _write_all_packages(self, packages: list[PackageRecord]) -> None:
        """Write all packages to database, replacing existing content.

        Args:
            packages: List of PackageRecord objects to write

        """
        with open(self.db_path, "w", encoding="utf-8") as f:
            for record in packages:
                json_line = orjson.dumps(record.to_dict()).decode("utf-8")
                f.write(json_line + "\n")

    def count_packages(self) -> int:
        """Get total count of tracked packages.

        Returns:
            Number of tracked packages

        """
        return len(self.get_tracked_packages())

    def clear_all(self) -> None:
        """Clear all tracked packages (empties the database)."""
        self.db_path.write_text("", encoding="utf-8")
