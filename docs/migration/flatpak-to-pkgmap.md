# Migration Guide: Flatpak Configuration Changes (v0.6.0+)

## Overview

As of version 0.6.0, Auto Penguin Setup (APS) has unified package resolution across all sources (official repos, AUR, COPR, and Flatpak). Previously, Flatpak packages were managed through a special `[flatpak]` category in `packages.ini`. This approach created inconsistencies and made it difficult to prefer different sources on different distributions.

**The change:** Flatpak is now treated as just another provider, configured through `pkgmap.ini`—the same mechanism used for AUR and COPR packages. This enables cleaner configuration, better distro-specific preferences, and a single source of truth for package resolution.

**Why this matters:**

- On Arch-based systems, you can now install Signal from the official repository instead of being forced to use Flatpak.
- Configuration is more consistent: all source selection happens in `pkgmap.ini`.
- The same category list (e.g., `[apps]`) can be mapped to different sources per distribution.

**Reference:** See [ADR-0001: Flatpak as a pkgmap.ini Provider](../adr/adr-0001-flatpak-pkgmap-provider.md)

---

## What Changed

### The Old Way (Deprecated)

In APS versions prior to 0.6.0, you'd list Flatpak apps in a dedicated `[flatpak]` section:

**`packages.ini` (old):**

```ini
[flatpak]
org.signal.Signal
com.spotify.Client
md.obsidian.Obsidian
```

This forced all listed packages to install via Flatpak, regardless of distribution or user preference.

### The New Way (Current)

Now, Flatpak apps are listed in regular categories (e.g., `[apps]`) and their source is determined by `pkgmap.ini` mappings:

**`packages.ini` (new):**

```ini
[apps]
signal
spotify
obsidian
```

**`pkgmap.ini` (new):**

```ini
[pkgmap.arch]
signal=signal-desktop
spotify=spotify
obsidian=AUR:obsidian

[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
spotify=flatpak:flathub:com.spotify.Client
obsidian=flatpak:flathub:md.obsidian.Obsidian
```

This approach gives you **per-distro control**: Arch users can choose official/AUR, while Fedora users can prefer Flatpak.

---

## Migration Steps

### Step 1: Understand Your Current Configuration

Check if you have a `[flatpak]` section in your `~/.config/auto-penguin-setup/packages.ini`:

```bash
grep -A 20 "^\[flatpak\]" ~/.config/auto-penguin-setup/packages.ini
```

If nothing is printed, you don't use `[flatpak]` and can skip this migration.

### Step 2: Choose a Regular Category

Move your Flatpak apps to an existing category like `[apps]`, or create a custom one (e.g., `[media-apps]`, `[productivity]`):

**Example:**

```ini
[apps]
signal
spotify
obsidian
# ... other apps
```

### Step 3: Define Generic Package Names

For each app, decide on a neutral generic name. You'll use this name across all distributions:

| Generic Name | Arch Source | Fedora Source |
|---|---|---|
| `signal` | Official repo: `signal-desktop` | Flatpak: `flatpak:flathub:org.signal.Signal` |
| `spotify` | Official repo: `spotify` | Flatpak: `flatpak:flathub:com.spotify.Client` |
| `obsidian` | AUR: `AUR:obsidian` | Flatpak: `flatpak:flathub:md.obsidian.Obsidian` |

### Step 4: Add Mappings to `pkgmap.ini`

Add mappings under `[pkgmap.arch]` and `[pkgmap.fedora]` (or your other distros):

**`pkgmap.ini`:**

```ini
[pkgmap.arch]
signal=signal-desktop
spotify=spotify
obsidian=AUR:obsidian

[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
spotify=flatpak:flathub:com.spotify.Client
obsidian=flatpak:flathub:md.obsidian.Obsidian
```

### Step 5: Remove or Rename `[flatpak]` Section

Delete the old `[flatpak]` section from your `packages.ini`:

