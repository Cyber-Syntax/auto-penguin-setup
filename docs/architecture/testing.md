## Testing Strategy

### Test Architecture

The testing structure mirrors the modular organization:

```text
tests/
├── test_setup.sh          # Integration tests (main orchestrator)
├── test_config.sh         # Configuration loading tests
├── test_logging.sh        # Logging system tests
├── test_packages.sh       # Package management tests
│
├── test_apps.sh           # Tests for src/apps/* modules
├── test_desktop.sh        # Tests for display & WM modules
├── test_laptop.sh         # Tests for hardware modules (laptop-specific)
├── test_general.sh        # Tests for system modules
│
├── test_helper.bash       # Shared test utilities
├── fixtures/              # Test data
│   └── librewolf.repo
├── mocks/                 # Mock commands
│   ├── dnf               # Mock package managers
│   ├── pacman
│   ├── apt-get
│   ├── sudo              # Mock privilege escalation
│   ├── git               # Mock VCS operations
│   ├── curl              # Mock downloads
│   └── ...
│
├── Dockerfile            # Fedora test container
└── fedora-compose.yml    # Docker Compose configuration
```

**Test Organization Principle**: Each test file corresponds to a module category, ensuring clear test ownership and easy location of relevant tests.

### Testing Layers

#### Layer 1: Unit Tests

Test individual functions in isolation:

```bash
@test "detect_distro identifies Fedora correctly" {
  # Mock /etc/os-release
  echo 'ID=fedora' > /etc/os-release
  
  # Test
  run detect_distro
  
  # Assert
  [ "$status" -eq 0 ]
  [ "$output" = "fedora" ]
}
```

#### Layer 2: Integration Tests

Test module interactions:

```bash
@test "package manager initializes and installs correctly" {
  # Setup
  init_package_manager
  
  # Test
  run pm_install "vim"
  
  # Assert
  [ "$status" -eq 0 ]
  [ -n "$PM_INSTALL" ]
}
```

#### Layer 3: System Tests

Test full workflows in containers:

```bash
docker-compose up -d fedora-test
docker exec fedora-test ./setup.sh -i
docker exec fedora-test rpm -q curl wget jq
```

### Mocking Strategy

Mock system commands to enable testing without actual installation:

```bash
# mocks/dnf
#!/usr/bin/env bash
# Mock dnf for testing

case "$*" in
  "install -y vim")
    echo "Installing vim..."
    exit 0
    ;;
  "install -y nonexistent")
    echo "Error: Package not found"
    exit 1
    ;;
esac
```

Usage in tests:

```bash
setup() {
  export PATH="$BATS_TEST_DIRNAME/mocks:$PATH"
}
```

---