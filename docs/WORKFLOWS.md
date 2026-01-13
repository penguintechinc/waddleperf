# WaddlePerf CI/CD Workflows

## Overview

WaddlePerf uses GitHub Actions for comprehensive continuous integration and continuous deployment. All workflows follow the .WORKFLOW compliance standard with version detection, epoch64 timestamps, and security scanning.

## Workflow Compliance Features

All WaddlePerf workflows include:
- **Version Detection**: `.version` file path filtering triggers version-aware builds
- **Epoch64 Timestamps**: Unix epoch timestamps for precise build tracking
- **Version Detection Step**: Automatic .version file parsing with fallback to epoch timestamp
- **Conditional Metadata Tags**: Dynamic Docker tags based on version patterns
- **Security Scanning**: gosec for Go security vulnerabilities

## Core Services

### Go Client (`go-client/`)

**Workflow**: `build-go-client.yml`

Multi-platform binary building and Docker image creation for the WaddlePerf Go client.

**Triggers:**
- Push to main, v4.x, develop branches (with go-client/ or .version changes)
- Pull requests to main, v4.x branches (with go-client/ or .version changes)
- Release creation
- Manual dispatch

**Jobs:**
1. **build-binaries**: Compiles Go binaries for multiple platforms
   - Platforms: Linux (amd64/arm64), macOS (amd64/arm64), Windows (amd64/arm64)
   - Includes version detection from `.version` file
   - Generates epoch64 timestamps
   - Runs tests for Linux AMD64
   - Executes gosec security scanning

2. **build-macos-universal**: Creates universal macOS binary
   - Combines AMD64 and ARM64 binaries using lipo
   - Depends on successful build-binaries job

3. **build-docker-images**: Builds and pushes multi-platform Docker images
   - Supports Linux amd64/arm64
   - Push to GHCR and Docker Hub
   - Generates semantic version tags
   - Caches builds using GitHub Actions cache

4. **create-release-packages**: Creates distribution packages
   - Generates tar.gz archives for Unix systems
   - Generates .zip archives for Windows
   - Creates SHA256SUMS.txt checksums
   - Uploads to GitHub releases

5. **summary**: Provides build summary and status

**Metadata Tags:**
- Semantic version: `type=semver,pattern={{version}}`
- Major/Minor: `type=semver,pattern={{major}}.{{minor}}`
- Branch: `type=raw,value={{branch}}-{{sha}}`
- Version file: Dynamic tag from .version

### Test Server (`testServer/`)

**Workflow**: `testserver.yml`

Comprehensive testing and Docker image building for the WaddlePerf test server.

**Triggers:**
- Push to main, 4.x branches (with testServer/ or .version changes)
- Tags matching `v*` pattern
- Pull requests to main, 4.x branches
- Manual dispatch

**Jobs:**
1. **test**: Validates Go code quality and security
   - Version detection from `.version` file
   - Runs `go test -v ./...`
   - Runs `go vet ./...`
   - Executes gosec security scanning with JSON output
   - Validates code formatting with gofmt

2. **build**: Multi-platform Docker image build and push
   - Requires successful test job
   - Supports Linux amd64/arm64 architectures
   - Authenticates with GHCR and Docker Hub
   - Generates version-specific tags
   - Caches builds for faster rebuild

3. **summary**: Build status reporting

**Metadata Tags:**
- Latest: `latest` on main branch
- Beta: `beta` on main branch
- Alpha: `alpha` on non-main, non-tag pushes
- Semantic version: `semver,pattern={{version}}`
- Branch and commit: `{{branch}}-{{sha}}`

## Version Management

### .version File Format

Location: `/home/penguin/code/WaddlePerf/.version`

Current version: `v4.0.0alpha`

**Format**:
```
vMajor.Minor.Patch[.build]
```

**Examples:**
- `v1.0.0` - Semantic version (build will add epoch64)
- `v4.0.0alpha` - Pre-release version
- `v2.5.1.1737727200` - Version with epoch64 timestamp

### Version Detection Step

All workflows include version detection that:
1. Reads `.version` file content
2. Strips whitespace
3. Falls back to `0.0.0.{epoch64}` if file missing
4. Exports both version and epoch64 timestamp
5. Uses version for Docker tags and release names

**Example Output:**
```bash
version=v4.0.0alpha
epoch64=1737727200
```

## Security Scanning

### gosec for Go Projects

