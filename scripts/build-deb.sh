#!/bin/bash
# Build TrustGet Debian package locally
# Usage: ./scripts/build-deb.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔐 Building TrustGet Debian Package..."

# Check for required tools
for cmd in dpkg-buildpackage python3 pip3; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: $cmd is not installed"
        exit 1
    fi
done

cd "$PROJECT_DIR"

# Install Python build dependencies
echo "📦 Installing Python build dependencies..."
pip3 install build wheel

# Build Python wheel
echo "🔨 Building Python wheel..."
python3 -m build --wheel

# Install deb build tools
echo "📦 Installing Debian build tools..."
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

# Get version from pyproject.toml
VERSION=$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)
echo "📋 Building version: $VERSION"

# Update changelog
cat > debian/changelog << EOF
trustget ($VERSION) unstable; urgency=medium

  * Release version $VERSION

 -- TrustGet Team <trustget@example.com>  $(date -R)
EOF

# Build Debian package
echo "🏗️  Building Debian package..."
dpkg-buildpackage -us -uc -b

# Move package to dist
mkdir -p dist/deb
mv ../trustget_*.deb dist/deb/ 2>/dev/null || true

echo ""
echo "✅ Build complete!"
echo "📦 Debian package: dist/deb/trustget_${VERSION}_all.deb"
echo ""
echo "To install:"
echo "  sudo apt install ./dist/deb/trustget_${VERSION}_all.deb"
