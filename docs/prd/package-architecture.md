# PRD: Package Architecture Redesign

- Version: 1.0
- Date: 2026-02-28
- Status: Draft

## 1. Product overview

### 1.1 Document title and version

- PRD: Package Architecture Redesign
- Version: 1.0

### 1.2 Product summary

Auto Penguin Setup (aps) automates Linux system setup across Fedora and Arch
family distributions. Today, aps stores the user's desired package list in
`packages.ini` (INI format), maps generic names to distro-specific names in
`pkgmap.ini`, and tracks what is actually installed in `metadata.jsonl` (JSONL
format). These three stores work independently, leading to configuration drift
when packages are installed ad-hoc via `aps install X` without manually editing
`packages.ini`.

This PRD proposes a full architecture redesign to solve the drift problem, move
to a modern configuration format (TOML), and add commands for bidirectional
synchronization between the "desired state" configuration and the "installed
state" database. The redesign must keep the tool simple and focused on its core
mission: automating repetitive setup tasks on fresh Linux installs.

## 2. Goals

### 2.1 Business goals

- Eliminate manual editing of configuration files after ad-hoc installs/removes.
- Reduce time-to-setup on a fresh machine by making the config file a reliable
  and portable "desired state" declaration.
- Make the tool approachable for users who just want to list packages and run
  one command.

### 2.2 User goals

- Install a package and have it persist in the desired-state config
  automatically.
- Remove a package and have it disappear from both the tracking DB and the
  desired-state config.
- Export the current setup to a portable file that can be applied on a new
  machine.
- Import/merge a config from another machine without losing local customizations.
- Understand what is installed vs. what is declared vs. what is missing at a
  glance.

### 2.3 Non-goals

- Building a full-blown package manager (aps delegates to dnf/pacman/flatpak).
- Replacing the distro's package database — aps only tracks what it installs.
- Supporting non-Linux platforms.
- Automatic conflict resolution between distro-specific package names (the user
  still maintains `pkgmap`).
- Real-time filesystem watching or daemon-based synchronization.

## 3. User personas

### 3.1 Key user types

- **Power user / tinkerer**: Maintains multiple Arch and Fedora machines,
  frequently installs/removes packages, wants a reproducible setup.
- **Fresh installer**: Reinstalls their OS periodically, wants a single command
  to restore their environment.
- **Contributor**: Maintains the aps project, cares about code simplicity,
  testability, and minimal dependencies.

### 3.2 Basic persona details

- **Kenji (power user)**: Runs CachyOS on his desktop and Fedora on his laptop.
  Uses aps daily to install new tools. Frustrated that ad-hoc installs are not
  remembered in the config file.
- **Lina (fresh installer)**: Reinstalls Fedora every 6 months. Keeps her
  `packages.ini` in a dotfiles repo. Wants `aps install @core @dev @apps` to
  give her the same environment every time.
- **Dev (contributor)**: Wants the architecture to be simple enough to add new
  features without touching complex parsing code.

### 3.3 Role-based access

- **Regular user**: All aps commands, config editing.
- **Root/sudo**: Package installation and removal (delegated to system package
  manager).

## 4. Functional requirements

This section presents **three architecture options**, each with trade-offs.
The final choice should be made based on the priorities of simplicity,
reliability, and feature completeness.

### 4.1 Architecture options overview

| Aspect | Option A: TOML + JSONL (Recommended) | Option B: Single TOML | Option C: TOML + SQLite |
|---|---|---|---|
| **Config format** | TOML (desired state) | TOML (combined) | TOML (desired state) |
| **Tracking store** | JSONL (installed state) | Embedded in TOML | SQLite database |
| **Sync model** | Explicit `aps save` / `--save` flag | Automatic (single file) | Explicit `aps save` / `--save` flag |
| **Complexity** | Low | Lowest initially, grows with features | Medium |
| **New dependencies** | None (tomllib is stdlib 3.11+, tomli-w for writing) | None (tomllib + tomli-w) | sqlite3 (stdlib) + tomli-w |
| **Portability** | Copy 2 TOML files | Copy 1 TOML file | Copy TOML file + SQLite file |
| **Comment preservation** | With tomli-w or tomlkit | Harder (metadata mixed in) | TOML only for config |

