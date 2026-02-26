# E2E Testing Strategy

## Overview

End-to-end (E2E) tests in this project exercise production code against real fixture data in temporary directories. Unlike unit tests that mock external dependencies, E2E tests:

- Use **real config files** from `tests/fixtures/`
- Create **temporary filesystems** for isolated testing
- Mock only **system calls** (via `run_privileged`), not the code being tested
- Verify **actual file I/O operations** against redirected paths

Currently, two modules have E2E tests:

1. **virtmanager** — `tests/e2e/test_virtmanager_e2e.py` (12 tests)
   - Tests libvirt configuration (qemu.conf, network.conf, etc.)
   - Validates Path redirection and file operations

2. **sudoers** — `tests/e2e/test_sudoers_e2e.py` (4 tests)
   - Tests sudoers configuration with real sudoers fixture
   - Validates backup creation and idempotency

This approach catches real behavior differences from unit tests and ensures file operations work correctly on test filesystems.

## Architecture

The E2E testing pattern uses four key layers:

```
┌─────────────────────────────────────────────────┐
│ Test Code                                        │
│ Calls production functions                       │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ Path Redirection Layer (PathRedirector class)   │
│ Intercepts Path("/etc/libvirt/...") → tmp_path  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ Command Handler Layer (mock_run_privileged)     │
│ Intercepts run_privileged(["tee"...]) → write   │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ Temporary Filesystem                             │
│ Real file operations on /tmp/pytest-*/           │
└──────────────────────────────────────────────────┘
```

**Key insight:** The production code sees normal Python Path objects and subprocess calls, but they're redirected to a test filesystem instead of the real system.

## Directory Structure

```
tests/
├── conftest.py                          # Global fixtures (mock_run_privileged)
├── e2e/
│   ├── conftest.py                      # E2E fixtures (Path redirection, command mocks)
│   ├── test_virtmanager_e2e.py          # 12 virtmanager E2E tests
│   └── test_sudoers_e2e.py              # 4 sudoers E2E tests
└── fixtures/
    ├── virt/                            # Real libvirt config files
    │   ├── libvirtd.conf
    │   ├── network.conf
    │   └── qemu.conf
    └── sudoers                          # Real sudoers fixture file
```

## How It Works

### 1. Global Mock Setup (`tests/conftest.py`)

The `pytest_configure` hook patches `run_privileged` globally for all tests:

```python
patcher = patch("aps.utils.privilege.run_privileged")
_run_privileged_mock = patcher.start()
```

The `mock_run_privileged` fixture resets this mock before each test, allowing individual tests to configure side_effect.

### 2. Fixture Chain for Virtmanager

**`e2e_tmp_root` fixture:**

```python
tmp_path_factory.mktemp("virtmanager-e2e")  # Creates /tmp/pytest-of-user-e2e/
```

**`mock_system_commands` fixture:**

- Configures `mock_run_privileged.side_effect` to handle commands
- `tee` command: writes stdin to redirected file
- `cp` command: copies source to redirected destination
- Other commands (systemctl, groupadd): return success

**`redirect_paths` fixture:**

- Creates `PathRedirector` class that wraps the real `Path`
- Intercepts `Path("/etc/libvirt/...")` and redirects to `e2e_tmp_root/etc/libvirt/...`
- Monkeypatches `aps.installers.virtmanager.Path` with this wrapper

**Fixture chain:**

```python
@pytest.fixture
def test_example(redirect_paths, mock_system_commands):
    # redirect_paths monkeypatches Path
    # mock_system_commands configures run_privileged.side_effect
```

### 3. Fixture Chain for Sudoers

**`sudoers_e2e_tmp_root` fixture:**

- Creates temporary directory specifically for sudoers tests
- Copies real sudoers fixture: `tests/fixtures/sudoers` → `tmp_root/etc/sudoers`

**`mock_sudoers_commands` fixture:**

- Configures `mock_run_privileged.side_effect` with sudoers-specific handlers
- `cat` command: reads from redirected file
- `tee` command: writes to redirected file
- `cp` command: copies to redirected paths
- `find` command: searches redirected directory and returns matching files

**Path redirection approach (different from virtmanager):**

- Uses `monkeypatch.setattr(sudoers_module, "SUDOERS_FILE", tmp_file)` in test
- Does NOT wrap Path class; instead patches module constants directly

## Writing a New E2E Test

