---
title: "ADR-0002: Single-Instance Enforcement via fcntl.flock"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "concurrency", "singleton"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed** | Accepted | Rejected | Superseded | Deprecated

## Context

Auto Penguin Setup (APS) is a CLI tool that modifies system state: it installs
and removes packages, writes to a JSONL tracking database
(`~/.config/auto-penguin-setup/metadata.jsonl`), and invokes system package
managers (`dnf`, `pacman`, `paru`). Running multiple concurrent `aps` processes
creates several hazards:

- **CTX-001**: **JSONL database corruption** — Two `aps install` processes
  appending to `metadata.jsonl` simultaneously can produce interleaved writes,
  resulting in malformed JSON lines or duplicate/missing records.
- **CTX-002**: **Package manager conflicts** — Native package managers (dnf,
  pacman) acquire their own lock files, but APS's higher-level orchestration
  (category resolution, mapping, tracking) has no coordination. A second
  instance may proceed past pre-flight checks while the first is mid-install,
  leading to confusing error messages or partial state.
- **CTX-003**: **Config file races** — Both `packages.ini` and `pkgmap.ini` are
  read during execution. A concurrent `aps sync-repos` or manual edit during an
  install could yield inconsistent package lists.
- **CTX-004**: **User confusion** — Without a clear "already running" message,
  users who accidentally invoke `aps` twice (e.g., in separate terminals) receive
  cryptic failures from the underlying package manager instead of a helpful
  diagnostic.

The todo list already identifies `fcntl.flock` as the preferred mechanism. This
ADR formalises the decision and documents the design.

## Decision

Enforce single-instance execution using an **advisory file lock** acquired via
`fcntl.flock()` at CLI startup, before any command handler runs.

### Design

1. **Lock file location**: `~/.config/auto-penguin-setup/aps.lock` (same
   directory as the tracking database, already guaranteed to exist by config
   initialisation).
2. **Locking mechanism**: Open the lock file with `open(..., "w")` and call
   `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`. The `LOCK_NB`
   (non-blocking) flag causes an immediate `BlockingIOError` if another process
   holds the lock, rather than waiting indefinitely.
3. **Placement**: The lock is acquired in `main()` (`src/aps/main.py`) after
   argument parsing but before command dispatch. This allows `--help` and
   `--version` to work without requiring the lock.
4. **Release**: The file descriptor is kept open for the lifetime of the process.
   On normal exit, `finally`-block cleanup closes it; on abnormal termination
   (SIGKILL, crash), the OS automatically releases the `flock` advisory lock.
5. **User-facing error**: When the lock cannot be acquired, APS prints a clear
   message — e.g., `"Another aps instance is already running. Exiting."` — and
   exits with a non-zero return code.
6. **Write PID**: The current PID is written to the lock file after acquiring
   the lock. This is informational only (for debugging); the lock itself is
   enforced by `flock`, not by PID-file parsing.

### Pseudocode

```python
import fcntl
import os
from pathlib import Path

LOCK_PATH = Path.home() / ".config" / "auto-penguin-setup" / "aps.lock"

def acquire_instance_lock() -> int:
    """Acquire a process-wide exclusive lock. Returns the fd."""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise SystemExit(
            "Another aps instance is already running. Exiting."
        )
    os.write(fd, str(os.getpid()).encode())
    return fd
```

### Rationale

- `fcntl.flock` is the simplest correct approach on Linux: it is race-free,
  requires no cleanup on crash, and is available in the Python stdlib.
- Advisory locks are sufficient because all participants (`aps` processes) are
  cooperative — we control the only code that accesses the lock.
- Non-blocking mode provides instant feedback instead of silently queuing.

## Consequences

### Positive

- **POS-001**: Eliminates all JSONL database corruption from concurrent writes,
  protecting the integrity of `metadata.jsonl`.
- **POS-002**: Prevents confusing double-invocation of system package managers,
  reducing user-facing error noise.
- **POS-003**: Zero external dependencies — `fcntl` is a Python stdlib module
  available on all Linux targets (Fedora, Arch).
- **POS-004**: No cleanup burden — unlike PID-file schemes, `flock` locks are
  automatically released by the kernel on process exit, including crashes and
  SIGKILL.