```bash
# Before
[flatpak]
org.signal.Signal
com.spotify.Client
md.obsidian.Obsidian

# After
# (section deleted)
```

### Step 6: Test Your Configuration

Run APS to verify it works:

```bash
# List all packages (should show your apps under [apps])
uv run aps list @apps

# Dry-run install to see what would be installed
uv run aps install @apps --noconfirm --dry-run

# If everything looks good, install (with confirmation disabled for batch installs)
uv run aps install @apps
```

---

## Common Scenarios

### Scenario 1: Fedora User Who Wants Flatpak Apps

**Your preference:** "I prefer Flatpak for desktop apps—cleaner sandboxing."

**Configuration:**

**`packages.ini`:**

```ini
[apps]
signal
spotify
obsidian
vlc
```

**`pkgmap.ini`:**

```ini
[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
spotify=flatpak:flathub:com.spotify.Client
obsidian=flatpak:flathub:md.obsidian.Obsidian
vlc=flatpak:flathub:org.videolan.VLC
```

**Result:** All apps install via Flatpak from Flathub.

---

### Scenario 2: Arch User Who Mixes Official, AUR, and Flatpak

**Your preference:** "I prefer official/AUR for stability, but some apps are only available on Flatpak."

**Configuration:**

**`packages.ini`:**

```ini
[apps]
signal
spotify
obsidian
vlc
discord
```

**`pkgmap.ini`:**

```ini
[pkgmap.arch]
signal=signal-desktop
spotify=spotify
obsidian=AUR:obsidian
vlc=vlc
discord=flatpak:flathub:com.discordapp.Discord
```

**Result:**

