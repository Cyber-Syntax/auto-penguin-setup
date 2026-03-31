---
title: "ADR-0006: Add Application-Specific Sections to variables.ini"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "configuration", "variables", "ollama", "borgbackup"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

APS installer modules (`src/aps/installers/`) currently hardcode filesystem paths and application-specific settings directly in Python source code. For example:

- **Ollama** (`src/aps/installers/ollama.py`) — The default Ollama model storage location is managed by the systemd service at `/usr/lib/systemd/system/ollama.service`. Users who store models on a separate mount (e.g., `/mnt/backups/ollama/models`) must manually edit the systemd unit to add `Environment="OLLAMA_MODELS=/mnt/backups/ollama/models"` after every package update, since updates overwrite the unit file.
- **Borgbackup** (`src/aps/installers/borgbackup.py`) — The repository path `/opt/borg` and the service user home `/var/lib/borg` are hardcoded. Users backing up to an external or network-mounted drive have no declarative way to configure the repo path.

The existing `variables.ini` already follows a section-per-concern pattern (`[system]`, `[browser]`, `[ssh]`, etc.) and `APSConfigParser` exposes `get()` and `get_variables()` methods that can read arbitrary sections. Adding new sections is therefore a natural extension of the current configuration model.

The problem can be summarised as:

1. There is no single, declarative place for users to declare application-specific paths and settings.
2. Installer modules cannot adapt behaviour (e.g., injecting environment variables into systemd units) without reading user-specific values at runtime.
3. Hardcoded paths make the tool non-portable across different disk layouts and user preferences.

## Decision

Introduce **application-specific sections** in `variables.ini` for any installer module that requires user-configurable paths or settings. Each section is named after its installer module (e.g., `[ollama]`, `[borgbackup]`).

### Concrete changes

1. **`variables.ini` schema** — Add new sections to the default config at `src/aps/configs/default_aps_configs/variables.ini`:

   ```ini
   # ============================================================================
   # Application-Specific Settings
   # ============================================================================

   [ollama]
   # Custom path for Ollama model storage.
   # Leave empty to use the Ollama default (~/.ollama/models or /usr/share/ollama).
   models_path=

   [borgbackup]
   # Path to the Borg repository used by the backup timer.
   repo_path=/opt/borg
   ```

2. **Installer reads config at runtime** — Each installer's `install()` function accepts (or internally loads) the parsed `variables.ini` and reads its own section:

   ```python
   # In ollama.py
   models_path = config.get("ollama", "models_path")
   if models_path:
       _configure_ollama_models_path(models_path)
   ```

3. **Ollama systemd unit patching** — Add a new helper `_configure_ollama_models_path(path: str)` inside `src/aps/installers/ollama.py` that:
   - Reads `/usr/lib/systemd/system/ollama.service` (or the distro-appropriate path).
   - Inserts or updates the `Environment="OLLAMA_MODELS=<path>"` line under the `[Service]` section.
   - Writes the patched unit to `/etc/systemd/system/ollama.service` (override location) so package updates do not clobber the customisation.
   - Runs `systemctl daemon-reload` to pick up the change.

4. **Borgbackup path variable** — The `install()` function in `src/aps/installers/borgbackup.py` replaces the hardcoded `/opt/borg` with the value of `repo_path` from the `[borgbackup]` section, falling back to `/opt/borg` if the key is empty or the section is missing.

5. **Convention** — Future installers that need user-configurable values follow the same pattern: add a `[module_name]` section to the default `variables.ini` and read it via `APSConfigParser.get()`.

## Consequences

### Positive

- **POS-001**: Users declare all site-specific paths in one file (`variables.ini`) instead of editing Python source or systemd units by hand.
- **POS-002**: Ollama model path survives package updates because the override is written to `/etc/systemd/system/` rather than patching the vendor unit in `/usr/lib/systemd/system/`.
- **POS-003**: The existing `APSConfigParser` API (`get()`, `get_variables()`) already supports this; no parser changes are required.
- **POS-004**: Consistent naming convention (`[module_name]`) makes it trivial for future installers to adopt the same pattern.
- **POS-005**: Sensible defaults (empty or current hardcoded values) ensure zero-config behaviour for users who do not customise.

