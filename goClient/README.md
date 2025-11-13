# WaddlePerf GoClient

A cross-platform network performance testing client written in Go. Part of the WaddlePerf suite.

## Features

- **Multi-Protocol Support**: HTTP/1.1, HTTP/2, TCP, UDP, ICMP (ping/traceroute)
- **Automated Scheduling**: Run tests periodically on a configurable schedule
- **System Tray Integration**: GUI mode for desktop environments (macOS, Windows, Linux)
- **Daemon Mode**: Headless operation for servers
- **Device Auto-Detection**: Automatically detects hostname, serial number, OS information
- **Result Upload**: Uploads test results to WaddlePerf managerServer via REST API
- **Cross-Platform**: Native binaries for macOS (Intel/ARM), Windows (x64/ARM64), Linux (x64/ARM64)

## Installation

### Pre-built Binaries

Download the latest release for your platform from the [Releases](https://github.com/penguintechinc/WaddlePerf/releases) page:

- **macOS Intel**: `waddleperf-darwin-amd64`
- **macOS Apple Silicon**: `waddleperf-darwin-arm64`
- **Windows x64**: `waddleperf-windows-amd64.exe`
- **Windows ARM64**: `waddleperf-windows-arm64.exe`
- **Linux x64**: `waddleperf-linux-amd64`
- **Linux ARM64**: `waddleperf-linux-arm64`

#### macOS

```bash
# Download the appropriate binary
curl -LO https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-darwin-arm64

# Make it executable
chmod +x waddleperf-darwin-arm64

# Move to PATH (optional)
sudo mv waddleperf-darwin-arm64 /usr/local/bin/waddleperf
```

#### Windows

1. Download `waddleperf-windows-amd64.exe`
2. Move to a directory in your PATH or create a shortcut

#### Linux (Debian/Ubuntu)

```bash
# Download the appropriate binary
curl -LO https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64

# Make it executable
chmod +x waddleperf-linux-amd64

# Move to PATH
sudo mv waddleperf-linux-amd64 /usr/local/bin/waddleperf
```

### Docker

```bash
docker pull ghcr.io/penguintechinc/waddleperf/goclient:latest
```

### Build from Source

```bash
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf/goClient
go build -o waddleperf ./cmd/waddleperf
```

## Configuration

### Generate Example Config

```bash
waddleperf init-config
```

This creates `~/.waddleperf/config.yaml` with example settings.

### Configuration File

Default location: `~/.waddleperf/config.yaml`

```yaml
manager:
  url: https://manager.example.com
  api_key: your-api-key-here

testServer:
  url: https://testserver.example.com

tests:
  http:
    enabled: true
    targets:
      - https://example.com
      - https://google.com
    protocol: auto  # auto, http1, http2, http3
    timeout: 30

  tcp:
    enabled: true
    targets:
      - address: example.com:443
        protocol: tls  # raw, tls, ssh
    timeout: 10

  udp:
    enabled: false
    targets:
      - address: 8.8.8.8:53
        protocol: dns
        query: google.com
    timeout: 5

  icmp:
    enabled: true
    targets:
      - 8.8.8.8
      - 1.1.1.1
    protocol: ping  # ping, traceroute
    count: 4
    timeout: 10

schedule:
  interval_seconds: 300  # Run every 5 minutes
  enabled: true
  run_on_startup: true

device:
  serial: auto    # auto-detect or specify manually
  hostname: auto  # auto-detect or specify manually

logging:
  level: info     # debug, info, warn, error
  file_path: ""   # Empty for no file logging
  console: true
```

## Usage

### Run Tests Once

Execute all enabled tests once and exit:

```bash
waddleperf run
```

### Daemon Mode (Headless)

Run continuously in the background with scheduled tests:

```bash
waddleperf daemon
```

Press `Ctrl+C` to stop.

### System Tray Mode (GUI)

Run with a system tray icon (desktop environments):

```bash
waddleperf tray
```

Features:
- Start/pause monitoring
- Run tests manually
- View statistics
- Quit from tray menu

### Manual Test Commands

Run individual tests without uploading results:

```bash
# HTTP test
waddleperf test --type http --target https://example.com

# HTTP/2 test
waddleperf test --type http --target https://example.com --protocol http2

# TCP test
waddleperf test --type tcp --target example.com:443 --protocol tls

# UDP/DNS test
waddleperf test --type udp --target 8.8.8.8:53 --protocol dns

# ICMP ping test
waddleperf test --type icmp --target 8.8.8.8

# Traceroute
waddleperf test --type icmp --target 8.8.8.8 --protocol traceroute
```

### Device Information

Display system and device information:

```bash
waddleperf info
```

### Version Information

```bash
waddleperf version
```

## Docker Usage

### Run Tests Once

```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  ghcr.io/penguintechinc/waddleperf/goclient:latest \
  run --config /app/config/config.yaml
```

### Run as Daemon

```bash
docker run -d \
  --name waddleperf-client \
  --restart unless-stopped \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  ghcr.io/penguintechinc/waddleperf/goclient:latest \
  daemon --config /app/config/config.yaml
```

### View Logs

```bash
docker logs -f waddleperf-client
```

## Systemd Service (Linux)

Create `/etc/systemd/system/waddleperf.service`:

```ini
[Unit]
Description=WaddlePerf Network Monitoring Client
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=waddleperf
Group=waddleperf
ExecStart=/usr/local/bin/waddleperf daemon --config /etc/waddleperf/config.yaml
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable waddleperf
sudo systemctl start waddleperf
sudo systemctl status waddleperf
```

## macOS Launch Agent

Create `~/Library/LaunchAgents/com.penguintechinc.waddleperf.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.penguintechinc.waddleperf</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/waddleperf</string>
        <string>daemon</string>
        <string>--config</string>
        <string>/Users/YOUR_USERNAME/.waddleperf/config.yaml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/waddleperf.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/waddleperf.err</string>
</dict>
</plist>
```

Load and start:

```bash
launchctl load ~/Library/LaunchAgents/com.penguintechinc.waddleperf.plist
launchctl start com.penguintechinc.waddleperf
```

## Windows Service

Use [NSSM](https://nssm.cc/) to create a Windows service:

```cmd
nssm install WaddlePerf "C:\Program Files\WaddlePerf\waddleperf.exe" daemon --config "C:\ProgramData\WaddlePerf\config.yaml"
nssm start WaddlePerf
```

## Troubleshooting

### Permission Issues (ICMP)

ICMP tests require elevated privileges on some systems:

**Linux/macOS**:
```bash
sudo waddleperf test --type icmp --target 8.8.8.8
```

Or grant capabilities (Linux only):
```bash
sudo setcap cap_net_raw+ep /usr/local/bin/waddleperf
```

**Windows**: Run as Administrator

### Connection Issues

Test connectivity to manager:

```bash
# Check if manager is reachable
curl https://manager.example.com/api/v1/health

# Run with verbose logging
waddleperf run --verbose
```

### Config File Not Found

Specify config explicitly:

```bash
waddleperf run --config /path/to/config.yaml
```

## Development

### Requirements

- Go 1.21 or later
- Make (optional)

### Build

```bash
cd goClient
go build -o waddleperf ./cmd/waddleperf
```

### Cross-Compile

```bash
# macOS ARM64
GOOS=darwin GOARCH=arm64 go build -o waddleperf-darwin-arm64 ./cmd/waddleperf

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -o waddleperf-windows-amd64.exe ./cmd/waddleperf

# Linux ARM64
GOOS=linux GOARCH=arm64 go build -o waddleperf-linux-arm64 ./cmd/waddleperf
```

### Run Tests

```bash
go test -v ./...
```

### Format Code

```bash
go fmt ./...
```

### Lint

```bash
go vet ./...
```

## License

Copyright (c) 2024 Penguin Technologies Inc.

## Support

- Issues: [GitHub Issues](https://github.com/penguintechinc/WaddlePerf/issues)
- Documentation: [WaddlePerf Docs](https://waddleperf.com/docs)
