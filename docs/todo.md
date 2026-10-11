# TODOS

## Testing and quality

- [ ] Improve automated coverage for every setup and install, including tests on both Arch and Fedora.
  - [ ] Find a better easy way to automate tests for every setup/install.
  - [ ] Test both Arch and Fedora for every setup/install.
- [ ] Organize pytest temporary folders by test type, such as `pytest-of-<user>-aps-e2e` and `pytest-of-<user>-aps-unit`, so test results are easier to find.
- [ ] Complete the development quality pass.
  - [ ] Fix type annotations in `firewall.py`, `multimedia.py`, and other modules.
  - [ ] Add a basic lock manager using `fcntl.flock` to prevent multiple APS instances from running at the same time.
  - [ ] Add a utility function to back up any config file and keep the implementation DRY.
  - [ ] Consider switching from INI to TOML for better parsing and performance.

## In progress

- [ ] Clean up this backlog and move hard issues to GitHub while keeping active development tasks here.
- [ ] Fix bundled configuration distribution and XDG storage.
  - [ ] Move configs out of the wrong bundled location and into the GitHub repository.
  - [ ] Let `setup.sh` or APS download configs from the github repository and save them to the correct XDG location instead of bundled in aps cli, so user can customize them without editing the APS source code.
- [ ] Fix Intel configuration installation permissions.
  - [ ] BUG: Intel setup cannot copy `20-intel.conf` into `/etc/X11/xorg.conf.d/` without permission errors.
- [ ] Make VS Code available through the package configuration.
  - [ ] Install VS Code through `packages.ini` so `aps install @dev` can use the distro package manager.

## Package and setup workflows

- [ ] Improve package mapping, installation, and upgrade workflows.
  - [ ] Make the upgrade command work with tag-based updates.
  - [ ] Detect packages before running setup modules such as `ollama.py`, then use `pkgmap.ini` for distro-specific names.
  - [ ] Warn when `pkgmap.ini` does not contain a package for the current distro.
  - [ ] Add extra official repository checks for CachyOS and Nobara, then test VS Code installation.
  - [ ] Make it easier to remove old or unmaintained packages through the CLI or a new `packages.ini` list.
  - [ ] Detect unmaintained COPR and AUR packages.
  - [ ] Handle Arch invalid package signatures with a clear warning while still showing the pacman output.
    - [x] Document the Arch package signature limitation in the README.
    - [ ] Explain that users may need to run `sudo pacman -Syu` and retry, without running the update automatically.

```bash
error: ollama: signature from "CachyOS <admin@cachyos.org>" is invalid
:: File /var/cache/pacman/pkg/ollama-0.17.1-1.1-x86_64_v3.pkg.tar.zst is corrupted (invalid or corrupted package (PGP signature)).
Do you want to delete it? [Y/n]
```

- [ ] Add package export and persistence commands.
  - [ ] Export installed packages to a file.
  - [ ] Save tracked/installed packages to `packages.ini` or another location so a command such as `aps install task` can be made persistent without manual edits.
- [ ] Support tracking and removal for setup-installed applications.
  - [ ] Track applications such as Ollama, VS Code, and Oh My Zsh even when they are installed by a vendor script or package manager outside the normal package flow.
  - [ ] Add `remove --setup` support for setups such as VS Code; Ollama is currently supported.
- [ ] Install and maintain additional applications and repositories.
  - [ ] Add installation support for personal applications such as Appman and ztarcompress when they reach MVP status.
  - [ ] Install LACT from Ilya Zlobintsev instead of nfancurve, or evaluate <https://gitlab.com/coolercontrol/coolercontrol/-/releases>.
  - [ ] Check <https://github.com/wz790/Fedora-Noble-Setup?tab=readme-ov-file#rpm-fusion---the-good-stuff> for useful Fedora setup ideas.

## Setup features

- [ ] Add new hardware, desktop, and system setup components.
  - [ ] Add a ckb-next setup that enables `ckb-next-daemon` at boot with `systemctl enable ckb-next-daemon`.
  - [ ] Add a tuned setup and document the required activation and CPU governor commands.
    - [ ] Test `tuned-adm profile desktop` and activate it with `sudo tuned-adm active`.
    - [ ] Test `sudo cpupower frequency-set --governor performance` and turbo boost with `sudo cpupower set --turbo-boost 1`.
    - [ ] Check status with `sudo cpupower frequency-info`.
  - [ ] Add an optional Thinkfan setup for users with NVIDIA ThinkPads.
  - [ ] Add Nvibrant, SDDM, Gammastep, and Wlsunset setup support where appropriate.
  - [ ] Call the SDDM setup from the Hyprland installation in `setup.sh`.
  - [ ] Add Zen Browser to the default applications with `zen.desktop`.
  - [ ] Improve browser profile saving with <https://docs.zen-browser.app/guides/manage-profiles>.
  - [ ] Add font setup.
  - [ ] Add Git setup.
