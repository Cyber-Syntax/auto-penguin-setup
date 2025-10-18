# Package Manager Abstraction

Describes the Strategy pattern used to provide a runtime-selected package manager interface (pm_install, pm_update, pm_remove, pm_is_installed) and global PM_* variables.

### Package Manager Command Mapping

| Operation | Fedora | Arch | Debian |
|-----------|--------|------|--------|
| Install | `dnf install -y` | `pacman -S --noconfirm` | `apt-get install -y` |
| Remove | `dnf remove -y` | `pacman -Rns --noconfirm` | `apt-get remove -y` |
| Update | `dnf update -y` | `pacman -Syu --noconfirm` | `apt-get update && apt-get upgrade -y` |
| Search | `dnf search` | `pacman -Ss` | `apt-cache search` |
| Is Installed | `rpm -q` | `pacman -Q` | `dpkg -l` |

### Repository System Mapping

| Type | Fedora | Arch | Debian |
|------|--------|------|--------|
| Extra Repos | COPR | AUR | PPA |
| Add Command | `dnf copr enable user/repo` | `paru -S package` | `add-apt-repository ppa:user/repo` |
| Example | `atim/lazygit` | `brave-bin` | `ppa:neovim-ppa/unstable` |

---