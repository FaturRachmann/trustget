# TrustGet Distribution Guide

This guide explains how to distribute TrustGet via PyPI and Debian packages.

## Overview

TrustGet can be distributed through two main channels:

1. **PyPI** - For `pip install trustget` (all Linux distributions)
2. **Debian Package** - For `apt install trustget` (Debian/Ubuntu)

---

## PyPI Distribution

### Prerequisites

1. Create a PyPI account at https://pypi.org
2. Create a TestPyPI account at https://test.pypi.org (for testing)
3. Save your API tokens securely

### Configure API Tokens

Add your PyPI tokens as GitHub Secrets:

- `PYPI_TOKEN` - For production PyPI
- `TESTPYPI_TOKEN` - For TestPyPI (optional)

### Manual Release Process

```bash
# 1. Update version in pyproject.toml
# 2. Commit and tag
git add pyproject.toml
git commit -m "chore: release v0.1.0"
git tag v0.1.0
git push origin main --tags

# 3. Build package
make build

# 4. Test locally
pip install dist/trustget-*-py3-none-any.whl

# 5. Upload to TestPyPI first
make upload-test

# 6. Upload to PyPI
make upload
```

### Automatic Release (GitHub Actions)

The `.github/workflows/pypi-release.yml` workflow automatically publishes to PyPI when you push a version tag:

```bash
git tag v0.1.0
git push origin --tags
```

This triggers:
1. Package build (wheel and sdist)
2. Metadata validation
3. Upload to PyPI

### Verify Publication

```bash
# Check on PyPI
https://pypi.org/project/trustget/

# Install and test
pip install trustget
sg --version
```

---

## Debian Package Distribution

### Prerequisites

Install Debian packaging tools:

```bash
sudo apt-get install -y \
    debhelper \
    python3-all \
    python3-setuptools \
    python3-build \
    python3-installer \
    python3-wheel \
    dpkg-dev \
    lintian
```

### Manual Build

```bash
# Using the build script
./scripts/build-deb.sh

# Or using make
make deb

# The package will be in dist/deb/
ls -lh dist/deb/
```

### Install Locally

```bash
sudo apt install ./dist/deb/trustget_0.1.0_all.deb
```

### Verify Installation

```bash
sg --version
which sg
dpkg -l | grep trustget
```

### Lint the Package

```bash
lintian dist/deb/trustget_*.deb
```

Fix any errors or warnings before distribution.

### Automatic Build (GitHub Actions)

The `.github/workflows/debian-package.yml` workflow automatically builds Debian packages when you push a version tag.

### Distribution Options

#### Option 1: GitHub Releases

Attach `.deb` files to GitHub Releases (automatic with the workflow).

Users download and install manually:
```bash
wget https://github.com/FaturRachmann/trustget/releases/download/v0.1.0/trustget_0.1.0_all.deb
sudo apt install ./trustget_0.1.0_all.deb
```

#### Option 2: Personal Package Archive (PPA)

For Ubuntu users, create a PPA:

1. Install `debhelper` and packaging tools
2. Create Launchpad account
3. Use `dput` to upload to PPA

#### Option 3: apt repository

Set up your own apt repository:

1. Use `reprepro` or `aptly` to create repo
2. Host on GitHub Pages, S3, or web server
3. Users add your repo to sources.list

Example with `aptly`:

```bash
# Create repo
aptly repo create trustget

# Add package
aptly repo add trustget trustget_0.1.0_all.deb

# Publish
aptly publish repo trustget

# Sync to S3 or web server
```

---

## Version Management

### Update Version

1. Update `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Update `debian/changelog`:
   ```
   trustget (0.2.0) unstable; urgency=medium

     * New features...

    -- TrustGet Team <trustget@example.com>  Date
   ```

3. Commit and tag:
   ```bash
   git add pyproject.toml debian/changelog
   git commit -m "chore: release v0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

---

## Testing Before Release

### Test PyPI Build

```bash
# Build
make build

# Install in virtualenv
python3 -m venv /tmp/test-trustget
source /tmp/test-trustget/bin/activate
pip install dist/trustget-*-py3-none-any.whl

# Test commands
sg --version
sg --help
sg trust https://example.com/file.tar.gz
```

### Test Debian Package

```bash
# Build in clean environment
docker run --rm -it ubuntu:latest bash
apt update && apt install -y python3-pip wget
# ... copy and install .deb package
```

---

## Troubleshooting

### PyPI Upload Fails

**Error: File already exists**
- Increment version number
- Delete file from PyPI (if test)

**Error: Invalid metadata**
- Run `twine check dist/*`
- Fix issues in pyproject.toml

### Debian Build Fails

**Error: Missing build dependencies**
```bash
sudo apt-get build-dep trustget
```

**Error: debian/changelog version mismatch**
- Ensure version matches pyproject.toml
- Run `dpkg-parsechangelog --show version`

### Package Installation Fails

**Error: Dependency issues**
```bash
# Fix broken dependencies
sudo apt --fix-broken install

# Force reinstall
sudo apt install --reinstall trustget
```

---

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `debian/changelog`
- [ ] Update `CHANGELOG.md`
- [ ] Run tests: `make test`
- [ ] Run linter: `make lint`
- [ ] Build package: `make build`
- [ ] Test wheel installation
- [ ] Build Debian package: `make deb`
- [ ] Test .deb installation
- [ ] Commit and tag: `git tag vX.Y.Z`
- [ ] Push tags: `git push origin --tags`
- [ ] Wait for GitHub Actions to complete
- [ ] Verify PyPI publication
- [ ] Verify GitHub Release with .deb attachment
- [ ] Update documentation

---

## Quick Reference

```bash
# Full release process
make release
git tag v0.1.0
git push origin --tags

# This triggers:
# 1. Clean build artifacts
# 2. Build Python package
# 3. Run tests
# 4. Run linter
# 5. GitHub Actions publishes to PyPI
# 6. GitHub Actions builds and attaches .deb package
```

---

## Resources

- [PyPI Documentation](https://packaging.python.org/)
- [Debian Python Policy](https://www.debian.org/doc/packaging-manuals/python-policy/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [twine Documentation](https://twine.readthedocs.io/)
