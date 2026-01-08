# WaddlePerf - Claude Code Context

## Project Overview

WaddlePerf is a comprehensive network performance testing and monitoring platform that tests user experience between endpoints. It provides both client and server components for network diagnostics, bandwidth testing, and connectivity analysis.

**Project Features:**
- Multi-tier testing system (Tier 1: Basic, Tier 2: Intermediate, Tier 3: Comprehensive)
- AutoPerf mode for continuous monitoring
- Multi-protocol support (TCP, UDP, HTTP, HTTPS, SSH, DNS)
- S3 integration for results storage
- Geographic IP analysis and performance tracking
- Client and server components for distributed testing
- React-based web UI with role-based access control
- Flask backend with PyDAL database abstraction

## Important Instructions for AI Assistants

### Core Principles
1. **NEVER leave placeholders** - Always fully complete each task without leaving TODO comments, placeholder values, or incomplete implementations
2. **Always test and lint** - Before marking any Go or Docker work as complete:
   - Run `go build` and `go test` for Go code
   - Run `docker build` for Dockerfiles
   - Ensure all linting passes without errors
3. **Verify functionality** - Test that your changes work as intended before moving on
4. **No partial implementations** - If you start a feature, complete it entirely

## Project Structure

### Client Component (`/client/`)
- Python-based with py4web framework
- Web UI at `client/web/apps/`
- Testing tools in `client/bins/`
- Ansible playbooks in `client/jobs/`
- Configuration in `client/vars/base.yml`

### Server Component (`/server/`)
- Python Flask application
- Web services in `server/web/`
- Server utilities in `server/bins/`
- LibreSpeed integration in `server/libs/speedtest/`
- Configuration in `server/vars/base.yml`

### Go Clients (`/go-client/`)
- Currently in development phase
- Will provide native desktop clients
- Requires multi-platform builds (Linux, Windows, macOS)

## Technology Stack

### Core Technologies
- **Languages**: Python 3.13, Go 1.23.x
- **Web Framework**: Flask 3.0+ with Flask-Security-Too
- **Frontend**: React 18+ with Tailwind CSS
- **Database**: PostgreSQL (default), MySQL, SQLite via DB_TYPE
- **ORM**: SQLAlchemy (initialization), PyDAL (day-to-day operations)
- **Infrastructure**: Docker, Docker Compose, MariaDB Galera Cluster (optional)
- **CI/CD**: GitHub Actions with comprehensive security scanning
- **Protocol Support**: REST API, gRPC, HTTP/1.1, HTTP/2, HTTP/3 (QUIC)

### Project Structure
```
WaddlePerf/
├── client/               # Python client component (py4web)
│   ├── web/apps/        # Web UI
│   ├── bins/            # Testing tools
│   ├── jobs/            # Ansible playbooks
│   └── vars/            # Configuration
├── server/              # Python Flask server
│   ├── web/             # Web services
│   ├── bins/            # Server utilities
│   ├── libs/            # Libraries (speedtest, etc.)
│   └── vars/            # Configuration
├── go-client/           # Go native clients
│   ├── cmd/             # Main applications
│   ├── internal/        # Internal packages
│   └── pkg/             # Public packages
├── shared/              # Shared libraries
│   ├── py_libs/         # Python shared (pip installable)
│   ├── go_libs/         # Go shared (Go module)
│   └── node_libs/       # TypeScript shared (npm package)
├── k8s/                 # Kubernetes deployment
├── tests/               # Test suites
├── docs/                # Documentation
└── docker-compose.yml   # Production environment
```

## License & Legal

**License File**: `LICENSE.md` (located at project root)

**License Type**: Limited AGPL-3.0 with commercial use restrictions and Contributor Employer Exception

The `LICENSE.md` file is located at the project root following industry standards. This project uses a modified AGPL-3.0 license with additional exceptions for commercial use and special provisions for companies employing contributors.

- **License Server**: https://license.penguintech.io
- **Company Website**: www.penguintech.io
- **Support**: support@penguintech.io

---

**Current Version**: See `.version` file
**Last Updated**: 2025-12-18
**Maintained by**: Penguin Tech Inc
