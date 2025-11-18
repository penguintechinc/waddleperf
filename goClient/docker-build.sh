#!/bin/bash
# Build goClient using Docker with all dependencies

set -e

echo "🐧 WaddlePerf goClient Docker Build"
echo "===================================="
echo ""

# Get version from args or use 'dev'
VERSION=${1:-dev}
export VERSION

# Build the builder image
echo "📦 Building Docker image with dependencies..."
docker build -f Dockerfile.builder -t waddleperf-goclient-builder .

echo ""
echo "🔨 Building goClient binaries for all platforms..."
echo ""

# Run the build
docker run --rm \
    -v $(pwd)/dist:/workspace/dist \
    -e HOME=/tmp \
    -e VERSION="${VERSION}" \
    waddleperf-goclient-builder

echo ""
echo "✅ Build complete!"
echo ""
echo "Built binaries:"
ls -lh dist/

echo ""
echo "To test the Linux build:"
echo "  ./dist/waddleperf-linux-amd64 version"
echo ""
echo "To test the Windows build (on Windows or Wine):"
echo "  ./dist/waddleperf-windows-amd64.exe version"
