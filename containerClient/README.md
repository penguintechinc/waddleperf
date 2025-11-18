# WaddlePerf containerClient

Python 3.13-based network performance testing client for WaddlePerf. Implements HTTP, TCP, UDP, and ICMP tests with multi-threading support and automatic result uploading to the managerServer.

## Features

- **Multi-Protocol Testing**: HTTP/HTTPS, TCP (raw/TLS/SSH), UDP (raw/DNS), ICMP ping
- **Async/Threaded**: High-performance async implementation with concurrent test execution
- **Auto-Scheduling**: Built-in cron-like scheduler for continuous monitoring
- **Authentication**: Supports JWT, API key, and Basic auth
- **Device Auto-Detection**: Automatically detects OS, hostname, and device serial
- **Result Upload**: Automatically uploads results to managerServer API
- **Docker Ready**: Multi-arch support (amd64/arm64) with non-root execution

## Quick Start

### Using Docker

```bash
# Run once with default targets
docker run --rm ghcr.io/penguintechinc/waddleperf/containerclient:latest \
  --test-type all

# Run with scheduler (every 90 seconds)
docker run -d \
  -e MANAGER_URL=https://manager.example.com \
  -e AUTH_TYPE=apikey \
  -e AUTH_APIKEY=your-api-key-here \
  -e RUN_SECONDS=90 \
  -e HTTP_TARGETS=https://example.com,https://google.com \
  -e ICMP_TARGETS=8.8.8.8,1.1.1.1 \
  ghcr.io/penguintechinc/waddleperf/containerclient:latest

# Run specific test type
docker run --rm \
  -e HTTP_TARGETS=https://example.com \
  ghcr.io/penguintechinc/waddleperf/containerclient:latest \
  --test-type http --http-target https://example.com
```

### Using Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run once
python client.py --test-type all

# Run with scheduler
python client.py --schedule

# Run specific test
python client.py --test-type http --http-target https://example.com
```

## Environment Variables

### Authentication

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `AUTH_TYPE` | Authentication type: `none`, `jwt`, `apikey`, `userpass` | `none` | `apikey` |
| `AUTH_JWT` | JWT token (when AUTH_TYPE=jwt) | - | `eyJhbGc...` |
| `AUTH_APIKEY` | API key (when AUTH_TYPE=apikey) | - | `abc123...` |
| `AUTH_USER` | Username (when AUTH_TYPE=userpass) | - | `admin` |
| `AUTH_PASS` | Password (when AUTH_TYPE=userpass) | - | `password` |

### Server Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MANAGER_URL` | managerServer API URL | `http://localhost:8080` | `https://manager.example.com` |
| `TEST_SERVER_URL` | testServer URL (future use) | `http://localhost:8081` | `https://tests.example.com` |

### Scheduling

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RUN_SECONDS` | Auto-run interval in seconds (0=disabled) | `0` | `90` |

### Test Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_HTTP_TEST` | Enable HTTP tests | `true` | `false` |
| `ENABLE_TCP_TEST` | Enable TCP tests | `true` | `false` |
| `ENABLE_UDP_TEST` | Enable UDP tests | `true` | `false` |
| `ENABLE_ICMP_TEST` | Enable ICMP tests | `true` | `false` |

### Test Targets

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HTTP_TARGETS` | Comma-separated HTTP/HTTPS URLs | `https://www.google.com` | `https://example.com,https://google.com` |
| `TCP_TARGETS` | Comma-separated TCP targets | - | `host:22,ssh://server:22,tls://host:443` |
| `UDP_TARGETS` | Comma-separated UDP targets | - | `host:2000,dns://example.com` |
| `ICMP_TARGETS` | Comma-separated ICMP targets | `8.8.8.8` | `8.8.8.8,1.1.1.1,example.com` |

### Device Information

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DEVICE_SERIAL` | Device serial number (auto-detected if not set) | auto | `abc123` |
| `DEVICE_HOSTNAME` | Device hostname (auto-detected if not set) | auto | `my-device` |

## CLI Usage

```bash
# Show help
python client.py --help

# Run all tests once
python client.py --test-type all

# Run specific test type
python client.py --test-type http
python client.py --test-type tcp
python client.py --test-type udp
python client.py --test-type icmp

# Run with specific target
python client.py --test-type http --http-target https://example.com
python client.py --test-type tcp --tcp-target ssh://server:22
python client.py --test-type udp --udp-target dns://example.com
python client.py --test-type icmp --icmp-target 8.8.8.8

# Run with config file
python client.py --config-file /path/to/config.json

# Run in scheduler mode
python client.py --schedule

