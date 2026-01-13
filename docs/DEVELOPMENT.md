# WaddlePerf Local Development Guide

Complete guide to setting up a local WaddlePerf development environment, running components locally, and following the development workflow for multi-component performance monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Component Startup](#component-startup)
4. [Development Workflow](#development-workflow)
5. [Testing Your Changes](#testing-your-changes)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: macOS 12+, Linux (Ubuntu 20.04+), or Windows 10+ with WSL2
- **Docker Desktop**: 4.0+ or Docker Engine 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Python**: 3.13+ (for server and client components)
- **Go**: 1.23+ (for testServer and goClient)
- **Node.js**: 18+ (for WebUI)

### Optional Tools

- **Docker Buildx**: For multi-architecture builds
- **Helm**: For Kubernetes deployments (production)
- **kubectl**: For Kubernetes clusters

### Installation

**macOS (Homebrew)**:
```bash
brew install docker docker-compose git python@3.13 node go
brew install --cask docker
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git python3.13 nodejs golang-1.23
sudo usermod -aG docker $USER  # Allow docker without sudo
newgrp docker
```

**Verify Installation**:
```bash
docker --version       # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
git --version
python3 --version     # Python 3.13+
node --version        # Node.js 18+
go version            # Go 1.23+
```

---

## Initial Setup

### Clone Repository

```bash
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf
```

### Install Dependencies

```bash
# Install all project dependencies
make setup
```

This runs:
1. Python environment setup (venv, requirements)
2. Node.js dependency installation (npm install)
3. Go module setup (go mod download)
4. Pre-commit hooks installation
5. Database initialization

### Environment Configuration

Copy and customize environment files:

```bash
# Copy example environment files
cp .env.example .env
cp .env.local.example .env.local  # Optional: local overrides
```

**Key Environment Variables**:
```bash
# Database Configuration
DB_TYPE=mysql              # mysql, postgres, sqlite
DB_HOST=localhost
DB_PORT=3306
DB_NAME=waddleperf_dev
DB_USER=root
DB_PASSWORD=waddleperf
DB_CHARSET=utf8mb4

# Release Mode (Development - all features available)
RELEASE_MODE=false
LICENSE_KEY=not-required-in-dev

# Port Configuration
MANAGER_API_PORT=5000      # Manager backend
MANAGER_UI_PORT=3000       # Manager UI
WEBCLIENT_API_PORT=5001    # WebClient backend
WEBCLIENT_UI_PORT=3001     # WebClient UI
TESTSERVER_PORT=8080       # testServer
ADMINER_PORT=8081          # Database UI

# Authentication
JWT_SECRET=dev-secret-key-change-in-prod
API_KEY_SALT=dev-salt-change-in-prod

# Performance Testing
ENABLE_SPEED_TEST=true
ENABLE_NETWORK_DIAGNOSTICS=true
ENABLE_AUTOPERF=false      # AutoPerf mode for continuous testing

# Storage (Optional: S3 integration)
S3_ENABLED=false
S3_BUCKET=waddleperf-results
S3_REGION=us-east-1
```

### Database Initialization

```bash
# Create database and run migrations
make db-init

# Seed with mock data (3-4 items per test type)
make seed-mock-data

# Verify database connection
make db-health
```

---

## Component Startup

### All Components (Recommended for Development)

```bash
# Start all components
make dev

# This starts:
# - MariaDB database (port 3306)
# - testServer (port 8080)
# - managerServer API (port 5000)
# - managerServer UI (port 3000)
# - webClient API (port 5001)
# - webClient UI (port 3001)
# - Adminer (port 8081)

# Access the application:
# Manager UI:    http://localhost:3000
# WebClient UI:  http://localhost:3001
# testServer:    http://localhost:8080
# Adminer:       http://localhost:8081 (database UI)
```

### Individual Component Management

**Start specific components**:
```bash
# Start only testServer
docker-compose up -d testserver

# Start manager components
docker-compose up -d manager-api manager-ui

# Start webClient components
docker-compose up -d webclient-api webclient-ui

# Start database only
docker-compose up -d mariadb
```

**View service logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f testserver

# Last 100 lines, follow new entries
docker-compose logs -f --tail=100 manager-api
```

**Stop services**:
```bash
# Stop all services (keep data)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart services
docker-compose restart

# Rebuild and restart (apply code changes)
docker-compose down && docker-compose up -d --build
```

### Development Docker Compose Files

- **`docker-compose.yml`**: Production-ready configuration
- **`docker-compose.dev.yml`**: Local development (hot-reload, debug ports)

Use dev version locally:
```bash
docker-compose -f docker-compose.dev.yml up
```

---

## Development Workflow

### 1. Start Development Environment

```bash
make dev           # Start all services
make seed-mock-data # Populate with test data
```

### 2. Make Code Changes

Edit files in your editor. Services with auto-reload:

- **Python (Flask)**: Reload on file save (FLASK_DEBUG=1)
- **Node.js (React)**: Hot reload (Webpack dev server)
- **Go**: Requires restart (`docker-compose restart testserver`)

### 3. Verify Changes

```bash
# Quick smoke tests
make smoke-test

# Run linters
make lint

# Run unit tests (specific service)
cd testserver && go test ./...

# Run all tests
make test
```

### 4. Populate Mock Data for Feature Testing

After implementing a new test type or feature:

```bash
# Create mock data script (e.g., for new test type)
cat > scripts/mock-data/seed-new-tests.py << 'EOF'
from dal import DAL

def seed_new_tests():
    db = DAL('mysql://user:password@localhost/waddleperf_dev')

    tests = [
        {"name": "Test Type A", "protocol": "http", "enabled": True},
        {"name": "Test Type B", "protocol": "tcp", "enabled": True},
        {"name": "Test Type C", "protocol": "udp", "enabled": True},
    ]

    for test in tests:
        db.test_configs.insert(**test)

    print(f"✓ Seeded {len(tests)} test configurations")

if __name__ == "__main__":
    seed_new_tests()
EOF

# Run the mock data script
python scripts/mock-data/seed-new-tests.py

# Add to seed-all.py orchestrator
echo "from seed_new_tests import seed_new_tests; seed_new_tests()" >> scripts/mock-data/seed-all.py
```

### 5. Run Pre-Commit Checklist

Before committing, run the comprehensive pre-commit script:

```bash
./scripts/pre-commit/pre-commit.sh
```

**Steps**:
1. Linters (flake8, black, eslint, golangci-lint, etc.)
2. Security scans (bandit, npm audit, gosec)
3. Secret detection (no API keys, passwords, tokens)
4. Build & Run (build all containers, verify runtime)
5. Smoke tests (build, health checks, UI loads)
6. Unit tests (isolated component testing)
7. Integration tests (component interactions)
8. Version update & Docker standards

### 6. Testing & Validation

```bash
# Smoke tests only (fast, <2 min)
make smoke-test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# All tests
make test

# Specific test file
pytest testserver/tests/unit/test_protocol.py

# Go client tests
cd goClient && go test ./...
```

### 7. Create Pull Request

Once tests pass:

```bash
# Push branch
git push origin feature-branch-name

# Create PR via GitHub CLI
gh pr create --title "Brief feature description" \
  --body "Detailed description of changes"

# Or use web UI: https://github.com/penguintechinc/WaddlePerf/compare
```

---

## Testing Your Changes

### Multi-Component Testing

WaddlePerf requires testing across multiple components:

```bash
# Test testServer (Go)
cd testserver && go test -v ./...

# Test manager API (Python)
cd managerServer && pytest tests/unit/

# Test webClient API (Python)
cd webClient && pytest tests/unit/

# Test manager UI (Node.js)
cd managerServer/ui && npm test

# Test webClient UI (Node.js)
cd webClient/ui && npm test

# Test goClient (Go)
cd goClient && go test ./...
```

### Integration Testing

Test component interactions:

```bash
# Manager API → Database
make test-manager-db

# WebClient API → testServer
make test-webclient-testserver

# UI → API endpoints
make test-ui-api

# All integration tests
make test-integration
```

---

## Common Tasks

### Adding a New Test Protocol

1. **Implement in testServer** (Go):
```bash
cd testserver
# Add new protocol handler in internal/protocols/
# Add tests in tests/unit/

# Test locally
go test -v ./internal/protocols/

# Test in Docker
docker-compose up -d --build testserver
docker-compose exec testserver go test ./...
```

2. **Add UI support** (React):
```bash
cd managerServer/ui
# Add test configuration form in components/
npm test  # Run tests
npm run build  # Verify build
```

3. **Add backend support** (Flask):
```bash
cd managerServer
# Add API endpoint for new protocol
pytest tests/unit/  # Run tests
```

### Adding a Python Dependency

```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> managerServer/requirements.txt

# Rebuild container
docker-compose up -d --build manager-api

# Verify import works
docker-compose exec manager-api python -c "import new_package"
```

### Adding a Node.js Dependency

```bash
# Add to package.json
cd managerServer/ui
npm install new-package

# Rebuild WebUI container
docker-compose up -d --build manager-ui

# Verify in running container
docker-compose exec manager-ui npm list new-package
```

### Debugging a Service

**View logs in real-time**:
```bash
docker-compose logs -f testserver
```

**Access container shell**:
```bash
# Go service
docker-compose exec testserver bash

# Python service
docker-compose exec manager-api bash

# Node.js service
docker-compose exec manager-ui sh
```

**Execute commands in container**:
```bash
# Run Go test
docker-compose exec testserver go test ./...

# Check service health
docker-compose exec testserver curl http://localhost:8080/health
```

### Database Operations

**Connect to database**:
```bash
# MariaDB
docker-compose exec mariadb mysql -u root -p

# View schema
SHOW TABLES;
DESCRIBE test_results;

# View sample data
SELECT * FROM test_results LIMIT 5;
```

**Reset database**:
```bash
# Full reset (deletes all data)
docker-compose down -v
make db-init
make seed-mock-data
```

### Multi-Tier Testing Validation

Verify multi-tier testing implementation:

```bash
# Tier 1: Basic connectivity
curl http://localhost:8080/api/v1/tests/basic

# Tier 2: Intermediate diagnostics
curl http://localhost:8080/api/v1/tests/intermediate

# Tier 3: Comprehensive analysis
curl http://localhost:8080/api/v1/tests/comprehensive

# Check AutoPerf mode
curl http://localhost:5000/api/v1/autoperf/status
```

---

## Troubleshooting

### Services Won't Start

**Check if ports are already in use**:
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use different ports in .env
TESTSERVER_PORT=8081
```

**Docker daemon not running**:
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker

# Windows (Docker Desktop)
# Start Docker Desktop from Applications
```

### Database Connection Error

```bash
# Verify database container is running
docker-compose ps mariadb

# Check database credentials in .env
cat .env | grep DB_

# Connect to database directly
docker-compose exec mariadb mysql -u root -p -e "SELECT 1"

# View logs
docker-compose logs mariadb
```

### testServer Won't Start

```bash
# Check logs
docker-compose logs testserver

# Verify Go compilation
docker-compose exec testserver go build ./...

# Reset and rebuild
docker-compose down
docker-compose up -d --build testserver
```

### Python Service Import Errors

```bash
# Reinstall dependencies
docker-compose exec manager-api pip install -r requirements.txt

# Check Python version
docker-compose exec manager-api python --version

# Verify virtual environment
docker-compose exec manager-api pip list
```

### Smoke Tests Failing

**Check which test failed**:
```bash
./tests/smoke/build/test-services-build.sh
./tests/smoke/api/test-testserver-health.sh
./tests/smoke/webui/test-pages-load.sh
```

**Common issues**:
- Service not healthy (logs: `docker-compose logs <service>`)
- Port not exposed (check docker-compose.yml)
- API endpoint not implemented
- Missing environment variables

### Git Merge Conflicts

```bash
# View conflicts
git status

# Edit conflicted files (marked with <<<<, ====, >>>>)
# Remove conflict markers and keep desired code

# Mark as resolved
git add <resolved-file>

# Complete merge
git commit -m "Resolve merge conflicts"
```

### Slow Docker Builds

```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
docker system prune

# Rebuild without cache (slow, but fresh)
docker-compose build --no-cache testserver
```

---

## Tips & Best Practices

### Hot Reload Development

For fastest iteration:
```bash
# Start services once
docker-compose up -d

# Edit Python files → auto-reload (FLASK_DEBUG=1)
# Edit JavaScript files → hot reload (Webpack)
# Edit Go files → restart service
```

### Environment-Specific Configuration

```bash
# Development settings (auto-loaded)
.env              # Default development config
.env.local        # Local machine overrides (gitignored)

# Production settings (via secret management)
Kubernetes secrets
AWS Secrets Manager
HashiCorp Vault
```

### Performance Tips

```bash
# Use specific services to reduce memory usage
docker-compose up manager-api webClient-api  # Skip UI, testServer

# Use lightweight testing
make smoke-test  # Instead of full test suite while developing

# Cache Docker layers by building in order of frequency of change
# Dockerfile: base → dependencies → code → entrypoint
```

---

## Related Documentation

- **Testing**: [Testing Documentation](TESTING.md)
  - Mock data scripts (Tier 1/2/3)
  - Smoke tests
  - Multi-tier testing strategies
  - Cross-architecture testing

- **Pre-Commit**: [Pre-Commit Checklist](PRE_COMMIT.md)
  - Linting requirements
  - Security scanning
  - Build verification
  - Test requirements

- **Standards**: [Development Standards](STANDARDS.md)
  - Architecture decisions
  - Code style
  - API conventions
  - Multi-tier testing patterns

- **Workflows**: [CI/CD Workflows](WORKFLOWS.md)
  - GitHub Actions pipelines
  - Build automation
  - Test automation
  - Release processes

---

**Last Updated**: 2026-01-06
**Maintained by**: Penguin Tech Inc
