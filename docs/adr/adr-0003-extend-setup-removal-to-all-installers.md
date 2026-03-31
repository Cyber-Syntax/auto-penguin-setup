---
title: "ADR-0003: Extend --setup Removal Flag to All Installer Modules"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "cli", "installers", "removal"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed** | Accepted | Rejected | Superseded | Deprecated

## Context

The `aps remove --setup` flag currently only supports Ollama, which was the
first installer module to implement the `uninstall()` convention introduced in
the setup-removal-flag plan. While the infrastructure is fully in place —
`SetupManager.remove_component()` dispatches to any installer module exposing an
`uninstall(distro)` function, and the CLI dynamically populates `--setup`
choices from `get_removable_components()` — Ollama remains the only module with
an `uninstall()` implementation.

Several installer modules configure system-level resources that are not cleaned
up by simply removing packages:

- **TLP** (`tlp.py`): Enables TLP and tlp-sleep services, masks
  `systemd-rfkill.service`/`.socket`, copies custom config to `/etc/tlp.d/`,
  disables and removes conflicting services (tuned, power-profiles-daemon). None
  of this is reversed if the user wants to switch to auto-cpufreq.
- **auto-cpufreq** (`autocpufreq.py`): Runs its own installer script, enables a
  systemd service. Switching back to TLP leaves auto-cpufreq residue.
- **trash-cli** (`trashcli.py`): Copies systemd service and timer files to
  `/etc/systemd/system/`, enables the timer. Uninstalling the package leaves
  orphaned systemd units.
- **VS Code** (`vscode.py`): Adds third-party repository and GPG key on Fedora,
  or installs from AUR on Arch. Removal should clean up the repo/key.
- **Syncthing** (`syncthing.py`): Enables a user-level systemd service.
- **Brave** (`brave.py`): Adds third-party repository and GPG key on Fedora.
- **Thinkfan** (`thinkfan.py`): Copies config, enables systemd service with
  `--now`, loads kernel module.
- **Borgbackup** (`borgbackup.py`): Creates systemd service/timer, SSH keys,
  wrapper script in `/usr/local/bin/`.
- **Virt-Manager** (`virtmanager.py`): Patches libvirt config files, manages
  libvirtd service, adds user to groups.
- **Oh-My-Zsh** (`ohmyzsh.py`): Clones Git repo into `~/.oh-my-zsh`, installs
  plugins.
- **Ueberzug++** (`ueberzugpp.py`): Builds from source and installs via cmake.
- **Paru** (`paru.py`): Builds from source into a temporary directory.

The existing `remove_component()` machinery in `SetupManager` and the parser's
dynamic `choices` list make extending removal straightforward: each new
`uninstall()` function is automatically picked up without touching core plumbing.

## Decision

Add `uninstall(distro: str | None = None) -> bool` functions to all installer
modules that create system-level side effects beyond package installation. Each
`uninstall()` will perform a best-effort cleanup of the artifacts created by its
corresponding `install()` function (services, config files, repos, keys, users,
groups, build artifacts).

Prioritized rollout order based on user impact and cleanup complexity:

1. **High priority** (system service conflicts / switching use case):
   `tlp`, `autocpufreq`, `trashcli`, `thinkfan`
2. **Medium priority** (repo/key cleanup):
   `vscode`, `brave`, `borgbackup`, `syncthing`
3. **Lower priority** (user-local or build artifacts):
   `virtmanager`, `ohmyzsh`, `ueberzugpp`, `paru`

Each `uninstall()` must:

- Stop and disable any systemd services/timers it created.
- Remove config files, service files, and repo/key files it placed.
- Unmask any services it masked (e.g., TLP masks rfkill services).
- Re-enable previously disabled conflicting services when appropriate (e.g., TLP
  uninstall should re-enable `power-profiles-daemon` if present).
- Remove system users/groups it created (where applicable).
- Use `run_privileged()` for all privileged operations.
- Return `True` on success, `False` on failure, using best-effort cleanup
  (continue on partial failures, log warnings).
- Follow the existing Ollama `uninstall()` pattern as reference implementation.

No changes are required to `SetupManager`, the CLI parser, or `cmd_remove` —
they already handle any module with an `uninstall()` function.

## Consequences

### Positive

- **POS-001**: Users can cleanly switch between conflicting tools (TLP <->
  auto-cpufreq) without manual service/config cleanup, which is the primary
  motivating use case.