- `signal`, `spotify`, `vlc` → Official Arch repos
- `obsidian` → AUR (via paru/yay)
- `discord` → Flatpak from Flathub (because it's not in official repos)

---

### Scenario 3: Multi-Distro User With Distro-Specific Preferences

**Your preference:** "I use both Fedora and Arch. On Fedora, I like Flatpak for apps. On Arch, I prefer official/AUR."

**Single config file shared across machines:**

**`packages.ini` (same on both distros):**

```ini
[core]
curl
git
tmux

[apps]
signal
spotify
obsidian
```

**`pkgmap.ini` (update based on each distro):**

**On Fedora:**

```ini
[pkgmap.fedora]
curl=curl
git=git
tmux=tmux
signal=flatpak:flathub:org.signal.Signal
spotify=flatpak:flathub:com.spotify.Client
obsidian=flatpak:flathub:md.obsidian.Obsidian
```

**On Arch:**

```ini
[pkgmap.arch]
curl=curl
git=git
tmux=tmux
signal=signal-desktop
spotify=spotify
obsidian=AUR:obsidian
```

**Result:** Same `packages.ini` works on both distros; each distro installs from its preferred source.

---

### Scenario 4: Finding the Correct Flatpak App ID

If you're not sure of the exact Flatpak app ID, use:

```bash
# Search Flathub
flatpak search signal

# Example output:
# org.signal.Signal             Signal                     Private messaging app
```

Then use these IDs in your mapping:

```ini
[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
```

---

## Flatpak Syntax in `pkgmap.ini`

The Flatpak provider syntax is:

```
flatpak:<remote>:<app-id>
```

| Component | Meaning | Example |
|---|---|---|
| `flatpak` | Provider type | Always `flatpak` |
| `<remote>` | Flatpak remote name | `flathub` (most common), `fedora` (for system Flatpaks) |
| `<app-id>` | Full Flatpak application ID | `org.signal.Signal`, `com.spotify.Client` |

**Examples:**

```ini
[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
obsidian=flatpak:flathub:md.obsidian.Obsidian
firefox=flatpak:flathub:org.mozilla.firefox
```

---

## Troubleshooting

### Issue: "What if I have no mapping for a package?"

If a package has no mapping in `pkgmap.ini`, APS uses the generic name as-is. This works for packages with identical names across distros:

```ini
# In packages.ini
[apps]
curl

# Without a mapping in pkgmap.ini, APS tries to install 'curl' directly
# This works because 'curl' exists in both Arch and Fedora repos
```

For Flatpak, however, you **must** provide a mapping—the generic name won't work:

```ini
# ❌ WRONG: Will fail
# packages.ini
[apps]
signal

# pkgmap.ini
# (no mapping for 'signal')
# → APS tries to install package named 'signal' → fails (doesn't exist)

# ✅ CORRECT: Provide mapping
# pkgmap.ini
[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
```

### Issue: "Old [flatpak] section detected"

If you still have a `[flatpak]` section in `packages.ini`, APS (v0.6.0+) will fail with an error:

```
Error: Legacy [flatpak] section found in packages.ini.
This section is no longer supported as of version 0.6.0.
Please migrate your configuration using:
  https://docs.auto-penguin-setup.dev/migration/flatpak-to-pkgmap.md
```

**Solution:** Delete the `[flatpak]` section and move your apps to regular categories with pkgmap.ini mappings (see Step 5 above).

### Issue: "Can I keep using @flatpak syntax?"

No. The `@flatpak` category syntax is **removed** in v0.6.0. Commands like:

```bash
# ❌ No longer works (v0.6.0+)
uv run aps install @flatpak
```

Instead, use your new category:

```bash
# ✅ Install from your [apps] category
uv run aps install @apps

# Which installs from each distro's preferred source per pkgmap.ini
```

### Issue: "How do I check what will be installed?"

Use the `--noconfirm` flag with a dry-run or the `list` command:

```bash
# See all packages in [apps]
uv run aps list @apps

# Dry-run install (shows what would happen without making changes)
uv run aps install @apps --dry-run
```

### Issue: "Can I uninstall Flatpak apps?"

Yes. As of v0.6.0, `aps remove` tracks the original source and removes Flatpak apps correctly:

```bash
uv run aps remove signal
# Removes whether 'signal' was installed as:
# - A system package
# - An AUR package
# - A Flatpak
```

---

## Timeline and Support

| Version | Status | Support |
|---|---|---|
| 0.5.0 and earlier | **Legacy** | `[flatpak]` section supported; migration recommended |
| 0.6.0+ | **Current** | `[flatpak]` section must be migrated; will error if found |

---

## Examples: Before and After

### Example 1: Multi-App Setup

**BEFORE (v0.5.0):**

**`~/.config/auto-penguin-setup/packages.ini`:**

```ini
[core]
curl
wget
git

[flatpak]
org.signal.Signal
com.spotify.Client
md.obsidian.Obsidian
org.mozilla.firefox
```

**AFTER (v0.6.0+):**

**`~/.config/auto-penguin-setup/packages.ini`:**

```ini
[core]
curl
wget
git

[apps]
signal
spotify
obsidian
firefox
```

**`~/.config/auto-penguin-setup/pkgmap.ini`:**

```ini
[pkgmap.arch]
signal=signal-desktop
spotify=spotify
obsidian=AUR:obsidian
firefox=firefox

[pkgmap.fedora]
signal=flatpak:flathub:org.signal.Signal
spotify=flatpak:flathub:com.spotify.Client
obsidian=flatpak:flathub:md.obsidian.Obsidian
firefox=flatpak:flathub:org.mozilla.firefox
```

---

## References

- [ADR-0001: Flatpak as a pkgmap.ini Provider](../adr/adr-0001-flatpak-pkgmap-provider.md)
- [Configuration Docs: wiki.md](../wiki.md)
- [Package Mapping Reference](../wiki.md#package-mapping-explained)

---

## Questions?

If you encounter issues during migration, check:

1. Exact Flatpak app IDs: `flatpak search <app-name>`
2. Correct mapping syntax: `flatpak:<remote>:<app-id>`
3. No remaining `[flatpak]` sections in `packages.ini`
4. Peruse actual configuration in `~/.config/auto-penguin-setup/`
