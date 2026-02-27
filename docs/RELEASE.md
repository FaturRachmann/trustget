# 🚀 TrustGet Release Guide

Panduan lengkap untuk release TrustGet v0.1.0 ke PyPI dan GitHub.

---

## ✅ Pre-Release Checklist

- [x] PyPI account created
- [x] Trusted publisher configured di PyPI
- [x] Status: **Pending** (normal, akan aktif setelah release pertama)
- [x] GitHub repository: `FaturRachmann/trustget`
- [x] Workflows configured
- [x] Documentation complete

---

## 📦 Release Steps

### Option 1: Menggunakan Release Script (Recommended)

```bash
# Clone repository (jika belum)
git clone https://github.com/FaturRachmann/trustget.git
cd trustget

# Jalankan release script
./scripts/release.sh
```

Script akan otomatis:
1. Commit semua perubahan
2. Push ke GitHub
3. Create tag v0.1.0
4. Push tag ke GitHub

---

### Option 2: Manual Steps

```bash
# 1. Clone dan checkout
git clone https://github.com/FaturRachmann/trustget.git
cd trustget
git checkout main

# 2. Commit semua perubahan
git add -A
git commit -m "chore: prepare for v0.1.0 release"

# 3. Push ke GitHub
git push origin main

# 4. Create release tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial release"

# 5. Push tag
git push origin v0.1.0
```

---

## 🔍 What Happens Next

Setelah push tag, GitHub Actions akan otomatis:

### Workflow 1: PyPI Release (`.github/workflows/pypi-release.yml`)

```
✅ Build Python package (wheel + sdist)
✅ Validate metadata
✅ Upload to PyPI using Trusted Publishing
```

**Status**: https://github.com/FaturRachmann/trustget/actions/workflows/pypi-release.yml

### Workflow 2: Debian Package (`.github/workflows/debian-package.yml`)

```
✅ Install build dependencies
✅ Build Python wheel
✅ Build Debian package (.deb)
✅ Attach to GitHub Release
```

**Status**: https://github.com/FaturRachmann/trustget/actions/workflows/debian-package.yml

---

## ⏱️ Expected Timeline

| Step | Duration |
|------|----------|
| GitHub Actions start | ~30 seconds |
| PyPI build & upload | 2-5 minutes |
| Debian package build | 3-7 minutes |
| **Total** | **~5-10 minutes** |

---

## ✅ Verification

### 1. Check GitHub Actions Status

```bash
# Kunjungi
https://github.com/FaturRachmann/trustget/actions
```

Tunggu sampai semua workflows ✅ (green checkmark)

### 2. Verify PyPI Publication

```bash
# Check di browser
https://pypi.org/project/trustget/

# Or install and test
pip install trustget
sg --version
```

Expected output:
```
TrustGet, version 0.1.0
```

### 3. Verify GitHub Release

```bash
# Check releases page
https://github.com/FaturRachmann/trustget/releases
```

Should have:
- ✅ Release tag v0.1.0
- ✅ `.deb` package attached
- ✅ Release notes (auto-generated)

### 4. Test Debian Package

```bash
# Download .deb
wget https://github.com/FaturRachmann/trustget/releases/download/v0.1.0/trustget_0.1.0_all.deb

# Install
sudo apt install ./trustget_0.1.0_all.deb

# Verify
sg --version
```

---

## 🔧 Troubleshooting

### Workflow Failed

**Check logs:**
```
https://github.com/FaturRachmann/trustget/actions
```

**Common issues:**
- Python version mismatch → Check `pyproject.toml`
- Missing dependencies → Update `dependencies` in `pyproject.toml`
- Build errors → Run `make build` locally first

### PyPI Upload Failed

**Trusted Publishing Error:**
- Verify PyPI trusted publisher setup
- Check environment name matches (`pypi`)
- Ensure workflow name is `pypi-release.yml`

**Already Exists:**
- Version already used → Increment version in `pyproject.toml`
- Delete from PyPI (if test) → https://pypi.org/manage/project/trustget/releases/

### Debian Build Failed

**Missing dependencies:**
```bash
sudo apt-get install -y debhelper python3-all python3-build
```

**Version mismatch:**
- Ensure `debian/changelog` version matches `pyproject.toml`

---

## 📋 Post-Release Tasks

### 1. Update Documentation

- [ ] Add release notes to `CHANGELOG.md`
- [ ] Update README if needed
- [ ] Announce in GitHub Discussions

### 2. Test Installation

```bash
# Fresh install test
pip install trustget
sg --help
sg trust https://example.com/file.tar.gz
```

### 3. Monitor

- [ ] Watch for issues on GitHub
- [ ] Check PyPI download stats
- [ ] Monitor GitHub Insights

---

## 🎯 Quick Reference

### Full Release Command

```bash
# One-liner (if already on main branch)
git add -A && git commit -m "chore: release v0.1.0" && git tag v0.1.0 && git push origin main --tags
```

### Check Status

```bash
# GitHub Actions
curl -s https://api.github.com/repos/FaturRachmann/trustget/actions/runs | jq '.workflow_runs[0].status'

# PyPI availability
curl -s https://pypi.org/pypi/trustget/json | jq '.info.version'
```

---

## 📞 Getting Help

If you encounter issues:

1. **Check GitHub Issues**: https://github.com/FaturRachmann/trustget/issues
2. **GitHub Discussions**: https://github.com/FaturRachmann/trustget/discussions
3. **PyPI Help**: https://pypi.org/help/

---

## 🎉 Success!

After successful release:

```
✅ PyPI: https://pypi.org/project/trustget/
✅ GitHub Release: https://github.com/FaturRachmann/trustget/releases
✅ Users can install via:
   - pip install trustget
   - apt install ./trustget_0.1.0_all.deb
```

**Congratulations! 🎊**
