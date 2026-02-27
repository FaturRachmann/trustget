# TrustGet Installation Guide

This guide covers all installation methods for TrustGet on Linux systems.

## Quick Install

### PyPI (Recommended for most users)

```bash
pip install trustget
```

### Debian/Ubuntu (.deb package)

```bash
# Download latest release
wget https://github.com/FaturRachmann/trustget/releases/latest/download/trustget_0.1.0_all.deb

# Install
sudo apt install ./trustget_0.1.0_all.deb
```

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [From PyPI](#from-pypi)
  - [From apt (Debian/Ubuntu)](#from-apt-debianubuntu)
  - [From Source](#from-source)
  - [From AUR (Arch Linux)](#from-aur-arch-linux)
- [Post-Installation](#post-installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Linux (Ubuntu, Debian, Arch, Fedora, etc.)
- **Dependencies**:
  - `python3-requests`
  - `python3-rich`
  - `python3-click`
  - `python3-gnupg` (optional, for GPG verification)
  - `gnupg` (optional, for GPG verification)

---

## Installation Methods

### From PyPI

**Best for**: Most users, quick installation, automatic updates via pip

```bash
# Install pip if not already installed
sudo apt install python3-pip  # Debian/Ubuntu
sudo dnf install python3-pip  # Fedora

# Install trustget
pip install trustget

# Verify installation
sg --version
```

**Optional**: Install to user directory (no sudo required)

```bash
pip install --user trustget
```

Make sure `~/.local/bin` is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

### From apt (Debian/Ubuntu)

**Best for**: System-wide installation, integration with system package manager

#### Option 1: Manual .deb installation

```bash
# Download the latest .deb package
wget https://github.com/FaturRachmann/trustget/releases/latest/download/trustget_0.1.0_all.deb

# Install the package
sudo apt install ./trustget_0.1.0_all.deb

# Verify installation
sg --version
```

#### Option 2: Build from source (advanced)

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y \
    debhelper \
    python3-all \
    python3-setuptools \
    python3-build \
    python3-installer \
    python3-wheel \
    python3-requests \
    python3-rich \
    python3-click \
    python3-gnupg \
    python3-platformdirs

# Clone the repository
git clone https://github.com/FaturRachmann/trustget.git
cd trustget

# Build the package
./scripts/build-deb.sh

# Install the built package
sudo apt install ./dist/deb/trustget_*.deb
```

---

### From Source

**Best for**: Developers, contributors, latest features

```bash
# Clone the repository
git clone https://github.com/FaturRachmann/trustget.git
cd trustget

# Install in development mode
pip install -e ".[dev]"

# Verify installation
sg --version
```

---

### From AUR (Arch Linux)

**Best for**: Arch Linux users

```bash
# Using yay
yay -S trustget

# Using paru
paru -S trustget

# Manual build
git clone https://aur.archlinux.org/trustget.git
cd trustget
makepkg -si
```

---

## Post-Installation

### Verify Installation

```bash
# Check version
sg --version

# Check help
sg --help

# Test trust analysis
sg trust https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz
```

### Install Optional Dependencies

For GPG signature verification:

```bash
# Debian/Ubuntu
sudo apt install gnupg

# Fedora
sudo dnf install gnupg

# Arch
sudo pacman -S gnupg
```

---

## Configuration

Configuration is stored in `~/.config/trustget/config.toml`:

```toml
timeout = 30
retries = 3
verify = true
json_output = false
quiet = false
min_trust_score = 0
```

Use the `sg config` command:

```bash
# Set timeout
sg config --set timeout 60

# Get timeout
sg config --get timeout

# View all config
sg config

# Reset to defaults
sg config --reset
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TRUSTGET_GITHUB_TOKEN` | GitHub token for higher API rate limits |
| `TRUSTGET_CONFIG` | Custom config file path |

---

## Troubleshooting

### `command not found: sg`

Ensure the installation directory is in your PATH:

```bash
# For user installation
export PATH="$HOME/.local/bin:$PATH"

# Add to ~/.bashrc for persistence
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Permission errors during installation

Use `--user` flag for pip installation:

```bash
pip install --user trustget
```

Or use sudo for system-wide installation:

```bash
sudo pip install trustget
```

### Missing dependencies

Install required Python packages:

```bash
pip install requests rich click python-gnupg platformdirs
```

### GPG verification not working

Install GPG:

```bash
# Debian/Ubuntu
sudo apt install gnupg

# Verify GPG is available
gpg --version
```

### Python version too old

TrustGet requires Python 3.11+. Check your version:

```bash
python3 --version
```

If your system has an older version, consider:
- Using a virtual environment with Python 3.11+
- Installing Python 3.11 from source
- Using the .deb package which bundles dependencies

---

## Uninstallation

### From PyPI

```bash
pip uninstall trustget
```

### From apt

```bash
sudo apt remove trustget
```

### From Source

```bash
pip uninstall trustget
# Or remove the cloned directory
rm -rf /path/to/trustget
```

---

## Getting Help

- **Documentation**: https://github.com/FaturRachmann/trustget/tree/main/docs
- **Issues**: https://github.com/FaturRachmann/trustget/issues
- **Discussions**: https://github.com/FaturRachmann/trustget/discussions
