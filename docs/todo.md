# TODOS

## review

- [ ] Test installers:
      - [x] vscode aur install test with paru
      - [x] vscode copr install test with dnf
      - [x] zenpower3 copr install test with dnf
      - [x] ohmyzsh installer
      - [ ] syncthing setup
      - [ ] thinkfan setup test on thinkpad
      - [ ] virtmanager

- [ ] Test setups:
      - [ ] qtile setup test
      - [ ] lightdm setup test
      - [ ] sddm setup test
      - [ ] firewall setup test
      - [ ] ssh setup test
      - [ ] sudoers setup test
      - [ ] multimedia setup test
      - [ ] repositories setup test
      - [ ] pm_optimizer setup test
      - [ ] nvidia hardware test on fedora

- [ ] Test Hardware detection modules:
      - [ ] nvidia (<https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#faq2>)
      - [ ] amd
      - [ ] intel
      - [ ] touchpad

- Better ruff linting rules
- auto-cpufreq installer outputs to terminal properly

## in-progress

- [ ] checkout: <https://github.com/wz790/Fedora-Noble-Setup?tab=readme-ov-file#rpm-fusion---the-good-stuff>
- [ ] It is save the token somewhere but couldn't figure out where it which it is
not shown on kdewallet, so probably not configured for kdewallet saves.
- [ ] add gnome-kerying to packages.ini and make sure to disable kdewallet.
- [ ] add `ttf-jetbrains-mono-nerd` for arch font, and find it for fedora?
- [ ] It isn't show pacman output

```bash
aps setup ollama
[sudo] password for gamer:
Installing Ollama...
Detected GPU vendor: nvidia
Installing Ollama package: ollama-cuda
```

- use default --noconfirm but we don't want that

```bash
2025-12-22 19:32:31,861 - aps.core.setup - INFO - Installing Ollama...
2025-12-22 19:32:31,862 - aps.core.setup - INFO - Detected GPU vendor: nvidia
2025-12-22 19:32:31,862 - aps.core.setup - INFO - Installing Ollama package: ollama-cuda
2025-12-22 19:32:31,862 - aps.utils.privilege - DEBUG - Running privileged command: pacman -S --needed --noconfirm ollama-cuda
```

- [ ] install lact from ilya-zlobintsev instead of nfancurve
      - [ ] or this: <https://gitlab.com/coolercontrol/coolercontrol/-/releases>

- [ ] one line install command to install via setup.sh script like:
      `bash <(curl -fsSL https://raw.githubusercontent.com/Cyber-Syntax/auto-penguin-setup/main/setup.sh)`

## todo

- [ ] add tuned setup:
      - testing `tuned-adm profile desktop` -> remember to activate it `sudo tuned-adm active`
      - after that enable `sudo cpupower frequency-set --governor performance` which
      stay powersave after auto-cpufreq
      - check the status `sudo cpupower frequency-info`
      - Enable turbo `sudo cpupower set --turbo-boost 1`

```bash
# Last status of cpu info,
sudo cpupower frequency-info
  energy performance preference: balance_performance
# This line was 3.79Ghz max before turbo-boost 1 command
  hardware limits: 561 MHz - 4.65 GHz
```

- [ ] disable p2p for fwupd.service
Disable local cache server (passim)

fwupd v1.9.5 from September 2023 introduced a dependency on passim, a local cache server intended to help reduce LVFS bandwidth usage by making each machine able to serve the metadata file it downloads everyday to others[2][3].

passimd is a daemon which listens for connections on port 27500 from any IP addresses (i.e. it listens on 0.0.0.0:27500). This has led to some criticism regarding the security implications[4][5], and indeed several vulnerabilities were reported just a few weeks later[6][7].

On Arch the request from FS#79614 to make the dependency optional at compile-time was denied because it would require creating a split-package for a library.

As a consequence, if you wish to disable passimd you should follow the advice given by the author[8]: add P2pPolicy=nothing to /etc/fwupd/fwupd.conf and/or mask passim.service.

- Make sure the optional dependency udisks2 is installed and the associated systemd unit is started before fwupd unit; it will provide UEFI firmware upgrade support.

- [ ] better to have util function to backup any config file to keep DRY principle

- [ ] Make aps singleton or another solution, one instance only to avoid issues with multiple instances
- [ ] extra official repo check for cachyos/nobara, install vscode to test it
- [ ] Creating config examples in ini format via python instead of copy-pasting config_examples/packages.ini...
- [ ] better code structure? <https://docs.python-guide.org/writing/structure/>
- [ ] <https://github.com/bahamas10/bash-style-guide> for setup.sh
- [ ] add ohmyzsh uninstall command? That command not work for custom ohmyzsh folder.
      If you want to uninstall oh-my-zsh, just run `uninstall_oh_my_zsh` from the command-line. It will remove itself and revert your previous bash or zsh configuration.

- [ ] add acknowledgements to readme.md
- [ ] track setup's too like ohmyzsh, tmux, neovim, hyprland, i3 etc.
- [ ] exclude configs/readme.md from uv builds
- [ ] add lightdm auto unlock keyring subcommand
- [ ] BUG: lightdm auto keyring unlock not work:

```bash
      "
      pam setup for auto unlock gnome keyring
      This is necessary for automatically opening the gnome-keyring on login
      for the lightdm, it won't work for autologin but it is good to open the keyring
      when the lightdm opens the session, so you won't write 2 times the password
      passwords need to be same with login user and keyring password
      Below is the automatically written to lightdm pam config file
      we only need to remove `-` in front of the lines to enable it
      of course we need to check if the lines already exist to avoid duplicates
      else we need to write them without `-` this line

      -auth       optional     pam_gnome_keyring.so
      -session    optional     pam_gnome_keyring.so auto_start

      #WARN: below isn't the one that make auto unlock gnome keyring

      something else is needed, research needed (one of my machine unlock without below)"

      ##%PAM-1.0
      #auth     [success=done ignore=ignore default=bad] pam_selinux_permit.so
      #auth       required    pam_env.so
      #auth       substack    system-auth
      #auth       optional    pam_gnome_keyring.so
      #-auth       optional    pam_kwallet5.so
      #-auth       optional    pam_kwallet.so
      #auth       include     postlogin
      #account    required    pam_nologin.so
      #account    include     system-auth
      #password   include     system-auth
      #session    required    pam_selinux.so close
      #session    required    pam_loginuid.so
      #-session    optional    pam_ck_connector.so
      #session    required    pam_selinux.so open
      #session    optional    pam_keyinit.so force revoke
      #session    required    pam_namespace.so
      #session    include     system-auth
      #session    optional    pam_gnome_keyring.so auto_start
      #-session    optional    pam_kwallet5.so
      #-session    optional    pam_kwallet.so
      #session    optional    pam_lastlog.so silent
      #session    include     postlogin
      #auth        sufficient  pam_succeed_if.so user ingroup nopasswdlogin
      #auth        include     system-login
```

- [ ] <https://wiki.cachyos.org/configuration/general_system_tweaks/#enable-rcu-lazy>
- [ ] re: rcu_nocbs, I read that it's often recommended to be used together with rcu_lazy:
- [ ] test new tlp feature
    - [ ] disable irqbalance and remove
- [ ] add a warning when the pkgmap.ini didn't found the packages for the current distro
- [ ] add zen.desktop to default apps
- [ ] disable intel_pstate , enable acpi-cpufreq or enable intel_pstate
- [ ] omarchy arch scripts good repo
- [ ] browser profile save advanced
      <https://docs.zen-browser.app/guides/manage-profiles>
- [ ] font setup
- [ ] git setup
- [ ] maybe user have nvidia and thinkpad
      so better to make thinkfan and similar to command not laptop package.
- [ ] create default config util
      config_examples copy not good because it is cumbersome, need to use create default config.sh util to handle it
- [ ] update docs
- [ ] setup custom_configs folder usage for user
      Setup custom_configs directory for user-specific config files would be better because current configs folder is only my configs which may not suit others.
- [ ] my-unicorn, autotarcompres add their setup
- [ ] my-unicorn compatibility for mimeapp.list
- [ ] bats unittest updates
- [ ] tmux dotfiles need to git clone tpm to tmux/plugins folder than install the plugins prefix and press shift and I to install

## backlog

- [ ] Option to delete old, unmaintaned packages more easily. (Maybe with cli, or packages.ini new list)
- [ ] Find a way to detect unmaintaned copr packages, AUR packages.
- [ ] we can call the sddm setup on the command hyprland installation in setup.sh

- add bluetooth settings configs

1. disable bluetooth via tlp and this:
   reenabled because modprobe not work when udev in there

- Note: when we disable bluetooth on bluetooth manager gui
  btusb not consume any power, when enabled it consume 1W
  so seems like, we could close when we not use it and enable it manually?
- Lets test it is it going to consume any power on next boot if we don't do any changes?

```bash
/etc/udev/rules.d/50-bluetooth.rules

# disable bluetooth
SUBSYSTEM=="rfkill", ATTR{type}=="bluetooth", ATTR{state}="0"
```

1. reconfigured the tlp settings

- [ ] display backlight show 3W usage even on 10% brightness
- [x] powertop need to run 1h 30min to detect power consumption correctly
- add enable to auto-cpufreq which we do same thing on tlp

1. disable leds like power led, numlock led, mic led

## cpu status

1. disable intel_pstate and enable acpid to get 4.6 Ghz turbo boost , intel_pstate only 1.3Ghz available
   which it would be good for battery and tempature but things would take more time with lower ghz though?

dependencies install:
`sudo dnf install acpi acpid acpitool kernel-tools`

enable turbo boost on other than intel_pstate

```bash
echo 1 > /sys/devices/system/cpu/cpufreq/boost

# disable
echo 0 > /sys/devices/system/cpu/cpufreq/boost
```

## irqbalance disable

> Resource: <https://github.com/konkor/cpufreq/issues/48>

IRQBALANCE for the IO Priority and NOT FOR USER SPACE APPLICATIONS!
GNU/Linux Debian (bug closing the issue) removed IRQBALANCE from dependencies. It means Ubuntu/PopOS/Mint and so on will do the same.
irqbalance doesn't support fully all kernel features to an example a turning on/off core threads supported by the extension. If you have installed irqbalance package and turn off some cores you can get freezes or not working devices like wi-fi, bluetooth, video cards, sound cards...
irqbalance is not a part of the Linux kernel.
It designed for special server configurations with many RAID/HDD/SDD controllers.
Only Debian Flowers have the irqbalance installed because Debian is very Server oriented. Red Hat doesn't have installed irqbalance by default but it doesn't make Red Hat less server OS.
It keeps all Linux core threads working so its not good for power saving, especially for laptops.
Any user-space application (like games, compilation...) can not get 100% of CPU resources on any thread because it's always sharing this resources with IO tasks.

disabled irqbalance

```bash
sudo systemctl disable --now irqbalance
sudo dnf remove irqbalance
```

## done

- [x] pure functions for better testability on setups and installers
    - [x] Remove base.py and switch to function base programming for setups
- [x] ohmyzsh, can be installed .config/oh-my-zsh config more easily with the new
      curl install.sh offical command but zsh shell need to set env variable for ZSH_CUSTOM probably or similar to it..
      #TODO: refactor to use below
      Below best one to keep zshrc unchanged:
      sh -c "$(curl -fsSL <https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh>)" "" --keep-zshrc
- pacman output display during package removal to ensure user sees relevant messages and errors directly in terminal.
- [x] remove hostname.py module, it just `hostnamectl set-hostname` command, no need for a module
- [x] Make installed packages one line output for better readability:
- [x] BUG: dry-run not work for copr enabling
- [x] logs rotation setup for aps logs to avoid large log files
- [x] Keep only the name, source and maybe time in the tracking database for simplicity
- [x] add option to remove the packages, which it would remove from tracked database
- [x] add upgrade command to self-update the cli tool via uv
- [x] add folder structure to tests/ folder similar to src/aps/ for better organization of tests
- [x] move test_system test to their own modules like tests/system/test_<distro>.py
- [x] add setup commands like system folder, hardware folder to cli which we didn't have yet
- `uv tool install .` tested on cachyos and work as expected.
- Brave setup works.
- [x] Switch to python for core modules, keep the bash for other simple scripts
- [x] switch to json or jsonl for tracking database instead of ini for performance and easier parsing (orjson library)
- [x] move tracking database to .config/auto-penguin-setup/metadata.jsonl
- [x] move logs to .config/auto-penguin-setup/logs/
- [x] keepchangelog
      <https://keepachangelog.com/en/1.1.0/>
- [x] make cli tool like `aps install`
- [x] ohmyzsh fail when in bash shell(arch linux virtual machine test):
- [x] refactor update_config.sh for new INI system
- [x] add flatpak tracking
- [x] test new tracking system for all of the packages.ini setups
    - [x] arch
    - [x] ubuntu qemu
- [x] Sources not recognized correctly: COPR:atim/starship found but no lazygit
      - now it is fixed with new tracking system
- [x] Errors on sync-repos, we can't change flatpak to official the flatpak repos.
      If user want to get the official, than they can easily remove the package from flatpak
      and move it to correct category like core, laptop, dev etc. to be able to install
      from official or AUR/COPR.

```bash
Repository Changes Detected:
============================
lazygit                       : COPR:atim/lazygit -> COPR:dejan/lazygit
io.github.martchus.syncthingtray: flatpak:flathub -> official
```

- [x] test wm-common package for x11 window manager package installs
    - [x] test i3, qtile
- [x] rename neovim.sh to uberzugpp.sh, handle setup.sh etc.
- [x] Disable old copr when copr pkgmap.ini changed. Example test atim/lazygit -> dejan/lazygit
- [x] Status all of the installed apps to take track of the apps more better way
    - [x] tracking migration option necessary which we already installed most of the packages to our system, so we need to compare the packages.ini with our distro specific package manager status command to check if the packages are installed or not than write to a tracked ini database those installed packages.
    - [x] packages_with_repos.ini seems used for tracking packages with their repositories, we already have pkgmap.ini to track the special naming of the packages that we specify on the packages.ini for different distros and we use pkgmap.ini to write the copr, aur, ppa repos there, and if we change that, it need to be use that instead of using a new config, or maybe we can make a new one file packages.ini to define everything in one file with more easy way which we can use maybe [arch] etc. specific [distro] specific things.