### 1. Create Fixture Files

Place real config files in `tests/fixtures/<module>/`:

```bash
tests/fixtures/mymodule/
├── config.conf
└── data.txt
```

### 2. Add Fixtures to `tests/e2e/conftest.py`

```python
@pytest.fixture
def mymodule_e2e_tmp_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("mymodule-e2e")

@pytest.fixture
def mock_mymodule_filesystem(mymodule_e2e_tmp_root: Path) -> Path:
    mymodule_dir = mymodule_e2e_tmp_root / "etc" / "mymodule"
    mymodule_dir.mkdir(parents=True, exist_ok=True)
    # Copy fixtures
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "mymodule"
    if fixture_dir.exists():
        for f in fixture_dir.glob("*"):
            shutil.copy2(f, mymodule_dir / f.name)
    return mymodule_dir

@pytest.fixture
def mock_mymodule_commands(
    mock_run_privileged: MagicMock, mymodule_e2e_tmp_root: Path
) -> MagicMock:
    def mock_run_command(cmd: list[str], **kwargs) -> MagicMock:
        # Handle tee, cp, cat, etc. with path redirection
        if cmd[0].endswith("tee"):
            target = redirect_mymodule_path(cmd[1])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(kwargs.get("stdin_input", ""))
        return MagicMock(returncode=0, stdout="", stderr="")
    
    mock_run_privileged.side_effect = mock_run_command
    return mock_run_privileged
```

### 3. Create Test File

Create `tests/e2e/test_mymodule_e2e.py`:

```python
def test_mymodule_configuration(
    mymodule_e2e_tmp_root: Path,
    mock_mymodule_filesystem: Path,
    mock_mymodule_commands: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test production code with real config on temp filesystem."""
    # Setup: patch module constants to use temp paths
    mymodule_file = mymodule_e2e_tmp_root / "etc" / "mymodule" / "config.conf"
    monkeypatch.setattr("aps.module.mymodule.CONFIG_PATH", mymodule_file)
    
    # Act: call production function
    result = my_setup_function()
    
    # Assert: check filesystem changes
    assert mymodule_file.exists()
    assert "expected content" in mymodule_file.read_text()
    assert result is True
```

### 4. Handling Failures

To test failure scenarios, wrap command handlers:

```python
original_result = mock_run_privileged.side_effect

def failing_handler(cmd, **kwargs):
    if "visudo" in cmd[0]:
        return MagicMock(returncode=1, stderr="syntax error")
    return original_result(cmd, **kwargs)

mock_sudoers_commands.side_effect = failing_handler
```

## Running E2E Tests

```bash
# Run only E2E tests
uv run pytest tests/e2e/ -v

# Run E2E tests with output
uv run pytest tests/e2e/ -v -s

# Run specific E2E test
uv run pytest tests/e2e/test_virtmanager_e2e.py::test_specific_name -v

# Run all tests (includes E2E)
uv run pytest -m "not slow"

# Inspect temp files after test (add --tb=no to skip tracebacks)
uv run pytest tests/e2e/test_sudoers_e2e.py -v -s --tb=short
# Files persist in /tmp/pytest-of-<user>-e2e/
```

## Examples

### Virtmanager E2E Test

See [test_virtmanager_e2e.py](../tests/e2e/test_virtmanager_e2e.py) for:

- Path redirection with `PathRedirector` class
- Testing `tee` and `cp` command operations
- Fixture configuration copying

### Sudoers E2E Test

See [test_sudoers_e2e.py](../tests/e2e/test_sudoers_e2e.py) for:

- Module constant patching (`SUDOERS_FILE`)
- Testing `cat`, `find`, `cp` operations
- Verifying file backups and idempotency

Both examples use the same global `mock_run_privileged` fixture from [tests/conftest.py](../tests/conftest.py), configured differently via `side_effect`.

## Debugging Tips

1. **Check temp files manually**: Look in `/tmp/pytest-of-<user>-e2e/` after test failure
2. **Print paths in tests**: Add `print(str(mymodule_file))` to see where files actually exist
3. **Verify side_effect**: Print the command being intercepted in your mock handler
4. **Check fixture chain**: Ensure fixtures are in correct dependency order (fixtures that depend on others must be listed after)
5. **Mock reset between tests**: The `mock_run_privileged` fixture auto-resets; if you modify `side_effect`, it persists until reset
