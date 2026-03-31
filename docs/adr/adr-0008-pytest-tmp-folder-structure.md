---
title: "ADR-0008: Organized Pytest Temporary Folder Structure"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "testing", "pytest", "developer-experience"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

Pytest creates temporary directories under `/tmp/pytest-of-<user>/` for every
test session. All test types (unit, integration, E2E) currently share a flat
hierarchy inside this root directory, making it difficult to:

- **CTX-001**: **Locate test artifacts** — When inspecting test output after a
  failure, developers must navigate an undifferentiated tree of numbered
  `pytest-NNN/` directories. There is no distinction between unit test temps,
  E2E filesystem simulations, or integration test outputs.
- **CTX-002**: **Clean up selectively** — Deleting stale E2E fixtures without
  affecting unit test artifacts (or vice-versa) is not possible when everything
  lands in the same base directory.
- **CTX-003**: **Parallel CI confusion** — When CI workers share a `/tmp`
  volume, interleaved test sessions produce competing `pytest-of-<user>/`
  directories with no semantic grouping.

Currently the E2E conftest in `tests/e2e/conftest.py` uses
`tmp_path_factory.mktemp("virtmanager-e2e")` and
`tmp_path_factory.mktemp("sudoers-e2e")`, which gives some per-module naming
but still lands inside the default pytest base temp. The global conftest in
`tests/conftest.py` relies on the built-in `tmp_path` fixture without any
custom prefix.

Pytest supports a `--basetemp` CLI flag and a `tmp_path_retention_policy`
config option, but neither solves the grouping problem. What is needed is a
convention that segregates temporary directories by test tier.

## Decision

Introduce per-tier base temporary directories by configuring
`tmp_path_factory`'s `basetemp` in each tier's `conftest.py`, producing the
following filesystem layout:

```
/tmp/
├── pytest-of-<user>-aps-unit/       # Unit test temps
├── pytest-of-<user>-aps-e2e/        # E2E test temps
└── pytest-of-<user>-aps-integration/ # Integration test temps
```

### Implementation approach

1. Add a **session-scoped** `tmp_path_factory` configuration in each tier's
   `conftest.py` that sets the `basetemp` to `/tmp/pytest-of-<user>-aps-<tier>`.
   This can be done using the `tmp_path_factory` fixture or by setting
   `tmp_path_retention_policy` and overriding `_basetemp` via a
   `pytest_configure` hook:

   ```python
   # tests/e2e/conftest.py
   def pytest_configure(config: pytest.Config) -> None:
       import getpass
       from pathlib import Path
       user = getpass.getuser()
       config._tmp_path_factory._basetemp = Path(f"/tmp/pytest-of-{user}-aps-e2e")
   ```

2. Update existing `tmp_path_factory.mktemp()` calls in E2E fixtures to
   continue using module-specific names (e.g., `virtmanager-e2e`,
   `sudoers-e2e`) but now nested under the tier-specific base directory.

3. Document the convention in `AGENTS.md` so future test authors follow the
   pattern.

### Rationale

- Pytest does not natively support per-directory `basetemp` overrides, so a
  `pytest_configure` hook is the least-intrusive approach.
- The naming pattern `pytest-of-<user>-aps-<tier>` preserves the standard
  pytest prefix while adding project and tier context.
- No changes to test logic or assertions are required — only the physical
  location of temp dirs changes.

## Consequences

### Positive

- **POS-001**: Test artifacts are instantly identifiable by tier, reducing
  debugging time when inspecting `/tmp`.
- **POS-002**: Selective cleanup is trivial (`rm -rf /tmp/pytest-of-*-aps-e2e`
  to remove only E2E artifacts).
- **POS-003**: CI logs and artifact uploads can target specific tier directories.
- **POS-004**: The convention is self-documenting via directory names, improving
  onboarding for new contributors.

### Negative

- **NEG-001**: Accessing `_basetemp` or `_tmp_path_factory` is technically
  using a private API; future pytest releases could change it (low risk — this
  has been stable for years).
- **NEG-002**: Adds a small amount of boilerplate to each tier's `conftest.py`.
- **NEG-003**: Developers who rely on `--basetemp` from the CLI will override
  the per-tier defaults, which may cause confusion if not documented.

## Alternatives Considered

### Use `--basetemp` CLI flag per test run

- **ALT-001**: **Description**: Pass `--basetemp=/tmp/pytest-of-<user>-aps-unit`
  to every pytest invocation via Makefile or shell alias.
- **ALT-002**: **Rejection Reason**: Requires all invocations (local dev, CI,
  IDE test runners) to consistently set the flag. Easy to forget and cannot be
  enforced in `pyproject.toml` without a plugin.

### Symlink-based organization

- **ALT-003**: **Description**: Use a post-test hook to symlink or move temp
  directories into an organized tree.
- **ALT-004**: **Rejection Reason**: Fragile, platform-dependent, and
  race-prone. The temp directories may be cleaned by pytest itself between
  sessions.

### Single shared basetemp with tier subdirectories via `mktemp` prefixes

- **ALT-005**: **Description**: Keep the default basetemp and use
  `tmp_path_factory.mktemp("unit-<module>")` / `mktemp("e2e-<module>")`.
- **ALT-006**: **Rejection Reason**: Each test session creates a new numbered
  subdirectory under `pytest-NNN/`, so `mktemp` prefixes are buried one level
  deeper. The top-level directory still provides no grouping.

## Implementation Notes

- **IMP-001**: Start with `tests/e2e/conftest.py` and `tests/conftest.py`
  (unit-level). Integration tests can adopt the pattern when the
  `tests/integrations/` directory gains its own conftest.
- **IMP-002**: Add a brief note in `AGENTS.md` under "Test Folder Structure
  Principles" explaining the convention.
- **IMP-003**: Validate the new paths work in CI by checking that test artifacts
  appear under the expected directories in a smoke-test workflow.

## References

- **REF-001**: [tests/conftest.py](../../tests/conftest.py) — Global test configuration
- **REF-002**: [tests/e2e/conftest.py](../../tests/e2e/conftest.py) — E2E test fixtures
- **REF-003**: [pytest `tmp_path` documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- **REF-004**: [pyproject.toml](../../pyproject.toml) — Current pytest configuration
