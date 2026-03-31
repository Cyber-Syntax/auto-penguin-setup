---
title: "ADR-0007: Unified Package Detection in Setup/Installer Modules via pkgmap.ini"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "DRY", "package-management", "installers", "pkgmap"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

Setup/installer modules under `src/aps/installers/` each implement their own package-detection and installation logic, duplicating work that the core `PackageManager` and `PackageMapper` abstractions already provide.

### Current duplicated patterns

| Module | How it checks "installed" | How it installs | Distro branching |
|--------|--------------------------|-----------------|------------------|
| `ollama.py` | `shutil.which("ollama")` | Hardcoded `pacman -S ollama-cuda/ollama-rocm/ollama` on Arch; `curl \| sh` fallback | `if distro == "arch"` |
| `brave.py` | `shutil.which("brave")` / `shutil.which("brave-browser")` | `curl \| bash` install script | None (script-only) |
| `paru.py` | `shutil.which("paru")` / `shutil.which("yay")` | Manual `git clone` + `makepkg` | `if distro != "arch"` early return |
| `vscode.py` | Tries `pm.install()` first | GPG key import + repo file creation on Fedora; `pm.install_aur()` on Arch | `if distro_id in (...)` |
| `thinkfan.py` | `pm.is_installed("thinkfan")` | `pm.install(["AUR:thinkfan"])` on Arch; `pm.install(["thinkfan"])` elsewhere | `if distro == "arch"` |
| `virtmanager.py` | None (always installs) | `run_privileged(["pacman", ...])` on Arch; `run_privileged(["dnf", ...])` on Fedora | `if distro == "fedora"` / `"arch"` |
| `tlp.py` | `pm.is_installed("tlp")` | `pm.install(["tlp"])` | None (uniform name) |

Problems:

1. **DRY violation** — Many modules re-implement "check installed → pick distro-specific package name → install" instead of using `PackageMapper.map_package()` + `PackageManager.is_installed()` + `PackageManager.install()`.
2. **Inconsistent detection** — Some modules use `shutil.which()` (binary check), others use `pm.is_installed()` (package-database check), and some skip detection entirely. Binary checks miss packages that are installed but not on `$PATH`, and package-database checks miss packages installed outside the package manager.
3. **Hardcoded package names** — Distro-specific names like `ollama-cuda`, `visual-studio-code-bin`, and `AUR:thinkfan` are embedded in Python source instead of living in the declarative `pkgmap.ini` where users and maintainers can override them.
4. **No GPU/variant awareness in pkgmap** — `ollama.py` hardcodes a `pkg_map = {"nvidia": "ollama-cuda", "amd": "ollama-rocm"}` dict. There is no mechanism for `pkgmap.ini` to express variant selection (e.g., GPU-specific packages).

## Decision

Introduce a **unified "ensure package" helper** that installer modules call instead of implementing their own detect-and-install logic. The helper combines `PackageMapper` lookups with `PackageManager` checks, keeping all distro-specific package names in `pkgmap.ini`.

### Concrete changes

### 1. Add a `ensure_package()` helper in `src/aps/core/package_manager.py`

A new function that encapsulates the detect → map → install flow:

```python
def ensure_package(
    generic_name: str,
    pm: PackageManager,
    mapper: PackageMapper,
    *,
    category: str | None = None,
) -> bool:
    """Ensure a package is installed, using pkgmap.ini for name resolution.

    1. Maps generic_name via PackageMapper to get the distro-specific name.
    2. Checks whether the mapped package is already installed.
    3. Installs it if missing.

    Args:
        generic_name: Distribution-agnostic package name (as it appears in
            pkgmap.ini keys).
        pm: PackageManager instance for the current distro.
        mapper: PackageMapper loaded with the user's pkgmap.ini.
        category: Optional tracking category.

    Returns:
        True if the package is installed (was already or just installed),
        False on installation failure.

    """
    mapping = mapper.map_package(generic_name, category=category)

    if pm.is_installed(mapping.mapped_name):
        logger.debug("Package %s already installed", mapping.mapped_name)
        return True

    logger.info("Installing %s (%s)...", generic_name, mapping.mapped_name)
    success, error = pm.install([mapping.mapped_name])
    if not success:
        logger.error("Failed to install %s: %s", mapping.mapped_name, error)
    return success
```

### 2. Extend `pkgmap.ini` with entries for installer packages

Add currently hardcoded package names to the declarative config:

```ini
[pkgmap.arch]
# Existing mappings...
ollama = ollama              # default; user overrides to ollama-cuda / ollama-rocm
vscode = AUR:visual-studio-code-bin
brave = AUR:brave-bin        # or keep script-based install as fallback
borgbackup = borg

[pkgmap.fedora]
# Existing mappings...
ollama = ollama              # fallback to install script when not available
vscode = code
borgbackup = borgbackup
```

GPU-variant selection for ollama is handled by either:

- The user setting `ollama = ollama-cuda` in their personal `pkgmap.ini`, or
- A new `variables.ini` key (per ADR-0006) that the installer reads for auto-detection.

### 3. Refactor installer modules to use `ensure_package()`

Each module replaces its bespoke install logic with:

```python
# Example: thinkfan.py (after refactor)
from aps.core.package_manager import ensure_package, get_package_manager
from aps.core.package_mapper import PackageMapper

def install(distro: str | None = None) -> bool:
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    mapper = PackageMapper(pkgmap_path, distro_info)

    if not ensure_package("thinkfan", pm, mapper):
        return False

    # ... continue with configuration (copy config, enable service, etc.)
```

Modules that have **post-install configuration** (service enablement, config file copying, user/group setup) keep those steps. Only the "detect + install package" portion is replaced.

