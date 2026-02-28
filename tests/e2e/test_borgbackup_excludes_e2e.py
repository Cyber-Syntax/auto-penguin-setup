"""E2E tests for borg exclude patterns (real borg binary).

Strategy: init one borg repo, create a fake home tree with excluded and
included dirs, run a real ``borg create`` (no dry-run), then list the
archive contents and assert excluded paths are absent while real
document files are present.  The repo is kept on disk so you can
manually inspect it afterwards.
"""

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

ARCHIVE_NAME = "test-backup"


def _borg_env() -> dict[str, str]:
    return {
        **os.environ,
        "BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK": "yes",
    }


def _create_archive(
    repo: Path,
    source: Path,
    excludes_file: Path,
) -> None:
    """Run ``borg create`` to produce a real archive."""
    result = subprocess.run(  # noqa: S603
        [
            "/usr/bin/borg",
            "create",
            "--exclude-caches",
            "--exclude-from",
            str(excludes_file),
            f"{repo}::{ARCHIVE_NAME}",
            str(source) + "/",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_borg_env(),
    )
    assert result.returncode == 0, (
        f"borg create failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )


def _list_archive(repo: Path) -> set[str]:
    """Return the set of paths stored in the archive."""
    result = subprocess.run(  # noqa: S603
        [
            "/usr/bin/borg",
            "list",
            "--short",
            f"{repo}::{ARCHIVE_NAME}",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=_borg_env(),
    )
    return {
        line.strip() for line in result.stdout.splitlines() if line.strip()
    }


@pytest.fixture(scope="module")
def borg_archive_paths(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[set[str], Path]:
    """Create a borg repo + archive once for the entire module.

    Returns:
        Tuple of (archived_paths, repo_path) for assertions and manual
        inspection.
    """
    root = tmp_path_factory.mktemp("pytest-borg-repo", numbered=False)
    home = root / "home" / "developer"
    home.mkdir(parents=True)

    # Directories that MUST be excluded
    for d in [
        ".cache/fontconfig",
        "Downloads/big-file",
        "node_modules/express",
        ".venv/lib",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "Trash",
        ".thumbnails",
        ".npm/_cacache/content-v2",
        "bower_components/jquery",
        ".config/Code/CachedData/abc123",
        ".config/Code/Cache/Cache_Data/74164214beca1c9e_0",
        ".config/Code/GPUCache",
        ".config/Code/logs/2026-02-28T10:00:00",
        ".config/Code/Crashpad",
        ".var/app/com.visualstudio.code/cache",
        ".tox/py312",
        ".backups/old",
        "venv/lib",
        ".local/share/Trash/files",
        "project/node_modules/lodash",
        "project/__pycache__",
        "project/.venv/bin",
        "project/dist",
        "project/build/output",
    ]:
        (home / d).mkdir(parents=True, exist_ok=True)
        (home / d / "dummy.txt").write_text("excluded")

    # Files/dirs that MUST be included
    for f in [
        "Documents/notes.txt",
        "Documents/my-repos/project/src/main.py",
        "Pictures/photo.jpg",
        ".config/borg/config.ini",
        ".bashrc",
    ]:
        fp = home / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text("included content")

    # Init borg repo
    repo = root / "test-repo"
    env = _borg_env()
    subprocess.run(  # noqa: S603
        ["/usr/bin/borg", "init", "--encryption=none", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    # Build adapted excludes (rewrite home/*/ → */)
    excludes_src = (
        Path(__file__).parent.parent.parent
        / "src"
        / "aps"
        / "configs"
        / "borg-scripts"
        / "borg-home-excludes.txt"
    )
    adapted_lines: list[str] = []
    for line in excludes_src.read_text().splitlines():
        s = line.strip()
        if s.startswith("#") or not s:
            adapted_lines.append(line)
        elif s.startswith("home/*/"):
            adapted_lines.append(line.replace("home/*/", "*/", 1))
        else:
            adapted_lines.append(line)

    excludes_file = root / "test-excludes.txt"
    excludes_file.write_text("\n".join(adapted_lines) + "\n")

    # Create real archive
    _create_archive(repo, root, excludes_file)

    # List archive contents
    paths = _list_archive(repo)

    # Print repo path so user can inspect manually
    print(f"\n[borg-e2e] repo kept at: {repo}")  # noqa: T201
    print(f"[borg-e2e] source tree:  {root}")  # noqa: T201

    return paths, repo


# ── Exclude assertions ───────────────────────────────────────


def test_excludes_filter_node_modules(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """node_modules directories must not appear in the archive."""
    paths, _repo = borg_archive_paths
    node_paths = [p for p in paths if "node_modules" in p]
    assert node_paths == [], f"node_modules found in archive: {node_paths}"


def test_excludes_filter_venv(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """.venv and venv directories must not appear in the archive."""
    paths, _repo = borg_archive_paths
    venv_paths = [p for p in paths if ".venv" in p or "/venv/" in p]
    assert venv_paths == [], f"venv found in archive: {venv_paths}"


def test_excludes_filter_pycache(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """__pycache__ directories must not appear in the archive."""
    paths, _repo = borg_archive_paths
    pycache_paths = [p for p in paths if "__pycache__" in p]
    assert pycache_paths == [], (
        f"__pycache__ found in archive: {pycache_paths}"
    )


def test_excludes_filter_cache(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """.cache directories must not appear in the archive."""
    paths, _repo = borg_archive_paths
    cache_paths = [p for p in paths if "/.cache/" in p or "/.cache" in p]
    assert cache_paths == [], f".cache found in archive: {cache_paths}"


def test_excludes_filter_vscode_caches_and_logs(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """VS Code cache and log directories must not appear in the archive."""
    paths, _repo = borg_archive_paths
    blocked_substrings = [
        "/.config/Code/Cache/",
        "/.config/Code/GPUCache/",
        "/.config/Code/logs/",
        "/.config/Code/Crashpad/",
        "/.var/app/com.visualstudio.code/cache/",
    ]
    found = [
        p for p in paths if any(blocked in p for blocked in blocked_substrings)
    ]
    assert found == [], "VS Code caches/logs found in archive:\n" + "\n".join(
        sorted(found)
    )


def test_excludes_preserve_real_documents(
    borg_archive_paths: tuple[set[str], Path],
) -> None:
    """Real document files must be present in the archive."""
    paths, _repo = borg_archive_paths
    doc_files = [p for p in paths if "Documents" in p]
    assert len(doc_files) > 0, (
        f"No Documents files found in archive.\nAll paths: {sorted(paths)}"
    )
