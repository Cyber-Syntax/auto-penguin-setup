# Core Architecture

## Introduction

### What is Auto-Penguin-Setup?

Auto-Penguin-Setup is an intelligent, cross-distribution Linux system setup automation tool designed to eliminate the repetitive tasks of configuring a new Linux system. Whether you're setting up a fresh Fedora desktop, an Arch Linux laptop, or a Debian-based workstation, this script adapts to your distribution and handles everything from package installation to hardware-specific configurations.

### Philosophy

The project is built on four core principles:

1. **Cross-Distribution Compatibility**: Write once, run anywhere (Fedora, Arch, Debian)
2. **Configuration-Driven**: All system-specific settings in INI files, not hardcoded
3. **XDG Compliance**: Respect standard Linux directory structures
4. **Modular Design**: Each component has a single, well-defined responsibility

### Supported Distributions

| Distribution | Package Manager | Repository System | Status |
|--------------|----------------|-------------------|--------|
| Fedora 41+ | DNF | COPR | ✅ Fully Tested |
| Arch Linux | pacman/paru/yay | AUR | 🧪 Testing |
| Debian/Ubuntu | APT | PPA | 🧪 Testing |

---

## Core Concepts

### 1. Distribution Abstraction

The script never calls `dnf`, `pacman`, or `apt` directly. Instead, it uses abstract functions like `pm_install`, `pm_remove`, and `pm_update` that automatically translate to the correct package manager command based on the detected distribution.

**Example:**

```bash
# Instead of: sudo dnf install vim
pm_install vim  # Works on Fedora, Arch, and Debian
```

### 2. Package Name Mapping

Package names often differ across distributions. The script maintains mapping sections in `packages.ini`:

```ini
[pkgmap.fedora]
fd-find = fd-find

[pkgmap.arch]
fd-find = fd

[pkgmap.debian]
fd-find = fd-find
```

When you request `fd-find`, the script automatically installs `fd` on Arch and `fd-find` on Fedora/Debian.

### 3. Configuration-Driven Setup

Configuration is centralized in a single reference document to avoid duplication. See `docs/architecture/config.arch.md` for the INI schema, examples (`variables.ini`, `packages.ini`, `pkgmap.ini`), loading rules, and migration notes.

### 4. Device-Specific Configurations

The script intelligently detects whether you're on a desktop or laptop (via hostname) and applies appropriate configurations:

- **Desktop**: Gaming packages, NVIDIA drivers, virtualization
- **Laptop**: TLP power management, Thinkfan, touchpad configs

---

## Design Philosophy

### Core Principles

The auto-penguin-setup architecture is built on six foundational principles:

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Abstraction Over Implementation**: Never expose distribution-specific details to high-level code
3. **Configuration Over Code**: System-specific settings live in JSON, not hardcoded
4. **Fail-Fast with Recovery**: Detect errors early, log comprehensively, provide recovery paths
5. **XDG Compliance**: Respect Linux standards for file locations
6. **Categorical Organization**: Group related functionality by purpose, not by scope

### Why These Principles?

**Separation of Concerns** enables:

- Independent testing of modules
- Easy addition of new distributions
- Clear understanding of code purpose

**Abstraction** provides:

- Write once, run anywhere capability
- Protection from package manager changes
- Consistent interface across distros

**Configuration-Driven** allows:

- Version control of system setup
- Easy migration between machines
- Sharing configurations across teams

**Categorical Organization** provides:

- Intuitive navigation: developers know where to find/add code
- Reduced cognitive load: related functions grouped together
- Clear boundaries: apps vs. system vs. hardware configurations
- Scalability: easy to add new categories as project grows

---

This file describes the modular monolith organization, core modules loaded first, and the role of the orchestrator `setup.sh`.

See the main index in `../ARCHITECTURE.md` for links to other architecture topics.
