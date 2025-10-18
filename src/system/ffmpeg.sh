#!/usr/bin/env bash

# Swaps ffmpeg-free with ffmpeg if ffmpeg-free is installed.
ffmpeg_swap() {
  log_info "Checking for ffmpeg-free package..."
  if sudo dnf list installed ffmpeg-free &>/dev/null; then
    log_info "Swapping ffmpeg-free with ffmpeg..."

    # Execute command directly instead of using log_cmd
    if ! sudo dnf swap ffmpeg-free ffmpeg --allowerasing -y; then
      log_error "Failed to swap ffmpeg packages"
      return 1
    fi
    log_info "ffmpeg swap completed successfully."
  else
    log_info "ffmpeg-free is not installed; skipping swap."
  fi
}