### 4.2 Option A: TOML config + JSONL tracking (recommended)

**Summary**: Replace `packages.ini` and `pkgmap.ini` with TOML equivalents
while keeping `metadata.jsonl` as the tracking database. Add commands to
synchronize between the two.

**Why TOML over INI?**

- Native Python support via `tomllib` (stdlib since 3.11, read-only) — no
  preprocessing hacks for bare lines needed.
- Supports arrays natively — `packages = ["curl", "wget", "git"]` — no
  comma-splitting parser needed.
- Supports inline comments.
- Supports nested tables — cleaner organization of categories and mappings.
- Widely adopted in the Python ecosystem (`pyproject.toml`, `ruff.toml`).
- Write support via `tomli-w` (lightweight, ~3KB) or `tomlkit` (preserves
  comments and formatting).

(Priority: High)

**4.2.1 New config format: `packages.toml`**

```toml
# packages.toml — desired package state for aps
# Categories are TOML tables. Packages are arrays.

[core]
packages = [
    "curl",
    "wget",
    "ufw",
    "gnome-keyring",
    "xclip",
]

[apps]
packages = [
    "chromium",
    "seahorse",
    "xournalpp",
    "keepassxc",
    "borgbackup",
    "syncthing",
    "syncthingtray",
    "obsidian",
    "signal",
    "neovim",
    "vim",
    "alacritty",
]

[dev]
packages = [
    "tmux",
    "trash-cli",
    "lazygit",
    "gh",
    "starship",
    "zoxide",
    "eza",
    "fd-find",
    "bat",
    "fzf",
    "ruff",
    "shfmt",
    "shellcheck",
    "zsh",
]

[laptop]
packages = [
    "brightnessctl",
    "powertop",
    "thinkfan",
    "acpi",
    "tlp",
]
```

**Advantages over current INI**:

- No need for `_preprocess_config_file()` hack to convert bare lines to
  `_pkg_N=value` keys.
- Native list type — no comma-splitting ambiguity.
- Clear, self-documenting structure.
- Inline comments and multi-line arrays are first-class features.

**4.2.2 New mapping format: `pkgmap.toml`**

```toml
# pkgmap.toml — distro-specific package name mappings

[fedora]
shellcheck = "ShellCheck"
fuse2 = "fuse"
# Flatpak packages use "flatpak:<remote>:<app-id>" format
syncthingtray = "flatpak:flathub:io.github.martchus.syncthingtray"
signal = "flatpak:flathub:org.signal.Signal"
obsidian = "flatpak:flathub:md.obsidian.Obsidian"
# COPR packages use "COPR:<user/repo>" or "COPR:<user/repo>:<pkg>" format
qtile-extras = "COPR:frostyx/qtile"
starship = "COPR:atim/starship"
lazygit = "COPR:dejan/lazygit"

[arch]
python3-dbus-fast = "python-dbus-fast"
gh = "github-cli"
fd-find = "fd"
pip = "python-pip"
signal = "signal-desktop"
borgbackup = "borg"
# AUR packages use "AUR:<pkg>" format
syncthingtray = "AUR:syncthingtray-qt6"
thinkfan = "AUR:thinkfan"
lazygit = "lazygit"
```

**Advantages over current INI**:

- Sections named `[fedora]` / `[arch]` instead of `[pkgmap.fedora]` /
  `[pkgmap.arch]` — simpler.
- Standard TOML key-value pairs, no custom parsing needed.
- Prefix format (`COPR:`, `AUR:`, `flatpak:`) stays the same — proven and
  familiar.

**4.2.3 JSONL tracking (unchanged)**

`metadata.jsonl` continues to work as-is. The `PackageRecord` dataclass and
`PackageTracker` class require no changes. JSONL remains ideal for:

- Append-only writes (fast installs).
- Line-by-line parsing (memory efficient).
- Human-readable.
- Fast serialization with `orjson`.

**4.2.4 New CLI commands and flags**

