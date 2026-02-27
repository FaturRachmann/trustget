#!/bin/bash
# Quick Push Script
# Jalankan ini untuk push semua perubahan ke GitHub

set -e

echo "🚀 Pushing changes to GitHub..."
echo ""

# Push commits
echo "📤 Pushing commits..."
git push origin main

echo ""
echo "🏷️  Pushing release tag..."
git push origin v0.1.0

echo ""
echo "✅ Done!"
echo ""
echo "📋 Monitor progress:"
echo "   https://github.com/FaturRachmann/trustget/actions"
echo ""
echo "🎉 After workflows complete:"
echo "   - PyPI: https://pypi.org/project/trustget/"
echo "   - Releases: https://github.com/FaturRachmann/trustget/releases"