- **POS-005**: Minimal code footprint — roughly 15-20 lines of new code in
  `main.py` (or a small utility function), well within the project's file-size
  guidelines.

### Negative

- **NEG-001**: `fcntl.flock` is Linux/Unix-only. APS already targets only Fedora
  and Arch-family distros, so this is not a practical limitation today, but it
  prevents future Windows or macOS portability without an abstraction layer.
- **NEG-002**: Advisory locks are cooperative. If a third-party tool directly
  modifies `metadata.jsonl` without respecting the lock, corruption is still
  possible. This is acceptable since `metadata.jsonl` is an internal store.
- **NEG-003**: `--help` and `--version` will work without the lock (by design),
  but all other subcommands — including read-only ones like `aps list` and
  `aps status` — will be blocked if another instance is running. This is
  intentional to keep the implementation simple and avoid read/write lock
  complexity.

## Alternatives Considered

### PID File Check (Without flock)

- **ALT-001**: **Description**: Write the current PID to a file at startup and
  check whether that PID is still alive before proceeding.
- **ALT-002**: **Rejection Reason**: PID-file schemes are inherently racy — a
  process can die after the PID check but before the file is updated, and PIDs
  can be recycled by the OS. Stale PID files after crashes require manual
  cleanup or heuristic "is-process-alive" logic, adding complexity without
  reliability.

### Named Socket / Unix Domain Socket

- **ALT-003**: **Description**: Bind a Unix domain socket to a fixed path. A
  second instance would fail to bind, signalling that one is already running.
- **ALT-004**: **Rejection Reason**: More complex to implement, requires socket
  cleanup on shutdown, and stale socket files can linger after crashes (requiring
  `SO_REUSEADDR` or manual unlink). Provides no benefit over `flock` for a
  simple mutual-exclusion use case.

### systemd Transient Unit / D-Bus Activation

- **ALT-005**: **Description**: Run `aps` as a systemd transient unit
  (`systemd-run`) so that systemd enforces single-instance semantics.
- **ALT-006**: **Rejection Reason**: Ties the tool to systemd, adds significant
  user-facing complexity, and changes the invocation pattern (no longer a simple
  `aps install @dev`). Overkill for a CLI tool.

### Database-Level Locking (e.g., SQLite)

- **ALT-007**: **Description**: Replace the JSONL tracking store with SQLite,
  which has built-in write locking.
- **ALT-008**: **Rejection Reason**: Solves only the database-corruption subset
  of the problem; does not prevent concurrent package-manager invocations.
  Additionally, migrating from JSONL to SQLite is a much larger scope change
  that is not warranted solely for locking.

## Implementation Notes

- **IMP-001**: Add an `acquire_instance_lock()` function to `src/aps/utils/` (a
  new module such as `instance_lock.py`, or inside the existing `privilege.py`
  if scope is small). Call it from `main()` in `src/aps/main.py` after
  `parser.parse_args()` but before command dispatch.
- **IMP-002**: Guard the lock acquisition behind a check for `args.command` so
  that bare `aps` (which prints help) and `aps --help` / `aps --version` do not
  require the lock.
- **IMP-003**: Add unit tests that verify: (a) the lock file is created, (b) a
  second call to `acquire_instance_lock()` raises `SystemExit`, and (c) the
  lock is released when the fd is closed. Use `unittest.mock` to patch
  `fcntl.flock` for the conflict case, and a real temp-directory lock file for
  the success case.
- **IMP-004**: Log the lock acquisition at `DEBUG` level
  (`logger.debug("Instance lock acquired: %s", LOCK_PATH)`) for
  troubleshooting.
- **IMP-005**: Document the lock file location in the project README or FAQ so
  users know what `aps.lock` is if they notice it in their config directory.

## References

- **REF-001**: [ADR-0001: Flatpak as pkgmap.ini Provider](../../plans/archive/adr-0001-flatpak-pkgmap-provider.md)
- **REF-002**: [Python fcntl documentation](https://docs.python.org/3/library/fcntl.html)
- **REF-003**: [Linux flock(2) man page](https://man7.org/linux/man-pages/man2/flock.2.html)
- **REF-004**: [Todo item](../todo.md) — "Make aps singleton or another solution"