### Negative

- **NEG-001**: Adding sections to `variables.ini` increases the file size and cognitive load for users who do not use those installers.
- **NEG-002**: Existing users who already have a `variables.ini` will not automatically get the new sections; they must copy them manually or regenerate the config.
- **NEG-003**: Patching systemd unit files requires careful parsing; a malformed write could break the Ollama service.
- **NEG-004**: Each new installer that needs config adds another section, which could lead to a large `variables.ini` over time.

## Alternatives Considered

### Separate per-installer config files

- **ALT-001**: **Description**: Create individual config files such as `ollama.ini`, `borgbackup.ini` in the APS config directory, each with its own variables.
- **ALT-002**: **Rejection Reason**: Proliferates config files that users must discover and manage individually. The section-based approach in a single file is simpler and consistent with the existing `variables.ini` pattern used for `[browser]`, `[ssh]`, etc.

### Environment variables only

- **ALT-003**: **Description**: Read application paths from shell environment variables (e.g., `APS_OLLAMA_MODELS_PATH`) instead of an INI section.
- **ALT-004**: **Rejection Reason**: Environment variables are session-scoped and harder to persist declaratively across reboots. `variables.ini` is always loaded by APS at startup, making it a more reliable and discoverable configuration surface.

### Patch the vendor systemd unit in-place

- **ALT-005**: **Description**: Modify `/usr/lib/systemd/system/ollama.service` directly instead of writing an override to `/etc/systemd/system/`.
- **ALT-006**: **Rejection Reason**: Package manager updates overwrite vendor units, causing user changes to be lost. Writing to the override path (`/etc/systemd/system/`) is the systemd-recommended approach for local customisation.

### Use systemd drop-in overrides

- **ALT-007**: **Description**: Instead of copying the full unit file to `/etc/systemd/system/`, create a drop-in snippet at `/etc/systemd/system/ollama.service.d/models-path.conf` that only sets the `Environment=` directive.
- **ALT-008**: **Rejection Reason**: Drop-ins are the most idiomatic systemd approach and could be adopted later. The full-unit override is chosen initially for simplicity—it avoids directory creation and is easier to inspect/debug. Migrating to drop-ins is a non-breaking future improvement.

## Implementation Notes

- **IMP-001**: The `_configure_ollama_models_path()` helper should validate that the target directory exists (or can be created) before writing the override to avoid starting the service with a broken `OLLAMA_MODELS` path.
- **IMP-002**: Writing the systemd override requires root privileges; use `run_privileged()` from `aps/utils/privilege.py` and ensure `ensure_sudo()` is called at the command entry point.
- **IMP-003**: For Borgbackup, the `repo_path` variable should replace every occurrence of the hardcoded `/opt/borg` in the install flow, including the `mkdir`, service-file copy source path, and script references.
- **IMP-004**: Add unit tests that mock `APSConfigParser.get()` to verify installers correctly read and apply the new variables, including the empty/missing fallback case.
- **IMP-005**: Document the new sections in the default `variables.ini` with inline comments explaining each key and its default.

## References

- **REF-001**: [variables.ini default config](../../src/aps/configs/default_aps_configs/variables.ini) — current schema
- **REF-002**: [APSConfigParser](../../src/aps/core/config.py) — `get()` and `get_variables()` methods
- **REF-003**: [Ollama installer](../../src/aps/installers/ollama.py) — current hardcoded paths
- **REF-004**: [Borgbackup installer](../../src/aps/installers/borgbackup.py) — current hardcoded paths
- **REF-005**: [systemd.unit(5) — override semantics](https://www.freedesktop.org/software/systemd/man/systemd.unit.html) — `/etc/systemd/system/` overrides `/usr/lib/systemd/system/`
