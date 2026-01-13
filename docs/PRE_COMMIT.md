# WaddlePerf Pre-Commit Checklist

**CRITICAL: This checklist MUST be followed before every commit to maintain code quality and performance monitoring standards.**

## Automated Pre-Commit Script

**Run the automated pre-commit script to execute all checks:**

```bash
./scripts/pre-commit/pre-commit.sh
```

This script will:
1. Run all checks in the correct order
2. Log output to `/tmp/pre-commit-waddleperf-<epoch>.log`
3. Provide a summary of pass/fail status
4. Echo the log file location for review

**Individual check scripts** (run separately if needed):
- `./scripts/pre-commit/check-python.sh` - Python linting & security
- `./scripts/pre-commit/check-go.sh` - Go linting & security
- `./scripts/pre-commit/check-node.sh` - Node.js/React linting, audit & build
- `./scripts/pre-commit/check-security.sh` - All security scans
- `./scripts/pre-commit/check-secrets.sh` - Secret detection
- `./scripts/pre-commit/check-docker.sh` - Docker build & validation
- `./scripts/pre-commit/check-tests.sh` - Unit and integration tests

---

## Required Steps (In Order)

Before committing, run in this order (or use `./scripts/pre-commit/pre-commit.sh`):

### Foundation Checks

- [ ] **Linters**: Run linters for all modified code
  ```bash
  make lint
  ```
  - Python: `flake8`, `black`, `isort`, `mypy`
  - Go: `golangci-lint`
  - Node.js: `eslint`, `prettier`

- [ ] **Security scans**: Check for vulnerabilities
  ```bash
  make security-scan
  ```
  - Python: `bandit -r .`, `safety check`
  - Go: `gosec ./...`
  - Node.js: `npm audit`

- [ ] **No secrets**: Verify no credentials, API keys, or tokens in code
  ```bash
  ./scripts/pre-commit/check-secrets.sh
  ```

### Build & Integration Verification

- [ ] **Build & Run**: Verify code compiles and containers start successfully
  ```bash
  docker-compose build --no-cache
  docker-compose up -d
  docker-compose ps  # Verify all services healthy
  ```