**Configuration:**
- Installed: `go install github.com/securego/gosec/v2/cmd/gosec@latest`
- Output: JSON format for programmatic processing
- Files: `gosec-results.json`
- Behavior: Warnings only (continue-on-error)

**Integration Points:**
- `build-go-client.yml`: Runs in Docker build (securitycheck target)
- `testserver.yml`: Runs directly in test job

**Output Handling:**
```bash
gosec -fmt json -out gosec-results.json ./...
```

## Docker Image Tagging Strategy

### Tag Types

**Semantic Versioning:**
```
ghcr.io/penguintechinc/waddleperf-go-client:v1.2.3
ghcr.io/penguintechinc/waddleperf-go-client:1.2
```

**Branch Tags:**
```
ghcr.io/penguintechinc/waddleperf-go-client:main-a1b2c3d4
ghcr.io/penguintechinc/waddleperf-go-client:v4.x-e5f6g7h8
```

**Release Tags:**
```
ghcr.io/penguintechinc/waddleperf-go-client:latest
ghcr.io/penguintechinc/waddleperf-go-client:beta
ghcr.io/penguintechinc/waddleperf-go-client:alpha
```

**Version File Tags:**
```
ghcr.io/penguintechinc/waddleperf-go-client:v4.0.0alpha
```

## Release Management

### Automatic Pre-Release Creation

**Workflow**: `version-release.yml`

Triggered when `.version` file is updated on main branch.

**Process:**
1. Detects version from `.version` file
2. Generates epoch64 timestamp
3. Checks if release already exists
4. Creates release notes with metadata tags
5. Tags release based on version pattern:
   - `[prerelease]` for alpha/beta versions
   - `[release-candidate]` for rc versions
   - `[stable]` for release versions
6. Creates pre-release in GitHub

**Release Notes Include:**
- Semantic version
- Full version with timestamp
- Epoch64 timestamp
- Commit SHA
- Branch name
- Build time (ISO 8601)

## Performance Optimization

### Build Caching

**Strategy:**
- GitHub Actions cache for Docker layers
- Go module cache: `~/.cache/go-build` and `~/go/pkg/mod`
- Buildx native caching for multi-platform builds

**Cache Keys:**
```yaml
key: ${{ runner.os }}-go-${{ matrix.go-version }}-${{ hashFiles('**/go.sum') }}
restore-keys: |
  ${{ runner.os }}-go-${{ matrix.go-version }}-
```

### Conditional Execution

**Test Execution:**
- Tests only run on Linux AMD64 platform in build-binaries job
- Avoids redundant testing for cross-compilation targets

**Build Parallelization:**
- build-binaries matrix: 6 platforms in parallel
- Docker push only on non-PR events
- Separate jobs for binary and Docker image builds

### Docker Layer Caching

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

Enables GitHub Actions cache for multi-architecture Docker builds.

## Monitoring and Troubleshooting

### Build Summary

All workflows include a summary job that:
- Reports job status for all dependencies
- Displays version information
- Shows event name and branch
- Provides commit SHA

### Common Issues

**Version Detection Fails:**
- Check `.version` file exists and is readable
- Verify no leading/trailing whitespace
- Confirm file contains valid semantic version

**Docker Push Fails:**
- Verify GitHub token has package write permissions
- Check Docker Hub credentials in secrets
- Ensure image names follow naming conventions

**gosec Security Warnings:**
- Warnings are non-blocking (continue-on-error)
- Review JSON output in `gosec-results.json`
- Address high-severity issues before release

**Cross-Platform Build Failures:**
- Platform-specific code may fail on unsupported architectures
- Build matrix tests on all platforms
- Check Docker buildx platform support

## Maintenance

### Updating Workflow Versions

1. Edit workflow file in `.github/workflows/`
2. Update action versions: `actions/checkout@v4` → `actions/checkout@vX`
3. Test in a feature branch
4. Create PR for review
5. Merge to main

### Adding New Workflows

1. Create new file: `.github/workflows/new-service.yml`
2. Include `.version` path filter
3. Add version detection step
4. Implement security scanning
5. Document in this file

### Dependency Updates

- Monitor GitHub Dependabot alerts
- Update action versions monthly
- Test thoroughly before pushing to main
- Update documentation if behavior changes

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx Documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [gosec Security Scanner](https://github.com/securego/gosec)
- [WaddlePerf Project Structure](./ARCHITECTURE.md)
- [WaddlePerf CI/CD Standards](./STANDARDS.md)