### 4. Dual-strategy support for script-based installers

For packages where the upstream install script is the canonical method (e.g., `ollama` on non-Arch, `brave`), `ensure_package()` is attempted first. If the package is not available in any configured repository, the module falls back to its existing script-based installer as a secondary strategy:

```python
if not pm.is_available_in_official_repos(mapping.mapped_name):
    return _install_via_script()
```

This preserves the current fallback behaviour while giving pkgmap-managed installs priority.

### 5. Standardise detection to `pm.is_installed()`

Replace `shutil.which()` checks with `pm.is_installed()` as the primary detection mechanism. For script-installed binaries (not managed by the package manager), a secondary `shutil.which()` check is acceptable but must come after the `pm.is_installed()` check:

```python
def _is_present(name: str, pm: PackageManager) -> bool:
    return pm.is_installed(name) or shutil.which(name) is not None
```

## Consequences

### Positive

- **POS-001**: Eliminates duplicated detect → install logic across 10+ installer modules, consolidating it into a single `ensure_package()` function.
- **POS-002**: All distro-specific package names live in `pkgmap.ini`, so users can override names (e.g., `ollama = ollama-cuda`) without editing Python source.
- **POS-003**: Consistent detection strategy (`pm.is_installed()` first, `shutil.which()` second) reduces false positives and false negatives.
- **POS-004**: New installers follow a uniform pattern: call `ensure_package()` for the package, then perform post-install configuration. This lowers the cost of adding new setup components.
- **POS-005**: GPU-variant and provider-variant package selection is declarative (via `pkgmap.ini` or `variables.ini`) rather than hardcoded in conditionals.

### Negative

- **NEG-001**: Existing installer modules must be refactored, which carries regression risk for each module. Thorough test coverage is required before and after migration.
- **NEG-002**: Script-based installers (ollama official script, brave install script) still need module-specific fallback code; `ensure_package()` cannot fully replace them when the package is not in any repository.
- **NEG-003**: Some packages have complex install flows (e.g., `vscode.py` imports GPG keys and creates repo files before installing). These multi-step flows must remain in the module; only the final `install()` call can be standardised.
- **NEG-004**: Users who rely on the current script-based installation behaviour may need to update their `pkgmap.ini` if the default mapping changes the install source.

## Alternatives Considered

### Alternative 1: Do nothing — keep per-module install logic

- **ALT-001**: **Description**: Each installer module continues to implement its own package detection and installation logic with distro-specific branching.
- **ALT-002**: **Rejection Reason**: The DRY violation grows with every new installer module. Inconsistent detection methods lead to bugs (e.g., a package is installed but not detected because `shutil.which()` was used instead of `pm.is_installed()`). Maintenance burden increases linearly with the number of modules.

### Alternative 2: Abstract base class for all installers

- **ALT-003**: **Description**: Create an `InstallerBase` ABC with `detect()`, `install()`, and `configure()` template methods. Each module becomes a subclass.
- **ALT-004**: **Rejection Reason**: The project convention favours functions over classes when state management is not needed (per AGENTS.md). Most installers are stateless — they detect, install, and configure in a single pass. An ABC would add inheritance complexity without matching benefit and would require refactoring every module to a class-based structure.

### Alternative 3: Declarative YAML/TOML installer manifests

- **ALT-005**: **Description**: Define each installer as a declarative manifest (YAML or TOML) specifying packages per distro, pre/post-install commands, service management, and config files. A generic runner interprets the manifest.
- **ALT-006**: **Rejection Reason**: Many installers have complex conditional logic (GPU detection, GPG key import, AUR build steps, systemd unit patching) that is difficult to express declaratively without creating a mini-DSL. The implementation cost is high and the benefit over a simple helper function is marginal for the current number of installers.

## Implementation Notes

- **IMP-001**: Migrate modules incrementally — start with the simplest modules (`tlp.py`, `syncthing.py`, `trashcli.py`) that already use `pm.is_installed()`, then move to modules with distro branching (`thinkfan.py`, `ollama.py`), and finally tackle complex modules (`vscode.py`, `virtmanager.py`).
- **IMP-002**: Add `pkgmap.ini` entries for all installer packages before refactoring the Python modules, so the mapping layer is ready.
- **IMP-003**: Write unit tests for `ensure_package()` covering: already-installed, successful install, failed install, unmapped package (passthrough), and AUR/COPR-prefixed packages.
- **IMP-004**: For GPU-variant selection (`ollama`), implement auto-detection in the ollama module that writes the resolved package name contextually, while still allowing `pkgmap.ini` user overrides to take priority.
- **IMP-005**: Update the `AGENTS.md` "Quick navigation" section to reference the new `ensure_package()` helper once it is implemented.

## References

- **REF-001**: [ADR-0006 — App-specific variables.ini sections](adr-0006-app-specific-variables-ini-sections.md) — Complements this ADR by providing runtime configuration for variant selection (e.g., Ollama GPU choice via `variables.ini`).
- **REF-002**: [ADR-0003 — Extend setup removal to all installers](adr-0003-extend-setup-removal-to-all-installers.md) — Removal logic also benefits from knowing the mapped package name.
- **REF-003**: [PackageMapper](../../src/aps/core/package_mapper.py) — Existing mapping infrastructure this ADR builds upon.
- **REF-004**: [PackageManager](../../src/aps/core/package_manager.py) — Existing `is_installed()` and `install()` APIs used by `ensure_package()`.
- **REF-005**: [pkgmap.ini defaults](../../src/aps/configs/default_aps_configs/pkgmap.ini) — Declarative config file extended with installer package entries.
