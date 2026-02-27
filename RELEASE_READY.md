# 🚀 TrustGet - Ready for Release

Project TrustGet sudah siap untuk dirilis di PyPI dan sebagai Debian package!

## ✅ Yang Sudah Dikerjakan

### 1. Repository GitHub Updated
- Semua URL sudah指向 repository Anda: `https://github.com/FaturRachmann/trustget`
- Badge dan links di README sudah benar
- User-Agent di semua module sudah diupdate

### 2. PyPI Distribution Ready
- `pyproject.toml` sudah dikonfigurasi dengan benar
- Workflow GitHub Actions: `.github/workflows/pypi-release.yml`
- Build test berhasil: `dist/trustget-0.1.0-py3-none-any.whl`

### 3. Debian Package Ready
- Directory `debian/` lengkap dengan semua file yang diperlukan
- Workflow GitHub Actions: `.github/workflows/debian-package.yml`
- Build script: `scripts/build-deb.sh`

### 4. Documentation Lengkap
- `README.md` - Updated dengan instalasi instructions
- `docs/INSTALL.md` - Panduan instalasi lengkap untuk users
- `docs/DISTRIBUTION.md` - Panduan distribusi untuk developers
- `Makefile` - Build commands yang mudah digunakan

### 5. Code Quality
- ✅ 101/102 tests passing
- ✅ Ruff linting passed
- ✅ Build wheel dan sdist berhasil

---

## 📦 Cara Release ke PyPI

### Step 1: Buat PyPI Account
1. Kunjungi https://pypi.org/account/
2. Buat account
3. Generate API token di Settings → API tokens

### Step 2: Add GitHub Secret
1. Buka repository di GitHub
2. Settings → Secrets and variables → Actions
3. New repository secret
4. Name: `PYPI_TOKEN`
5. Value: API token dari PyPI

### Step 3: Tag dan Push
```bash
# Pastikan semua perubahan di-commit
git add .
git commit -m "chore: prepare for release v0.1.0"

# Tag versi
git tag v0.1.0

# Push ke GitHub (termasuk tags)
git push origin main --tags
```

### Step 4: Tunggu GitHub Actions
Workflow akan otomatis:
1. Build package (wheel + sdist)
2. Upload ke PyPI

### Step 5: Verify
```bash
# Cek di PyPI
https://pypi.org/project/trustget/

# Install dan test
pip install trustget
sg --version
```

---

## 📦 Cara Release Debian Package

### Otomatis (via GitHub Actions)
Workflow `.github/workflows/debian-package.yml` akan otomatis build .deb saat push tag.

Package akan tersedia di:
```
https://github.com/FaturRachmann/trustget/releases/download/v0.1.0/trustget_0.1.0_all.deb
```

### Manual Build
```bash
# Install dependencies
sudo apt-get install -y debhelper python3-all python3-build

# Build
./scripts/build-deb.sh
# atau
make deb

# Package ada di dist/deb/
ls -lh dist/deb/
```

---

## 🎯 Quick Commands

```bash
# Build Python package
make build

# Build Debian package
make deb

# Run tests
make test

# Run linter
make lint

# Full release build
make release
```

---

## 📋 Checklist Release

- [x] Update semua URL ke repository GitHub
- [x] Build test lokal
- [x] Test install dari wheel
- [x] Documentation lengkap
- [x] GitHub Actions workflows
- [ ] Create PyPI account (manual)
- [ ] Add PYPI_TOKEN secret (manual)
- [ ] Push tag v0.1.0 (manual)
- [ ] Verify di PyPI (manual)

---

## 🔗 Links Penting

- **Repository**: https://github.com/FaturRachmann/trustget
- **PyPI (akan datang)**: https://pypi.org/project/trustget/
- **GitHub Actions**: https://github.com/FaturRachmann/trustget/actions
- **Issues**: https://github.com/FaturRachmann/trustget/issues

---

## 🎉 Next Steps

1. **Commit semua perubahan**
   ```bash
   git add .
   git commit -m "chore: prepare for v0.1.0 release"
   ```

2. **Push ke GitHub**
   ```bash
   git push origin main
   ```

3. **Setup PyPI account** (jika belum)

4. **Add GitHub secret** `PYPI_TOKEN`

5. **Tag dan release**
   ```bash
   git tag v0.1.0
   git push origin --tags
   ```

6. **Tunggu workflow selesai** dan cek di PyPI!

---

**Good luck! 🚀**