| Command | Description |
|---|---|
| `aps install X --save` | Install package AND add to `packages.toml` under a specified or default category |
| `aps install X` | Install and track in JSONL only (current behavior) |
| `aps remove X --save` | Remove package AND delete from `packages.toml` |
| `aps remove X` | Remove and untrack from JSONL only (current behavior) |
| `aps save [--category CAT]` | Write all tracked-but-not-in-config packages to `packages.toml` |
| `aps diff` | Show what's tracked vs. what's in config (drift detection) |
| `aps export [--output FILE]` | Export `packages.toml` + `pkgmap.toml` as a portable bundle |
| `aps import FILE [--merge]` | Import a config bundle, optionally merging with current config |

**4.2.5 Sync architecture**

```
┌─────────────────────┐       ┌──────────────────────┐
│   packages.toml     │       │   metadata.jsonl     │
│   (desired state)   │       │   (installed state)   │
│                     │       │                       │
│  What SHOULD be     │       │  What IS installed    │
│  installed on any   │◄─────►│  on THIS machine      │
│  fresh setup        │ sync  │  right now            │
└─────────────────────┘       └──────────────────────┘
        │                              │
        │  aps install @core           │  aps install X --save
        │  (reads desired list)        │  (writes to both)
        │                              │
        ▼                              ▼
┌─────────────────────┐       ┌──────────────────────┐
│   pkgmap.toml       │       │  System package mgr  │
│   (name mapping)    │       │  (dnf/pacman/flatpak)│
└─────────────────────┘       └──────────────────────┘

Key flows:
  aps install @core      → Read packages.toml → Map via pkgmap.toml → Install → Track in JSONL
  aps install X --save   → Install → Track in JSONL → Write to packages.toml
  aps install X          → Install → Track in JSONL (no config change)
  aps save               → Read JSONL → Write untracked packages to packages.toml
  aps diff               → Compare packages.toml vs JSONL → Show drift
  aps remove X --save    → Remove → Untrack from JSONL → Remove from packages.toml
  aps export             → Bundle packages.toml + pkgmap.toml → Output file
  aps import             → Read bundle → Merge/replace into local config
```

**4.2.6 TOML read/write strategy**

- **Reading**: Use `tomllib` (stdlib 3.11+) — zero dependencies, fast.
- **Writing**: Use `tomlkit` library — preserves comments, formatting, and
  ordering when modifying existing files. This is critical because users add
  comments to their config files (e.g., `# download tools`, `# backup tools`).
- **Alternative write**: `tomli-w` is lighter but does NOT preserve comments.
  Since auto-saving to config is a key feature, preserving user comments is
  important, making `tomlkit` the better choice.

**4.2.7 Migration path from INI to TOML**

- Add `aps migrate` command that reads existing INI files and writes equivalent
  TOML files.
- Keep INI support in a legacy parser for one major version (deprecation period).
- Auto-detect config format: if `packages.toml` exists, use it; otherwise fall
  back to `packages.ini` with a deprecation warning.

### 4.3 Option B: Single TOML file (DENIED)

**Summary**: Merge packages, mappings, and tracking into a single
`aps-config.toml`. The file is both the desired state and the tracking
database.

```toml
# aps-config.toml

[settings]
# variables previously in variables.ini
python_version = "3.12"

[packages.core]
list = ["curl", "wget", "ufw", "gnome-keyring"]

[packages.dev]
list = ["tmux", "lazygit", "starship", "ruff"]

[pkgmap.fedora]
lazygit = "COPR:dejan/lazygit"
signal = "flatpak:flathub:org.signal.Signal"

[pkgmap.arch]
gh = "github-cli"
signal = "signal-desktop"

# Tracking section — auto-managed by aps, DO NOT EDIT
[tracked]
curl = { source = "official", installed_at = "2026-02-28 10:00:00 +0300" }
lazygit = { source = "COPR:dejan/lazygit", mapped = "lazygit", installed_at = "2026-02-28 10:01:00 +0300" }
```

**Pros**:

- Single file to manage, backup, and version-control.
- No drift by definition — config and tracking are the same file.
- Simplest mental model.

**Cons**:

