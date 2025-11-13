# WaddlePerf Usage Guide

**Version**: 2.0
**Last Updated**: November 12, 2025

## Table of Contents

- [Quick Start](#quick-start)
- [managerServer Usage](#managerserver-usage)
- [webClient Usage](#webclient-usage)
- [goClient Usage](#goclient-usage)
- [containerClient Usage](#containerclient-usage)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Starting WaddlePerf (Development)

1. **Clone the repository**
```bash
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings (optional for dev)
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the interfaces**
- **managerServer Frontend**: http://localhost:3000
- **webClient Frontend**: http://localhost:3001
- **Adminer (Database UI)**: http://localhost:8081

5. **Default credentials**
- Username: `admin`
- Password: `admin123`
- **IMPORTANT**: Change this password immediately in production!

### First Steps

1. **Login to managerServer** (http://localhost:3000)
2. **Create a new user** (Users → Add User)
3. **Get your API key** (Profile → API Key)
4. **Run your first test** in webClient (http://localhost:3001)

---

## managerServer Usage

The managerServer provides centralized management, authentication, and statistics visualization.

**Access**: http://localhost:3000 (development) or your configured domain (production)

### Logging In

1. Navigate to the managerServer URL
2. Enter username and password
3. If MFA is enabled, enter your 6-digit TOTP code
4. Click **Login**

After successful login, you'll see the dashboard with system statistics.

---

### User Management

#### Creating Users

**Required Role**: `global_admin` or `ou_admin`

1. Navigate to **Users** in the sidebar
2. Click **Add User** button
3. Fill in the form:
   - **Username**: Unique username (required)
   - **Email**: Valid email address (required)
   - **Password**: Minimum 8 characters (required)
   - **Role**: Select from dropdown
   - **Organization**: Select OU (optional)
4. Click **Create User**

**Roles Explained**:
- **global_admin**: Full access to all features across all OUs
- **global_reporter**: Read-only access across all OUs
- **ou_admin**: Admin access within assigned OU only
- **ou_reporter**: Read-only access within assigned OU only
- **user**: Can execute tests and view own results

#### Viewing Users

1. Navigate to **Users** in the sidebar
2. View list of all users with:
   - Username
   - Email
   - Role
   - Organization
   - Status (active/inactive)
   - Created date
3. Use search box to filter users
4. Click on a user to view details

#### Editing Users

1. Navigate to **Users** → Click on user
2. Click **Edit** button
3. Modify fields:
   - Email
   - Role
   - Organization
   - Active status
4. Click **Save Changes**

**Note**: Username cannot be changed after creation.

#### Changing Passwords

**As Admin**:
1. Navigate to **Users** → Click on user
2. Click **Change Password**
3. Enter new password
4. Click **Update Password**

**As User** (own password):
1. Click **Profile** (top right)
2. Click **Change Password**
3. Enter current password
4. Enter new password twice
5. Click **Update Password**

#### Deleting Users

**Warning**: This action cannot be undone.

1. Navigate to **Users** → Click on user
2. Click **Delete User** button
3. Confirm deletion in dialog
4. User and all their test results will be deleted

---

### Organization Management

#### Creating Organizations

**Required Role**: `global_admin`

1. Navigate to **Organizations** in the sidebar
2. Click **Add Organization** button
3. Fill in the form:
   - **Name**: Organization name (required)
   - **Description**: Optional description
4. Click **Create Organization**

#### Viewing Organizations

1. Navigate to **Organizations** in the sidebar
2. View list with:
   - Name
   - Description
   - User count
   - Created date
3. Click on an organization to view details and users

#### Assigning Users to Organizations

1. Navigate to **Users** → Edit user
2. Select organization from dropdown
3. Click **Save Changes**

---

### Setting Up MFA (Multi-Factor Authentication)

#### Enabling MFA for Your Account

1. Click **Profile** (top right)
2. Click **Setup MFA**
3. Scan QR code with authenticator app:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator
   - 1Password
4. Enter 6-digit code from app
5. Click **Verify and Enable**

**Important**: Save your backup codes in a secure location.

#### Disabling MFA

1. Click **Profile** (top right)
2. Click **Disable MFA**
3. Enter current password
4. Enter 6-digit MFA code
5. Click **Disable**

---

### Managing API Keys

#### Viewing Your API Key

1. Click **Profile** (top right)
2. Your API key is displayed in the **API Key** section
3. Click **Show** to reveal the full key
4. Click **Copy** to copy to clipboard

**Important**: Never share your API key. It provides full access to your account.

#### Regenerating API Key

**Warning**: This will invalidate all existing clients using this key.

1. Click **Profile** (top right)
2. Click **Regenerate API Key**
3. Confirm regeneration
4. Update all clients with new key

---

### Viewing Statistics

#### Dashboard

The dashboard shows:
- **Total Tests**: Count of all tests in last 24 hours
- **Active Devices**: Unique devices that ran tests
- **Average Latency**: Mean latency across all test types
- **Success Rate**: Percentage of successful tests

#### Recent Tests

1. Navigate to **Statistics** → **Recent Tests**
2. View table with:
   - Timestamp
   - Device
   - Test type
   - Target
   - Latency
   - Success/Failure
3. Filter by:
   - Date range
   - Test type
   - Device
   - Success status
4. Export to CSV

#### Device Statistics

1. Navigate to **Statistics** → **Devices**
2. Select device from dropdown
3. View charts:
   - Latency over time
   - Test success rate
   - Tests by type
4. View table with detailed metrics

---

## webClient Usage

The webClient provides a browser-based interface for running network performance tests in real-time.

**Access**: http://localhost:3001 (development) or your configured domain (production)

### Logging In

1. Navigate to the webClient URL
2. Enter username and password (same as managerServer)
3. Click **Login**

**Note**: If authentication is disabled (`AUTH_ENABLED=false`), you can use webClient without logging in.

---

### Speed Test

The webClient includes a built-in browser-based speed test that measures your connection's download, upload, latency, and jitter.

![Speed Test Running](screenshots/webclient-speedtest-running.png)

**To run a speed test:**

1. Navigate to the **Speed Test** tab
2. Click **Start Test**
3. Wait for the test to complete (approximately 15-30 seconds)
4. View results in the modal that appears

The speed test runs in three phases:
1. **Latency**: Measures ping time with 20 samples
2. **Download**: Tests download speed using 6 parallel streams
3. **Upload**: Tests upload speed using 6 parallel streams

![Speed Test Results](screenshots/webclient-speedtest-results.png)

**Speed Test Results Include:**
- **Download Speed**: Maximum throughput in Mbps
- **Upload Speed**: Maximum throughput in Mbps
- **Latency**: Average round-trip time in milliseconds
- **Jitter**: Latency variation in milliseconds

**Use Cases:**
- Verify ISP bandwidth claims
- Diagnose slow connection issues
- Compare performance across locations
- Test before/after network changes

---

### Download Test

The Download Test measures download performance with various file sizes to test sustained transfer speeds.

![Download Test Options](screenshots/webclient-downloadtest-options.png)

**To run a download test:**

1. Navigate to the **Download Test** tab
2. Select file size:
   - **10 MB**: Quick test
   - **50 MB**: Medium test
   - **100 MB**: Standard test (default)
   - **500 MB**: Long test
   - **1 GB**: Extended test
3. Click **Start Test**
4. Monitor real-time speed during download
5. View final results in the modal

![Download Test Results](screenshots/webclient-downloadtest-results.png)

**Download Test Results Include:**
- **File Size**: Total data transferred
- **Duration**: Time taken in seconds
- **Average Speed**: Mean download speed in Mbps
- **Peak Speed**: Maximum download speed achieved

**Use Cases:**
- Test sustained download performance
- Verify large file transfer speeds
- Compare speeds across different file sizes
- Diagnose throttling or speed degradation

---

### Network Tests

The Network Tests tab provides HTTP, TCP, UDP, and ICMP testing capabilities for comprehensive network diagnostics.

![Network Test Options](screenshots/webclient-networktest-options.png)

### Running HTTP/HTTPS Tests

1. Navigate to **HTTP Test** tab
2. Fill in the form:
   - **Target URL**: Full URL including protocol (e.g., https://www.google.com)
   - **Protocol**: Select HTTP version
     - `auto`: Automatic detection (recommended)
     - `http1`: Force HTTP/1.1
     - `http2`: Force HTTP/2
     - `http3`: Force HTTP/3 (QUIC)
   - **Method**: GET, POST, or HEAD
   - **Timeout**: Seconds to wait (default: 30)
3. Click **Run Test**

#### Advanced Options

Click **Show Advanced Options** to configure:
- **Follow Redirects**: Follow HTTP 3xx redirects
- **Verify TLS**: Verify SSL/TLS certificates
- **Max Redirects**: Maximum redirects to follow
- **Custom Headers**: Add custom HTTP headers (JSON format)

#### Understanding Results

After the test completes, you'll see:
- **Status Code**: HTTP response code (200, 404, etc.)
- **Protocol**: Actual protocol used (HTTP/1.1, HTTP/2, etc.)
- **Latency**: Time to first byte (TTFB)
- **DNS Lookup**: Time for DNS resolution
- **TCP Connect**: Time to establish TCP connection
- **TLS Handshake**: Time for TLS negotiation
- **Total Time**: Complete request time
- **Content Size**: Response body size
- **Transfer Speed**: Download speed in MB/s

**Real-Time Chart**: Shows latency over time if running multiple tests.

---

### Running TCP Tests

1. Navigate to **TCP Test** tab
2. Fill in the form:
   - **Target**: Host:port (e.g., www.google.com:443)
   - **Protocol**: Select protocol variant
     - `raw`: Raw TCP connection
     - `tls`: TCP with TLS/SSL
     - `ssh`: SSH connection
   - **Timeout**: Seconds to wait (default: 10)
3. Click **Run Test**

#### Understanding Results

- **Connected**: Whether connection succeeded
- **Latency**: Connection establishment time
- **Handshake Time**: TLS/SSH handshake duration
- **Remote Address**: Connected IP:port
- **Local Address**: Your IP:port
- **TLS Version**: If using TLS (e.g., TLS 1.3)
- **Cipher Suite**: If using TLS

**Use Cases**:
- **Raw TCP**: Test port availability
- **TLS**: Test HTTPS server connectivity
- **SSH**: Test SSH server availability

---

### Running UDP Tests

1. Navigate to **UDP Test** tab
2. Fill in the form:
   - **Target**: Host:port (e.g., 8.8.8.8:53)
   - **Protocol**: Select protocol variant
     - `raw`: Raw UDP packet
     - `dns`: DNS query
   - **DNS Query**: Hostname to resolve (if protocol=dns)
   - **Timeout**: Seconds to wait (default: 5)
3. Click **Run Test**

#### Understanding Results

- **Latency**: Round-trip time
- **Remote Address**: Target IP:port
- **DNS Results**: IP addresses returned (if DNS query)
- **Response**: Response data or status

**Common Use Cases**:
- **DNS Test**: Test DNS server response time
- **UDP Echo**: Test UDP port availability

---

### Running ICMP Tests

1. Navigate to **ICMP Test** tab
2. Fill in the form:
   - **Target**: Hostname or IP (e.g., 8.8.8.8)
   - **Protocol**: Select test type
     - `ping`: Standard ping test
     - `traceroute`: Trace route to target
   - **Count**: Number of packets (default: 4)
   - **Timeout**: Seconds to wait (default: 10)
3. Click **Run Test**

#### Understanding Ping Results

- **Packets Sent**: Number of packets sent
- **Packets Received**: Number of responses
- **Packet Loss**: Percentage lost
- **Latency (avg)**: Average round-trip time
- **Latency (min)**: Minimum RTT
- **Latency (max)**: Maximum RTT
- **Jitter**: Latency variation
- **Std Dev**: Standard deviation

#### Understanding Traceroute Results

- **Hop Count**: Number of hops to target
- **Hop List**: Each router along the path with:
  - Hop number
  - IP address
  - Hostname (if resolvable)
  - Round-trip time

**Real-Time Updates**: Ping tests show live results as packets are sent.

---

### Real-Time Monitoring

The webClient uses WebSocket for real-time test updates.

#### Progress Indicators

- **Progress Bar**: Shows test completion percentage
- **Live Gauge**: Real-time latency visualization
- **Status Messages**: Current test stage

#### Multiple Tests

Run multiple tests in sequence:
1. Enter targets separated by commas
2. Click **Run All Tests**
3. Watch results appear in real-time

#### Exporting Results

1. Complete one or more tests
2. Click **Export Results** button
3. Choose format:
   - **JSON**: Raw data for analysis
   - **CSV**: Import into Excel/Sheets
   - **PDF**: Formatted report

---

## goClient Usage

The goClient is a cross-platform desktop application for running scheduled network tests.

### Installation

#### macOS

```bash
# Download latest release
curl -L https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-darwin-universal -o waddleperf

# Make executable
chmod +x waddleperf

# Move to PATH
sudo mv waddleperf /usr/local/bin/
```

#### Windows

1. Download `waddleperf-windows-amd64.exe` from releases
2. Rename to `waddleperf.exe`
3. Move to `C:\Program Files\WaddlePerf\`
4. Add to PATH in System Environment Variables

#### Linux

```bash
# Download latest release
curl -L https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64 -o waddleperf

# Make executable
chmod +x waddleperf

# Move to PATH
sudo mv waddleperf /usr/local/bin/
```

---

### Initial Setup

#### Generate Configuration File

```bash
waddleperf init-config
```

This creates `~/.waddleperf/config.yaml` with example configuration.

#### Edit Configuration

```bash
# macOS/Linux
nano ~/.waddleperf/config.yaml

# Windows
notepad %USERPROFILE%\.waddleperf\config.yaml
```

**Minimum Required Settings**:
```yaml
manager:
  url: https://your-manager-server.com
  api_key: your-api-key-here

testServer:
  url: https://your-test-server.com

tests:
  http:
    enabled: true
    targets:
      - https://www.google.com
      - https://www.cloudflare.com

schedule:
  enabled: true
  interval_seconds: 300  # Run every 5 minutes
```

---

### CLI Commands

#### Display Device Information

```bash
waddleperf info
```

Output:
```
Device Information:
  Hostname:     my-laptop
  Serial:       abc123def456
  OS:           darwin
  OS Version:   14.1.0
  Architecture: arm64
  CPU Count:    10
  Go Version:   go1.21.5
  IP Address:   192.168.1.100
  MAC Address:  aa:bb:cc:dd:ee:ff
```

#### Run Tests Once

```bash
# Run all enabled tests once
waddleperf run

# With custom config file
waddleperf run --config /path/to/config.yaml

# Verbose output
waddleperf run -v
```

#### Run as Daemon (Background)

```bash
# Start daemon (headless mode)
waddleperf daemon

# With custom config
waddleperf daemon --config /path/to/config.yaml
```

Press `Ctrl+C` to stop.

#### Run with System Tray Icon

```bash
# Start with GUI (macOS/Windows/Linux desktop)
waddleperf tray
```

This shows a system tray icon with:
- **Run Tests Now**: Execute tests immediately
- **View Statistics**: Open web dashboard
- **Settings**: Edit configuration
- **Quit**: Stop application

#### Run Single Test

```bash
# HTTP test
waddleperf test --type http --target https://www.google.com

# TCP test with TLS
waddleperf test --type tcp --target www.google.com:443 --protocol tls

# UDP DNS test
waddleperf test --type udp --target 8.8.8.8:53 --protocol dns

# ICMP ping
waddleperf test --type icmp --target 8.8.8.8
```

#### Version Information

```bash
waddleperf version
```

---

### Configuration File Reference

```yaml
# Manager server configuration
manager:
  url: https://manager.example.com     # Required
  api_key: your-api-key-here           # Required

# Test server configuration
testServer:
  url: https://testserver.example.com  # Required

# Test configurations
tests:
  # HTTP/HTTPS tests
  http:
    enabled: true
    targets:
      - https://www.google.com
      - https://www.cloudflare.com
    protocol: auto  # auto, http1, http2, http3
    timeout: 30
    advanced:
      method: GET
      follow_redirects: true
      verify_tls: true
      max_redirects: 10
      user_agent: "WaddlePerf-GoClient/1.0"

  # TCP tests
  tcp:
    enabled: true
    targets:
      - address: www.google.com:443
        protocol: tls
      - address: github.com:22
        protocol: ssh
    timeout: 10
    advanced:
      verify_tls: true
      keep_alive: true
      retry_on_failure: true
      retry_attempts: 3

  # UDP tests
  udp:
    enabled: false
    targets:
      - address: 8.8.8.8:53
        protocol: dns
        query: google.com
    timeout: 5
    advanced:
      retry_on_failure: true
      retry_attempts: 3

  # ICMP tests
  icmp:
    enabled: true
    targets:
      - 8.8.8.8
      - 1.1.1.1
    protocol: ping  # ping or traceroute
    count: 4
    timeout: 10
    advanced:
      packet_size: 32
      dont_fragment: false
      measure_jitter: true

# Scheduling configuration
schedule:
  interval_seconds: 300  # Run every 5 minutes
  enabled: true
  run_on_startup: true

# Device identification
device:
  serial: auto    # "auto" for auto-detect
  hostname: auto  # "auto" for auto-detect

# Logging configuration
logging:
  level: info     # debug, info, warn, error
  file_path: ""   # Empty = stdout only
  console: true
```

---

### Running as System Service

#### systemd (Linux)

Create `/etc/systemd/system/waddleperf.service`:

```ini
[Unit]
Description=WaddlePerf Network Performance Monitor
After=network.target

[Service]
Type=simple
User=waddleperf
ExecStart=/usr/local/bin/waddleperf daemon
Restart=always
RestartSec=10

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

#### launchd (macOS)

Create `~/Library/LaunchAgents/com.penguintech.waddleperf.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.penguintech.waddleperf</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/waddleperf</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load and start:
```bash
launchctl load ~/Library/LaunchAgents/com.penguintech.waddleperf.plist
launchctl start com.penguintech.waddleperf
```

#### Windows Service

Use NSSM (Non-Sucking Service Manager):

```powershell
# Download and install NSSM
# Install service
nssm install WaddlePerf "C:\Program Files\WaddlePerf\waddleperf.exe" daemon

# Start service
nssm start WaddlePerf
```

---

## containerClient Usage

The containerClient runs automated tests in a Docker container for continuous monitoring.

### Docker Run (Standalone)

```bash
docker run -d \
  --name waddleperf-client \
  -e AUTH_TYPE=apikey \
  -e AUTH_APIKEY=your-api-key-here \
  -e MANAGER_URL=http://your-manager:5000 \
  -e TEST_SERVER_URL=http://your-testserver:8080 \
  -e RUN_SECONDS=300 \
  -e ENABLE_HTTP_TEST=true \
  -e HTTP_TARGETS=https://www.google.com,https://www.cloudflare.com \
  -e DEVICE_SERIAL=docker-client-001 \
  -e DEVICE_HOSTNAME=monitoring-container \
  ghcr.io/penguincloud/waddleperf-containerclient:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  waddleperf-client:
    image: ghcr.io/penguincloud/waddleperf-containerclient:latest
    container_name: waddleperf-client
    environment:
      AUTH_TYPE: apikey
      AUTH_APIKEY: your-api-key-here
      MANAGER_URL: http://manager:5000
      TEST_SERVER_URL: http://testserver:8080
      RUN_SECONDS: 300
      ENABLE_HTTP_TEST: true
      ENABLE_TCP_TEST: true
      ENABLE_UDP_TEST: false
      ENABLE_ICMP_TEST: true
      HTTP_TARGETS: https://www.google.com
      TCP_TARGETS: www.google.com:443
      ICMP_TARGETS: 8.8.8.8
      DEVICE_SERIAL: auto
      DEVICE_HOSTNAME: auto
      LOG_LEVEL: info
    restart: unless-stopped
```

Start:
```bash
docker-compose up -d
```

---

### Kubernetes DaemonSet

Deploy containerClient on every Kubernetes node for distributed monitoring:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: waddleperf-client
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: waddleperf-client
  template:
    metadata:
      labels:
        app: waddleperf-client
    spec:
      containers:
      - name: waddleperf-client
        image: ghcr.io/penguincloud/waddleperf-containerclient:latest
        env:
        - name: AUTH_TYPE
          value: "apikey"
        - name: AUTH_APIKEY
          valueFrom:
            secretKeyRef:
              name: waddleperf-secret
              key: api-key
        - name: MANAGER_URL
          value: "http://waddleperf-manager.monitoring.svc.cluster.local:5000"
        - name: TEST_SERVER_URL
          value: "http://waddleperf-testserver.monitoring.svc.cluster.local:8080"
        - name: RUN_SECONDS
          value: "300"
        - name: ENABLE_HTTP_TEST
          value: "true"
        - name: HTTP_TARGETS
          value: "https://www.google.com"
        - name: DEVICE_SERIAL
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: DEVICE_HOSTNAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 128Mi
```

---

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| AUTH_TYPE | No | none | Authentication type: apikey, jwt, userpass, none |
| AUTH_APIKEY | Conditional | - | API key (if AUTH_TYPE=apikey) |
| AUTH_JWT | Conditional | - | JWT token (if AUTH_TYPE=jwt) |
| AUTH_USER | Conditional | - | Username (if AUTH_TYPE=userpass) |
| AUTH_PASS | Conditional | - | Password (if AUTH_TYPE=userpass) |
| MANAGER_URL | Yes | - | Manager server URL |
| TEST_SERVER_URL | Yes | - | Test server URL |
| RUN_SECONDS | No | 0 | Interval between tests (0=manual only) |
| ENABLE_HTTP_TEST | No | true | Enable HTTP tests |
| ENABLE_TCP_TEST | No | true | Enable TCP tests |
| ENABLE_UDP_TEST | No | true | Enable UDP tests |
| ENABLE_ICMP_TEST | No | true | Enable ICMP tests |
| HTTP_TARGETS | No | - | Comma-separated HTTP targets |
| TCP_TARGETS | No | - | Comma-separated TCP targets |
| UDP_TARGETS | No | - | Comma-separated UDP targets |
| ICMP_TARGETS | No | - | Comma-separated ICMP targets |
| DEVICE_SERIAL | No | auto | Device serial (auto-detect if "auto") |
| DEVICE_HOSTNAME | No | auto | Device hostname (auto-detect if "auto") |
| LOG_LEVEL | No | info | Log level: debug, info, warning, error |

---

### Viewing Logs

```bash
# Docker
docker logs -f waddleperf-client

# Docker Compose
docker-compose logs -f waddleperf-client

# Kubernetes
kubectl logs -f daemonset/waddleperf-client -n monitoring
```

---

## Common Workflows

### Workflow 1: Setting Up Organization-Based Monitoring

1. **Create Organization** in managerServer
   - Navigate to Organizations → Add Organization
   - Name: "Engineering"

2. **Create OU Admin**
   - Navigate to Users → Add User
   - Role: `ou_admin`
   - Organization: Engineering

3. **Create OU Users**
   - Login as OU Admin
   - Create users within Engineering OU
   - Each user gets unique API key

4. **Deploy containerClients**
   - Each department deploys containers with their API keys
   - Tests run automatically every 5 minutes
   - Results visible only to OU members

---

### Workflow 2: Troubleshooting Network Issues

1. **Run HTTP Test** to target website
   - If fails, note error message

2. **Run TCP Test** to same target
   - Tests basic connectivity
   - If fails, network/firewall issue

3. **Run ICMP Ping** to target IP
   - Tests ICMP reachability
   - Shows packet loss and latency

4. **Run Traceroute** to target
   - Identifies where packets are dropped
   - Shows routing path

5. **Review Statistics**
   - Check historical data for patterns
   - Compare with other devices/locations

---

### Workflow 3: Continuous Monitoring Dashboard

1. **Deploy containerClients** in multiple locations
   - Data centers
   - Cloud regions
   - Edge locations

2. **Configure Alert Thresholds** (future feature)
   - Latency > 100ms
   - Packet loss > 1%
   - Success rate < 95%

3. **View Dashboard** in managerServer
   - Real-time statistics by location
   - Latency heatmaps
   - Trend analysis

---

## Troubleshooting

### Cannot Login to managerServer

**Problem**: Invalid credentials error

**Solutions**:
1. Verify username and password are correct
2. Check if user account is active
3. If MFA enabled, ensure TOTP code is current
4. Check server logs: `docker logs waddleperf-manager-api`

---

### Tests Failing with "Unauthorized"

**Problem**: 401 Unauthorized error

**Solutions**:
1. Verify API key is correct
2. Check if JWT token has expired (24 hour default)
3. Ensure authentication is enabled on testServer
4. Regenerate API key if compromised

---

### containerClient Not Running Tests

**Problem**: Container running but no tests executing

**Solutions**:
1. Check `RUN_SECONDS` is greater than 0
2. Verify at least one test type is enabled
3. Check target lists are not empty
4. View logs: `docker logs waddleperf-client`
5. Verify network connectivity to testServer

---

### High Latency Results

**Problem**: Unexpectedly high latency measurements

**Solutions**:
1. Run traceroute to identify bottleneck
2. Compare with ping from command line
3. Check if target server is overloaded
4. Verify network path (VPN, proxy)
5. Test from different device/location

---

### Database Connection Errors

**Problem**: Services cannot connect to database

**Solutions**:
1. Verify MariaDB is running: `docker ps | grep mariadb`
2. Check database credentials in `.env`
3. Ensure network connectivity between containers
4. Check MariaDB logs: `docker logs waddleperf-mariadb`
5. Verify database exists: `docker exec -it waddleperf-mariadb mysql -u root -p`

---

### WebSocket Connection Failed

**Problem**: webClient cannot establish WebSocket connection

**Solutions**:
1. Check if webClient API is running
2. Verify CORS configuration
3. Check browser console for errors
4. Ensure firewall allows WebSocket connections
5. Try using HTTP instead of HTTPS (development only)

---

## Getting Help

- **Documentation**: https://github.com/penguintechinc/WaddlePerf/tree/main/docs
- **Issues**: https://github.com/penguintechinc/WaddlePerf/issues
- **Discussions**: https://github.com/penguintechinc/WaddlePerf/discussions

---

**Copyright © 2025 Penguin Technologies Inc.**
