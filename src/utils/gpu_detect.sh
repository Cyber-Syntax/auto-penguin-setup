#!/usr/bin/env bash
set -euo pipefail

#TODO: simplify and test
# Detect GPUs via lspci
function list_pci_gpus() {
  # list PCI devices of class VGA / 3D / display
  lspci -D -nn | grep -E " VGA | 3D controller | Display controller"
}

# Given a vendor ID, return vendor name
function vendor_from_id() {
  local vid="$1"
  case "$vid" in
    10de) echo "nvidia" ;;
    1002|1022) echo "amd" ;;   # Some AMD/ATI devices
    8086) echo "intel" ;;
    *) echo "unknown" ;;
  esac
}

declare -A GPU_VENDORS  # vendor → count or PCI slots

# Parse lspci output to detect vendor(s)
while IFS= read -r line; do
  # Example line:
  # 0000:01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GP104 [GeForce GTX 1070] [10de:1b81] (rev a1)
  # We extract the vendor ID between the square brackets after device: [10de:1b81]
  if [[ "$line" =~ \[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\] ]]; then
    vid="${BASH_REMATCH[1]}"
    vname=$(vendor_from_id "$vid")
    if [[ "$vname" != "unknown" ]]; then
      GPU_VENDORS["$vname"]+="$line"$'\n'
    else
      # record unknown if you like
      GPU_VENDORS["unknown"]+="$line"$'\n'
    fi
  else
    # fallback: you might parse textual vendor name
    GPU_VENDORS["unknown"]+="$line"$'\n'
  fi
done < <(list_pci_gpus)

# Now for each known vendor, try vendor-specific checks
echo "Detected GPU vendors and devices:"
for v in "${!GPU_VENDORS[@]}"; do
  echo "---- $v ----"
  echo "${GPU_VENDORS[$v]}"
done
echo

# NVIDIA check: nvidia-smi
if command -v nvidia-smi &>/dev/null; then
  echo "nvidia-smi found. Querying NVIDIA GPUs..."
  if nvidia-smi -L &>/dev/null; then
    echo "NVIDIA GPUs (via nvidia-smi):"
    nvidia-smi -L
  else
    echo "nvidia-smi exists but failed listing GPUs."
  fi
else
  echo "nvidia-smi not installed or not in PATH."
fi

# AMD check: check /sys for amdgpu
echo
echo "AMD/ATI details:"
for dev in /sys/class/drm/card*/device; do
  if [ -d "$dev" ]; then
    driver=$(basename "$(readlink "$dev/driver" 2>/dev/null || echo "")")
    if [[ "$driver" == "amdgpu" || "$driver" == "radeon" ]]; then
      echo "Found AMD device: $dev → driver = $driver"
      # You could read VRAM via mem_info_vram_total if present:
      if [ -f "$dev/mem_info_vram_total" ]; then
        vram_bytes=$(cat "$dev/mem_info_vram_total")
        echo "  VRAM bytes: $vram_bytes"
      fi
    fi
  fi
done

# Intel check: check i915 / xe driver
echo
echo "Intel GPU details:"
for dev in /sys/class/drm/card*/device; do
  if [ -d "$dev" ]; then
    driver=$(basename "$(readlink "$dev/driver" 2>/dev/null || echo "")")
    if [[ "$driver" == "i915" || "$driver" == "intel" || "$driver" == "xe" ]]; then
      echo "Found Intel device: $dev → driver = $driver"
      # You could check modinfo or other info:
      if modinfo i915 &>/dev/null; then
        modinfo i915 | grep -E "^parm:|^version:"
      fi
    fi
  fi
done

# You can also detect via “intel_gpu_top” if installed, or use glxinfo / vainfo etc.
