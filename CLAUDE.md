# WaddlePerf - Claude Code Context

## Project Overview

WaddlePerf is a comprehensive network performance testing and monitoring platform that tests user experience between endpoints. It provides both client and server components for network diagnostics, bandwidth testing, and connectivity analysis.

**Key Capabilities:**
- Speed Testing: Browser-based bandwidth testing (download, upload, latency, jitter)
- Network Diagnostics: Comprehensive HTTP/TCP/UDP/ICMP testing
- Real-Time Monitoring: WebSocket-based live test progress
- Multi-Client Support: Web, Desktop (Go), Container clients
- Centralized Management: User authentication, API keys, organization units
- Historical Analytics: Database-backed results storage and analysis

## Architecture

WaddlePerf 4.x uses a modern, containerized architecture with multiple components:

### Components

- **testServer** (Go) - High-performance test execution engine (single container)
- **managerServer** (Python/Flask + React) - Centralized management and authentication (split: API + frontend containers)
- **webClient** (Python/Flask + React) - Browser-based testing interface (split: API + frontend containers)
- **containerClient** (Python) - Automated container-based testing (single container)
- **go-client** (Go) - Cross-platform desktop client with GUI support (Linux, Windows, macOS)
- **MariaDB Galera Cluster** - High-availability database with multi-master replication

## Technology Stack

### Languages & Frameworks
- **Python 3.13**: Web applications, APIs, business logic
- **Go 1.23**: High-performance test execution, desktop clients
- **React 18**: Frontend applications (managerServer, webClient)
- **Flask 3.0**: Backend API services
- **Node.js 20**: Frontend build tooling

### Infrastructure & DevOps
- **Containers**: Docker with multi-stage builds, Docker Compose
- **CI/CD**: GitHub Actions with comprehensive pipelines
- **Database**: MariaDB 11.2 with Galera Cluster support
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Logging**: Structured logging with configurable levels

## Essential Documentation

📚 **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup guide
- Prerequisites and installation
- Environment configuration
- Starting services locally
- Development workflow and mock data injection

📚 **[docs/TESTING.md](docs/TESTING.md)** - Testing & validation guide
- Mock data scripts
- Smoke tests (mandatory)
- Unit, integration, and E2E testing
- Performance testing procedures

📚 **[docs/PRE_COMMIT.md](docs/PRE_COMMIT.md)** - Pre-commit checklist
- Required steps before every commit
- Smoke tests (mandatory, <2 min)
- Security scanning requirements
- Build and test verification

📚 **[docs/DATABASE.md](docs/DATABASE.md)** - MariaDB Galera compatibility guide
- Critical restrictions and requirements
- Schema design best practices
- Transaction and replication limitations

📚 **[docs/STANDARDS.md](docs/STANDARDS.md)** - Development standards
- API versioning
- Database standards
- Docker standards
- Testing requirements

## Important Instructions for AI Assistants

### Core Principles
1. **NEVER leave placeholders** - Always fully complete each task without leaving TODO comments, placeholder values, or incomplete implementations
2. **Always test and lint** - Before marking any Go or Docker work as complete:
   - Run `go build` and `go test` for Go code
   - Run `docker build` for Dockerfiles
   - Ensure all linting passes without errors
3. **Verify functionality** - Test that your changes work as intended before moving on
4. **No partial implementations** - If you start a feature, complete it entirely
5. **NEVER commit automatically** - Only commit when explicitly requested by the user

## Project Structure

```
WaddlePerf/
├── .github/workflows/        # CI/CD pipelines for each container
├── testServer/              # Go high-performance test execution engine
├── managerServer/           # Management server (API + frontend)
│   ├── api/                 # Flask backend
│   └── frontend/            # React frontend
├── webClient/               # Web-based test client (API + frontend)
│   ├── api/                 # Flask backend
│   └── frontend/            # React frontend
├── containerClient/         # Automated container-based testing
├── go-client/               # Cross-platform desktop client
├── database/                # Database schemas and migrations
│   ├── schema.sql           # Core schema
│   └── seeds/               # Development seed data
├── docs/                    # Documentation
│   ├── DEVELOPMENT.md       # Development setup
│   ├── TESTING.md           # Testing guide
│   ├── PRE_COMMIT.md        # Pre-commit checklist
│   ├── DATABASE.md          # Database guide
│   └── STANDARDS.md         # Development standards
├── docker-compose.yml       # Production environment
└── .version                 # Version tracking
```

## MariaDB Galera Cluster Compatibility

⚠️ **CRITICAL**: Before making ANY database or schema changes, read [docs/DATABASE.md](docs/DATABASE.md) for complete Galera restrictions and best practices.

