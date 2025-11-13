```
     ___     
    (.  \    
     \   |   ___   ___   _| | _| | | |  ___   ___    ___   _ _   ___ 
      >  )  |Wad| |ddl| |dl| |dl| | | ||Per| |rfo|  |rma| |nce| |   |
     /  /    \_/   \_/   \_/  \_/  |_/  \_/   \_/    \_/  \_\_\ |___|
    /  /     Waddle fast, test faster! 🚀
   (  (      Network Performance Testing at Penguin Speed
    \ \_     
     \__)    
```

<div align="center">
  <img src="waddleperf-penguin.svg" alt="WaddlePerf Northern Rockhopper Penguin Mascot" width="200" height="200">
</div>

# WaddlePerf

This is a project to allow for complete testing of user experience from one system to another.

This can be an endpoint testing it's internet connectivity, testing latency between regions, or even within cluster.

## Features

- **Speed Testing**: Browser-based bandwidth testing (download, upload, latency, jitter)
- **Network Diagnostics**: Comprehensive HTTP/TCP/UDP/ICMP testing
- **Real-Time Monitoring**: WebSocket-based live test progress
- **Multi-Client Support**: Web, Desktop (Go), Container clients
- **Centralized Management**: User authentication, API keys, organization units
- **Historical Analytics**: Database-backed results storage and analysis

## Screenshots

<div align="center">

### Network Testing Interface
<a href="docs/screenshots/webclient-networktest-options.png" target="_blank">
  <img src="docs/screenshots/webclient-networktest-options.png" alt="Network Testing Interface" width="800">
</a>

*Configure and run HTTP, TCP, UDP, and ICMP tests with real-time results*

---

### Speed Test - Running
<a href="docs/screenshots/webclient-speedtest-running.png" target="_blank">
  <img src="docs/screenshots/webclient-speedtest-running.png" alt="Speed Test Running" width="800">
</a>

*Real-time bandwidth testing with live speed measurements*

---

### Speed Test - Results
<a href="docs/screenshots/webclient-speedtest-results.png" target="_blank">
  <img src="docs/screenshots/webclient-speedtest-results.png" alt="Speed Test Results" width="800">
</a>

*Comprehensive results showing download, upload, latency, and jitter*

---

### Download Test - Options
<a href="docs/screenshots/webclient-downloadtest-options.png" target="_blank">
  <img src="docs/screenshots/webclient-downloadtest-options.png" alt="Download Test Options" width="800">
</a>

*Select file size for sustained download performance testing*

---

### Download Test - Results
<a href="docs/screenshots/webclient-downloadtest-results.png" target="_blank">
  <img src="docs/screenshots/webclient-downloadtest-results.png" alt="Download Test Results" width="800">
</a>

*Detailed download metrics including average and peak speeds*

</div>

## Architecture

WaddlePerf 2.0 uses a modern, containerized architecture with multiple components:

### Components

- **testServer** (Go) - High-performance test execution engine
- **managerServer** (Python/Flask + React) - Centralized management and authentication
- **webClient** (Python/Flask + React) - Browser-based testing interface
- **containerClient** (Python) - Automated container-based testing
- **goClient** (Go) - Cross-platform desktop client (in development)
- **MariaDB** - Centralized database for user management and test results

### Test Types

WaddlePerf implements all network testing natively without external dependencies:

- **HTTP/HTTPS Tests**: HTTP/1.1, HTTP/2, and HTTP/3 support with detailed timing metrics
- **TCP Tests**: Raw TCP, TLS/SSL, and SSH connection testing
- **UDP Tests**: Raw UDP packets and DNS query testing
- **ICMP Tests**: Ping and traceroute with comprehensive latency analysis
- **Speed Tests**: Browser-based bandwidth testing with multi-stream downloads/uploads
- **Download Tests**: Sustained transfer performance measurement

All tests provide:
- Real-time progress updates via WebSocket
- Detailed timing breakdowns (DNS, TCP connect, TLS handshake, etc.)
- Packet loss and jitter measurements
- Historical result storage and analysis

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 4GB RAM minimum
- Ports 3000, 3001, 5000, 5001, 8080, 8081 available

### Installation

```bash
# Clone the repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Access the Interfaces

- **webClient**: http://localhost:3001 (browser-based testing)
- **managerServer**: http://localhost:3000 (user management & analytics)
- **Adminer**: http://localhost:8081 (database management)

**Default Credentials:**
- Username: `admin`
- Password: `ChangeMeAlready`
- **⚠️ Change immediately in production!**

## Documentation

📚 **[Complete Usage Guide](docs/USAGE.md)** - Detailed instructions for all features

📖 **Other Documentation:**
- [Installation Guide](docs/INSTALLATION.md) - Deployment instructions
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Contributing Guide](docs/CONTRIBUTING.md) - Development guidelines
- [API Documentation](docs/API.md) - REST API reference
- [License](docs/LICENSE.md) - Terms and conditions

## Results Storage

Test results are stored in:
- **Database** - MariaDB for centralized storage and querying
- **Web Interface** - Real-time display in browser
- **API** - REST endpoints for programmatic access
- **S3** (optional) - Long-term archival storage
- **Syslog** (coming soon) - Integration with logging infrastructure

## Security

All packages are scanned by:
- socket.dev
- Snyk
- GitHub Security Advisories

**Found a security issue?**
Please report it to: security@penguintech.io

## Support

- **Issues**: [GitHub Issues](https://github.com/penguintechinc/WaddlePerf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/penguintechinc/WaddlePerf/discussions)
- **Documentation**: [docs/](docs/)

## Production Deployment

⚠️ Please use named stable releases (not `main` or `latest`) for production deployments unless instructed by Penguin Technologies Inc.

Check [releases page](https://github.com/penguintechinc/WaddlePerf/releases) for stable versions.

## License

See [docs/LICENSE.md](docs/LICENSE.md) for full license terms.

## Contributors

- **PenguinzTech** - Original author and maintainer

---

**Copyright © 2025 Penguin Technologies Inc.**
