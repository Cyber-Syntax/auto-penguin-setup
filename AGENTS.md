# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

auto-penguin-setup (CLI: `aps`) is a Python 3.12+ tool for automating Linux
system setup across Fedora- and Arch-family distributions.

**Core features**:

- Install/remove packages using INI-based categories (e.g. `@core`, `@dev`) and
    cross-distro name mapping (`packages.ini` + `pkgmap.ini`).
- Handle third-party sources such as Fedora COPR and Arch AUR, plus Flatpak.
- Run optional “setup components” (hardware/system/WM/tool installers).
- Track installed packages in a JSONL database at
    `~/.config/auto-penguin-setup/metadata.jsonl`.

**Package/dependency manager**: uv (replaces pip/poetry)

## Core Technologies

- **Python**: 3.12+
- **Storage**:
    - INI configs via `configparser` (see `src/aps/core/config.py`)
    - JSONL tracking via **orjson** (see `src/aps/core/tracking.py`)
- **Testing**: pytest + pytest-cov (tests primarily use `unittest.mock`)
- **Linting**: ruff (linter + formatter)
- **Type Checking**: mypy config exists in `pyproject.toml` (mypy is not part of
    the default dependency groups yet)

## Configuration Files

APS reads INI configs from `~/.config/auto-penguin-setup/`:

- `variables.ini` (host/device settings)
- `packages.ini` (categories such as `@core`, `@apps`)
- `pkgmap.ini` (distro-specific mapping and provider prefixes like `AUR:`/`COPR:`/`flatpak:`)

If these files are missing, the defaults are copied from
`src/aps/configs/default_aps_configs/` on demand.

## Repository Structure

```
scripts/                    # Helper scripts
autocomplete/               # Shell autocomplete scripts (bash, zsh)

src
└── aps
   ├── __init__.py
   ├── cli
   │  ├── __init__.py
   │  ├── commands
   │  │  ├── __init__.py
   │  │  ├── install.py
   │  │  ├── list.py
   │  │  ├── remove.py
   │  │  ├── setup.py
   │  │  ├── status.py
   │  │  ├── sync_repos.py
   │  │  └── upgrade.py
   │  ├── parser.py
   │  └── utils.py
   ├── configs
   │  ├── 01-mytlp.conf
   │  ├── 20-intel.conf
   │  ├── 99-backlight.conf
   │  ├── 99-qtile.rules
   │  ├── 99-touchpad.conf
   │  ├── default_aps_configs
   │  │  ├── packages.ini
   │  │  ├── pkgmap.ini
   │  │  └── variables.ini
   │  ├── libvirt
   │  │  └── network.conf
   │  ├── mpv
   │  │  ├── input.conf
   │  │  └── mpv.conf
   │  ├── nvidia
   │  │  └── xorg_04-06-25.conf
   │  ├── README.md
   │  ├── thinkfan.conf
   │  └── trash-cli
   │     ├── trash-cli.service
   │     └── trash-cli.timer
   ├── core
   │  ├── __init__.py
   │  ├── config.py
   │  ├── distro.py
   │  ├── logger.py
   │  ├── package_manager.py
   │  ├── package_mapper.py
   │  ├── repo_manager.py
   │  ├── setup.py
   │  └── tracking.py
   ├── display
   │  ├── __init__.py
   │  ├── lightdm.py
   │  └── sddm.py
   ├── hardware
   │  ├── __init__.py
   │  ├── amd.py
   │  ├── intel.py
   │  ├── nvidia.py
   │  └── touchpad.py
   ├── installers
   │  ├── __init__.py
   │  ├── autocpufreq.py
   │  ├── brave.py
   │  ├── ohmyzsh.py
   │  ├── syncthing.py
   │  ├── thinkfan.py
   │  ├── tlp.py
   │  ├── trashcli.py
   │  ├── ueberzugpp.py
   │  ├── virtmanager.py
   │  └── vscode.py
   ├── main.py
   ├── system
   │  ├── __init__.py
   │  ├── firewall.py
   │  ├── multimedia.py
   │  ├── pm_optimizer.py
   │  ├── repositories.py
   │  ├── ssh.py
   │  └── sudoers.py
   ├── utils
   │  ├── __init__.py
   │  ├── file_operations.py
   │  ├── paths.py
   │  ├── privilege.py
   │  └── version.py
   └── wm
      ├── __init__.py
      └── qtile.py
```