### Key Requirements
- **PRIMARY KEYS REQUIRED**: All tables MUST have a primary key
- **Use InnoDB only**: All tables must use InnoDB storage engine
- **AVOID explicit table locks**: Do NOT use `LOCK TABLES`
- **NO distributed transactions (XA)**: Do not use XA transactions
- **Row-based replication only**: `binlog_format` must be ROW
- **Auto-increment gaps**: Do NOT rely on sequential auto-increment values

## Docker Image Standards

- **Python services**: MUST use Debian-based images (e.g., `python:3.13-slim`)
  - Alpine images cause compilation issues with packages like gevent, bcrypt, cryptography
- **Go services**: Use Debian for build, Alpine for runtime
  - Build stage: `golang:1.23-bookworm`
  - Runtime stage: `alpine:3.19`
- **Frontend services**: Use Alpine nginx (e.g., `nginx:alpine`)
- **Node.js build stages**: Use Alpine (e.g., `node:20-alpine`)

## Development Workflow

### Quick Start

```bash
# Start all services
docker-compose up -d

# Rebuild after code changes (ALWAYS use --build)
docker-compose down && docker-compose up -d --build

# Rebuild single service
docker-compose up -d --build <service-name>

# View logs
docker-compose logs -f <service-name>
```

### Testing Requirements

**For Python Code:**
- Use async and threading where possible for performance
- Verify Docker containers build and run successfully
- Run linting: `flake8`, `black`, `isort`, `mypy`

**For Go Code:**
- Run `go mod tidy` to manage dependencies
- Run `go fmt` for code formatting
- Run `go vet` for static analysis
- Run `go test ./...` for all tests
- Run `gosec ./...` for security scanning

**For Docker:**
- **ALWAYS** use `--no-cache` flag when building Docker images
- **ALWAYS** use `docker-compose down -v` when rebuilding clusters
- Test builds with `docker-compose build --no-cache`
- Verify containers run with `docker-compose up -d`

### Pre-Commit Requirements

**CRITICAL: Run before every commit:**

```bash
./scripts/pre-commit/pre-commit.sh
```

This includes:
1. Linters (Python, Go, Node.js)
2. Security scans (gosec, bandit, npm audit)
3. No secrets check
4. Build & run verification
5. Smoke tests (mandatory)
6. Unit and integration tests
7. Docker debian-slim validation

📚 See [docs/PRE_COMMIT.md](docs/PRE_COMMIT.md) for complete checklist

## Network Ports

- **8080**: testServer (HTTP API)
- **5000**: managerServer API (Flask)
- **50051**: managerServer gRPC
- **3000**: managerServer frontend (React)
- **5001**: webClient API (Flask)
- **3001**: webClient frontend (React)
- **3306**: MariaDB (internal)
- **8081**: Adminer (database UI)

## Version Management

**Format**: `vMajor.Minor.Patch.build`

**Update Commands**:
```bash
./scripts/version/update-version.sh          # Increment build timestamp
./scripts/version/update-version.sh patch    # Increment patch version
./scripts/version/update-version.sh minor    # Increment minor version
./scripts/version/update-version.sh major    # Increment major version
```

## Git Workflow

- **NEVER commit automatically** unless explicitly requested by user
- **NEVER push to remote repositories** under any circumstances
- Always use feature branches for development
- Run pre-commit checks before every commit
- Update documentation with code changes

## Key Features to Maintain

- AutoPerf mode for continuous monitoring
- Multi-tier escalation testing
- S3 integration for results storage
- Geographic IP analysis
- Multiple protocol support (TCP, UDP, HTTP, HTTPS, ICMP)
- Real-time WebSocket progress updates
- JWT-based authentication
- API key management
- Organization unit support

## Security Considerations

- Containers run as non-root user
- SSL/TLS certificate management
- Input validation for all user inputs
- No hardcoded secrets or credentials
- Environment variables for configuration
- JWT and MFA authentication
- CodeQL security analysis required

## Common Tasks

### Adding a New Test Tool
1. Add implementation to appropriate service
2. Update API endpoints
3. Add frontend UI components
4. Update database schema if needed
5. Test in Docker container
6. Document usage

### Updating Dependencies
1. **Python**: Update requirements.txt
2. **Go**: Update go.mod and run `go mod tidy`
3. **Node.js**: Update package.json and package-lock.json
4. **Docker**: Update base images in Dockerfiles
5. Run security scans: `npm audit`, `gosec`, `bandit`
6. Test all changes thoroughly

### Creating a Release
1. Update version with `./scripts/version/update-version.sh`
2. Update RELEASE_NOTES.md
3. Test all components
4. Run full pre-commit validation
5. Tag release in git
6. GitHub Actions will build and publish

## Contact and Support

- **Organization**: Penguin Technologies Inc.
- **Repository**: https://github.com/penguintechinc/WaddlePerf
- **Issues**: Report at GitHub Issues page
- **Support**: support@penguintech.io

---

**Remember**: Always complete tasks fully, test thoroughly, run pre-commit checks, and never leave placeholders!