# Set log level
python client.py --log-level DEBUG --test-type all
```

## Configuration File Format

JSON configuration file example:

```json
{
  "auth_type": "apikey",
  "auth_apikey": "your-api-key-here",
  "manager_url": "https://manager.example.com",
  "test_server_url": "https://tests.example.com",
  "run_seconds": 90,
  "enable_http_test": true,
  "enable_tcp_test": true,
  "enable_udp_test": false,
  "enable_icmp_test": true,
  "http_targets": [
    "https://example.com",
    "https://google.com"
  ],
  "tcp_targets": [
    "ssh://server.example.com:22",
    "tls://api.example.com:443"
  ],
  "icmp_targets": [
    "8.8.8.8",
    "1.1.1.1"
  ]
}
```

## Test Types

### HTTP/HTTPS Tests

Tests HTTP/HTTPS connectivity with detailed timing metrics:

- DNS lookup time
- Connection establishment time
- Transfer time
- Total request time
- Throughput calculation
- HTTP status code
- Protocol version detection (HTTP/1.1, HTTP/2, HTTP/3)

Target format: `https://example.com` or `http://example.com`

### TCP Tests

Tests TCP connectivity with support for:

- **Raw TCP**: Basic TCP connection
- **TCP+TLS**: Encrypted TCP connection
- **SSH**: SSH banner exchange

Target formats:
- `host:port` - Raw TCP
- `tls://host:port` - TCP+TLS
- `ssh://host:port` - SSH (default port 22)

### UDP Tests

Tests UDP connectivity with:

- **Raw UDP**: UDP ping with RTT measurement
- **DNS**: DNS query timing

Target formats:
- `host:port` - Raw UDP ping
- `dns://hostname` - DNS query (uses system resolver)

### ICMP Tests

Tests ICMP ping with:

- Round-trip time (RTT) measurement
- Jitter calculation
- Packet loss percentage
- Multiple ping support

Target format: `hostname` or `IP address`

## Docker Compose Example

```yaml
version: '3.8'

services:
  waddleperf-client:
    image: ghcr.io/penguintechinc/waddleperf/containerclient:latest
    restart: unless-stopped
    environment:
      - MANAGER_URL=https://manager.example.com
      - AUTH_TYPE=apikey
      - AUTH_APIKEY=${WADDLEPERF_API_KEY}
      - RUN_SECONDS=300
      - ENABLE_HTTP_TEST=true
      - ENABLE_TCP_TEST=true
      - ENABLE_UDP_TEST=true
      - ENABLE_ICMP_TEST=true
      - HTTP_TARGETS=https://example.com,https://google.com
      - TCP_TARGETS=ssh://server.example.com:22
      - ICMP_TARGETS=8.8.8.8,1.1.1.1
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

## Building from Source

```bash
# Build Docker image
cd containerClient
docker build -t waddleperf-containerclient .

# Multi-arch build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t waddleperf-containerclient:latest \
  .
```

## Architecture

```
containerClient/
├── client.py              # Main client application
├── tests/                 # Test implementations
│   ├── __init__.py       # Test module exports
│   ├── http_test.py      # HTTP/HTTPS tests
│   ├── tcp_test.py       # TCP tests
│   ├── udp_test.py       # UDP tests
│   └── icmp_test.py      # ICMP tests
├── requirements.txt       # Python dependencies
├── Dockerfile            # Multi-arch Docker image
└── README.md             # This file
```

## Result Format

Results are uploaded to managerServer in the following format:

```json
{
  "test_type": "http",
  "protocol_detail": "http/2",
  "target_host": "example.com",
  "target_ip": "93.184.216.34",
  "device_serial": "abc123...",
  "device_hostname": "my-device",
  "device_os": "Linux",
  "device_os_version": "5.15.0",
  "latency_ms": 45.23,
  "throughput_mbps": 12.5,
  "success": true,
  "timestamp": "2025-11-12T15:30:00Z",
  "raw_results": {
    "http_code": 200,
    "content_length": 1234,
    "time_namelookup": 5.2,
    "time_connect": 15.3,
    "time_transfer": 24.73
  }
}
```

## Troubleshooting

### Permission Errors

ICMP tests require `CAP_NET_RAW` capability. If running in Docker:

```bash
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...
```

### Connection Refused

If tests fail with "connection refused":
- Verify target hosts are reachable
- Check firewall rules
- Ensure correct ports are specified

### Upload Failures

If results fail to upload:
- Verify `MANAGER_URL` is correct
- Check authentication credentials
- Ensure managerServer is running and accessible
- Review logs with `--log-level DEBUG`

## Performance Tuning

### Concurrent Tests

By default, tests run concurrently by protocol type. To reduce load:

```bash
# Disable some test types
docker run -e ENABLE_TCP_TEST=false -e ENABLE_UDP_TEST=false ...
```

### Scheduling Interval

Adjust `RUN_SECONDS` based on your monitoring needs:

```bash
# Every 5 minutes
-e RUN_SECONDS=300

# Every 30 seconds
-e RUN_SECONDS=30

# Run once (manual mode)
-e RUN_SECONDS=0
```

## Security

- Container runs as non-root user (UID 1000)
- No sensitive data in logs
- Supports encrypted communication (HTTPS, TLS)
- Authentication credentials via environment variables only
- No hardcoded secrets

## License

Part of the WaddlePerf project by Penguin Technologies Inc.

## Support

For issues and questions:
- GitHub Issues: https://github.com/penguintechinc/WaddlePerf/issues
- Documentation: https://github.com/penguintechinc/WaddlePerf
