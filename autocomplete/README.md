# Autocomplete

This directory contains tab completion scripts for the `aps` command for both `bash` and `zsh`.

## Files

- `bash_autocomplete` - Bash completion script for aps
- `zsh_autocomplete` - Zsh completion script for aps

## Manual Installation

### Bash

Copy the bash completion file to your bash completions directory:

```bash
# System-wide (requires sudo)
sudo cp bash_autocomplete /etc/bash_completion.d/aps

# User-specific
mkdir -p ~/.local/share/bash-completion/completions
cp bash_autocomplete ~/.local/share/bash-completion/completions/aps
```

Then source your `.bashrc` or start a new shell.

### Zsh

Copy the zsh completion file to your zsh completions directory:

```bash
# System-wide (requires sudo)
sudo cp zsh_autocomplete /usr/share/zsh/site-functions/_aps

# User-specific
mkdir -p ~/.local/share/zsh/site-functions
cp zsh_autocomplete ~/.local/share/zsh/site-functions/_aps
```

Add the user-specific completion directory to your `fpath` in `.zshrc` (if using user-specific install):

```bash
fpath=(~/.local/share/zsh/site-functions $fpath)
autoload -Uz compinit && compinit
```

## Automatic Installation

The `setup.sh` script will automatically install these completion scripts when you run:

```bash
./setup.sh install
```
