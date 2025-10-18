# Directory Structure

The modular architecture organizes code by functional responsibility:

```text
auto-penguin-setup/
├── setup.sh                         # Main orchestrator
├── src/
│   ├── core/                        # Foundation modules (loaded first)
│   │   ├── logging.sh              # Logging system
│   │   ├── distro_detection.sh     # Distribution detection
│   │   ├── package_manager.sh      # Package manager abstraction
│   │   ├── package_mapping.sh      # Package name translation
│   │   ├── repository_manager.sh   # Repository management
│   │   ├── config.sh               # Configuration loading
│   │   ├── install_packages.sh     # Package installation functions
│   │   ├── constants.sh            # Global constants
│   │   ├── create_config.sh        # Config creation wizard
│   │   └── update_config.sh        # Config schema migration
│   │
│   ├── apps/                        # Third-party applications
│   │   ├── brave.sh                # Brave Browser
│   │   ├── vscode.sh               # Visual Studio Code
│   │   ├── ollama.sh               # Ollama AI
│   │   ├── lazygit.sh              # LazyGit TUI
│   │   ├── protonvpn.sh            # ProtonVPN
│   │   ├── syncthing.sh            # Syncthing sync
│   │   ├── ohmyzsh.sh              # Oh My Zsh
│   │   ├── virtmanager.sh          # Virtual Machine Manager
│   │   ├── tlp.sh                  # TLP power management
│   │   ├── thinkfan.sh             # ThinkFan fan control
│   │   ├── borgbackup.sh           # BorgBackup
│   │   ├── trash-cli.sh            # Trash-CLI
│   │   ├── autocpufreq.sh          # Auto-CPUFreq
│   │   └── nfancurve.sh            # NVIDIA fan curve
│   │
│   ├── system/                      # System configurations
│   │   ├── grub.sh                 # GRUB bootloader
│   │   ├── network.sh              # Network settings
│   │   ├── ufw.sh                  # UFW firewall
│   │   ├── ffmpeg.sh               # FFmpeg codecs
│   │   ├── speedup_pm.sh           # Package manager tuning
│   │   ├── update_boot.sh          # Boot optimizations
│   │   ├── enable_nonfree.sh       # Non-free repos
│   │   ├── fedora.sh               # Fedora-specific
│   │   ├── ssh.sh                  # SSH server
│   │   ├── sudoers.sh              # Sudoers config
│   │   └── setup_default_apps.sh   # MIME associations
│   │
│   ├── hardware/                    # Hardware-specific
│   │   ├── nvidia.sh               # NVIDIA drivers/CUDA
│   │   ├── amd.sh                  # AMD drivers
│   │   ├── intel.sh                # Intel optimizations
│   │   ├── touchpad.sh             # Touchpad gestures
│   │   └── hostname.sh             # Hostname management
│   │
│   ├── display/                     # Display managers
│   │   ├── sddm.sh                 # SDDM
│   │   ├── gdm.sh                  # GDM
│   │   └── lightdm.sh              # LightDM
│   │
│   └── wm/                          # Window managers
│       ├── qtile.sh                # Qtile tiling WM
│       └── hyprland.sh             # Hyprland compositor
│
├── configs/                         # System config templates
├── config_examples/                 # User config examples
│   ├── packages.ini               # Package lists & mappings
│   └── variables.ini              # System variables
└── docs/                            # Documentation
    ├── ARCHITECTURE.md             # This file
    ├── DEVELOPER.md                # Developer guide
    └── AGENTS.md                   # AI agent instructions
```
