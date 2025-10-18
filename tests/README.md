# Auto-Penguin-Setup Test Suite

This directory contains the BATS test suite for auto-penguin-setup.

## Container Testing

For container-based testing across multiple distributions (Fedora, Arch, Debian), see the **`../container/`** directory.

The container setup has been moved to provide:

- Multi-distro testing (Fedora, Arch, Debian)
- Isolated configuration environments
- Read-only source mounting
- Persistent config volumes

**Quick Start:**

```bash
cd ../container/
./manage.sh build all
./manage.sh shell fedora
```

See `../container/README.md` for complete container documentation.

## BATS Testing

This directory contains unit and integration tests using BATS (Bash Automated Testing System).

### Test Files

- `test_setup.sh` - Integration tests for main orchestrator
- `test_config.sh` - Configuration system tests
- `test_logging.sh` - Logging system tests
- `test_packages.sh` - Package management tests
- `test_apps.sh` - Application module tests
- `test_desktop.sh` - Display & WM module tests
- `test_laptop.sh` - Hardware module tests (laptop-specific)
- `test_general.sh` - System module tests

### Running Tests

```bash
# Run all tests
bats test_*.sh

# Run specific test file
bats test_config.sh

# Run with verbose output
bats -t test_setup.sh
```

### Test Helpers

- `test_helper.bash` - Shared utilities and mock commands
- `mocks/` - Mock system commands for testing
- `fixtures/` - Test data files