- **POS-002**: Orphaned systemd units, repo files, and GPG keys are properly
  cleaned up, reducing system clutter and potential conflicts after removal.
- **POS-003**: The `aps remove --setup` choices list grows automatically as
  modules gain `uninstall()`, providing a consistent UX without CLI changes.
- **POS-004**: Each `uninstall()` is self-contained within its module, following
  the existing convention and keeping the codebase modular.
- **POS-005**: Enables future tracking of setup component state in the JSONL
  database, building toward `aps list` / `aps status` visibility for components.

### Negative

- **NEG-001**: Each `uninstall()` must accurately mirror the side effects of its
  `install()`. If `install()` changes, the corresponding `uninstall()` must be
  updated, creating a maintenance coupling within each module.
- **NEG-002**: Best-effort cleanup may leave partial artifacts on failure (e.g.,
  service stopped but config not removed). Users may need manual intervention in
  edge cases.
- **NEG-003**: Significant implementation effort across 12+ modules, each
  requiring dedicated unit tests. Increases total test surface area.
- **NEG-004**: Some uninstall operations are inherently risky (e.g., removing
  libvirt configs that may have been manually customized by the user). Need to
  handle user-modified files cautiously.

## Alternatives Considered

### Manual uninstall documentation

- **ALT-001**: **Description**: Document manual uninstall steps in a wiki or
  `--help` output instead of implementing `uninstall()` functions.
- **ALT-002**: **Rejection Reason**: Defeats the purpose of an automation tool.
  Users chose APS specifically to avoid manual system configuration. Manual steps
  are error-prone and frequently become outdated.

### Generic uninstall via package manager only

- **ALT-003**: **Description**: Only run `pm.remove()` for the component's
  packages, without cleaning up services, configs, or repos.
- **ALT-004**: **Rejection Reason**: Package removal alone does not reverse the
  system-level side effects (enabled services, masked units, custom configs,
  repo/key files). This is the exact problem motivating this ADR — switching
  from TLP to auto-cpufreq requires more than `dnf remove tlp`.

### Declarative uninstall registry

- **ALT-005**: **Description**: Define cleanup actions declaratively in the
  `COMPONENT_REGISTRY` (e.g., list of services to stop, files to remove) and
  have `SetupManager` execute them generically.
- **ALT-006**: **Rejection Reason**: Many uninstall procedures have
  conditional logic (e.g., Ollama checks `pacman -Qo` ownership, TLP should
  re-enable `power-profiles-daemon`). A declarative approach cannot cover
  these cases without becoming as complex as imperative code, while losing
  readability and debuggability.

### All-at-once implementation

- **ALT-007**: **Description**: Implement all `uninstall()` functions in a
  single phase rather than prioritized rollout.
- **ALT-008**: **Rejection Reason**: High risk of introducing bugs across many
  modules simultaneously. Phased rollout allows validating the pattern with
  high-impact modules first and incorporating lessons learned.

## Implementation Notes

- **IMP-001**: Follow TDD approach per the project's existing convention — write
  failing tests for each `uninstall()`, then implement. Each module's tests live
  in the corresponding `tests/installers/test_<module>.py` file.
- **IMP-002**: Use the Ollama `uninstall()` in
  [ollama.py](src/aps/installers/ollama.py) as the reference pattern: check if
  installed, distro-specific path, then best-effort artifact cleanup.
- **IMP-003**: For TLP specifically, `uninstall()` should unmask
  `systemd-rfkill.service`/`.socket` and optionally re-enable
  `power-profiles-daemon`, reversing the conflict resolution done during install.
- **IMP-004**: For modules that add repos/keys (vscode, brave), `uninstall()`
  should remove the `.repo` file and GPG key to prevent stale repo errors on
  system update.
- **IMP-005**: Success criteria: `aps remove --setup <component>` leaves the
  system in a state where a conflicting tool can be set up cleanly via
  `aps setup <other-component>` without manual intervention.

## References

- **REF-001**: [ADR-0002: Singleton via fcntl.flock](adr-0002-singleton-via-fcntl-flock.md)
- **REF-002**: [Setup removal flag plan](../../plans/archive/setup-removal-flag-plan.md)
  — original 5-phase plan that introduced the `--setup` flag and Ollama
  `uninstall()` convention
- **REF-003**: Ollama `uninstall()` reference implementation in
  `src/aps/installers/ollama.py`
- **REF-004**: `SetupManager.remove_component()` and
  `get_removable_components()` in `src/aps/core/setup.py`
