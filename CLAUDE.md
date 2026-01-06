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

## Database Architecture

WaddlePerf uses a hybrid database approach for optimal performance and flexibility:

### Database Support
- **Supported Types**: PostgreSQL, MySQL, SQLite
- **Note**: DB_TYPE configuration only supports `postgres`, `mysql`, or `sqlite` values

### Hybrid Database Approach
- **Initialization Phase**: SQLAlchemy ORM for schema creation, migrations, and initial setup
- **Day-to-Day Operations**: PyDAL for rapid development and flexible data access patterns
- **Migration Path**: SQLAlchemy handles schema management, PyDAL provides runtime flexibility

### Required Dependencies
```
Flask>=3.0
Flask-Security-Too>=5.1.0
SQLAlchemy>=2.0
PyDAL>=20.04
PyMySQL  # for MySQL support
psycopg2-binary  # for PostgreSQL support
```

## MariaDB Galera Cluster Requirements

WaddlePerf is designed to work with MariaDB Galera Cluster for high availability. To maintain compatibility, follow these critical rules:

⚠️ **IMPORTANT**: Before making ANY database or schema changes, read [docs/DATABASE.md](docs/DATABASE.md) for complete Galera restrictions and best practices.

### Cluster Configuration Requirements
- **Minimum Version**: MariaDB 10.6 with Galera 4.x
- **Replication Mode**: Row-based (binlog_format=ROW)
- **Storage Engine**: InnoDB (required for Galera)
- **Minimum Nodes**: 3 nodes for quorum (odd numbers recommended)
- **Network**: Low-latency, reliable network between nodes (LAN recommended)
- **Configuration**: wsrep_sync_wait=7 for read consistency

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

## Container Architecture

WaddlePerf uses a microservices architecture with separated API/Backend and WebUI components:

### Service Containers
- **API/Backend Container**: Flask-based REST API and business logic
  - Handles all database operations
  - Processes test requests and results
  - Manages authentication and authorization via Flask-Security-Too
  - Exposes REST endpoints for client communication

- **WebUI Container**: React-based frontend application
  - Standalone nginx-based web server
  - Communicates with API Container via REST API
  - Runs on port 8080 (configurable)
  - Independent scaling from backend

- **Database Container**: MariaDB Galera Cluster
  - Shared database for all services
  - High availability configuration
  - Persistent volume for data storage

### Communication Patterns
- WebUI → API: HTTPS/HTTP REST calls
- API → Database: SQL queries via PyDAL/SQLAlchemy
- Multiple API instances can run in parallel with load balancing

## Docker Image Standards
- **Python services**: MUST use Debian-based images (e.g., `python:3.13-slim` or `python:3.13`)
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

## Critical Development Rules

### Development Philosophy: Safe, Stable, and Feature-Complete

**NEVER take shortcuts or the "easy route" - ALWAYS prioritize safety, stability, and feature completeness**

#### Core Principles
- **No Quick Fixes**: Resist quick workarounds or partial solutions
- **Complete Features**: Fully implemented with proper error handling and validation
- **Safety First**: Security, data integrity, and fault tolerance are non-negotiable
- **Stable Foundations**: Build on solid, tested components
- **Future-Proof Design**: Consider long-term maintainability and scalability
- **No Technical Debt**: Address issues properly the first time

#### Red Flags (Never Do These)
- Skipping input validation "just this once"
- Hardcoding credentials or configuration
- Ignoring error returns or exceptions
- Commenting out failing tests to make CI pass
- Deploying without proper testing
- Using deprecated or unmaintained dependencies
- Implementing partial features with "TODO" placeholders
- Bypassing security checks for convenience
- Assuming data is valid without verification
- Leaving debug code or backdoors in production

#### Quality Checklist Before Completion
- All error cases handled properly
- Unit tests cover all code paths
- Integration tests verify component interactions
- Security requirements fully implemented
- Performance meets acceptable standards
- Documentation complete and accurate
- Code review standards met
- No hardcoded secrets or credentials
- Logging and monitoring in place
- Build passes in containerized environment
- No security vulnerabilities in dependencies
- Edge cases and boundary conditions tested

### Git Workflow
- **NEVER commit automatically** unless explicitly requested by the user
- **NEVER push to remote repositories** under any circumstances
- **ONLY commit when explicitly asked** - never assume commit permission
- Always use feature branches for development
- Require pull request reviews for main branch
- Automated testing must pass before merge

