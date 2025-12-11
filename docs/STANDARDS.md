# WaddlePerf Development Standards

## Table of Contents
1. [Code Quality Standards](#code-quality-standards)
2. [CI/CD Standards](#cicd-standards)
3. [Version Management](#version-management)
4. [Documentation Standards](#documentation-standards)
5. [Performance Optimization](#performance-optimization)

## Code Quality Standards

### Go Code

**Code Formatting:**
- Use `gofmt` for consistent formatting (mandatory)
- All code must pass `go fmt` check in CI/CD

**Code Analysis:**
- `go vet ./...` must pass with zero issues
- Static analysis via GitHub Actions
- No deprecated functions or patterns

**Testing:**
- Minimum 70% code coverage
- All tests must pass before merge
- Tests run on Linux AMD64 platform
- Use table-driven tests for edge cases
- Mock external dependencies

**Security:**
- gosec scanning mandatory
- Address high/medium severity issues
- Use `crypto/rand` for random number generation
- Validate all external inputs
- No hardcoded credentials or secrets

**Dependencies:**
- Use `go mod tidy` to manage dependencies
- Pin to stable versions
- Minimize external dependencies
- Regular security audits

### Docker Images

**Base Image Standards:**
- Go services: Use `golang:1.23-bookworm` for build, `alpine:3.19` for runtime
- Multi-stage builds required for Go
- Alpine images for minimal size
- Regular base image updates for security patches

**Dockerfile Best Practices:**
- Use specific image tags (avoid `latest`)
- Multi-architecture support (amd64/arm64)
- Health checks included
- Non-root user (www-data or specific service user)
- Layer caching optimization

**Build Standards:**
- All builds use `docker buildx` for multi-platform
- Build caching enabled via GitHub Actions
- Container scans pass security requirements
- No hardcoded secrets in images

## CI/CD Standards

### Workflow Design

**Compliance Requirements:**
All workflows must include:
1. **.version path filter**: Detect version file changes
2. **Version detection step**: Parse `.version` file with epoch64 fallback
3. **Epoch64 timestamps**: Unix epoch for precise build tracking
4. **Conditional metadata tags**: Docker tags based on version patterns
5. **Security scanning**: gosec for Go, language-specific scanners

**Trigger Configuration:**
- Push: Monitor main, release branches, and version changes
- Pull request: Run tests and validation
- Tags: Version-based release workflows
- Schedule: Optional cron jobs for critical tests
- Manual dispatch: Allow on-demand runs

**Job Dependencies:**
- Test job must pass before build
- Build job must pass before push
- Summary job always runs for reporting

### Build Process

**Version Workflow:**
```
.version file → version-detect step → epoch64 timestamp
                           ↓
              Docker metadata generation
                           ↓
         Semantic tags + custom version tags
```

**Build Performance:**
- Parallel platform building (amd64/arm64)
- Conditional test execution (Linux AMD64 only)
- Layer caching enabled
- Artifact upload with retention policies

### Security Scanning

**gosec for Go:**
- **Installation**: `go install github.com/securego/gosec/v2/cmd/gosec@latest`
- **Execution**: `gosec -fmt json -out results.json ./...`
- **Output**: JSON format for parsing and analysis
- **Treatment**: Warning-only (workflow continues on findings)
- **Review**: High/medium severity issues must be addressed

**Integration Points:**
- testserver.yml: Direct execution in test job
- build-go-client.yml: Docker build target securitycheck

### Release Process

**Version Detection:**
- Automatic from `.version` file
- Falls back to `0.0.0.{epoch64}` if missing
- Semantic version extraction (Major.Minor.Patch)

**Release Tags:**
- Pattern-based labeling: `[prerelease]`, `[release-candidate]`, `[stable]`
- Only creates release if version != 0.0.0
- Prevents duplicate releases
- Auto-generated release notes with metadata

**Artifact Management:**
- Binary packages for all platforms
- SHA256SUMS.txt for integrity verification
- Compressed archives (tar.gz for Unix, zip for Windows)
- 30-day retention for release artifacts
- 7-day retention for build artifacts

## Version Management

### Version File Format

**Location**: `.version` at project root

**Format**: `vMajor.Minor.Patch[.build]`

**Examples:**
- `v4.0.0` - Stable release
- `v4.0.0alpha` - Alpha pre-release
- `v4.0.0beta.1` - Beta pre-release
- `v4.0.0rc1` - Release candidate
- `v4.0.0.1737727200` - Version with epoch64

**Update Process:**
1. Edit `.version` file with new version
2. Commit to feature branch
3. Create PR with version change
4. After merge to main, `version-release.yml` auto-triggers
5. Pre-release created automatically with metadata

### Versioning Strategy

**Semantic Versioning (SemVer):**
- **Major**: Breaking changes, API changes, removed features
- **Minor**: Significant new features and functionality
- **Patch**: Bug fixes, security patches, minor updates

**Build Component:**
- Optional 4th component: epoch64 timestamp
- Automatically appended by build system
- Useful for nightly builds and CI tracking

**Release Tagging:**
- Tags created as `vX.Y.Z` (e.g., `v4.0.0`)
- Pre-releases marked with alpha/beta/rc
- Auto-released from `.version` file on main branch

## Documentation Standards

### README.md

- Overview and key features
- Quick start guide
- Contributing section
- License information
- Links to detailed documentation

### Docs/ Folder Structure

```
docs/
├── WORKFLOWS.md         # CI/CD pipeline documentation
├── STANDARDS.md         # This file
├── ARCHITECTURE.md      # System architecture
├── API.md              # API documentation
├── SECURITY.md         # Security policies
├── INSTALLATION.md     # Setup and installation
├── USAGE.md            # User guide
├── DATABASE.md         # Database schema and Galera
└── RELEASE_NOTES.md    # Version history
```

### Code Documentation

**Go Code:**
- Package-level comments explaining purpose
- Function comments for exported functions
- Parameter and return documentation
- Example code in comments for complex functions
- TODOs for future work (with context)

**Comments:**
- Explain WHY not WHAT
- Keep up-to-date with code changes
- Remove outdated comments
- Use clear, professional language

### Release Notes

- Prepend new versions to top of RELEASE_NOTES.md
- Group changes: Features, Improvements, Fixes, Security
- Include breaking changes prominently
- Thank contributors
- Link to GitHub release

## Performance Optimization

### Go Optimization

**Build Optimization:**
```bash
# Minimal binary
go build -ldflags="-s -w"

# Strip debug symbols further
strip binary
```

**Runtime Optimization:**
- Avoid allocations in hot paths
- Use sync.Pool for object reuse
- Pre-allocate slices with capacity
- Buffer I/O operations
- Use goroutines for I/O-bound work

**Profiling:**
- Use pprof for CPU and memory profiling
- Analyze goroutine leaks
- Check memory allocations in tests
- Compare performance across versions

### Docker Image Optimization

**Size Optimization:**
- Multi-stage builds: build in debian, run on alpine
- Remove build artifacts and caches
- Compress binaries with upx (if compatible)
- Use alpine:3.19 or debian:bookworm-slim

**Build Speed:**
- Layer caching: base image → dependencies → code
- Order Dockerfile instructions by change frequency
- Use BuildKit for faster parallel builds
- Cache external downloads

**Startup Performance:**
- Minimal init process (static binaries)
- Pre-warm connections at startup
- Fast health checks (< 100ms)
- Ready states before accepting traffic

### CI/CD Performance

**Build Parallelization:**
- Matrix builds for multi-platform (6x parallel)
- Independent job execution
- Conditional test execution (Linux AMD64 only)
- Parallel action execution

**Caching Strategy:**
- GitHub Actions cache for build artifacts
- Go module cache: ~/.cache/go-build
- Docker layer caching via buildx
- npm package cache for Node builds

**Artifact Management:**
- Upload only needed artifacts
- Set appropriate retention policies
- Clean up old artifacts regularly
- Use compression for downloads

## Quality Metrics

### Code Coverage

**Targets:**
- New code: ≥ 80% coverage
- Existing code: ≥ 70% coverage
- Critical functions: ≥ 90% coverage

**Measurement:**
```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
```

### Test Execution

**Time Limits:**
- Unit tests: < 30 seconds total
- Integration tests: < 2 minutes
- E2E tests: < 5 minutes

**Failure Handling:**
- No test skips (except platform-specific)
- Failing tests must be addressed immediately
- Root cause analysis for flaky tests
- Quarantine unreliable tests

### Build Reliability

**Success Rate Target**: ≥ 99%

**Failure Recovery:**
- Retry transient network failures (3 attempts)
- Clear error messages for debugging
- Build logs archived for analysis
- Alerts for repeated failures

## Monitoring and Observability

### Build Metrics

**Tracked:**
- Build duration (by platform)
- Success/failure rates
- Security scan results
- Artifact sizes
- Cache hit rates

**Dashboard:**
- GitHub Actions workflow runs page
- Build time trends
- Failure root causes

### Logging

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error conditions

**Log Format:**
- Timestamps (ISO 8601)
- Log level
- Component/function name
- Message
- Context data when relevant

## Review and Approval

### Code Review

**Requirements:**
- Minimum 1 approval before merge
- All conversation threads resolved
- CI checks must pass
- No new security vulnerabilities

**Focus Areas:**
- Code quality and style
- Test coverage
- Performance implications
- Security considerations
- Documentation completeness

### Release Review

**Pre-Release Checklist:**
- [ ] All tests passing
- [ ] Security scans cleared
- [ ] Version number updated
- [ ] Release notes drafted
- [ ] Documentation updated
- [ ] Performance benchmarks acceptable
- [ ] Changelog entry added
- [ ] Breaking changes documented

---

**Document Version**: 1.0
**Last Updated**: 2025-12-11
**Maintained by**: Penguin Tech Inc

For questions or updates to these standards, please contact the development team or submit an issue on GitHub.
