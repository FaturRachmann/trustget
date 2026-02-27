# 🚀 PUSH TO GITHUB - Instruksi Lengkap

## Status Saat Ini

✅ Semua file sudah di-commit
✅ Tag v0.1.0 sudah dibuat
⏳ Tinggal push ke GitHub

---

## Langkah 1: Pull Perubahan Terbaru

Karena ada perubahan di remote, pull dulu:

```bash
cd /mnt/d/My\ Project/trustget

# Pull dengan rebase
git pull --rebase origin main
```

**Output yang diharapkan:**
```
Successfully rebased and updated refs/heads/main.
```

---

## Langkah 2: Push Commit

```bash
# Push semua commit ke main
git push origin main
```

**Output yang diharapkan:**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
Writing objects: 100% (XX/XX), done.
Total XX (delta XX), reused XX (delta XX), pack-reused XX
remote: Resolving deltas: 100% (XX/XX), completed with XX local objects
To https://github.com/FaturRachmann/trustget.git
   abc1234..def5678  main -> main
```

---

## Langkah 3: Push Tag Release

```bash
# Push tag v0.1.0 (ini yang trigger workflows)
git push origin v0.1.0
```

**Output yang diharapkan:**
```
Total XX (delta X), reused XX (delta X), pack-reused X
remote: 
remote: Create a pull request for 'v0.1.0' on the GitHub website.
remote: 
remote: View it in a browser at:
remote:   https://github.com/FaturRachmann/trustget/compare/v0.1.0
To https://github.com/FaturRachmann/trustget.git
 * [new tag]         v0.1.0 -> v0.1.0
```

---

## Langkah 4: Monitor Workflows

Setelah push tag, GitHub Actions akan otomatis run:

### 1. Check Actions Tab
```
https://github.com/FaturRachmann/trustget/actions
```

Anda akan lihat:
- ✅ CI workflow (lint, test, build)
- ✅ Publish to PyPI workflow
- ✅ Build Debian Package workflow

### 2. Tunggu Selesai
Biasanya 5-10 menit.

---

## Langkah 5: Verify Release

### PyPI
```
https://pypi.org/project/trustget/
```

Harusnya muncul dengan version 0.1.0

### GitHub Releases
```
https://github.com/FaturRachmann/trustget/releases
```

Harusnya ada release v0.1.0 dengan .deb package attached

---

## Troubleshooting

### Error: "Updates were rejected"

```bash
# Pull dulu
git pull --rebase origin main

# Lalu push lagi
git push origin main
```

### Error: "tag already exists"

```bash
# Delete tag lokal dan remote
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# Buat tag lagi
git tag v0.1.0
git push origin v0.1.0
```

### Workflows Failed

Check logs di:
```
https://github.com/FaturRachmann/trustget/actions
```

Klik workflow yang failed, lihat error di log.

---

## Quick One-Liner

Jika sudah yakin semua OK:

```bash
cd /mnt/d/My\ Project/trustget && git pull --rebase origin main && git push origin main && git push origin v0.1.0
```

---

## ✅ Done!

Setelah semua workflow ✅ green:

```bash
# Test install dari PyPI
pip install trustget
sg --version

# Output: TrustGet, version 0.1.0
```

**Congratulations! 🎉**