### Local State Management (Crash Recovery)
- **ALWAYS maintain local .PLAN and .TODO files** for crash recovery
- **Keep .PLAN file updated** with current implementation plans and progress
- **Keep .TODO file updated** with task lists and completion status
- **Update these files in real-time** as work progresses
- **Add to .gitignore**: Both .PLAN and .TODO files must be in .gitignore
- **File format**: Use simple text format for easy recovery
- **Automatic recovery**: Upon restart, check for existing files to resume work

### Dependency Security Requirements
- **ALWAYS check for Dependabot alerts** before every commit
- **Monitor vulnerabilities via Socket.dev** for all dependencies
- **Mandatory security scanning** before any dependency changes
- **Fix all security alerts immediately** - no commits with outstanding vulnerabilities
- **Regular security audits**: `npm audit`, `go mod audit`, `safety check`

### Linting & Code Quality Requirements
- **ALL code must pass linting** before commit - no exceptions
- **Python**: flake8, black, isort, mypy (type checking), bandit (security)
- **JavaScript/TypeScript**: ESLint, Prettier
- **Go**: golangci-lint (includes staticcheck, gosec, etc.)
- **Ansible**: ansible-lint
- **Docker**: hadolint
- **YAML**: yamllint
- **Markdown**: markdownlint
- **Shell**: shellcheck
- **CodeQL**: All code must pass CodeQL security analysis
- **PEP Compliance**: Python code must follow PEP 8, PEP 257 (docstrings), PEP 484 (type hints)

### Build & Deployment Requirements
- **NEVER mark tasks as completed until successful build verification**
- All Go and Python builds MUST be executed within Docker containers
- Use containerized builds for local development and CI/CD pipelines
- Build failures must be resolved before task completion

### Documentation Standards
- **README.md**: Keep as overview and pointer to comprehensive docs/ folder
- **docs/ folder**: Create comprehensive documentation for all aspects
- **RELEASE_NOTES.md**: Maintain in docs/ folder, prepend new version releases to top
- Update CLAUDE.md when adding significant context
- **Build status badges**: Always include in README.md
- **ASCII art**: Include catchy, project-appropriate ASCII art in README
- **Company homepage**: Point to www.penguintech.io
- **License**: All projects use Limited AGPL3 with preamble for fair use

### File Size Limits
- **Maximum file size**: 25,000 characters for ALL code and markdown files
- **Split large files**: Decompose into modules, libraries, or separate documents
- **CLAUDE.md exception**: Maximum 39,000 characters (only exception to 25K rule)
- **High-level approach**: CLAUDE.md contains high-level context and references detailed docs
- **Documentation strategy**: Create detailed documentation in `docs/` folder and link to them from CLAUDE.md
- **Keep focused**: Critical context, architectural decisions, and workflow instructions only
- **User approval required**: ALWAYS ask user permission before splitting CLAUDE.md files

## Version Management System

**Format**: `vMajor.Minor.Patch.build`
- **Major**: Breaking changes, API changes, removed features
- **Minor**: Significant new features and functionality additions
- **Patch**: Minor updates, bug fixes, security patches
- **Build**: Epoch64 timestamp of build time

**Update Commands**:
```bash
./scripts/version/update-version.sh          # Increment build timestamp
./scripts/version/update-version.sh patch    # Increment patch version
./scripts/version/update-version.sh minor    # Increment minor version
./scripts/version/update-version.sh major    # Increment major version
```

## PenguinTech License Server Integration

All projects integrate with the centralized PenguinTech License Server at `https://license.penguintech.io` for feature gating and enterprise functionality.

**IMPORTANT: License enforcement is ONLY enabled when project is marked as release-ready**
- Development phase: All features available, no license checks
- Release phase: License validation required, feature gating active

**License Key Format**: `PENG-XXXX-XXXX-XXXX-XXXX-ABCD`

**Core Endpoints**:
- `POST /api/v2/validate` - Validate license
- `POST /api/v2/features` - Check feature entitlements
- `POST /api/v2/keepalive` - Report usage statistics

**Environment Variables**:
```bash
# License configuration
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
LICENSE_SERVER_URL=https://license.penguintech.io
PRODUCT_NAME=waddleperf

# Release mode (enables license enforcement)
RELEASE_MODE=false  # Development (default)
RELEASE_MODE=true   # Production (explicitly set)
```

**License Management Commands**:
```bash
make license-validate        # Validate license
make license-check-features  # Check available features
make license-debug           # Test license server connectivity
```

## CI/CD Pipeline & Workflows

