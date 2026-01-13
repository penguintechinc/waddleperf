<div align="center">

# 🐧 WaddlePerf

### Network Performance Testing at Penguin Speed

*Waddle fast, test faster!* 🚀

<img src="waddleperf-penguin.svg" alt="WaddlePerf Northern Rockhopper Penguin Mascot" width="200" height="200">

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](docs/LICENSE.md)
[![Version](https://img.shields.io/badge/version-4.0.0-green.svg)](https://github.com/penguintechinc/WaddlePerf/releases)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](docker-compose.yml)

</div>

---

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

WaddlePerf 4.x uses a modern, containerized architecture with multiple components:

### Components

- **testServer** (Go) - High-performance test execution engine (single container)
- **managerServer** (Python/Flask + React) - Centralized management and authentication (split: API + frontend containers)
- **webClient** (Python/Flask + React) - Browser-based testing interface (split: API + frontend containers)
- **containerClient** (Python) - Automated container-based testing (single container)
- **goClient** (Go) - Cross-platform desktop client with GUI support (Linux, Windows, macOS)
- **MariaDB Galera Cluster** - High-availability database with multi-master replication
  - Supports multi-write nodes for active-active configuration
  - Automatic failover and synchronous replication
  - Horizontal scaling for increased capacity

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

### High Availability

WaddlePerf is designed for enterprise-grade reliability:

- **MariaDB Galera Cluster Support**
  - Multi-master replication with active-active writes
  - Synchronous replication ensures zero data loss
  - Automatic node failover with no manual intervention
  - Scales horizontally by adding more nodes

- **Distributed Architecture**
  - Multiple testServer instances can run in parallel
  - Load balancing across managerServer nodes
  - Containerized components for easy orchestration
  - Kubernetes-ready deployment manifests

- **Data Persistence**
  - Persistent volumes for database storage
  - Optional S3 integration for long-term archival
  - Backup and restore procedures documented

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
<<<<<<< HEAD
- Password: `ChangeMeAlready`
=======
- Password: `admin123`
>>>>>>> main
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

<<<<<<< HEAD
=======
**License Highlights:**
- **Personal & Internal Use**: Free under AGPL-3.0
- **Commercial Use**: Requires commercial license
- **SaaS Deployment**: Requires commercial license if providing as a service

### Contributor Employer Exception (GPL-2.0 Grant)

Companies employing official contributors receive GPL-2.0 access to community features:

- **Perpetual for Contributed Versions**: GPL-2.0 rights to versions where the employee contributed remain valid permanently, even after the employee leaves the company
- **Attribution Required**: Employee must be credited in CONTRIBUTORS, AUTHORS, commit history, or release notes
- **Future Versions**: New versions released after employment ends require standard licensing
- **Community Only**: Enterprise features still require a commercial license

This exception rewards contributors by providing lasting fair use rights to their employers.

>>>>>>> main
See [docs/LICENSE.md](docs/LICENSE.md) for full license terms.

## Contributors

- **PenguinzTech** - Original author and maintainer

---

**Copyright © 2025 Penguin Technologies Inc.**