## Development Workflow

### Common Development Tasks

#### Running the CLI

```bash
# Run from source without installation
uv run aps <command> [options]

# Examples
uv run aps install @dev
uv run aps install neovim lazygit
uv run aps list
uv run aps status
uv run aps sync-repos --auto
uv run aps upgrade
uv run aps --help # for more command examples
```

#### Making Code Changes

**CRITICAL**: Always run ruff on modified files before committing.

```bash
# 1. Make your changes to files in src/aps/ and/or tests/

# 2. Run linting (auto-fix issues)
ruff check --fix path/to/file.py
ruff check --fix . # or all Python files

# 3. Run formatting
ruff format path/to/file.py
ruff format . # or all Python files

# 4. Run type checking
uv run mypy src/aps/

# 5. Run fast tests (excludes slow logger tests)
uv run pytest -m "not slow"

# 6. Verify CLI still works
uv run aps --help

# 7. Quick smoke test
uv run aps --help
```

## Code Quality Standards

### Type Hints

CRITICAL: All Python code MUST include type hints and return types.

```python
# CORRECT
def filter_unknown_users(users: list[str], known_users: set[str]) -> list[str]:
    """Filter out users that are not in the known users set.

    Args:
        users: List of user identifiers to filter.
        known_users: Set of known/valid user identifiers.

    Returns:
        List of users that are not in the `known_users` set.
    """
    return [u for u in users if u not in known_users]

# INCORRECT (no type hints)
def filter_unknown_users(users, known_users):
    return [u for u in users if u not in known_users]
```

- **Type Annotations**: Use built-in types: `list[str]`, `dict[str, int]` (not `typing.List`, `typing.Dict`)

### Coding Standards

- **Logging Format**: Use `%s` style formatting in logging statements: `logger.info("User %s logged in", username)`
- **PEP 8**: Enforced by ruff
- **Datetime**: Use `astimezone()` for local time conversions
- **Variable Names**: Use descriptive, self-explanatory names
- **Functions**: Use functions over classes when state management is not needed
- **Function Size**: Keep functions focused (<20 lines when possible)
- **Pure Functions**: Prefer pure functions without side effects when possible
- **Error Handling**: Prefer module-scoped exception types with actionable messages
- **DRY Approach**:
    - Reuse existing abstractions; don't duplicate
    - Refactor safely when duplication is found
    - Check existing protocols before creating new ones

### File Organization

CRITICAL: Keep files between 150-500 lines for maintainability. If a file exceeds 550 lines, refactor by splitting into focused modules.

```bash
# Check file line counts
uv run pytest tests/test_lines.py -v

# If tests fail, refactor large files:
# 1. Find natural split points (don't force arbitrary divisions)
# 2. Extract related functionality into new modules
# 3. Re-run tests until they pass
```

## Security Guidelines

- Always call `ensure_sudo()` once at the start of commands that require privileges (not in helpers).
- Use only the helpers in `aps/utils/privilege.py` for any privileged operations.
- Always pass the command and its arguments as a list (e.g., `["/usr/bin/ls", "-l"]`) in subprocess calls.
- Use `run_privileged()` for all commands needing sudo/root.
- Use a fully qualified path for the executable in subprocess calls (e.g., `/usr/bin/ls` instead of just `ls`).
- Avoid using `shell=True` in subprocess calls unless absolutely necessary.
- Let user see command output unless there's a specific reason to suppress it.

