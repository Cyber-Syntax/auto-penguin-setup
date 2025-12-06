#!/usr/bin/env bash

# oh-my-zsh setup with custom installation path
# The official installer doesn't consistently honor ZSH env var when piped,
# so we install to default location then move to desired location.

install_ohmyzsh() {
  echo "Installing oh-my-zsh..."

  local target_dir="$HOME/.config/oh-my-zsh"
  local default_dir="$HOME/.oh-my-zsh"

  # Determine which zshrc file to use - prefer ~/.config/zsh/.zshrc
  local zshrc_path
  if [ -f "$HOME/.config/zsh/.zshrc" ]; then
    zshrc_path="$HOME/.config/zsh/.zshrc"
  elif [ -f "$HOME/.zshrc" ]; then
    zshrc_path="$HOME/.zshrc"
  else
    # Create ~/.config/zsh/.zshrc if neither exists (preferred location)
    mkdir -p "$HOME/.config/zsh"
    zshrc_path="$HOME/.config/zsh/.zshrc"
    touch "$zshrc_path"
  fi

  echo "Using zshrc at: $zshrc_path"

  # Run the installer non-interactively (skip shell change prompt)
  RUNZSH=no CHSH=no sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || {
    echo "Error: oh-my-zsh installation failed"
    return 1
  }

  # Move installation to target directory if it was installed to default location
  if [ -d "$default_dir" ] && [ "$default_dir" != "$target_dir" ]; then
    echo "Moving oh-my-zsh from $default_dir to $target_dir"
    mkdir -p "$(dirname "$target_dir")"
    mv "$default_dir" "$target_dir" || {
      echo "Error: Failed to move oh-my-zsh to target directory"
      return 1
    }
  fi

  # Ensure custom plugins directory exists
  local zsh_custom="$target_dir/custom"
  mkdir -p "$zsh_custom/plugins"

  # Install additional plugins
  if [ ! -d "$zsh_custom/plugins/zsh-syntax-highlighting" ]; then
    echo "Installing zsh-syntax-highlighting plugin..."
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
      "$zsh_custom/plugins/zsh-syntax-highlighting" || echo "Warning: Failed to install zsh-syntax-highlighting"
  fi

  if [ ! -d "$zsh_custom/plugins/zsh-autosuggestions" ]; then
    echo "Installing zsh-autosuggestions plugin..."
    git clone https://github.com/zsh-users/zsh-autosuggestions \
      "$zsh_custom/plugins/zsh-autosuggestions" || echo "Warning: Failed to install zsh-autosuggestions"
  fi

  # Fix all path references in zshrc
  echo "Updating $zshrc_path with correct paths..."

  # Create a backup
  cp "$zshrc_path" "${zshrc_path}.backup.$(date +%Y%m%d_%H%M%S)"

  # Remove any existing export ZSH lines
  sed -i '/^[[:space:]]*export ZSH=/d' "$zshrc_path"

  # Add correct export ZSH at the top (before any oh-my-zsh source line)
  # Use single quotes to prevent variable expansion in the sed command
  # shellcheck disable=SC2016
  sed -i '1iexport ZSH="$HOME/.config/oh-my-zsh"' "$zshrc_path"

  # Replace all variations of oh-my-zsh path references
  # Keep $HOME variable instead of expanding it for portability
  # shellcheck disable=SC2016
  sed -i 's|\$HOME/.oh-my-zsh|$HOME/.config/oh-my-zsh|g' "$zshrc_path"
  # shellcheck disable=SC2016
  sed -i 's|~/.oh-my-zsh|$HOME/.config/oh-my-zsh|g' "$zshrc_path"
  
  # Replace any hardcoded absolute paths (e.g., /home/username/.oh-my-zsh) with $HOME
  # shellcheck disable=SC2016
  sed -i 's|/home/[^/]*/\.oh-my-zsh|$HOME/.config/oh-my-zsh|g' "$zshrc_path"

  # Ensure source line uses the $ZSH variable
  # shellcheck disable=SC2016
  sed -i 's|source [^[:space:]]*/oh-my-zsh\.sh|source $ZSH/oh-my-zsh.sh|g' "$zshrc_path"

  # Verify the critical lines exist
  if ! grep -q "^export ZSH=" "$zshrc_path"; then
    echo "Warning: export ZSH line may not have been added correctly"
  fi

  if ! grep -q "source.*oh-my-zsh\.sh" "$zshrc_path"; then
    echo "Warning: oh-my-zsh.sh source line not found in $zshrc_path"
  fi

  echo "oh-my-zsh installation completed successfully!"
  echo "Installation directory: $target_dir"
  echo "Configuration file: $zshrc_path"
  echo ""
  echo "Please restart your shell or run: source $zshrc_path"
}