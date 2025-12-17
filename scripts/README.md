# Helper Scripts

Helper scripts for managing the auto-penguin-setup project.

- **Autocomplete**: `scripts/autocomplete.bash` - Manages shell completion setup for bash and zsh. Called automatically by `setup.sh` during installation.

## About the Installer

The top-level `setup.sh` script handles installation using `uv tool install`. It:

1. Checks for/installs UV if needed
2. Runs `uv tool install .` to install the `aps` CLI
3. Sets up shell autocomplete via `scripts/autocomplete.bash`