- Mixing human-edited config with machine-written tracking data in one file is
  fragile — any write operation risks corrupting user comments/formatting.
- The `[tracked]` section would grow large and pollute the config.
- Harder to share the "desired state" separately from machine-specific tracking.
- TOML writing libraries may reformat the entire file on each save.
- Portability suffers: you'd need to strip `[tracked]` before sharing the file.

**Verdict**: Not recommended. The simplicity gain is offset by the fragility of
mixing human-editable config with auto-generated tracking data.

### 4.4 Option C: TOML config + SQLite tracking

**Summary**: Use TOML for the desired state (same as Option A) but replace JSONL
with SQLite for tracking.

```sql
CREATE TABLE packages (
    name TEXT PRIMARY KEY,
    mapped_name TEXT,
    source TEXT DEFAULT 'official',
    category TEXT,
    installed_at TEXT
);
```

**Pros**:

- SQL queries for reporting (e.g., `SELECT * FROM packages WHERE source LIKE 'COPR:%'`).
- Atomic writes — no partial-write corruption risk.
- Built into Python stdlib (`sqlite3`).
- Better performance for large datasets.

**Cons**:

- Binary file — not human-readable, harder to debug.
- `metadata.jsonl` is currently ~50-200 entries at most — SQL is overkill.
- JSONL is already fast enough with `orjson` for this scale.
- Adds complexity without meaningful benefit at current scale.
- Harder to manually inspect or edit tracking data.

**Verdict**: Viable but over-engineered for the current use case. JSONL handles
the scale (< 500 packages) perfectly. Consider SQLite only if aps grows to
manage thousands of packages or needs complex query capabilities.

### 4.5 Recommendation summary

| Criteria | Option A (TOML + JSONL) | Option B (Single TOML) | Option C (TOML + SQLite) |
|---|---|---|---|
| Simplicity | ★★★★☆ | ★★★★★ (initially) | ★★★☆☆ |
| Reliability | ★★★★★ | ★★★☆☆ | ★★★★★ |
| Portability | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| Comment preservation | ★★★★★ (tomlkit) | ★★☆☆☆ | ★★★★★ (TOML only) |
| Human readability | ★★★★★ | ★★★★☆ | ★★★☆☆ (SQLite is binary) |
| Scale for aps needs | ★★★★★ | ★★★★☆ | ★★★★★ (overkill) |
| Migration effort | ★★★★☆ | ★★★★★ | ★★★☆☆ |

**Recommendation: Option A (TOML + JSONL)** — it preserves the proven
separation of concerns, upgrades the config format with zero-dependency reading
(`tomllib`), keeps JSONL for lightweight tracking, and adds explicit sync
commands that the user controls.

## 5. User experience

### 5.1 Entry points and first-time user flow

- First run: `aps` checks for config files. If `packages.toml` doesn't exist
  but `packages.ini` does, prompt user to run `aps migrate`. If neither exists,
  copy defaults from `src/aps/configs/default_aps_configs/`.
- Default config files are now `packages.toml`, `pkgmap.toml`, `variables.ini`
  (variables.ini stays INI — it's simple key-value pairs with no need for
  arrays).

### 5.2 Core experience

- **Category install** (`aps install @core`): Reads `packages.toml` → maps
  via `pkgmap.toml` → installs via system PM → tracks in JSONL. Same flow as
  today but with cleaner config parsing.

- **Ad-hoc install with save** (`aps install neovim --save`): Installs the
  package → tracks in JSONL → appends `"neovim"` to `packages.toml` under the
  specified category (prompted or defaulted to `[uncategorized]`).

- **Ad-hoc install without save** (`aps install neovim`): Installs and tracks
  in JSONL only. Identical to current behavior.

- **Drift detection** (`aps diff`): Compares `packages.toml` entries against
  JSONL records. Outputs three groups:
  1. **In config, not installed** — packages declared but not yet installed.
  2. **Installed, not in config** — ad-hoc installs not saved to config.
  3. **In sync** — packages that are both declared and installed.

- **Bulk save** (`aps save`): Takes all "installed, not in config" packages and
  writes them to `packages.toml`. Prompts user for category assignment or uses
  `[uncategorized]`.