WaddlePerf implements comprehensive CI/CD with full .WORKFLOW compliance. All workflows include version detection, epoch64 timestamps, security scanning, and conditional metadata tags.

### .WORKFLOW Compliance Standard

All workflows include:
1. **.version path filters**: Detect version file changes for automatic versioning
2. **Version detection step**: Parse `.version` file with epoch64 fallback
3. **Epoch64 timestamp generation**: Unix epoch (seconds since 1970) for precise build tracking
4. **Version detection step**: Automatic .version parsing with 0.0.0.{epoch64} fallback
5. **Conditional metadata tags**: Dynamic Docker tags based on version patterns
6. **Security scanning**: gosec for Go projects, language-specific scanners for others

### Core Workflows

**Go Client** (`build-go-client.yml`):
- Multi-platform binary building (Linux/macOS/Windows, AMD64/ARM64)
- Version detection from `.version` file
- gosec security scanning for Go
- Docker image builds for GHCR and Docker Hub
- Creates universal macOS binaries
- Generates distribution packages with checksums
- Supports semantic versioning and pre-release labels

**Test Server** (`testserver.yml`):
- Comprehensive Go testing (unit tests, vet, formatting)
- gosec security scanning with JSON output
- Multi-platform Docker builds (Linux AMD64/ARM64)
- Automatic Docker registry push on success
- Version-based tagging strategy
- Build caching for faster iterations

**Version Release** (`version-release.yml`):
- Triggered on `.version` file changes
- Automatic pre-release creation on main branch
- Epoch64 timestamp generation and storage
- Conditional metadata tags: [prerelease], [release-candidate], [stable]
- Prevents duplicate releases (idempotent)
- Auto-generated release notes with build metadata

### Version Management

**File**: `.version` (v4.0.0alpha)

**Format**: `vMajor.Minor.Patch[.build]`
- Major: Breaking changes, API changes
- Minor: New features and functionality
- Patch: Bug fixes and security patches
- Build: Optional epoch64 timestamp (auto-appended by CI/CD)

**Detection Strategy**:
```bash
if [ -f .version ]; then
  VERSION=$(cat .version)
else
  VERSION="0.0.0.$(date +%s)"
fi
```

**Release Process**:
1. Update `.version` file in feature branch
2. Commit and create PR
3. Merge to main branch
4. GitHub Actions auto-triggers `version-release.yml`
5. Pre-release created with metadata tags

### Security Scanning

**gosec Integration** (Go Security Scanner):
- Installed: `go install github.com/securego/gosec/v2/cmd/gosec@latest`
- Execution: `gosec -fmt json -out results.json ./...`
- Output Format: JSON for programmatic analysis
- Behavior: Warning-only (non-blocking, continues on findings)
- Review: High/medium severity issues must be addressed before release

**Implementation Points**:
- `build-go-client.yml`: Docker build target securitycheck
- `testserver.yml`: Direct execution in test job after gofmt/govet

**High Severity Issues**:
- SQL injection vulnerabilities
- Hardcoded credentials or secrets
- Unsafe cryptographic operations
- Insecure random number generation
- Must be fixed before merge to main

### Docker Image Tagging

**Tag Strategy**:
```
Semantic:    ghcr.io/penguintechinc/waddleperf-go-client:v1.2.3
Branch:      ghcr.io/penguintechinc/waddleperf-go-client:main-a1b2c3d4
Release:     ghcr.io/penguintechinc/waddleperf-go-client:latest
Pre-release: ghcr.io/penguintechinc/waddleperf-go-client:alpha
Version tag: ghcr.io/penguintechinc/waddleperf-go-client:v4.0.0alpha
```

**Registries**:
- GitHub Container Registry (GHCR): ghcr.io/penguintechinc/
- Docker Hub: docker.io/penguincloud/

### Performance Optimization

**Build Parallelization**:
- 6 platform builds in parallel (Linux/macOS/Windows × amd64/arm64)
- Separate jobs for binaries, Docker images, and release packages
- Conditional execution: tests only on Linux AMD64

**Caching Strategy**:
- GitHub Actions cache for Docker layers
- Go module cache: ~/.cache/go-build, ~/go/pkg/mod
- Buildx native caching with mode=max

**Build Time Targets**:
- Go test: < 30 seconds
- Docker build: < 2 minutes per platform
- Total pipeline: < 10 minutes

### Documentation

See detailed documentation in:
- **[docs/WORKFLOWS.md](docs/WORKFLOWS.md)**: Complete workflow reference
- **[docs/STANDARDS.md](docs/STANDARDS.md)**: CI/CD standards and practices
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Development guidelines

