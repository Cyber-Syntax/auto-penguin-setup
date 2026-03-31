---
title: "ADR-0010: Disable KDE Wallet When gnome-keyring Is Installed"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "keyring", "kde", "gnome", "desktop-integration"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

APS includes `gnome-keyring` in the `@core` package category
(`src/aps/configs/default_aps_configs/packages.ini`) and `seahorse` (the GNOME
keyring GUI) in `@apps`. On KDE Plasma desktops, the system also ships KDE
Wallet (`kwallet` / `kwalletd6`), which serves the same credential-storage
role. When both keyring backends are active simultaneously, several problems
arise:

- **CTX-001**: **Double credential prompts** — Applications that use the
  freedesktop Secret Service D-Bus API (e.g., Chromium, Brave, SSH agents) may
  trigger unlock dialogs from both `gnome-keyring-daemon` and `kwalletd`,
  confusing users with duplicate password prompts at login.
- **CTX-002**: **Credential fragmentation** — Some applications store secrets in
  `gnome-keyring` while others default to `kwallet`, splitting the user's
  credential store across two backends. This makes secret management and backup
  harder.
- **CTX-003**: **Brave browser workaround already exists** — The Brave installer
  (`src/aps/installers/brave.py`) already has a `_disable_keyring()` function
  that patches the Brave `.desktop` file to use `--password-store=basic`. This
  is a per-app workaround for the broader keyring conflict. A system-level
  solution is more robust.
- **CTX-004**: **APS installs gnome-keyring by default** — Since APS explicitly
  installs `gnome-keyring` as part of `@core`, it should take responsibility for
  ensuring a clean keyring state on systems where KDE Wallet would otherwise
  conflict.

The conflict primarily affects users who:

- Install APS packages on a KDE Plasma desktop (Fedora KDE Spin, Arch with Plasma).
- Use Chromium-based browsers that query the Secret Service API.

## Decision

Add a post-install hook to the `gnome-keyring` installation flow (or to the
`@core` category install) that detects the presence of KDE Wallet and disables
it when `gnome-keyring` is the intended primary keyring backend.

### Implementation approach

1. **Detection**: Check whether `kwalletd5` or `kwalletd6` is installed
   (via `shutil.which` or the package manager's `is_installed` method).

2. **Disable KDE Wallet**: Write a KDE config entry to disable the wallet
   subsystem:

   ```ini
   # ~/.config/kwalletrc
   [Wallet]
   Enabled=false
   First Use=false
   ```

   This is the standard KDE mechanism for disabling kwallet without
   uninstalling it. It avoids removing packages that may be dependencies of
   the Plasma desktop itself.

3. **Scope**: Apply only during `aps install @core` (or any install that
   includes `gnome-keyring`). Do not run during `aps install @apps` or
   unrelated operations.

4. **User notification**: Log an informational message when kwallet is
   disabled, explaining the reason and how to re-enable it.

5. **Idempotency**: If `kwalletrc` already has `Enabled=false`, skip the write.
   If the file does not exist, create it. If it exists with `Enabled=true`,
   update it.

### Rationale

- Disabling via config is non-destructive and easily reversible.
- `gnome-keyring` is already the APS-endorsed keyring (it is in `@core`), so
  disabling the competing backend is consistent with the project's opinionated
  defaults.
- The existing per-app workaround in `brave.py` can eventually be simplified
  once the system-level conflict is resolved.

## Consequences

### Positive

- **POS-001**: Eliminates double credential prompts on KDE desktops after APS
  package installation.
- **POS-002**: All Secret Service clients consistently use `gnome-keyring`,
  preventing credential fragmentation.
- **POS-003**: Simplifies the Brave installer's `_disable_keyring()` workaround
  — the `--password-store=basic` flag may become unnecessary once
  `gnome-keyring` is the sole backend.
- **POS-004**: The change is easily reversible by setting `Enabled=true` in
  `~/.config/kwalletrc`.

### Negative

- **NEG-001**: Users who intentionally use KDE Wallet for some applications
  will have it silently disabled. Mitigated by logging a clear message and
  documenting re-enablement.
- **NEG-002**: Writing to `~/.config/kwalletrc` modifies user-level KDE state,
  which is outside the typical scope of a package manager tool.
- **NEG-003**: The detection logic must handle both `kwalletd5` (Plasma 5) and
  `kwalletd6` (Plasma 6), adding minor complexity.
- **NEG-004**: If the user is not on a KDE desktop but has `kwalletd` installed
  as a dependency, the disable is a no-op but may generate a confusing log
  message.

## Alternatives Considered

### Uninstall KDE Wallet packages

- **ALT-001**: **Description**: Remove `kwallet` / `kwalletd6` packages when
  `gnome-keyring` is installed by APS.
- **ALT-002**: **Rejection Reason**: KDE Wallet packages are often hard
  dependencies of `plasma-desktop` or `plasma-workspace`. Removing them would
  break the desktop environment. Disabling via config is safer.

### Per-application password-store flags only

- **ALT-003**: **Description**: Expand the existing `_disable_keyring()` pattern
  from Brave to all Chromium-based browsers by patching their `.desktop` files
  with `--password-store=gnome-libsecret`.
- **ALT-004**: **Rejection Reason**: Does not solve the problem for non-browser
  applications (SSH agents, NetworkManager, etc.). Each new app would require
  its own workaround.

### Set `gnome-keyring` as the default Secret Service provider via D-Bus

- **ALT-005**: **Description**: Ensure `gnome-keyring-daemon` claims the
  `org.freedesktop.secrets` D-Bus name at session startup by adjusting XDG
  autostart priority.
- **ALT-006**: **Rejection Reason**: D-Bus name ownership depends on startup
  ordering, which varies across display managers and session types. Unreliable
  and hard to debug. Disabling kwallet is more deterministic.

### Do nothing and document the conflict

- **ALT-007**: **Description**: Add a FAQ entry or warning message without
  automated remediation.
- **ALT-008**: **Rejection Reason**: APS is an automation tool — users expect it
  to handle configuration conflicts, not merely document them. A tool that
  installs `gnome-keyring` should ensure it works cleanly.

## Implementation Notes

- **IMP-001**: Create a utility function (e.g., in `src/aps/utils/` or a new
  `src/aps/system/keyring.py`) that handles kwallet detection and config writing.
  This keeps the logic reusable and testable.
- **IMP-002**: Add unit tests covering: kwallet not installed (no-op), kwallet
  installed with no existing config, kwallet installed with existing
  `Enabled=true`, and kwallet installed with existing `Enabled=false`
  (idempotent).
- **IMP-003**: Integrate the hook into the install command's post-install phase,
  triggered only when `gnome-keyring` is in the resolved package list.
- **IMP-004**: Consider a `--no-keyring-fix` flag or `variables.ini` option to
  let advanced users opt out.

## References

- **REF-001**: [src/aps/configs/default_aps_configs/packages.ini](../../src/aps/configs/default_aps_configs/packages.ini) — `gnome-keyring` in `@core`
- **REF-002**: [src/aps/installers/brave.py](../../src/aps/installers/brave.py) — Existing `_disable_keyring()` workaround
- **REF-003**: [KDE Wallet documentation](https://docs.kde.org/stable5/en/kwalletmanager/kwallet/) — Official KDE Wallet settings
- **REF-004**: [freedesktop.org Secret Service API](https://specifications.freedesktop.org/secret-service/latest/) — D-Bus API both backends implement
