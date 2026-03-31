"""E2E test fixtures for mock filesystem and privileged operations."""

import shutil
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def e2e_tmp_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create E2E test root directory under system temp.

    Creates `/tmp/pytest-of-<user>-e2e/virtmanager-e2e/` for E2E tests.
    This directory persists after tests for manual inspection.

    Args:
        tmp_path_factory: pytest's temporary directory factory

    Returns:
        Path to the E2E test root directory
    """
    return tmp_path_factory.mktemp("virtmanager-e2e")


@pytest.fixture
def mock_libvirt_filesystem(e2e_tmp_root: Path) -> Path:
    """Create mock libvirt filesystem structure under tmp_root.

    Creates `/etc/libvirt/` directory structure with standard subdirectories
    and copies fixture config files from tests/fixtures/virt/ if they exist.

    Args:
        e2e_tmp_root: E2E test root directory fixture

    Returns:
        Path to the mock libvirt directory
    """
    # Create mock libvirt directory under the e2e tmp root
    libvirt_dir = e2e_tmp_root / "etc" / "libvirt"
    libvirt_dir.mkdir(parents=True, exist_ok=True)

    # Create standard libvirt subdirectories
    standard_subdirs = [
        "qemu",
        "qemu-kvm",
        "networks",
        "storage",
        "hooks",
    ]
    for subdir in standard_subdirs:
        (libvirt_dir / subdir).mkdir(exist_ok=True)

    # Copy fixture config files from tests/fixtures/virt/ if they exist
    fixture_virt_dir = Path(__file__).parent.parent / "fixtures" / "virt"
    if fixture_virt_dir.exists():
        for config_file in fixture_virt_dir.glob("*.conf"):
            dest = libvirt_dir / config_file.name
            shutil.copy2(config_file, dest)

    return libvirt_dir


@pytest.fixture
def mock_system_commands(  # noqa: C901
    mock_run_privileged: MagicMock, e2e_tmp_root: Path
) -> MagicMock:
    """Configure run_privileged mock to handle system commands.

    Configures the global run_privileged mock to handle common commands:
    tee, cp, systemctl, groupadd, usermod. For tee and cp, performs actual
    file operations on the filesystem, with /etc/libvirt/* paths redirected
    to the temporary test filesystem.

    Args:
        mock_run_privileged: Global mock of run_privileged
        e2e_tmp_root: Temporary root directory for redirecting paths

    Returns:
        Configured mock_run_privileged for further customization if needed
    """

    def redirect_path(path_str: str) -> Path:
        """Redirect /etc/libvirt/* paths to e2e_tmp_root.

        Args:
            path_str: Path string to redirect

        Returns:
            Redirected Path object
        """
        if path_str.startswith("/etc/libvirt/"):
            return e2e_tmp_root / path_str.lstrip("/")
        return Path(path_str)

    def handle_tee(cmd: list[str], **kwargs: object) -> MagicMock:
        """Handle tee command: write stdin_input to file.

        Args:
            cmd: Command list with ['/usr/bin/tee', target_file]
            **kwargs: Keyword arguments including stdin_input

        Returns:
            MagicMock object representing successful command result
        """
        min_cmd_len = 2
        if len(cmd) >= min_cmd_len:
            target_file = redirect_path(cmd[1])
            stdin_content = kwargs.get("stdin_input", "")
            if stdin_content:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(stdin_content)
        return MagicMock(returncode=0, stdout="", stderr="")

    def handle_cp(cmd: list[str], **_kwargs: object) -> MagicMock:
        """Handle cp command: copy source to destination.

        Args:
            cmd: Command list with ['/usr/bin/cp', ..., source, dest]
            **_kwargs: Keyword arguments (unused for cp)

        Returns:
            MagicMock object representing successful command result
        """
        min_cmd_len = 3
        if len(cmd) >= min_cmd_len:
            source = redirect_path(cmd[-2])
            dest = redirect_path(cmd[-1])
            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
        return MagicMock(returncode=0, stdout="", stderr="")

    def mock_run_command(cmd: list[str], **kwargs: object) -> MagicMock:
        """Mock run_privileged for system commands.

        Args:
            cmd: Command list to execute
            **kwargs: Keyword arguments (e.g., stdin_input)

        Returns:
            MagicMock object representing command result
        """
        if not cmd:
            return MagicMock(returncode=0, stdout="", stderr="")

        command_name = cmd[0].split("/")[-1] if "/" in cmd[0] else cmd[0]

        if command_name == "tee":
            return handle_tee(cmd, **kwargs)
        if command_name == "cp":
            return handle_cp(cmd, **kwargs)
        # For systemctl, groupadd, usermod: return success by default
        if command_name in ("systemctl", "groupadd", "usermod"):
            return MagicMock(returncode=0, stdout="", stderr="")
        # Default response for unknown commands
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run_privileged.side_effect = mock_run_command
    return mock_run_privileged


@pytest.fixture
def redirect_paths(  # noqa: C901
    monkeypatch: pytest.MonkeyPatch, e2e_tmp_root: Path
) -> tuple[Path, Path]:
    """Monkeypatch Path to redirect /etc/libvirt/* paths to tmp_path.

    Intercepts uses of Path("/etc/libvirt/...") in the virtmanager module
    and redirects them to tmp_path/etc/libvirt/... for testing without
    modifying the source code.

    Args:
        monkeypatch: pytest's monkeypatch fixture
        e2e_tmp_root: E2E test root directory fixture

    Returns:
        Tuple of (e2e_tmp_root, libvirt_dir) for assertions
    """
    # Create the directory structure for redirected paths
    libvirt_dir = e2e_tmp_root / "etc" / "libvirt"
    libvirt_dir.mkdir(parents=True, exist_ok=True)

    original_path = Path

    class PathRedirector:
        """Wrapper that redirects /etc/libvirt/* paths to tmp_path."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize PathRedirector with redirect logic.

            Args:
                *args: Positional arguments for Path constructor
                **kwargs: Keyword arguments for Path constructor
            """
            # Process first argument for redirection
            if args and isinstance(args[0], (str, Path)):
                path_str = str(args[0])
                if path_str.startswith("/etc/libvirt/"):
                    # Redirect /etc/libvirt/ paths to tmp_path
                    redirected = e2e_tmp_root / path_str.lstrip("/")
                    args = (redirected, *args[1:])

            # Create the actual Path object with redirected path
            self._path = original_path(*args, **kwargs)

        def __getattr__(self, name: str) -> Any:  # noqa: ANN401
            """Delegate attribute access to the wrapped Path object.

            Args:
                name: Attribute name to access

            Returns:
                The attribute from the wrapped Path object
            """
            return getattr(self._path, name)

        def __str__(self) -> str:
            """Return string representation of the path."""
            return str(self._path)

        def __repr__(self) -> str:
            """Return representation of the path."""
            return repr(self._path)

        def resolve(self) -> Path:
            """Resolve the path to absolute path."""
            return self._path.resolve()

        def exists(self) -> bool:
            """Check if path exists."""
            return self._path.exists()

        def is_dir(self) -> bool:
            """Check if path is a directory."""
            return self._path.is_dir()

        def is_file(self) -> bool:
            """Check if path is a file."""
            return self._path.is_file()

        def mkdir(self, *args: object, **kwargs: object) -> None:
            """Create a directory at the path."""
            return self._path.mkdir(*args, **kwargs)

        def read_text(self, *args: object, **kwargs: object) -> str:
            """Read text from the file."""
            return self._path.read_text(*args, **kwargs)

        def write_text(self, *args: object, **kwargs: object) -> None:
            """Write text to the file."""
            return self._path.write_text(*args, **kwargs)

        def __truediv__(self, other: object) -> Path:
            """Support path division operator (/)."""
            return self._path / other

    # Patch Path in the virtmanager module
    monkeypatch.setattr(
        "aps.installers.virtmanager.Path",
        PathRedirector,  # type: ignore[arg-type]
    )

    return (e2e_tmp_root, libvirt_dir)


@pytest.fixture
def sudoers_e2e_tmp_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create E2E test root directory for sudoers tests.

    Args:
        tmp_path_factory: pytest's temporary directory factory

    Returns:
        Path to the E2E test root directory for sudoers
    """
    return tmp_path_factory.mktemp("sudoers-e2e")


@pytest.fixture
def mock_sudoers_filesystem(sudoers_e2e_tmp_root: Path) -> Path:
    """Create mock sudoers filesystem with fixture data.

    Copies the real sudoers fixture from tests/fixtures/sudoers
    into the tmp filesystem at <tmp_root>/etc/sudoers.

    Args:
        sudoers_e2e_tmp_root: E2E test root directory for sudoers

    Returns:
        Path to the tmp etc directory containing the sudoers file.
    """
    etc_dir = sudoers_e2e_tmp_root / "etc"
    etc_dir.mkdir(parents=True, exist_ok=True)

    # Copy fixture sudoers file
    fixture_file = Path(__file__).parent.parent / "fixtures" / "sudoers"
    shutil.copy2(fixture_file, etc_dir / "sudoers")

    return etc_dir


MIN_CAT_CMD_LEN = 2
MIN_TEE_CMD_LEN = 2
MIN_CP_CMD_LEN = 3
MIN_FIND_CMD_LEN = 3


@pytest.fixture
def mock_sudoers_commands(
    mock_run_privileged: MagicMock, sudoers_e2e_tmp_root: Path
) -> MagicMock:
    """Configure run_privileged mock to handle sudoers commands.

    Configures the global run_privileged mock to handle sudoers-related
    commands: cat, tee, cp, find, visudo. For tee and cp, performs actual
    file operations on the filesystem, with /etc/ paths redirected
    to the temporary test filesystem.

    Args:
        mock_run_privileged: Global mock of run_privileged
        sudoers_e2e_tmp_root: Temporary root directory for redirecting paths

    Returns:
        Configured mock_run_privileged for further customization if needed
    """

    def mock_run_command(cmd: list[str], **kwargs: object) -> MagicMock:
        """Mock run_privileged for sudoers commands."""
        return _handle_sudoers_command(cmd, kwargs, sudoers_e2e_tmp_root)

    mock_run_privileged.side_effect = mock_run_command
    return mock_run_privileged


def _redirect_sudoers_path(path_str: str, tmp_root: Path) -> Path:
    """Redirect /etc/* paths to tmp_root.

    Args:
        path_str: Path string to redirect
        tmp_root: Root directory for redirection

    Returns:
        Redirected Path object
    """
    if path_str.startswith("/etc/") or path_str == "/etc":
        return tmp_root / path_str.lstrip("/")
    return Path(path_str)


def _handle_sudoers_command(  # noqa: C901, PLR0911, PLR0912
    cmd: list[str], kwargs: dict[str, object], tmp_root: Path
) -> MagicMock:
    """Handle sudoers-related mock commands.

    Args:
        cmd: Command list
        kwargs: Keyword arguments
        tmp_root: Temporary root directory

    Returns:
        MagicMock result
    """
    if not cmd:
        return MagicMock(returncode=0, stdout="", stderr="")

    command_name = cmd[0].split("/")[-1] if "/" in cmd[0] else cmd[0]

    if command_name == "cat":
        stdout = ""
        if len(cmd) >= MIN_CAT_CMD_LEN:
            file_path = _redirect_sudoers_path(cmd[1], tmp_root)
            if file_path.exists():
                stdout = file_path.read_text()
        return MagicMock(returncode=0, stdout=stdout, stderr="")

    if command_name == "tee":
        if len(cmd) >= MIN_TEE_CMD_LEN:
            target_file = _redirect_sudoers_path(cmd[1], tmp_root)
            stdin_content = kwargs.get("stdin_input", "")
            if stdin_content:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(stdin_content)
        return MagicMock(returncode=0, stdout="", stderr="")

    if command_name == "cp":
        if len(cmd) >= MIN_CP_CMD_LEN:
            source = _redirect_sudoers_path(cmd[-2], tmp_root)
            dest = _redirect_sudoers_path(cmd[-1], tmp_root)
            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
        return MagicMock(returncode=0, stdout="", stderr="")

    if command_name == "find":
        if len(cmd) < MIN_FIND_CMD_LEN:
            return MagicMock(returncode=0, stdout="", stderr="")

        search_dir = _redirect_sudoers_path(cmd[1], tmp_root)
        pattern = cmd[-1] if not cmd[-1].startswith("-") else ""

        if not search_dir.exists():
            return MagicMock(returncode=0, stdout="", stderr="")

        matching_files = sorted(
            [str(f) for f in search_dir.glob(pattern) if f.is_file()],
            reverse=True,
        )
        stdout = "\n".join(matching_files)
        return MagicMock(returncode=0, stdout=stdout, stderr="")

    return MagicMock(returncode=0, stdout="", stderr="")