## WaddleAI Integration

For AI-powered performance analysis and anomaly detection, WaddlePerf can integrate with WaddleAI located at `~/code/WaddleAI`.

**Use Cases for WaddlePerf:**
- Intelligent performance anomaly detection with statistical analysis
- Predictive network issue identification using ML models
- Natural language queries for performance data analysis
- Automated root cause analysis and recommendations
- Smart alerting and intelligent notifications

**Enhanced Capabilities:**
- **Anomaly Detection**: Automatically identify unusual network patterns and performance deviations
- **Predictive Analysis**: Forecast network degradation before issues impact users
- **Natural Language Queries**: Ask questions like "What caused the spike at 3pm?" and get intelligent responses

**Integration Pattern:**
- WaddleAI runs as separate microservice container
- Communicate via REST API or gRPC
- Environment variables: `WADDLEAI_URL`, `WADDLEAI_API_KEY`
- License-gate AI features as enterprise functionality
- Test data flow with mock performance metrics in development

**Implementation Checklist:**
- Add WaddleAI service to `docker-compose.yml`
- Implement API client in Flask backend
- Add anomaly detection endpoint: `POST /api/v1/analysis/anomalies`
- Add prediction endpoint: `POST /api/v1/analysis/predict`
- Add NLP query endpoint: `POST /api/v1/analysis/query`
- Store analysis results in PostgreSQL for historical tracking
- Feature-gate under `WADDLEAI_ENABLED` license flag

## Development Standards

WaddlePerf follows comprehensive development standards to ensure quality, consistency, and maintainability across all components.

**Multi-Tier Testing Approach:**
- **Tier 1 (Smoke Tests)**: Basic connectivity, API health, UI loads, build verification
  - Run on every commit, must complete in <2 minutes
  - Validates core functionality hasn't broken
  - Required before merging to main
- **Tier 2 (Integration Tests)**: Component interactions, database operations, multi-service scenarios
  - Runs on feature branches and main
  - Tests Flask-React integration, performance metric collection, S3 integration
  - Must complete in <5 minutes
- **Tier 3 (Comprehensive Tests)**: Performance benchmarks, load testing, cross-platform validation
  - Runs nightly or pre-release
  - Validates Tier 2 and Tier 3 testing in network scenarios
  - Tests multi-node Galera cluster, cross-architecture builds

**Code Quality Standards:**
- All Python code: flake8, black, isort, mypy, bandit
- All Go code: golangci-lint, gosec, gofmt, govet
- JavaScript/React: ESLint, Prettier
- Security scanning mandatory before every commit
- No commits with outstanding security vulnerabilities
- Type hints required for all Python and TypeScript code

**Database Standards for WaddlePerf:**
- PyDAL for all runtime operations (SQLAlchemy for initialization only)
- All database changes must consider MariaDB Galera compatibility
- Review [docs/DATABASE.md](docs/DATABASE.md) before schema modifications
- Test changes against multi-node cluster configuration
- Use transactions for data consistency across test results

## Application Architecture

**Microservices Architecture** - WaddlePerf uses three main containers:

1. **API/Backend Container** (Flask)
   - REST API endpoints for test operations
   - Authentication and authorization via Flask-Security-Too
   - Database operations via PyDAL
   - S3 integration for result storage
   - Performance metric aggregation
   - License validation and feature gating
   - Runs on port 5000 (internal), exposed via MarchProxy

2. **WebUI Container** (React + nginx)
   - React-based dashboard for performance visualization
   - Role-based access control (Admin, Maintainer, Viewer)
   - Real-time test status monitoring
   - Historical performance charts and reports
   - Geographic performance heatmaps
   - Runs on port 8080, independent from API

3. **Database Container** (MariaDB Galera)
   - Centralized data storage for all services
   - Test results, network metrics, user data
   - High availability with multi-node replication
   - Persistent volumes for data retention

**Service Communication:**
- WebUI ↔ API: HTTPS/HTTP REST calls
- API ↔ Database: SQL queries via PyDAL
- Multiple API instances scale horizontally behind load balancer
- WaddleAI service (optional): REST/gRPC for analysis features

**Architecture Benefits:**
- Independent scaling of frontend and backend
- Technology-specific optimization per service
- Separate deployment lifecycles
- Enhanced resilience through service isolation

## Common Integration Patterns

**Flask Backend + React Frontend + Performance Testing Integration:**