### 5.3 Advanced features and edge cases

- **`aps save --category dev`**: Save all unsaved tracked packages to a specific
  category.
- **`aps save --interactive`**: Prompt for each package's category assignment
  one by one.
- **`aps export --output ~/dotfiles/aps-config.tar`**: Bundle `packages.toml`
    - `pkgmap.toml` into a portable archive.
- **`aps import ~/dotfiles/aps-config.tar --merge`**: Merge imported config with
  local config (union of packages). Without `--merge`, replace entirely.
- **Removing a package that's in config** (`aps remove X --save`): Removes from
  system → removes from JSONL → removes from `packages.toml` while preserving
  all other comments and formatting (via `tomlkit`).
- **Edge case — package in config but not in JSONL**: This means it was never
  installed via aps. `aps diff` flags it. `aps install @category` installs it.
- **Edge case — package in JSONL but not in config**: This means it was
  installed ad-hoc. `aps diff` flags it. `aps save` can persist it.

### 5.4 UI/UX highlights

- `aps diff` output uses color-coded terminal output:
    - Green: in sync.
    - Yellow: installed but not in config.
    - Red: in config but not installed.
- `aps save` shows a preview of changes before writing.
- `aps migrate` shows a before/after diff before converting INI → TOML.

## 6. Narrative

Kenji just installed `taskwarrior` on his CachyOS desktop using
`aps install taskwarrior --save`. The package was installed via pacman, tracked
in his JSONL database, and automatically added to `packages.toml` under
`[apps]`. Later, when he sets up his new Fedora laptop, he copies his dotfiles
repo containing `packages.toml` and `pkgmap.toml`, runs `aps install @apps`,
and `taskwarrior` is installed alongside everything else — no manual config
editing required.

A week later, Kenji decides he no longer needs `xournalpp`. He runs
`aps remove xournalpp --save`. The package is uninstalled, removed from JSONL
tracking, and deleted from `packages.toml`. His config stays clean and
accurate.

Before his next OS reinstall, he runs `aps diff` and notices three packages
he installed ad-hoc but forgot to save. He runs `aps save --interactive`,
assigns each to a category, and his config is up to date.

## 7. Success metrics

### 7.1 User-centric metrics

- Zero manual `packages.toml` edits needed for ad-hoc installs when using
  `--save`.
- `aps diff` accurately reports drift with zero false positives.
- Fresh install time (config copy + `aps install @core @dev @apps`) takes
  < 30 seconds of user interaction (excluding download time).

### 7.2 Business metrics

- Reduction in "how do I save my packages" support questions/issues.
- Config portability: users can share TOML configs across machines without
  post-editing.

### 7.3 Technical metrics

- TOML config parsing is at least as fast as current INI parsing (no
  preprocessing overhead).
- JSONL write latency stays under 5ms per package record.
- `aps diff` completes in < 200ms for 500 packages.
- Zero new runtime dependencies for reading (tomllib is stdlib). Only `tomlkit`
  added for writing.
- All new commands have > 90% test coverage.

## 8. Technical considerations

### 8.1 Integration points

- **tomllib** (stdlib 3.11+): Read-only TOML parsing — already available in
  Python 3.12+ (aps requirement).
- **tomlkit**: TOML writing that preserves comments, formatting, and ordering.
  Needed for `--save`, `aps save`, and `aps remove --save` operations. Actively
  maintained, used by Poetry.
- **orjson**: Already a dependency — continues to handle JSONL serialization.
- **Package managers**: dnf, pacman, paru/yay, flatpak — no changes to the
  interface.

### 8.2 Data storage and privacy

- All data stays local in `~/.config/auto-penguin-setup/`.
- No network calls for config management — only for package installation
  (delegated to system PM).
- Export files contain only package names and mappings — no sensitive data.

### 8.3 Scalability and performance

- TOML parsing with `tomllib` is C-accelerated — handles configs with hundreds
  of packages in < 1ms.
- JSONL with `orjson` handles thousands of records efficiently.
- The bottleneck is always the system package manager, not aps.

### 8.4 Potential challenges

