# TODOS

## testing

- [ ] Creating config examples in ini format via python instead of copy-pasting config_examples/packages.ini...
- [ ] extra official repo check for cachyos/nobara, install vscode to test it
- [ ] Testing installers:
      - [ ] vscode aur install test with paru
      - [ ] vscode copr install test with dnf
      - [ ] lazygit copr install test with dnf
      - [ ] syncthing setup
      - [ ] thinkfan setup test on thinkpad
      - [ ] virtmanager
- [ ] move test_system test to their own modules like tests/system/test_<distro>.py
- [ ] add folder structure to tests/ folder similar to src/aps/ for better organization of tests

## in-progress

- [ ] test all aps commands in virtual machines for all distros
- [ ] add option to remove the packages, which it would remove from tracked database
- [ ] logs rotation setup for aps logs to avoid large log files
- [ ] Keep only the name, source and maybe time in the tracking database for simplicity
- [ ] test auto-cpufreq installer outputs to terminal properly

## todo

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
- [ ] handle battery todos file in the docs/battery.md
- [ ] ohmyzsh, can be installed .config/oh-my-zsh config more easily with the new
      curl install.sh offical command but zsh shell need to set env variable for ZSH_CUSTOM probably or similar to it..
      #TODO: refactor to use below
      Below best one to keep zshrc unchanged:
      sh -c "$(curl -fsSL <https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh>)" "" --keep-zshrc

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
- [ ] qtile-extras need to handled on debian based systems

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

2. reconfigured the tlp settings

- [ ] display backlight show 3W usage even on 10% brightness
- [x] powertop need to run 1h 30min to detect power consumption correctly
- add enable to auto-cpufreq which we do same thing on tlp

3. disable leds like power led, numlock led, mic led

## cpu status

4. disable intel_pstate and enable acpid to get 4.6 Ghz turbo boost , intel_pstate only 1.3Ghz available
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

- `uv tool install .` tested on cachyos and work as expected.
- Brave setup works.
- [ ] Switch to python for core modules, keep the bash for other simple scripts
- [ ] switch to json or jsonl for tracking database instead of ini for performance and easier parsing (orjson library)
- [ ] move tracking database to .config/auto-penguin-setup/metadata.jsonl
- [ ] move logs to .config/auto-penguin-setup/logs/
- [ ] keepchangelog
      <https://keepachangelog.com/en/1.1.0/>
- [ ] make cli tool like `aps install`
- [ ] ohmyzsh fail when in bash shell(arch linux virtual machine test):
- [ ] refactor update_config.sh for new INI system
- [ ] add flatpak tracking
- [ ] test new tracking system for all of the packages.ini setups
    - [ ] arch
    - [ ] debian
    - [ ] ubuntu qemu
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
