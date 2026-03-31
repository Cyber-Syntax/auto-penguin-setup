---
title: "ADR-0005: Add Tuned Setup Component for CPU Performance Tuning"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "performance", "cpu", "tuned", "cpupower"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

APS currently offers `auto-cpufreq` and `tlp` as power/performance management
setup components. However, `auto-cpufreq` has a known limitation: after
installation the CPU governor remains locked to `powersave`, and users cannot
override it to `performance` without fighting the daemon. This prevents users
from unlocking the full hardware frequency range (for example, a CPU capped at
3.79 GHz instead of the hardware-supported 4.65 GHz with turbo boost).

`tuned` is the Red Hat-maintained, profile-based system tuning daemon that ships
in both Fedora and Arch repositories. Combined with `cpupower` (from
`kernel-tools` / `cpupower`), it provides fine-grained control over:

- System-wide tuning profiles (`desktop`, `throughput-performance`,
  `laptop-battery-powersave`, etc.)
- CPU frequency governor selection (`performance`, `powersave`, `schedutil`)
- Turbo boost toggling

Observed results when switching from `auto-cpufreq` to `tuned` + `cpupower`:

```bash
# Before (auto-cpufreq active)
energy performance preference: balance_performance
hardware limits: 561 MHz - 3.79 GHz   # turbo boost not unlocked

# After (tuned desktop profile + performance governor + turbo boost enabled)
energy performance preference: balance_performance
hardware limits: 561 MHz - 4.65 GHz   # full turbo boost unlocked
```

The project needs a `tuned` installer module that is offered as an **alternative
to `auto-cpufreq`** so users can choose the approach that best fits their
workload. Because `tuned` and `auto-cpufreq` both manage CPU governors, running
them simultaneously would cause conflicts; they must be treated as mutually
exclusive options.

## Decision

Add a new `tuned` setup component under `src/aps/installers/tuned.py` that:

1. **Installs packages** — `tuned` and `cpupower` (mapped via `pkgmap.ini` for
   cross-distro support).
2. **Supports multiple profiles** — Lets the user select a `tuned-adm` profile
   (e.g. `desktop`, `throughput-performance`, `laptop-battery-powersave`),
   defaulting to `desktop`.
3. **Applies CPU settings** — Sets the CPU governor via `cpupower frequency-set
   --governor <governor>` and optionally enables turbo boost via `cpupower set
   --turbo-boost 1`.
4. **Enables the service** — Starts and enables `tuned.service` via systemd.
5. **Conflict guard** — Checks whether `auto-cpufreq` is active and warns (or
   offers to disable it) before proceeding, since both tools manage the CPU
   governor.
6. **Registers in `SetupManager.COMPONENT_REGISTRY`** — Follows the existing
   pattern in `src/aps/core/setup.py`.
7. **Supports removal** — Implements `remove()` to disable the service, restore
   the previous governor, and optionally uninstall the packages.

The rationale for choosing this approach:

- `tuned` is distribution-maintained and well-tested on both Fedora and Arch.
- Profile-based tuning is simpler to reason about than `auto-cpufreq`'s
  automated daemon logic.
- `cpupower` gives direct, transparent control over governor and turbo settings.
- Users can verify the result immediately with `cpupower frequency-info`.

## Consequences

### Positive

- **POS-001**: Users gain access to the full hardware frequency range including
  turbo boost (e.g. 4.65 GHz vs. 3.79 GHz).
- **POS-002**: Profile-based approach (`tuned-adm profile <name>`) is intuitive
  and covers desktop, laptop, and server workloads without code changes.
- **POS-003**: `tuned` is maintained by Red Hat and packaged in both Fedora and
  Arch, reducing maintenance burden compared to building `auto-cpufreq` from
  source.
- **POS-004**: Transparent CPU state — users can audit settings with standard
  tools (`cpupower frequency-info`, `tuned-adm active`).
- **POS-005**: Follows the existing installer module pattern, keeping the
  codebase consistent.