- [ ] **Smoke tests** (mandatory, <2 min): `make smoke-test`
  - All containers build without errors
  - All containers start and remain healthy
  - All API health endpoints respond with 200 status
  - All web pages load without JavaScript errors
  - See: [Testing Documentation - Smoke Tests](TESTING.md#tier-1-smoke-tests)

### Feature Testing & Documentation

- [ ] **Mock data** (for testing features): Ensure 3-4 test items per feature via `make seed-mock-data`
  - Populate development database with realistic test data
  - Needed before capturing screenshots and UI testing
  - See: [Testing Documentation - Mock Data Scripts](TESTING.md#mock-data-scripts)

- [ ] **Screenshots** (for UI changes): `node scripts/capture-screenshots.cjs`
  - Requires running `make dev` and `make seed-mock-data` first
  - Screenshots should showcase features with realistic mock data
  - Automatically removes old screenshots, captures fresh ones
  - Commit updated screenshots with feature/UI changes

### Comprehensive Testing

- [ ] **Unit tests**: `make test-unit`
  - Network isolated, mocked dependencies
  - Must pass before committing

- [ ] **Integration tests**: `make test-integration`
  - Component interaction verification
  - Multi-service flow validation
  - See: [Testing Documentation - Integration Tests](TESTING.md#tier-2-integration-tests)

### Multi-Tier Testing Validation

- [ ] **Tier 1 validation**: Quick connectivity tests
  ```bash
  ./tests/tier1/run-tier1-tests.sh
  ```

- [ ] **Tier 2 validation** (if applicable): Intermediate diagnostics
  ```bash
  ./tests/tier2/run-tier2-tests.sh
  ```

### Finalization

- [ ] **Version updates**: Update `.version` if releasing new version
- [ ] **Documentation**: Update docs if adding/changing features
- [ ] **Docker builds**: Verify Dockerfile uses debian-slim base (no alpine)
  ```bash
  grep -E "^FROM.*slim" */Dockerfile
  ```

---

## Language-Specific Commands

### Python

```bash
# Linting
flake8 managerServer webClient --max-line-length=120
black --check --line-length=120 managerServer webClient
isort --check-only --profile black managerServer webClient
mypy managerServer webClient --strict

# Security
bandit -r managerServer webClient -ll
safety check

# Build & Run
python -m py_compile **/*.py          # Syntax check
pip install -r requirements.txt       # Dependencies
python app.py &                       # Verify it starts (then kill)

# Tests
pytest tests/unit/
pytest tests/integration/
```

### Go

```bash
# Linting
golangci-lint run ./... --timeout=5m

# Security
gosec -fmt json ./...

# Build & Run
go build ./...                        # Compile all packages
go run main.go &                      # Verify it starts (then kill)
go vet ./...

# Tests
go test ./...
go test -race ./...                   # Race condition detection
```

### Node.js / JavaScript / TypeScript / ReactJS

```bash
# Linting
npm run lint
# or
npx eslint .

# Formatting
npx prettier --write .

# Security (REQUIRED)
npm audit                             # Check for vulnerabilities
npm audit fix                         # Auto-fix if possible

# Build & Run
npm run build                         # Compile/bundle
npm start &                           # Verify it starts (then kill)
# For React: npm run dev or npm run preview

# Tests
npm test
```

### Docker / Containers

```bash
# Lint Dockerfiles
hadolint */Dockerfile

# Verify base image (debian-slim, NOT alpine)
grep -E "^FROM.*slim" */Dockerfile

# Build & Run
docker-compose build --no-cache                   # Build all services
docker-compose up -d                              # Start all services
docker-compose ps                                 # Check health
docker-compose logs -f                            # View logs
docker-compose down                               # Cleanup

# Test specific service
docker-compose build --no-cache testserver
docker-compose up -d testserver
docker-compose logs testserver
```

---

## Commit Rules

- **NEVER commit automatically** unless explicitly requested by the user
- **NEVER push to remote repositories** under any circumstances
- **ONLY commit when explicitly asked** - never assume commit permission
- **Wait for approval** before running `git commit`

---

## Security Scanning Requirements

### Before Every Commit

- **Run security audits on all modified packages**:
  - **Go packages**: Run `gosec ./...` on modified Go services
  - **Node.js packages**: Run `npm audit` on modified Node.js services
  - **Python packages**: Run `bandit -r .` and `safety check` on modified Python services

- **Do NOT commit if security vulnerabilities are found** - fix all issues first
- **Document vulnerability fixes** in commit message if applicable

### Vulnerability Response

1. Identify affected packages and severity
2. Update to patched versions immediately
3. Test updated dependencies thoroughly
4. Document security fixes in commit messages
5. Verify no new vulnerabilities introduced

---

## Protocol Testing Requirements

Before committing protocol-related changes:

- **Create and run protocol testing scripts** for each modified protocol handler
- **Testing scope**: All new protocols and modified functionality
- **Test files location**: `tests/protocols/` directory
  - `tests/protocols/test_http_protocol.py` - HTTP/HTTPS testing
  - `tests/protocols/test_tcp_protocol.py` - TCP testing
  - `tests/protocols/test_udp_protocol.py` - UDP testing
  - `tests/protocols/test_icmp_protocol.py` - ICMP testing

- **Run before commit**: Each test script should be executable and pass completely
- **Test coverage**:
  - Protocol initialization
  - Test execution
  - Result collection
  - Error handling
  - Timeout scenarios
  - Connection failures

---

## Performance Testing Requirements

For performance-critical changes:

- **Run performance tests**: `make test-performance`
- **Verify metrics collection**:
  ```bash
  # Run a test and verify metrics are collected correctly
  curl -X POST http://localhost:8080/api/v1/tests/speed
  ```

- **Check performance targets**:
  - Latency metrics within acceptable range
  - Throughput meets specification
  - Resource usage within limits
  - No memory leaks

---

## Multi-Tier Testing Validation

For test execution changes:

- **Verify all tiers work correctly**:
  ```bash
  # Tier 1: Quick test
  ./tests/tier1/run-basic-test.sh

  # Tier 2: Intermediate test
  ./tests/tier2/run-intermediate-test.sh

  # Tier 3: Comprehensive test
  ./tests/tier3/run-comprehensive-test.sh
  ```

- **Verify escalation works**:
  - Tier 1 passes → Return results
  - Tier 1 fails → Escalate to Tier 2
  - Tier 2 fails → Escalate to Tier 3

---

## Screenshot & Mock Data Requirements

### Prerequisites

Before capturing screenshots, ensure development environment is running with mock data:

```bash
make dev                   # Start all services
make seed-mock-data        # Populate with 3-4 test items per feature
```

### Capture Screenshots

For all UI changes, update screenshots to show current application state with realistic data:

```bash
node scripts/capture-screenshots.cjs
# Or via npm script if configured: npm run screenshots
```

### What to Screenshot

- **Login page** (unauthenticated state)
- **Test execution page** (running state)
- **Results page** with realistic metrics
- **Settings/configuration pages** if changed
- **All new features** with sample data (3-4 items)

### Commit Guidelines

- Automatically removes old screenshots and captures fresh ones
- Commit updated screenshots with relevant feature/UI/documentation changes
- Screenshots demonstrate feature purpose and functionality
- Helpful error message if login fails: "Ensure mock data is seeded"

---

## Multi-Component Testing

For changes affecting multiple services:

- **Test all affected components**:
  ```bash
  # testServer (Go)
  cd testserver && go test ./...

  # managerServer (Python)
  cd managerServer && pytest tests/

  # webClient (Python)
  cd webClient && pytest tests/

  # UIs (Node.js)
  cd managerServer/ui && npm test
  cd webClient/ui && npm test
  ```

- **Test integration between components**:
  ```bash
  make test-integration
  ```

- **Verify cross-component communication**:
  - API → testServer
  - WebUI → API
  - All authentication flows

---

## Cross-Architecture Testing (Optional)

For final commits before release:

- **Test alternate architecture with QEMU**:
  ```bash
  # If developing on amd64, test arm64
  docker buildx build --platform linux/arm64 .

  # If developing on arm64, test amd64
  docker buildx build --platform linux/amd64 .

  # Or test both
  docker buildx build --platform linux/amd64,linux/arm64 .
  ```

- **Verify no architecture-specific issues**:
  - Binary compatibility
  - Endianness handling
  - Floating-point precision
  - Package availability

---

## Quick Pre-Commit Checklist

Use this minimal checklist for quick verification:

```
[ ] All linters pass (make lint)
[ ] Security scans pass (make security-scan)
[ ] Smoke tests pass (make smoke-test)
[ ] Unit tests pass (make test-unit)
[ ] Integration tests pass (make test-integration)
[ ] No secrets in code (grep for passwords, API keys, tokens)
[ ] Docker builds successfully (docker-compose build --no-cache)
[ ] All containers healthy (docker-compose ps)
[ ] Code is documented (docstrings, comments)
[ ] Changes committed with meaningful message
```

---

## Debugging Failed Checks

### Linting Failures

```bash
# See all linting issues
make lint-verbose

# Auto-fix some issues
black --line-length=120 managerServer webClient
isort --profile black managerServer webClient
```

### Security Scan Failures

```bash
# See details of vulnerabilities
bandit -r managerServer -v
gosec -fmt=json ./...
npm audit --json
```

### Build Failures

```bash
# Detailed Docker build output
docker-compose build --no-cache --progress=plain testserver

# Check logs
docker-compose logs testserver
```

### Test Failures

```bash
# Verbose test output
pytest -v tests/
go test -v ./...
npm test -- --verbose
```

---

## Related Documentation

- **Testing**: [Testing Documentation](TESTING.md)
  - Detailed testing strategies
  - Mock data implementation
  - Smoke/unit/integration test patterns
  - Performance testing

- **Development**: [Development Guide](DEVELOPMENT.md)
  - Local development setup
  - Component startup
  - Debugging techniques

- **Standards**: [Development Standards](STANDARDS.md)
  - Code quality standards
  - Performance testing standards
  - Security standards

- **Workflows**: [CI/CD Workflows](WORKFLOWS.md)
  - Automated testing pipelines
  - Build and deployment

---

**Last Updated**: 2026-01-06
**Maintained by**: Penguin Tech Inc