- **Comment preservation in TOML writes**: `tomlkit` handles this but adds a
  dependency (~50KB). If the dependency is unacceptable, `tomli-w` can be used
  but comments will be lost on write. This is a hard trade-off.
- **Migration from INI**: Users with heavily customized `packages.ini` files
  need a reliable migration path. The `aps migrate` command must handle edge
  cases (inline comments, mixed comma/newline formats).
- **Category assignment on `--save`**: When saving an ad-hoc package, aps needs
  to know which category to put it in. Options:
    - Default to `[uncategorized]` and let user reorganize later.
    - Accept `--category` flag: `aps install X --save --category dev`.
    - Interactive prompt (slow for bulk operations).
- **Concurrent writes**: If two aps instances run simultaneously, JSONL and TOML
  writes could conflict. The planned singleton lock (fcntl.flock from the todo)
  solves this.
- **pkgmap.toml backwards compatibility**: The prefix format (`COPR:`, `AUR:`,
  `flatpak:`) stays identical — only the file format changes from INI to TOML.
  The `PackageMapper` class needs minimal changes.

## 9. Milestones and sequencing

### 9.1 Project estimate

- Medium: 4-6 weeks of development (part-time).

### 9.2 Team size and composition

- 1 developer (solo project) with AI-assisted development.

### 9.3 Suggested phases

- **Phase 1: TOML config parser** (~1 week)
    - Create `TOMLConfigParser` that reads `packages.toml` / `pkgmap.toml`.
    - Add `tomlkit` dependency.
    - Write comprehensive tests for the new parser.
    - Key deliverable: aps can read TOML configs.

- **Phase 2: Migration command** (~1 week)
    - Implement `aps migrate` to convert INI → TOML.
    - Add auto-detection logic (TOML preferred, INI fallback with deprecation
    warning).
    - Generate default TOML config files in `src/aps/configs/default_aps_configs/`.
    - Key deliverable: existing users can migrate seamlessly.

- **Phase 3: `--save` flag and TOML writing** (~1 week)
    - Implement `--save` flag on `aps install` and `aps remove`.
    - Use `tomlkit` for comment-preserving writes to `packages.toml`.
    - Add `--category` support.
    - Key deliverable: ad-hoc installs can be persisted.

- **Phase 4: `aps diff` and `aps save`** (~1 week)
    - Implement drift detection command.
    - Implement bulk save command.
    - Add interactive category assignment.
    - Key deliverable: users can detect and fix drift.

- **Phase 5: Export/import** (~0.5 week)
    - Implement `aps export` and `aps import --merge`.
    - Key deliverable: configs are portable across machines.

- **Phase 6: Cleanup and deprecation** (~0.5 week)
    - Remove INI preprocessing hacks from `APSConfigParser`.
    - Update all documentation and default configs.
    - Key deliverable: clean codebase with TOML as the sole format.

## 10. User stories

### 10.1 Install package with auto-save to config

- **ID**: GH-001
- **Description**: As a power user, I want to install a package and have it
  automatically saved to my `packages.toml` config, so that my desired state
  stays up to date without manual file editing.
- **Acceptance criteria**:
    - Running `aps install neovim --save` installs the package via the system
    package manager.
    - The package is tracked in `metadata.jsonl`.
    - The package is appended to `packages.toml` under the specified category
    (default: `[uncategorized]`).
    - Running `aps install neovim --save --category dev` places it under `[dev]`.
    - If the package already exists in `packages.toml`, no duplicate is added.
    - User comments and formatting in `packages.toml` are preserved.

### 10.2 Remove package with auto-save

- **ID**: GH-002
- **Description**: As a power user, I want to remove a package and have it
  automatically removed from my config, so that my desired state reflects what
  I actually want installed.
- **Acceptance criteria**:
    - Running `aps remove xournalpp --save` removes the package via the system
    package manager.
    - The package is removed from `metadata.jsonl`.
    - The package is removed from `packages.toml` (regardless of which category
    it was in).
    - User comments and formatting in `packages.toml` are preserved.
    - If the package is not in `packages.toml`, only JSONL removal occurs (no
    error).

### 10.3 Detect configuration drift

