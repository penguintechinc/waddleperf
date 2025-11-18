#!/bin/bash
# Build goClient for all platforms
set -e

VERSION=${VERSION:-"dev"}
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

LDFLAGS="-w -s -X main.Version=${VERSION} -X main.BuildTime=${BUILD_TIME} -X main.GitCommit=${GIT_COMMIT}"

echo "🐧 Building WaddlePerf goClient"
echo "Version: ${VERSION}"
echo "Build Time: ${BUILD_TIME}"
echo "Git Commit: ${GIT_COMMIT}"
echo ""

# Create output directory
mkdir -p dist

# Linux AMD64 (with GUI support)
echo "📦 Building for Linux AMD64..."
GOOS=linux GOARCH=amd64 CGO_ENABLED=1 go build \
    -ldflags="${LDFLAGS}" \
    -o dist/waddleperf-linux-amd64 \
    ./cmd/waddleperf
echo "✓ Linux AMD64 build complete"

# Linux ARM64 (without GUI - cross-compilation is complex)
echo "📦 Building for Linux ARM64 (no GUI)..."
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build \
    -ldflags="${LDFLAGS}" \
    -tags nogui \
    -o dist/waddleperf-linux-arm64 \
    ./cmd/waddleperf
echo "✓ Linux ARM64 build complete (no GUI)"

# Windows AMD64 (with GUI support via mingw)
echo "📦 Building for Windows AMD64..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=1 CC=x86_64-w64-mingw32-gcc CXX=x86_64-w64-mingw32-g++ go build \
    -ldflags="${LDFLAGS} -H windowsgui" \
    -o dist/waddleperf-windows-amd64.exe \
    ./cmd/waddleperf
echo "✓ Windows AMD64 build complete"

# macOS builds require osxcross or building on macOS
echo "⚠️  macOS builds require building on macOS or using osxcross"
echo "   Skipping macOS builds in Docker environment"

# Create checksums
echo ""
echo "📝 Generating checksums..."
cd dist
sha256sum * > SHA256SUMS
cd ..

echo ""
echo "✅ Build complete! Binaries available in dist/"
ls -lh dist/
