# CLAUDE.md - AI Assistant Context for WaddlePerf

## Project Overview
WaddlePerf is a comprehensive network performance testing and monitoring platform that tests user experience between endpoints. It provides both client and server components for network diagnostics, bandwidth testing, and connectivity analysis.

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
- **Languages**: Python 3.12, Go 1.23
- **Frameworks**: Flask 3.0 (APIs), React 18 (frontends)
- **Infrastructure**: Docker, Docker Compose, MariaDB Galera
- **Testing Tools**: Native implementations (HTTP/TCP/UDP/ICMP)
- **CI/CD**: GitHub Actions

## MariaDB Galera Cluster Compatibility

WaddlePerf is designed to work with MariaDB Galera Cluster for high availability. To maintain compatibility, follow these critical rules:

⚠️ **IMPORTANT**: Before making ANY database or schema changes, read [docs/DATABASE.md](docs/DATABASE.md) for complete Galera restrictions and best practices.

### Database Schema Requirements
- **PRIMARY KEYS REQUIRED**: All tables MUST have a primary key (multi-column keys are supported)
  - DELETE operations will FAIL on tables without primary keys
  - Always define primary keys in schema migrations
- **Use InnoDB only**: All tables must use InnoDB storage engine
  - MyISAM has experimental support but should be avoided
  - System tables (mysql.*) are not replicated

### Locking Restrictions
- **AVOID explicit table locks**: Do NOT use `LOCK TABLES` or `FLUSH TABLES {table_list} WITH READ LOCK`
- **GET_LOCK() / RELEASE_LOCK()**: These functions are NOT supported
- **Global locks ARE supported**: `FLUSH TABLES WITH READ LOCK` works for full database locks
- **DDL does NOT wait**: DDL statements execute immediately without waiting for metadata locks from parallel DML transactions

### Transaction and Replication Limitations
- **NO distributed transactions (XA)**: Do not use XA transactions or two-phase commits
- **Row-based replication only**: `binlog_format` must be ROW (never change at runtime)
- **FLUSH PRIVILEGES not replicated**: After user/permission changes, run on ALL nodes or restart cluster
- **Auto-increment gaps**: Do NOT rely on sequential auto-increment values
  - Galera uses increment offsets to avoid conflicts
  - Gaps in sequences are normal and expected

### Operations to Avoid
- **Large transactions**: Keep transactions small to avoid certification conflicts
- **Hot spots**: Avoid high-contention updates to the same rows across nodes
- **Long-running transactions**: May cause certification failures on commit
- **Changing binlog_format at runtime**: Will crash ALL nodes in the cluster

### Best Practices for WaddlePerf Development
1. **Always define primary keys** in CREATE TABLE statements
2. **Use InnoDB explicitly** for all tables
3. **Keep transactions short** - commit frequently
4. **Avoid table locks** - use row-level locking patterns
5. **Test with multiple nodes** - verify no certification conflicts occur
6. **Handle deadlocks gracefully** - Galera can have different deadlock patterns than standalone MariaDB
7. **Monitor cluster status** - check `wsrep_cluster_status` and `wsrep_ready` variables

### Performance Considerations
- Cluster performance is limited by the **slowest node**
- Write performance may be lower than standalone due to certification overhead
- Read performance can scale horizontally across nodes
- Network latency between nodes directly impacts commit times

## Docker Image Standards
- **Python services**: MUST use Debian-based images (e.g., `python:3.12-slim` or `python:3.12`)
  - Alpine images cause compilation issues with packages like gevent, bcrypt, cryptography
  - Debian images provide better compatibility and faster builds
- **Go services**: Use Debian-based images for build stage (e.g., `golang:1.23-bookworm`), Alpine for runtime
  - Build stage: `golang:1.23-bookworm` - better compatibility, faster builds
  - Runtime stage: `alpine:3.19` - minimal size for static binaries
