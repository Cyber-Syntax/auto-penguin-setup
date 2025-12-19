#!/usr/bin/env bash
#
# setup.sh
# ------------------------------------------------
# Installer for "auto-penguin-setup" (aps)
# - Ensures UV is installed
# - Installs aps CLI via `uv tool install .`
# - Sets up shell autocomplete (bash/zsh)
#
# Usage:
#   ./setup.sh install       # Install aps and autocomplete
#   ./setup.sh update        # Update aps to latest version
#   ./setup.sh autocomplete  # Install autocomplete only
#
# Exit immediately if:
# - a command exits with a non-zero status (`-e`)
# - an unset variable is used (`-u`)
# - a pipeline fails anywhere (`-o pipefail`)
set -euo pipefail

# -- Configuration -----------------------------------------------------------

# Project name
PROJECT_NAME="auto-penguin-setup"
CLI_NAME="aps"

# -- Helper functions --------------------------------------------------------

# Log messages to stderr
log() {
  printf '%s\n' "$*" >&2
}

# Check if UV is available
has_uv() {
  command -v uv >/dev/null 2>&1
}

# Install UV using the official installer
install_uv() {
  echo "📥 UV not found. Attempting installation via package manager..."

  # Detect package manager
  if command -v dnf >/dev/null 2>&1; then
    PKG_MGR="dnf"
    INSTALL_CMD="sudo dnf install -y uv"
  elif command -v pacman >/dev/null 2>&1; then
    PKG_MGR="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm uv"
  elif command -v apt >/dev/null 2>&1; then
    PKG_MGR="apt"
    INSTALL_CMD="sudo apt-get update && sudo apt-get install -y uv"
  elif command -v zypper >/dev/null 2>&1; then
    PKG_MGR="zypper"
    INSTALL_CMD="sudo zypper install -y uv"
  else
    PKG_MGR=""
    INSTALL_CMD=""
  fi

  if [[ -n "$PKG_MGR" ]]; then
    echo "🔎 Detected package manager: $PKG_MGR"
    if $INSTALL_CMD; then
      if command -v uv >/dev/null 2>&1; then
        echo "✅ UV installed successfully via $PKG_MGR"
        return 0
      fi
      echo "⚠️  UV package not found in $PKG_MGR repositories or install failed."
    else
      echo "⚠️  Failed to install UV using $PKG_MGR."
    fi
  else
    echo "⚠️  No supported package manager detected."
  fi

  echo "➡️  Falling back to Astral official install script..."
  if command -v curl >/dev/null 2>&1; then
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
      echo "✅ UV installed successfully via Astral script"
      echo "⚠️  Please restart your shell or run: source \$HOME/.cargo/env"
      echo "Then run this script again."
      exit 0
    else
      echo "❌ UV installation via Astral script failed."
      exit 1
    fi
  else
    echo "❌ curl is required to install UV via Astral script"
    echo "Please install curl first, or install UV manually from: https://docs.astral.sh/uv/"
    exit 1
  fi
}

# Ensure UV is available
ensure_uv() {
  if ! has_uv; then
    install_uv
  else
    echo "✅ UV is already installed ($(uv --version))"
  fi
}

# Install or update aps using uv tool install
install_aps_cli() {
  local action="${1:-install}"
  echo "📦 ${action^}ing ${CLI_NAME} CLI..."
  if has_uv; then
    uv tool install git+https://github.com/Cyber-Syntax/auto-penguin-setup
    echo "✅ ${CLI_NAME} ${action}ed successfully"
  else
    echo "❌ UV not found. Cannot ${action} ${CLI_NAME}"
    exit 1
  fi
}

# Update aps by delegating to install_aps_cli
update_aps_cli() {
  install_aps_cli "update"
}

# Set up shell autocomplete by delegating to autocomplete.bash
setup_autocomplete() {
  local helper="./scripts/autocomplete.bash"

  if [[ -x "$helper" ]]; then
    echo "🔁 Setting up autocomplete..."
    # Set INSTALL_DIR to current directory for autocomplete.bash
    INSTALL_DIR="$(pwd)" bash "$helper"
  else
    echo "❌ Autocomplete helper script not found at: $helper"
    return 1
  fi
}

# Full installation process
install_auto_penguin() {
  echo "=== Installing ${PROJECT_NAME} (${CLI_NAME}) ==="
  ensure_uv
  install_aps_cli
  setup_autocomplete

  echo ""
  echo "✅ Installation complete!"
  echo ""
  echo "Usage:"
  echo "  ${CLI_NAME} --help              # Show available commands"
  echo "  ${CLI_NAME} install @core       # Install core packages"
  echo "  ${CLI_NAME} status              # Show installation status"
  echo ""
  echo "To update later, run:"
  echo "  ./setup.sh update"
  echo ""
  echo "To uninstall, run:"
  echo "  uv tool uninstall ${PROJECT_NAME}"
}

# Update process
update_auto_penguin() {
  echo "=== Updating ${PROJECT_NAME} (${CLI_NAME}) ==="
  ensure_uv
  update_aps_cli
  setup_autocomplete
  echo "✅ Update complete!"
}

# Standalone autocomplete installation
install_autocomplete() {
  echo "${PROJECT_NAME} Autocomplete Installation"
  echo "========================================"

  if setup_autocomplete; then
    echo "✅ Autocomplete installation complete!"
    echo ""
    echo "Please restart your shell or source your shell's rc file to enable autocompletion."
    echo "Test completion by typing: ${CLI_NAME} <TAB>"
  else
    echo "❌ Autocomplete setup failed"
    exit 1
  fi
}

# -- Entry point -------------------------------------------------------------
case "${1-}" in
install | "") install_auto_penguin ;;
update) update_auto_penguin ;;
autocomplete) install_autocomplete ;;
*)
  cat <<EOF
Usage: $(basename "$0") [install|update|autocomplete]

  install       Full installation with uv tool and autocomplete (default)
  update        Update aps CLI to latest version
  autocomplete  Install shell completion only

Examples:
  $(basename "$0") install            # Full installation (default)
  $(basename "$0") update             # Update to latest version
  $(basename "$0") autocomplete       # Install completion for current shell

Note: This script uses 'uv tool install' to manage the aps CLI.
EOF
  exit 1
  ;;
esac