### Negative

- **NEG-001**: Introduces a mutually-exclusive relationship with `auto-cpufreq`
  that must be communicated to users and enforced in code.
- **NEG-002**: `cpupower` governor and turbo settings are not persistent across
  reboots by default — the installer must rely on `tuned.service` or a systemd
  unit to reapply them.
- **NEG-003**: Users migrating from `auto-cpufreq` must manually (or via APS
  remove) disable the old service before switching, adding a migration step.
- **NEG-004**: Multi-profile support adds complexity to the installer (profile
  validation, user prompting) compared to a single hardcoded profile.

## Alternatives Considered

### Keep auto-cpufreq Only

- **ALT-001**: **Description**: Continue using `auto-cpufreq` as the sole CPU
  tuning component and document governor overrides as manual post-install steps.
- **ALT-002**: **Rejection Reason**: `auto-cpufreq` actively overrides manual
  governor changes back to `powersave`, making it impossible to maintain a
  `performance` governor without disabling the daemon. This defeats the purpose
  of automating the setup.

### Use cpupower Alone (Without tuned)

- **ALT-003**: **Description**: Install only `cpupower` and apply governor +
  turbo settings via a custom systemd service, skipping `tuned` entirely.
- **ALT-004**: **Rejection Reason**: `tuned` provides a broader set of
  system-wide optimizations (disk I/O scheduler, kernel parameters, network
  tuning) beyond just CPU frequency. Using `cpupower` alone would require
  reimplementing these tuning knobs manually and maintaining custom systemd
  units.

### Use power-profiles-daemon

- **ALT-005**: **Description**: Use GNOME's `power-profiles-daemon` which
  provides `balanced`, `power-saver`, and `performance` profiles via D-Bus.
- **ALT-006**: **Rejection Reason**: `power-profiles-daemon` is tightly coupled
  to GNOME/desktop environments and provides fewer tuning knobs than `tuned`. It
  also conflicts with `tuned` and `tlp`, limiting flexibility. APS targets
  multiple WM/DE setups including Qtile without a full desktop stack.

## Implementation Notes

- **IMP-001**: The installer module should follow the existing pattern in
  `src/aps/installers/tlp.py` — detect distro, install packages via
  `PackageManager`, copy configs, enable systemd service.
- **IMP-002**: Add `tuned` and `cpupower` (or `kernel-tools` on Fedora) to
  `pkgmap.ini` for cross-distro package name resolution.
- **IMP-003**: Implement conflict detection: check for active `auto-cpufreq`
  service via `systemctl is-active auto-cpufreq` and warn or offer to disable
  before proceeding.
- **IMP-004**: The `tuned-adm profile` selection can be presented interactively
  via the CLI or accepted as a parameter, with `desktop` as the default.
- **IMP-005**: Turbo boost and governor settings should be applied after the
  `tuned` profile to layer on top of the profile defaults. Document that
  `tuned.service` reapplies the profile on boot, ensuring persistence.
- **IMP-006**: Register `"tuned"` in `SetupManager.COMPONENT_REGISTRY` in
  `src/aps/core/setup.py` following the existing component pattern.
- **IMP-007**: Add unit tests mocking `subprocess`/`run_privileged` calls, and
  verify conflict detection logic against `auto-cpufreq`.

## References

- **REF-001**: [ADR-0003: Extend Setup Removal to All Installers](adr-0003-extend-setup-removal-to-all-installers.md) —
  removal support pattern for the new installer
- **REF-002**: [tuned documentation (Red Hat)](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/monitoring_and_managing_system_status_and_performance/getting-started-with-tuned_monitoring-and-managing-system-status-and-performance)
- **REF-003**: [cpupower(1) man page](https://man7.org/linux/man-pages/man1/cpupower.1.html)
- **REF-004**: Existing installer modules: `src/aps/installers/autocpufreq.py`,
  `src/aps/installers/tlp.py`
