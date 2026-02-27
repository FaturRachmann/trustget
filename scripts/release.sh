#!/bin/bash
# TrustGet Release Script
# Script ini akan commit semua perubahan, tag, dan push ke GitHub

set -e

echo "🚀 TrustGet Release Script"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the trustget directory"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    exit 1
fi

echo "📝 Step 1: Committing changes..."
git add -A
git commit -m "chore: prepare for v0.1.0 release

- Update all repository URLs to FaturRachmann/trustget
- Add PyPI and Debian packaging workflows  
- Add installation and distribution documentation
- Update README with installation instructions
- Configure PyPI Trusted Publishing (OIDC)" || echo "  (No changes to commit or already committed)"

echo ""
echo "📤 Step 2: Pushing to GitHub..."
git push origin main

echo ""
echo "🏷️  Step 3: Creating release tag v0.1.0..."
git tag -a v0.1.0 -m "Release v0.1.0 - Initial release"

echo ""
echo "📤 Step 4: Pushing tag to GitHub..."
git push origin v0.1.0

echo ""
echo "✅ Release initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Check GitHub Actions: https://github.com/FaturRachmann/trustget/actions"
echo "2. Wait for workflows to complete"
echo "3. Verify on PyPI: https://pypi.org/project/trustget/"
echo "4. Download .deb from Releases: https://github.com/FaturRachmann/trustget/releases"
echo ""
echo "🎉 Good luck!"
