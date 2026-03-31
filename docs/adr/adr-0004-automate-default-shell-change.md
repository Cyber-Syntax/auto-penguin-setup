---
title: "ADR-0004: Automate Default Shell Change from Fish to Bash"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "shell", "automation", "ohmyzsh"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

Some systems end up with fish as the default login shell, which can conflict with
scripts and tooling that assume a POSIX-compatible shell (`/bin/bash`). Today,
resetting the shell is a manual step (`chsh -s /bin/bash`) that is easy to forget
during a fresh system setup.

The existing Oh-My-Zsh installer (`src/aps/installers/ohmyzsh.py`) explicitly
passes `CHSH: "no"` to the upstream install script, meaning it does **not**
change the user's login shell. This is intentional—Oh-My-Zsh should not
silently alter the login shell without the user's awareness.

Since APS already runs a zsh/Oh-My-Zsh setup component that assumes zsh is the
desired interactive shell, a logical place to also ensure the login shell is a
POSIX-compatible default (bash) is within that same flow or as a small
pre-/post-step.

**Key forces:**

- Users who previously set fish as default may not realize it until something
  breaks.
- `chsh` requires the target shell to exist and be listed in `/etc/shells`.
- A single `chsh -s /bin/bash` call is sufficient but must run as the target
  user (not root), so `sudo` is **not** needed for the current user.
- Oh-My-Zsh installs zsh plugins but intentionally avoids changing the login
  shell; this decision should remain independent.

## Decision

Add a `default-shell` reset step that runs `chsh -s /bin/bash` for the current
user. This step will:

1. **Be invocable as a standalone setup component** (`aps setup default-shell`)
   so it can be run independently.
2. **Optionally be triggered at the end of the `ohmyzsh` setup** when the
   current login shell is not `/bin/bash` (with a logged informational message),
   keeping the two concerns loosely coupled.
3. **Validate preconditions**: verify `/bin/bash` exists and is listed in
   `/etc/shells` before calling `chsh`.
4. **Skip with a log message** if the shell is already `/bin/bash`.

Rationale: a standalone component keeps the single-responsibility principle
intact while still allowing composed workflows. Tying it to the ohmyzsh
installer only would hide useful functionality from users who don't use zsh.

## Consequences

### Positive

- **POS-001**: Eliminates a manual post-install step, reducing setup friction.
- **POS-002**: Prevents subtle breakage caused by fish being the login shell for
  POSIX-dependent scripts and tools.
- **POS-003**: Keeps Oh-My-Zsh installer unchanged (`CHSH: "no"` stays),
  maintaining separation of concerns.
- **POS-004**: Can be composed with other setup components via
  `aps setup default-shell ohmyzsh`.

### Negative

- **NEG-001**: Changing the login shell is a user-visible side effect; if someone
  intentionally uses fish as their login shell, this could be surprising.
- **NEG-002**: Adds another setup component to maintain and test, including edge
  cases around `/etc/shells` content and missing `/bin/bash`.
- **NEG-003**: Running `chsh` may prompt for a password on some distributions,
  which could break non-interactive automation unless PAM is configured to allow
  it without a password.

## Alternatives Considered

### Integrate directly into ohmyzsh installer

- **ALT-001**: **Description**: Change `CHSH: "no"` to `CHSH: "yes"` in
  `ohmyzsh.py`, letting the upstream Oh-My-Zsh script handle the shell change
  to zsh (not bash).
- **ALT-002**: **Rejection Reason**: This changes the login shell to zsh rather
  than bash, which is not the desired outcome. It also couples shell management
  to Oh-My-Zsh, and the upstream script's `chsh` behavior varies between
  versions.

### Do nothing (manual step)

- **ALT-003**: **Description**: Keep the `chsh -s /bin/bash` step as a manual
  task documented in the todo list.
- **ALT-004**: **Rejection Reason**: The entire purpose of APS is to automate
  repetitive setup tasks. A one-line command is simple but still gets forgotten;
  automating it is consistent with the project's philosophy.

### Change to zsh instead of bash

- **ALT-005**: **Description**: Use `chsh -s /bin/zsh` since Oh-My-Zsh is
  being installed anyway.
- **ALT-006**: **Rejection Reason**: Bash is the universal POSIX-compatible
  default expected by system scripts, cron jobs, and login environments.
  Oh-My-Zsh is an interactive enhancement, not a replacement for the login
  shell on most setups. Users who want zsh as their login shell can override
  manually.

## Implementation Notes

- **IMP-001**: Create `src/aps/installers/default_shell.py` with `install()` and
  `is_installed()` following the existing installer module pattern. `install()`
  runs `chsh -s /bin/bash` after validation; `is_installed()` checks if the
  current login shell is already `/bin/bash`.
- **IMP-002**: Register the component in `SetupManager.COMPONENT_REGISTRY` in
  `src/aps/core/setup.py` as `"default-shell"`.
- **IMP-003**: Validate `/bin/bash` exists and appears in `/etc/shells` before
  executing `chsh`. Log a clear error if either check fails.
- **IMP-004**: Add unit tests in `tests/installers/test_default_shell.py`
  mocking `subprocess.run` and `/etc/shells` reads.

## References

- **REF-001**: [ohmyzsh installer](../../src/aps/installers/ohmyzsh.py) — current
  Oh-My-Zsh setup with `CHSH: "no"`
- **REF-002**: [SetupManager registry](../../src/aps/core/setup.py) — component
  registration pattern
- **REF-003**: `chsh(1)` man page — standard utility for changing login shell
- **REF-004**: [Todo item](../todo.md) — original task entry