- **Frontend services**: Use Alpine nginx (e.g., `nginx:alpine`)
- **Node.js build stages**: Use Alpine (e.g., `node:18-alpine`)

## Testing Requirements

### For Python Code
- Use async and threading where possible for performance
- Test with py4web's built-in testing if modifying web components
- Verify Docker containers build and run successfully

### For Go Code
- Run `go mod tidy` to manage dependencies
- Run `go fmt` for code formatting
- Run `go vet` for static analysis
- Run `go test ./...` for all tests
- Build for target platforms before committing

### For Docker
- **ALWAYS** use `--no-cache` flag when building Docker images to ensure all changes are applied
- **ALWAYS** use `docker-compose down -v` when rebuilding containers or clusters to remove cached volumes and avoid stale data
- Test builds with `docker-compose build --no-cache`
- When rebuilding: `docker-compose down -v && docker-compose up -d`
- Verify containers run with `docker-compose up -d`
- Check health endpoints work correctly

## Build Commands

### Client Docker Build
```bash
docker build -t waddleperf-client ./client
```

### Server Docker Build
```bash
docker build -t waddleperf-server ./server
```

### Go Client Build (multi-platform)
```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 go build -o waddleperf-linux-amd64

# Linux ARM64
GOOS=linux GOARCH=arm64 go build -o waddleperf-linux-arm64

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -o waddleperf-windows-amd64.exe

# macOS Universal (requires additional tooling)
GOOS=darwin GOARCH=amd64 go build -o waddleperf-darwin-amd64
GOOS=darwin GOARCH=arm64 go build -o waddleperf-darwin-arm64
# Then use lipo to create universal binary
```

## Testing Approach
WaddlePerf uses a 3-tier testing system:
1. **Tier 1**: Basic connectivity tests (frequent)
2. **Tier 2**: Intermediate diagnostics (on threshold breach)
3. **Tier 3**: Comprehensive analysis (on critical issues)

## Configuration Files
- Docker Compose: `/docker-compose.yml`
- Client config: `/client/vars/base.yml`
- Server config: `/server/vars/base.yml`
- GitHub Actions: `/.github/workflows/`

## Network Ports
- HTTP: 80
- HTTPS: 443
- iperf3: 5201
- Web UI: 8080
- UDP Ping: 2000

## Development Workflow
1. Make changes in feature branch
2. Test thoroughly (unit, integration, Docker builds)
3. Lint and format code
4. Update documentation if needed
5. Create pull request to main branch

## Key Features to Maintain
- AutoPerf mode for continuous monitoring
- Multi-tier escalation testing
- S3 integration for results storage
- Geographic IP analysis
- Multiple protocol support (TCP, UDP, HTTP, HTTPS, SSH, DNS)

## Security Considerations
- Containers run as non-root user (www-data)
- SSL/TLS certificate management
- Input validation for all user inputs
- No hardcoded secrets or credentials
- Use environment variables for configuration

## Documentation
- Main docs in `/docs/` folder
- README.md for overview
- RELEASE_NOTES.md for version history
- In-code comments for complex logic only

## Common Tasks

### Adding a New Test Tool
1. Add binary to appropriate bins/ folder
2. Create wrapper function in Python
3. Update Ansible playbook to install
4. Add to configuration variables
5. Test in Docker container
6. Document usage

### Updating Dependencies
1. Python: Update requirements.txt
2. Go: Update go.mod and run `go mod tidy`
3. Docker: Update base images in Dockerfiles
4. Test all changes thoroughly

### Creating a Release
1. Update version numbers
2. Update RELEASE_NOTES.md
3. Test all components
4. Tag release in git
5. GitHub Actions will build and publish

## Contact and Support
- Organization: Penguin Technologies Inc.
- Repository: https://github.com/penguintechinc/WaddlePerf
- Issues: Report at GitHub Issues page

Remember: Always complete tasks fully, test thoroughly, and never leave placeholders!