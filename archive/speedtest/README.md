# WaddlePerf Speed Test Server (Go)

High-performance network speed testing server built with Go for maximum throughput and minimal latency overhead.

## Features

- **Lightning Fast**: Native Go implementation with zero-copy I/O where possible
- **Multiple Tests**: Ping, Download, Upload, and Jitter measurements
- **Flexible Authentication**: Optional JWT and/or Basic Auth
- **Anonymous Mode**: Can run without authentication for public speed tests
- **CORS Enabled**: Ready for cross-origin requests
- **Docker Ready**: Minimal Alpine-based container (~15MB)

## API Endpoints

### Health Check
```
GET /health
```
Returns server health status (no authentication required).

### Ping Test
```
GET /ping
```
Returns server timestamp with nanosecond precision for latency measurement.

**Response:**
```json
{
  "timestamp": 1699632000000000000,
  "server_time": "2024-11-10T19:00:00.000000000Z",
  "latency": "125.5µs"
}
```

### Download Test
```
GET /download?size=<bytes>
```
Streams random data for download speed testing.

**Parameters:**
- `size` (optional): Number of bytes to download (default: 100MB, max: 1GB)

### Upload Test
```
POST /upload
```
Receives uploaded data and returns throughput statistics.

**Response:**
```json
{
  "bytes_received": 104857600,
  "duration_seconds": 2.54,
  "throughput_mbps": 329.14
}
```

### Jitter Test
```
GET /jitter?samples=<count>
```
Measures packet timing variance.

**Parameters:**
- `samples` (optional): Number of samples to collect (default: 10, max: 100)

**Response:**
```json
{
  "samples": 10,
  "average_latency_ms": 1.23,
  "min_latency_ms": 1.01,
  "max_latency_ms": 1.45,
  "jitter_ms": 0.12,
  "std_dev_ms": 0.15,
  "timestamps": [...]
}
```

## Authentication

The server supports three authentication modes:

### 1. Anonymous Mode (Default)
No authentication required. All endpoints are publicly accessible.

### 2. JWT Authentication
Validates JWT tokens from the Authorization header.

**Environment Variables:**
```bash
JWT_SECRET=your-secret-key-shared-with-manager
```

**Request:**
```bash
curl -H "Authorization: Bearer <jwt-token>" http://localhost:5000/ping
```

### 3. Basic Authentication
HTTP Basic Auth with username/password.

**Environment Variables:**
```bash
SPEEDTEST_USER=admin
SPEEDTEST_PASS=secret
```

**Request:**
```bash
curl -u admin:secret http://localhost:5000/ping
```

### 4. Combined Mode
Both JWT and Basic Auth can be enabled simultaneously. The server will accept either authentication method.

## Configuration

All configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `5000` |
| `JWT_SECRET` | JWT signing secret (enables JWT auth if set) | - |
| `SPEEDTEST_USER` | Basic auth username (requires SPEEDTEST_PASS) | - |
| `SPEEDTEST_PASS` | Basic auth password (requires SPEEDTEST_USER) | - |

## Running with Docker

### Build
```bash
docker build -t waddleperf-speedtest .
```

### Run (Anonymous Mode)
```bash
docker run -p 5000:5000 waddleperf-speedtest
```

### Run (With JWT)
```bash
docker run -p 5000:5000 \
  -e JWT_SECRET=your-secret-key \
  waddleperf-speedtest
```

### Run (With Basic Auth)
```bash
docker run -p 5000:5000 \
  -e SPEEDTEST_USER=admin \
  -e SPEEDTEST_PASS=secret \
  waddleperf-speedtest
```

## Development

### Build Locally
```bash
go build -o speedtest ./cmd/speedtest
```

### Run Locally
```bash
./speedtest
```

### Run Tests
```bash
go test ./...
```

### Test Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Ping test
curl http://localhost:5000/ping

# Download 10MB
curl http://localhost:5000/download?size=10485760 -o /dev/null

# Upload 10MB
dd if=/dev/zero bs=1M count=10 | curl -X POST --data-binary @- http://localhost:5000/upload

# Jitter test
curl http://localhost:5000/jitter?samples=20
```

## Performance Optimizations

- **Zero-allocation handlers**: Minimal memory allocations in hot paths
- **Pre-generated random data**: 1MB random buffer reused for downloads
- **Chunked streaming**: Efficient data transfer with HTTP/1.1 chunking
- **io.Discard for uploads**: Zero-copy upload processing
- **GOMAXPROCS**: Defaults to number of CPU cores
- **Connection pooling**: Reuses connections for better performance

## Security Features

- Non-root user execution (UID 1000)
- Minimal Alpine Linux base image
- No CGO dependencies (fully static binary)
- Constant-time password comparison (timing attack protection)
- Configurable authentication (can be public or private)
- CORS headers for controlled cross-origin access

## Architecture

```
speedtest/
├── cmd/
│   └── speedtest/
│       └── main.go           # Entry point and server setup
├── internal/
│   ├── auth/
│   │   ├── config.go         # Configuration loading
│   │   └── jwt.go            # JWT validation
│   ├── handlers/
│   │   ├── ping.go           # Ping endpoint
│   │   ├── download.go       # Download endpoint
│   │   ├── upload.go         # Upload endpoint
│   │   ├── jitter.go         # Jitter measurement
│   │   └── health.go         # Health check
│   └── middleware/
│       └── auth.go           # Authentication middleware
├── Dockerfile
├── go.mod
└── README.md
```

## Integration with WaddlePerf

This speed test server is designed to integrate with the WaddlePerf ecosystem:

- **Manager API** (Flask): Issues JWT tokens for authenticated clients
- **Client Dashboard** (Node.js + React): Provides UI for running tests
- **Docker Compose**: Orchestrates all services together

The server validates JWTs issued by the manager API, allowing seamless authentication across the platform.

## License

Part of the WaddlePerf project by Penguin Technologies Inc.
