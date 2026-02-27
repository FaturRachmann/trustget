#!/bin/bash
# TrustGet v0.2.0 Release Script
# Script ini akan release versi baru dengan semua enhancements

set -e

echo "🚀 TrustGet v0.2.0 Release Script"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the trustget directory"
    exit 1
fi

echo "📝 Step 1: Update version to 0.2.0"
echo ""

# Update version in pyproject.toml
sed -i 's/^version = "0.1.0"/version = "0.2.0"/' pyproject.toml

# Update debian changelog
cat > debian/changelog << EOF
trustget (0.2.0) unstable; urgency=medium

  * Enhanced GitHub URL detection (support all GitHub URLs)
  * Richer trust analysis output with repo info
  * Risk-based recommendations and security tips
  * Better visual output with emojis
  * Fixed CI workflows (mypy non-blocking, twine dependency)
  * Improved test coverage (102/102 tests passing)

 -- TrustGet Team <trustget@example.com>  $(date -R)
EOF

echo "✅ Version updated to 0.2.0"
echo ""

echo "📝 Step 2: Commit release preparation"
git add -A
git commit -m "chore: prepare for v0.2.0 release" || echo "  (Already committed)"
echo ""

echo "📤 Step 3: Push to GitHub"
git push origin main
echo ""

echo "🏷️  Step 4: Create and push release tag"
git tag -a v0.2.0 -m "Release v0.2.0 - Enhanced GitHub support and trust analysis"
git push origin v0.2.0
echo ""

echo "✅ Release v0.2.0 initiated!"
echo ""
echo "📋 Monitor progress:"
echo "   https://github.com/FaturRachmann/trustget/actions"
echo ""
echo "🎉 After workflows complete:"
echo "   - PyPI: https://pypi.org/project/trustget/"
echo "   - Releases: https://github.com/FaturRachmann/trustget/releases"
echo ""
echo "📦 Install new version:"
echo "   pip install --upgrade trustget"
echo ""