## Testing Instructions

### Test Folder Structure Principles

Test fixtures follow a hierarchical organization principle:

| Fixture Scope | Location | Purpose |
|---------------|----------|---------|
| **Module-specific fixtures** | `tests/<module>/conftest.py` | Fixtures used only by tests in that module (e.g., `tests/core/install/conftest.py`) |
| **Module-group fixtures** | `tests/<group>/conftest.py` | Fixtures shared across submodules (e.g., `tests/core/conftest.py` for all core tests) |
| **Global fixtures** | `tests/conftest.py` | Fixtures shared across all test modules (e.g., `enable_log_propagation`) |

**Example Structure:**

```
tests/                             # Test suite (mirrors src structure)
├── conftest.py             # Pytest fixtures and configuration
├── integration/                   # Integration tests (network calls not allowed)
├── custom/                 # Custom tests (e.g., GitHub Action CI test, line count test)
├── e2e/                           # End-to-end tests
├── fixtures/                      # Test fixtures
│   └── checksums/                 # Real checksum data for integration tests
└── [other subdirs mirror src/aps structure]
```

**Fixture Discovery Order:** pytest automatically discovers fixtures by checking parent directories, so fixtures are available in child test modules without explicit imports.

### Writing Tests

**CRITICAL**: Every new feature or bugfix MUST be covered by unit tests.

```python
# Example test structure
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aps.core.services import InstallWorkflow
from aps.exceptions import VerificationError


@pytest.mark.asyncio
async def test_install_workflow_success(tmp_path, mock_session):
    """Test successful installation workflow."""
    # Arrange
    workflow = InstallWorkflow(...)

    # Act
    result = await workflow.execute()

    # Assert
    assert result.success is True
    assert result.app_name == "test-app"


def test_hash_verification_failure():
    """Test that verification fails with incorrect hash."""
    # Arrange
    expected_hash = "abc123"
    actual_hash = "def456"

    # Act & Assert
    with pytest.raises(VerificationError):
        verify_hash(actual_hash, expected_hash)
```

### Running Tests

```bash
# Run fast tests only (excludes slow logger integration tests)
uv run pytest -m "not slow"

# Run all tests (including slow tests)
uv run pytest

# Run tests with coverage
uv run pytest --cov=aps --cov-report=html

# Run specific test file
uv run pytest tests/test_install.py

# Run specific test function
uv run pytest tests/test_install.py::test_install_success
```

## Quick navigation for agents

- CLI entry point: `src/aps/main.py`
- Argument parsing: `src/aps/cli/parser.py`
- Command handlers: `src/aps/cli/commands/*.py`
- Config parsing + defaults: `src/aps/core/config.py` and `src/aps/configs/default_aps_configs/`
- Package mapping: `src/aps/core/package_mapper.py`
- Package tracking DB (JSONL): `src/aps/core/tracking.py`

### Test Checklist

Before committing, verify:

- [ ] Tests fail when your new logic is broken
- [ ] Happy path is covered
- [ ] Edge cases and error conditions are tested
- [ ] External dependencies are mocked (no real network calls in unit tests)
- [ ] Tests are deterministic (no flaky tests)
- [ ] **Async-safe**: Support async/await patterns
- [ ] Async tests use `@pytest.mark.asyncio`
- [ ] Test names clearly describe what they test

## Debugging and Troubleshooting

### Common Issues and Solutions

#### Linting/Formatting Issues

```bash
# Problem: Ruff errors that can't be auto-fixed
# Solution: Review ruff output and fix manually
ruff check path/to/file.py

# Problem: Type checking errors
# Solution: Run mypy with verbose output
uv run mypy --show-error-codes src/aps/

# Common type error fixes:
# - Update type hints to match actual usage
# - Check for missing return type annotations
# - Ensure correct use of built-in types (list[str], dict[str, int], etc.)
```