- **ID**: GH-003
- **Description**: As a user preparing for a fresh install, I want to see what
  packages are installed but not saved in my config, so that I can save them
  before wiping my system.
- **Acceptance criteria**:
    - Running `aps diff` shows three groups: "in config not installed",
    "installed not in config", and "in sync".
    - Output is color-coded (green/yellow/red).
    - Exit code is 0 when fully in sync, 1 when drift exists.
    - Output supports `--json` flag for machine-readable output.

### 10.4 Bulk save tracked packages to config

- **ID**: GH-004
- **Description**: As a user who has many ad-hoc installs, I want to save all
  untracked packages to my config at once, so that I don't lose my setup on
  reinstall.
- **Acceptance criteria**:
    - Running `aps save` shows a preview of packages to be added.
    - User is prompted to confirm before writing.
    - `aps save --category dev` assigns all packages to `[dev]`.
    - `aps save --interactive` prompts for each package's category.
    - Packages already in `packages.toml` are skipped.

### 10.5 Export configuration for portability

- **ID**: GH-005
- **Description**: As a user with multiple machines, I want to export my
  package configuration to a portable file, so that I can apply the same
  setup on a different machine.
- **Acceptance criteria**:
    - Running `aps export` outputs `packages.toml` + `pkgmap.toml` to stdout
    or a specified file.
    - `aps export --output ~/backup.tar` creates a tar archive.
    - Export includes only config files, not tracking data.

### 10.6 Import configuration from another machine

- **ID**: GH-006
- **Description**: As a user setting up a new machine, I want to import a
  package configuration from my other machine, so that I can quickly replicate
  my environment.
- **Acceptance criteria**:
    - Running `aps import config.tar` replaces local config with imported config.
    - `aps import config.tar --merge` performs a union merge (adds new packages
    from import without removing existing local packages).
    - Merge conflicts (same package, different categories) are reported to the
    user.

### 10.7 Migrate from INI to TOML

- **ID**: GH-007
- **Description**: As an existing aps user, I want to migrate my INI config
  files to TOML format, so that I benefit from the new architecture.
- **Acceptance criteria**:
    - Running `aps migrate` reads `packages.ini` and `pkgmap.ini`.
    - Outputs equivalent `packages.toml` and `pkgmap.toml`.
    - Shows a diff/preview before writing.
    - Original INI files are backed up as `*.ini.backup`.
    - Comments from INI files are preserved as TOML comments where possible.
    - If TOML files already exist, warns and requires `--force` to overwrite.

### 10.8 Read packages from TOML config

- **ID**: GH-008
- **Description**: As a developer, I want aps to parse TOML config files
  natively, so that the codebase is simpler and doesn't need INI preprocessing
  hacks.
- **Acceptance criteria**:
    - `APSConfigParser` (or a new `TOMLConfigParser`) reads `packages.toml` using
    `tomllib`.
    - All existing functionality (category listing, package listing, section
    iteration) works identically with TOML input.
    - The `_preprocess_config_file()` method is no longer needed for TOML paths.
    - Unit tests cover all package list formats (arrays, inline arrays).

### 10.9 Auto-detect config format

- **ID**: GH-009
- **Description**: As an existing user who hasn't migrated yet, I want aps to
  automatically detect my config format, so that the tool keeps working during
  the transition period.
- **Acceptance criteria**:
    - If `packages.toml` exists, use TOML parser.
    - If only `packages.ini` exists, use INI parser with a deprecation warning
    (logged once per session).
    - Deprecation warning includes migration instructions.
    - After 1 major version, INI support is removed.

### 10.10 Preserve comments when writing TOML

- **ID**: GH-010
- **Description**: As a user who annotates their config with comments, I want
  aps to preserve my comments when it modifies `packages.toml`, so that my
  notes and organization are not lost.
- **Acceptance criteria**:
    - `aps install X --save` does not remove or reorder existing comments.
    - `aps remove X --save` does not remove or reorder existing comments.
    - `aps save` does not remove or reorder existing comments.
    - New packages are appended at the end of the target category's array.
    - Tests verify comment preservation using `tomlkit` round-trip parsing.