- [ ] Improve shell, desktop, and application integration.
  - [ ] Change the default shell from fish to Bash with `chsh -s /bin/bash`, possibly as part of the Zsh setup.
  - [ ] Add fish autocomplete support.
  - [ ] Add a one-line installer through `setup.sh`:
    - `bash <(curl -fsSL https://raw.githubusercontent.com/Cyber-Syntax/auto-penguin-setup/main/setup.sh)`
  - [ ] Add an Oh My Zsh uninstall command that supports custom Oh My Zsh folders, using `uninstall_oh_my_zsh` where appropriate.
- [ ] Improve device, power, and service configuration.
  - [ ] Remove the NVIDIA Xorg configuration setup; users should manage it with `nvidia-settings`.
  - [ ] Disable KDE Wallet when GNOME Keyring is installed to avoid conflicts.
  - [ ] Enable `autocpufreq` at boot with `systemctl enable auto-cpufreq`, similar to TLP.
  - [ ] Disable Bluetooth with a udev rule and test power consumption after reboot.
  - [ ] Investigate disabling `irqbalance` for laptop power saving and performance.
    - Resource: <https://github.com/konkor/cpufreq/issues/48>
    - IRQBALANCE is intended for I/O priority, not user-space applications.
    - It is designed for server configurations with many RAID/HDD/SSD controllers and may interfere with disabled CPU cores or devices.
    - Test the following commands where appropriate:

```bash
/etc/udev/rules.d/50-bluetooth.rules

SUBSYSTEM=="rfkill", ATTR{type}=="bluetooth", ATTR{state}="0"

sudo systemctl disable --now irqbalance
sudo dnf remove irqbalance
```

- [ ] Improve firmware update service configuration.
  - [ ] Disable peer-to-peer caching for `fwupd.service` by setting `P2pPolicy=nothing` in `/etc/fwupd/fwupd.conf` and/or masking `passim.service`.
  - [ ] Ensure the optional `udisks2` dependency is installed and its systemd unit starts before the fwupd unit for UEFI firmware support.
  - [ ] Keep the security context: `passimd` listens on `0.0.0.0:27500`; the change avoids exposing the local cache server unnecessarily.
  - [ ] Preserve the investigation notes: fwupd 1.9.5 introduced passim as a local LVFS metadata cache; the Arch request to make it optional was rejected because it would require a split package.
- [ ] Evaluate CachyOS and Arch system tuning ideas.
  - [ ] Review <https://wiki.cachyos.org/configuration/general_system_tweaks/#enable-rcu-lazy>.
  - [ ] Investigate whether `rcu_nocbs` should be used with `rcu_lazy`.
  - [ ] Look for useful ideas in the Omarchy Arch scripts.

```bash
# Last status of CPU info
sudo cpupower frequency-info
  energy performance preference: balance_performance
# This line was 3.79 GHz max before turbo-boost 1 command
  hardware limits: 561 MHz - 4.65 GHz
```

## Configuration and data

- [ ] Make variables and generated configuration easier to manage.
  - [ ] Add sections to `variables.ini` for application-specific values such as Borg repository paths and Ollama model storage.
  - [ ] For Ollama, update `/usr/lib/systemd/system/ollama.service` with `Environment="OLLAMA_MODELS=/mnt/backups/ollama/models"`, using the real path from `variables.ini`.
  - [ ] Generate INI config examples with Python instead of copying `config_examples/packages.ini`.
- [ ] Expand Ollama CUDA setup support.
  - [ ] Document the CUDA binaries at `/opt/cuda/bin/` and the need to source `/etc/profile` or restart the session.
  - [ ] Document `$NVCC_CCBIN` in `/etc/profile.d/cuda.sh` as the default host compiler configuration.
  - [ ] Document clearing build caches after CUDA compiler path changes or GCC removal.
  - [ ] Track optional dependencies: `gdb`, `glu`, `nvidia-utils`, `nsight-compute`, `nsight-systems`, and `rdma-core`.

```text
The CUDA binaries are in /opt/cuda/bin/.
Source /etc/profile or restart the session for the CUDA binaries and
$NVCC_CCBIN environment variable to appear.
```

## Developer experience and documentation

- [ ] Remove duplicated command output.
  - [ ] Examples include repeated VS Code setup messages, repeated `virtmanager setup completed successfully`, and duplicate firewall/network configuration messages.

```text
Successfully installed AUR packages
Visual Studio Code installation completed.
vscode setup completed successfully
vscode setup completed successfully

Added firewall_backend = iptables
Successfully configured network.conf
Virtualization setup completed successfully
Note: You may need to log out and back in for group changes to take effect
virtmanager setup completed successfully
virtmanager setup completed successfully
```

- [ ] Add acknowledgements to `README.md`.
