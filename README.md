# 🔐 TrustGet

> **wget yang punya otak keamanan.**
>
> TrustGet = download + verify + trust analysis — satu perintah, nol drama.

[![PyPI version](https://img.shields.io/pypi/v/trustget.svg)](https://pypi.org/project/trustget/)
[![Python versions](https://img.shields.io/pypi/pyversions/trustget.svg)](https://pypi.org/project/trustget/)
[![Build Status](https://github.com/FaturRachmann/trustget/actions/workflows/ci.yml/badge.svg)](https://github.com/FaturRachmann/trustget/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Built for:** SysAdmin · DevOps · Homelab · Linux Dev

---

## ✨ Features

- 🚀 **Smart Download** — Streaming download with progress bar, resume support, and retry logic
- 🔐 **Auto Verification** — Automatically finds and verifies SHA256/SHA512/MD5 checksums
- 🎯 **GitHub Smart Mode** — Zero-config security for GitHub Releases
- 📊 **Trust Score** — Transparent 0-100 security scoring with explainable factors
- 🧪 **Sandbox Execution** — Run downloaded files in isolated environment
- 📦 **Zero Config** — Works out of the box, no setup required

---

## 🚀 Quick Start

### Installation

#### From PyPI (Recommended)

```bash
pip install trustget
```

#### From apt (Debian/Ubuntu)

```bash
# Download the .deb package from releases
wget https://github.com/FaturRachmann/trustget/releases/latest/download/trustget_0.1.0_all.deb

# Install
sudo apt install ./trustget_0.1.0_all.deb
```

#### From Source

```bash
git clone https://github.com/FaturRachmann/trustget.git
cd trustget
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Download with automatic verification
sg https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz

# Or use the full command
trustget <url>

# Just verify a local file
sg verify ./file.tar.gz

# Check trust score without downloading
sg trust https://example.com/file.tar.gz

# Get release info
sg info https://github.com/user/repo/releases/download/v1.0/file.tar.gz

# Run in sandbox (experimental)
sg run ./AppImage
```

---

## 📖 Commands

| Command | Description |
|---------|-------------|
| `sg <url>` | Download + verify + trust analysis |
| `sg verify <file>` | Verify file against checksum |
| `sg trust <url>` | Analyze trust without download |
| `sg run <file>` | Execute file in sandbox |
| `sg info <url>` | Show file/release metadata |
| `sg config` | Manage configuration |

### Global Flags

| Flag | Description |
|------|-------------|
| `--json`, `-j` | Output in JSON format |
| `--quiet`, `-q` | Suppress non-essential output |
| `--verbose`, `-v` | Enable verbose output |
| `--no-color` | Disable colored output |
| `--no-verify` | Skip checksum verification |
| `--timeout`, `-t` | HTTP request timeout (default: 30s) |
| `--retry`, `-r` | Number of retry attempts (default: 3) |
| `--force`, `-f` | Force download even if trust score is low |

---

## 📋 Examples

### Download from GitHub Releases

```bash
$ Trustget https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz

 Trustget v0.1.0

 Analyzing URL...
 ✓ GitHub Release detected: cli/cli @ v2.40.0
 ✓ Published: 2024-01-15 by maintainer @williammartin
 ✓ Not a pre-release or draft

 Downloading gh_2.40.0_linux_amd64.tar.gz
 ████████████████████████████████ 100% • 11.2 MB • 4.2 MB/s • ETA 0s

 Verification
 ✓ SHA256 matched (from gh_2.40.0_checksums.txt)
   Expected : 4b49d4ddce8a6d56b67d95f9d99f1e17e5b5c5c
   Got      : 4b49d4ddce8a6d56b67d95f9d99f1e17e5b5c5c

 Security Analysis
 ┌─────────────────────────────────────────┐
 │  Trust Score    92 / 100    ◆ LOW RISK  │
 ├─────────────────────────────────────────┤
 │  ✓ HTTPS connection              +20    │
 │  ✓ Checksum verified             +25    │
 │  ✓ Known platform (github.com)   +10    │
 │  ✓ Maintainer verified           +20    │
 │  ✓ Recent release (< 30 days)    +10    │
 │  ✓ Repo age > 1 year             +07    │
 └─────────────────────────────────────────┘

 ✓ File saved → ./gh_2.40.0_linux_amd64.tar.gz
```

### JSON Output for CI/CD

```bash
$ Trustget --json https://example.com/file.tar.gz | jq

{
  "download": {
    "success": true,
    "filepath": "/path/to/file.tar.gz",
    "size": 1234567
  },
  "verification": {
    "status": "VERIFIED",
    "algorithm": "sha256",
    "expected_hash": "abc123...",
    "actual_hash": "abc123..."
  },
  "trust": {
    "score": 85,
    "risk_level": "LOW",
    "factors": [...]
  }
}
```

### Verify Local File

```bash
$ Trustget verify ./file.tar.gz --checksum abc123...

✓ SHA256 matched
  Expected : abc123...
  Got      : abc123...
```

### Check Trust Score

```bash
$ Trustget trust https://example.com/file.tar.gz

┌─────────────────────────────────────────┐
│  Trust Score    45 / 100    ◆ HIGH RISK │
├─────────────────────────────────────────┤
│  ✓ HTTPS connection              +20    │
│  ⚠ Unknown domain               -20    │
│  ⚠ No checksum found            -15    │
└─────────────────────────────────────────┘
```

---

## 🔒 Security Model

### Trust Score Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| HTTPS connection | +20 | Secure HTTPS connection |
| Checksum available | +10 | Checksum file found |
| Checksum verified | +25 | Hash verification passed |
| GPG signature | +25 | GPG signature verified |
| Known domain | +10 | Trusted domain (github.com, kernel.org, etc.) |
| Maintainer verified | +20 | Release by repo owner |
| Repo age > 1 year | +7 | Established repository |
| Recent release | +10 | Published < 30 days ago |
| HTTP redirect | -10 | Redirect to different domain |
| Unknown domain | -20 | Untrusted domain |
| No checksum | -15 | No checksum available |
| Repo < 3 months | -20 | New repository |
| Pre-release | -10 | Draft or pre-release version |

### Risk Levels

| Score | Level | Action |
|-------|-------|--------|
| < 40 | 🔴 CRITICAL | Abort download |
| 40–59 | 🟠 HIGH | Confirm with user |
| 60–79 | 🟡 MEDIUM | Proceed with warning |
| 80–100 | 🟢 LOW | Safe to proceed |

---

## ⚙️ Configuration

Configuration is stored in `~/.config/Trustget/config.toml`:

```toml
timeout = 30
retries = 3
verify = true
json_output = false
quiet = false
min_trust_score = 0
```

Use `Trustget config` to manage:

```bash
# Set a value
Trustget config --set timeout 60

# Get a value
Trustget config --get timeout

# Reset to defaults
Trustget config --reset
```

---

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=Trustget

# Run specific test file
pytest tests/unit/test_utils.py
```

### Code Quality

```bash
# Lint with ruff
ruff check Trustget/

# Type check with mypy
mypy Trustget/

# Format code
ruff format Trustget/
```

### Build Package

```bash
python -m build
twine check dist/*
```

---

## 📁 Project Structure

```
Trustget/
├── Trustget/
│   ├── __init__.py       # Version, public API
│   ├── cli.py            # Click commands
│   ├── downloader.py     # Streaming download
│   ├── verifier.py       # Hash/GPG verification
│   ├── scanner.py        # Checksum file detection
│   ├── github.py         # GitHub API integration
│   ├── trust.py          # Trust score engine
│   ├── reporter.py       # Output formatting
│   └── utils.py          # Shared utilities
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or corrections
- `chore:` Maintenance tasks
- `refactor:` Code refactoring

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Inspired by the need for secure downloading in production environments.

**Make secure the default, not the exception.**
