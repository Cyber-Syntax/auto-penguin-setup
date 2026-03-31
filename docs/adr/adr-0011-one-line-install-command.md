---
title: "ADR-0011: One-Line Remote Install Command via setup.sh"
status: "Proposed"
date: "2026-02-28"
authors: "dev"
tags: ["architecture", "decision", "installation", "UX", "setup"]
supersedes: ""
superseded_by: ""
---

## Status

**Proposed**

## Context

APS currently requires a multi-step installation process: clone the repository,
ensure `uv` is installed, then run `./setup.sh install`. This friction reduces
adoption and makes it harder to recommend APS in documentation, blog posts, or
quick-start guides.

The existing `setup.sh` already handles:

- UV detection and installation (via system package manager or Astral's script).
- APS CLI installation via `uv tool install git+https://github.com/...`.
- Shell autocomplete setup (bash/zsh).

A one-line install command would allow users to bootstrap APS directly:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Cyber-Syntax/auto-penguin-setup/main/setup.sh)
```

However, the current `setup.sh` has a design assumption that it runs from the
repository root (it references `./scripts/autocomplete.bash` via a relative
path). This needs to be addressed for the remote-execution scenario.

- **CTX-001**: **Relative path dependency** — `setup_autocomplete()` calls
  `./scripts/autocomplete.bash`. When `setup.sh` is piped from curl, the
  working directory is the user's current directory, not the repository root.
  The autocomplete step will fail with "script not found".
- **CTX-002**: **Security expectations** — Piping curl output to bash is a
  well-understood pattern (used by Rust/rustup, Homebrew, nvm, uv itself), but
  it requires the script to be safe for execution in any working directory and
  to not assume local files exist.
- **CTX-003**: **Branch targeting** — The URL references the `main` branch,
  which is the stable/default branch. Users installing from `dev` or a tag
  should be able to override this.
- **CTX-004**: **Autocomplete gap** — `uv tool install` places the `aps` binary
  in `~/.local/bin/` but does not clone the repository, so autocomplete scripts
  in `autocomplete/` are not available locally. The install script needs an
  alternative way to deploy completions.

## Decision

Modify `setup.sh` to support remote (piped) execution as a one-line install
command, and document the canonical install invocation:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Cyber-Syntax/auto-penguin-setup/main/setup.sh)
```

### Implementation approach

1. **Detect remote execution**: Check whether the script is running from a
   local repository checkout or was piped/process-substituted. This can be
   detected by checking if `$0` is a real file path or `/dev/fd/*` / `bash`:

   ```bash
   is_remote_install() {
     [[ ! -f "./setup.sh" ]] || [[ "$0" == *"/dev/fd/"* ]] || [[ "$0" == "bash" ]]
   }
   ```

2. **Skip autocomplete in remote mode**: When running remotely, skip the
   `setup_autocomplete()` call and print a message instructing users to set up
   autocomplete separately after installation:

   ```
   ℹ️  Autocomplete not installed (remote install).
       To set up autocomplete, run:
         aps setup autocomplete   # (future command)
       Or manually source from:
         https://github.com/Cyber-Syntax/auto-penguin-setup/tree/main/autocomplete
   ```

3. **Alternatively, download autocomplete scripts**: Fetch autocomplete files
   from GitHub raw URLs and install them to the appropriate shell config
   location. This makes the one-liner fully self-contained.

4. **Ensure idempotency**: The script must be safe to run multiple times
   (`uv tool install --force` is already used).

5. **Default `install` action**: When invoked without arguments (the common
   case for piped execution), `setup.sh` already defaults to the `install`
   action via `case "${1-}" in install | "")`.

6. **Document in README**: Add a "Quick Install" section to `README.md` with
   the one-line command.

### Rationale

- The existing `setup.sh` already does the heavy lifting. Only the
  autocomplete path assumption needs fixing for remote execution.
- `uv tool install git+https://...` does not require a local clone, making
  remote installation viable today.
- Process substitution (`bash <(curl ...)`) is safer than pipe (`curl | bash`)
  because bash can detect the full script before executing, though functionally
  they are equivalent for this use case.

## Consequences

### Positive

- **POS-001**: Reduces installation from multi-step (clone → cd → run) to a
  single copy-pasteable command.
- **POS-002**: Enables inclusion of APS in automated provisioning scripts,
  cloud-init configs, and Ansible playbooks with minimal boilerplate.
- **POS-003**: Aligns with user expectations set by tools like `rustup`, `nvm`,
  and `uv` itself, all of which offer `curl | bash` installation.
- **POS-004**: The `setup.sh` remains backward-compatible — local execution
  from a cloned repository continues to work exactly as before.

### Negative

- **NEG-001**: Autocomplete is not available immediately after remote install
  (unless the download-from-GitHub approach is implemented). Users must set
  it up separately.
- **NEG-002**: The `curl | bash` pattern inherently trusts the remote server.
  If the GitHub repository is compromised, the install script could be
  malicious. Mitigated by using HTTPS and pinning to the `main` branch.
- **NEG-003**: Users behind corporate proxies or firewalls may not be able to
  reach `raw.githubusercontent.com`.
- **NEG-004**: The script must handle the case where `curl` itself is not
  installed (unlikely on modern Linux, but possible on minimal containers).

## Alternatives Considered

### Provide a separate `install-remote.sh` script

- **ALT-001**: **Description**: Create a dedicated script for remote installation
  that does not share code with `setup.sh`.
- **ALT-002**: **Rejection Reason**: Duplicates logic (UV detection, APS
  installation) and creates a maintenance burden. A single script with
  remote-mode detection is simpler.

### Use `pip install` or `pipx install` instead of `uv tool install`

- **ALT-003**: **Description**: Publish APS to PyPI and let users install via
  `pip install auto-penguin-setup` or `pipx install auto-penguin-setup`.
- **ALT-004**: **Rejection Reason**: APS uses `uv` as its package/dependency
  manager. Requiring `pip` or `pipx` adds a dependency the project has
  intentionally moved away from. `uv tool install` is the canonical approach.

### Clone the repository in /tmp and run setup.sh locally

- **ALT-005**: **Description**: The one-liner clones the repo to a temp
  directory, runs `setup.sh install` from there, then cleans up:

  ```bash
  bash -c 'git clone ... /tmp/aps && cd /tmp/aps && ./setup.sh install && rm -rf /tmp/aps'
  ```

- **ALT-006**: **Rejection Reason**: Requires `git` to be installed (not always
  present). Significantly slower than piping a single script. More complex
  one-liner that is harder to remember or type.

## Implementation Notes

- **IMP-001**: Add an `is_remote_install()` helper to `setup.sh` that checks
  execution context. Guard the `setup_autocomplete` call with this check.
- **IMP-002**: Add a "Quick Install" section to `README.md` with the one-liner
  and a brief explanation. Place it near the top for visibility.
- **IMP-003**: Consider downloading autocomplete scripts from raw GitHub URLs in
  remote mode to make the install fully self-contained. Use the same branch as
  the install URL (default: `main`).
- **IMP-004**: Test the one-liner in a clean container (Fedora and Arch) to
  confirm it works end-to-end without a local clone.

## References

- **REF-001**: [setup.sh](../../setup.sh) — Current installation script
- **REF-002**: [scripts/autocomplete.bash](../../scripts/autocomplete.bash) — Autocomplete installer
- **REF-003**: [autocomplete/](../../autocomplete/) — Shell completion scripts (bash, zsh)
- **REF-004**: [README.md](../../README.md) — Project README (install section to be updated)
