# Building goClient

The goClient is a cross-platform desktop application with GUI support (system tray). This document describes how to build it for multiple platforms using Docker.

## Quick Start

Build all platforms using Docker:

```bash
./docker-build.sh [version]
```

Example:
```bash
./docker-build.sh 4.0.0
```

This will create binaries in the `dist/` directory:
- `waddleperf-linux-amd64` - Linux 64-bit (with GUI)
- `waddleperf-linux-arm64` - Linux ARM64 (no GUI)
- `waddleperf-windows-amd64.exe` - Windows 64-bit (with GUI)
- `SHA256SUMS` - Checksum file

## Platform Support

| Platform | Architecture | GUI Support | Build Method |
|----------|-------------|-------------|--------------|
| Linux | AMD64 | ✅ Yes (systray) | Docker |
| Linux | ARM64 | ❌ No | Docker |
| Windows | AMD64 | ✅ Yes (systray) | Docker (mingw cross-compile) |
| macOS | AMD64 | ⚠️ Requires macOS | Native only |
| macOS | ARM64 (M1/M2) | ⚠️ Requires macOS | Native only |

### macOS Builds

macOS builds cannot be cross-compiled from Linux due to licensing and toolchain restrictions. To build for macOS:

1. On a Mac, install Go 1.23+
2. Run:
   ```bash
   # AMD64 (Intel Macs)
   GOOS=darwin GOARCH=amd64 go build -ldflags="-w -s" -o waddleperf-darwin-amd64 ./cmd/waddleperf

   # ARM64 (Apple Silicon M1/M2)
   GOOS=darwin GOARCH=arm64 go build -ldflags="-w -s" -o waddleperf-darwin-arm64 ./cmd/waddleperf

   # Universal binary (both architectures)
   lipo -create waddleperf-darwin-amd64 waddleperf-darwin-arm64 -output waddleperf-darwin-universal
   ```

## Docker Build Process

### Building the Builder Image

The builder image contains all dependencies needed for cross-platform builds:

```bash
docker build -f Dockerfile.builder -t waddleperf-goclient-builder .
```

This creates a ~2.2GB image with:
- Go 1.23
- GCC and G++ (Linux native compilation)
- mingw-w64 (Windows cross-compilation)
- libayatana-appindicator3-dev (Linux system tray)
- libgtk-3-dev (GTK3 GUI toolkit)
- X11 development libraries

### Running the Build

```bash
docker run --rm \
    -v $(pwd)/dist:/workspace/dist \
    -e HOME=/tmp \
    -e VERSION="4.0.0" \
    waddleperf-goclient-builder
```

Parameters:
- `-v $(pwd)/dist:/workspace/dist` - Mount dist directory for output
- `-e HOME=/tmp` - Set HOME for Go build cache
- `-e VERSION="4.0.0"` - Version number to embed in binaries

### Build Output

Built binaries include embedded version information:

```bash
$ ./dist/waddleperf-linux-amd64 version
WaddlePerf goClient v4.0.0
Build Time: 2025-11-18T03:57:02Z
Git Commit: unknown
```

## Manual Builds (Without Docker)

### Linux (Native)

Requirements:
- Go 1.23+
- gcc, g++, make, pkg-config
- libayatana-appindicator3-dev
- libgtk-3-dev

Build:
```bash
go build -ldflags="-w -s" -o waddleperf ./cmd/waddleperf
```

### Windows (Cross-compile from Linux)

Requirements:
- Go 1.23+
- mingw-w64

Build:
```bash
GOOS=windows GOARCH=amd64 \
  CGO_ENABLED=1 \
  CC=x86_64-w64-mingw32-gcc \
  CXX=x86_64-w64-mingw32-g++ \
  go build -ldflags="-w -s -H windowsgui" -o waddleperf.exe ./cmd/waddleperf
```

### Linux ARM64 (No GUI)

Build without CGO (no system tray support):
```bash
GOOS=linux GOARCH=arm64 \
  CGO_ENABLED=0 \
  go build -ldflags="-w -s" -tags nogui -o waddleperf-arm64 ./cmd/waddleperf
```

## Dependencies

### Go Modules

The goClient uses these key dependencies:

- `github.com/getlantern/systray` - System tray integration
- `github.com/go-ping/ping` - ICMP ping functionality
- `github.com/spf13/cobra` - CLI framework
- `gopkg.in/yaml.v3` - Configuration file parsing

Run `go mod download` to fetch all dependencies.

### System Libraries (Linux)

For system tray support:
- **Debian/Ubuntu**: `sudo apt-get install libayatana-appindicator3-dev libgtk-3-dev`
- **Fedora/RHEL**: `sudo dnf install libappindicator-gtk3-devel gtk3-devel`
- **Arch**: `sudo pacman -S libappindicator-gtk3 gtk3`

## Testing Builds

### Linux
```bash
./dist/waddleperf-linux-amd64 version
./dist/waddleperf-linux-amd64 test --target google.com
```

### Windows
```bash
# On Windows
waddleperf-windows-amd64.exe version

# On Linux with Wine
wine dist/waddleperf-windows-amd64.exe version
```

## Build Artifacts

After building, you'll have:

```
dist/
├── waddleperf-linux-amd64          # 9.0 MB - Linux binary with GUI
├── waddleperf-linux-arm64          # 8.2 MB - Linux ARM binary (no GUI)
├── waddleperf-windows-amd64.exe    # 9.3 MB - Windows binary with GUI
└── SHA256SUMS                       # Checksums for verification
```

Verify checksums:
```bash
cd dist && sha256sum -c SHA256SUMS
```

## Troubleshooting

### CGO Errors on macOS/Windows

If you get CGO-related errors, ensure:
1. CGO_ENABLED=1 is set
2. Appropriate C compiler is available (mingw for Windows cross-compile)
3. System libraries are installed (Linux only)

### System Tray Not Working

If the system tray doesn't appear:
- **Linux**: Ensure your desktop environment supports system trays (GNOME requires an extension)
- **Windows**: Check that the systray is not hidden in the overflow area
- **No GUI**: Use `--no-gui` flag or build with `CGO_ENABLED=0`

### Permission Denied

If you get "permission denied" when running binaries:
```bash
chmod +x dist/waddleperf-*
```

## CI/CD Integration

### GitHub Actions Example

``
`yaml
name: Build goClient

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          cd goClient
          docker build -f Dockerfile.builder -t waddleperf-goclient-builder .

      - name: Build binaries
        run: |
          cd goClient
          ./docker-build.sh ${{ github.ref_name }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: goClient-binaries
          path: goClient/dist/*
```

## Additional Resources

- **Go Cross-Compilation**: https://go.dev/doc/install/source#environment
- **systray Library**: https://github.com/getlantern/systray
- **mingw-w64**: https://www.mingw-w64.org/

## Support

For build issues, please open an issue on GitHub with:
- Your OS and version
- Go version (`go version`)
- Full build output
- Error messages