1. **API Endpoint Pattern** (Flask Backend)
   ```python
   @api_v1.route('/tests/run', methods=['POST'])
   @jwt_required()
   def run_test():
       # Validate license
       if not check_feature('advanced_tests'):
           return {'error': 'Feature not available'}, 403
       # Create test job in database via PyDAL
       # Queue for background execution
       # Return test_id for status polling
       return {'test_id': job_id, 'status': 'queued'}
   ```

2. **React Component Pattern** (WebUI)
   - Component queries `/api/v1/tests/{test_id}/status`
   - Updates chart data with new metrics
   - Handles role-based visibility (Admin sees all, Viewer sees filtered)
   - Caches results locally for performance

3. **Performance Testing Integration**
   - Test execution runs in background worker
   - Results stored in PostgreSQL via PyDAL
   - Metrics aggregated by geographic region
   - S3 stores large result files (packet captures, logs)
   - WebUI polls for updates or uses WebSocket for real-time

4. **Multi-Tier Testing Flow**
   - Tier 1: Quick connectivity check (30 seconds)
   - If pass → return success
   - If fail → escalate to Tier 2 (2 minutes)
   - If Tier 2 fails → escalate to Tier 3 (5 minutes)
   - Store results with escalation metadata

5. **Authentication Pattern**
   - Flask-Security-Too issues JWT tokens
   - React stores token in secure HTTP-only cookie
   - All API calls include `Authorization: Bearer <token>`
   - Token refresh on 401 response
   - License status validated per request

## Website Integration Requirements

WaddlePerf requires an integrated website for marketing and documentation:

**Website Components:**
- **Marketing Site**: Node.js-based, modern aesthetic, showcasing features
  - Performance statistics and use cases
  - Customer testimonials and case studies
  - Feature comparison and pricing tiers
  - Download links for clients

- **Documentation Site**: Markdown-based, comprehensive developer guides
  - API documentation with examples
  - Client configuration guides
  - Troubleshooting and FAQ
  - Architecture and design decisions

**Repository Integration:**
- Sparse checkout submodule from `github.com/penguintechinc/website`
- Folders: `waddleperf/` (marketing) and `waddleperf-docs/` (documentation)
- Deployed separately from main application
- Versioned alongside main release

**Design Requirements:**
- Modern, responsive UI with subtle gradients
- Performance-focused (lazy loading, optimized images)
- Mobile-first approach for all pages
- Dark mode support for documentation
- Fast load times (<2 seconds first paint)

## Template Customization

**WaddlePerf-Specific Customizations:**

1. **Network Protocol Support**
   - Custom implementations for TCP, UDP, HTTP/HTTPS, SSH, DNS testing
   - Located in `server/libs/` for protocol handlers
   - `shared/py_libs/` for shared protocol utilities
   - Test configuration via `client/vars/base.yml` and `server/vars/base.yml`

2. **Performance Metric Collection**
   - Custom dataclasses in `server/libs/metrics.py`
   - Database schema in migrations for result storage
   - Aggregation functions for multi-node analysis
   - S3 integration for large result archives

3. **Geographic Analysis**
   - IP geolocation service integration
   - Regional performance aggregation
   - Heatmap generation for WebUI
   - Timezone-aware result grouping

4. **AutoPerf Mode**
   - Scheduled test execution at configurable intervals
   - Automatic escalation based on threshold breaches
   - Result notification via email/webhook
   - License-gated for enterprise use

5. **Adding New Test Protocols**
   - Create protocol handler in `server/libs/{protocol}/`
   - Implement `TestBase` interface with setup/run/teardown
   - Register in test registry
   - Add WebUI component for protocol options
   - Test with both Tier 1 and Tier 3 scenarios
   - Update documentation with examples

6. **Extending Flask Backend**
   - Add endpoints in `server/web/api/routes/`
   - Implement PyDAL queries for data access
   - Add Flask-Security decorators for auth/roles
   - Include license checks for premium features
   - Follow REST conventions: `/api/v1/{resource}`

7. **React Dashboard Extensions**
   - Add components in `client/web/apps/components/`
   - Implement Redux/Context for state management
   - Use Tailwind CSS for styling consistency
   - Add role-based conditional rendering
   - Test with sample performance data

## Contact and Support
- Organization: Penguin Technologies Inc.
- Repository: https://github.com/penguintechinc/WaddlePerf
- Issues: Report at GitHub Issues page
- **Integration Support**: support@penguintech.io
- **Sales Inquiries**: sales@penguintech.io
- **License Server Status**: https://status.penguintech.io

Remember: Always complete tasks fully, test thoroughly, and never leave placeholders!