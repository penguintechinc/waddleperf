# Contributing to WaddlePerf

**Version**: 2.0
**Last Updated**: November 12, 2025

Thank you for your interest in contributing to WaddlePerf! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Pull Request Process](#pull-request-process)
- [Building and Testing](#building-and-testing)
- [Documentation](#documentation)
- [License](#license)

---

## Code of Conduct

This project and everyone participating in it is governed by the Penguin Technologies Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to conduct@penguintech.com.

**Expected Behavior**:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior**:
- Harassment, discrimination, or hate speech
- Publishing others' private information
- Trolling, insulting/derogatory comments
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

Before you begin contributing, make sure you have:

1. A GitHub account
2. Git installed and configured
3. Development tools installed (see Development Setup)
4. Familiarity with the technologies used:
   - Go 1.21+ (for testServer and goClient)
   - Python 3.13+ (for managerServer API and containerClient)
   - TypeScript/React (for frontends)
   - Docker and Docker Compose
   - MariaDB/MySQL

### Finding Work

**Good First Issues**: Look for issues labeled `good first issue` for beginner-friendly tasks.

**Help Wanted**: Issues labeled `help wanted` are priorities that need contributors.

**Feature Requests**: Check issues labeled `enhancement` for new features.

**Bug Reports**: Issues labeled `bug` need investigation and fixes.

You can also:
- Review open pull requests
- Improve documentation
- Add tests
- Fix typos or improve clarity

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/WaddlePerf.git
cd WaddlePerf

# Add upstream remote
git remote add upstream https://github.com/penguintechinc/WaddlePerf.git
```

### 2. Install Dependencies

#### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  git \
  docker.io docker-compose \
  golang-go \
  python3 python3-pip python3-venv \
  nodejs npm \
  build-essential

# macOS (with Homebrew)
brew install git docker docker-compose go python@3.13 node

# Verify installations
go version        # Should be 1.21+
python3 --version # Should be 3.13+
node --version    # Should be 18+
docker --version
```

#### Go Dependencies

```bash
cd testServer
go mod download
go mod tidy

cd ../goClient
go mod download
go mod tidy
```

#### Python Dependencies

```bash
# managerServer API
cd managerServer/api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# webClient API
cd ../../webClient/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# containerClient
cd ../../containerClient
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Frontend Dependencies

```bash
# managerServer Frontend
cd managerServer/frontend
npm install

# webClient Frontend
cd ../../webClient/frontend
npm install
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with development settings (default values work for dev)
```

### 4. Start Development Environment

```bash
# Start database and backend services
docker-compose -f docker-compose.dev.yml up -d mariadb testserver managerserver-api webclient-api

# Start frontends in development mode (hot reload)
cd managerServer/frontend
npm run dev &

cd ../../webClient/frontend
npm run dev &
```

### 5. Verify Setup

```bash
# Check services are running
curl http://localhost:8080/health  # testServer
curl http://localhost:5000/health  # managerServer API
curl http://localhost:5001/health  # webClient API

# Check frontends
open http://localhost:3000  # managerServer Frontend
open http://localhost:3001  # webClient Frontend
```

---

## Project Structure

```
WaddlePerf/
├── testServer/              # Go - High-performance test execution
│   ├── cmd/testserver/      # Main application
│   ├── internal/
│   │   ├── auth/           # Authentication logic
│   │   ├── database/       # Database operations
│   │   ├── handlers/       # HTTP handlers
│   │   └── protocols/      # Test implementations (HTTP/TCP/UDP/ICMP)
│   └── Dockerfile
│
├── managerServer/          # Management backend and frontend
│   ├── api/                # Python Flask API
│   │   ├── routes/         # API endpoints
│   │   ├── models.py       # Database models
│   │   ├── config.py       # Configuration
│   │   └── app.py          # Main application
│   └── frontend/           # React/TypeScript UI
│       ├── src/
│       │   ├── components/ # React components
│       │   ├── pages/      # Page components
│       │   └── api/        # API client
│       └── Dockerfile.frontend
│
├── webClient/              # Browser-based test client
│   ├── api/                # Python Flask API with WebSocket
│   │   └── app.py          # Main application
│   └── frontend/           # React/TypeScript UI
│       ├── src/
│       │   ├── components/ # React components
│       │   └── pages/      # Page components
│       └── Dockerfile.frontend
│
├── goClient/               # Cross-platform desktop client
│   ├── cmd/waddleperf/     # Main application
│   ├── internal/
│   │   ├── config/         # Configuration management
│   │   ├── protocols/      # Test implementations
│   │   ├── scheduler/      # Test scheduling
│   │   ├── uploader/       # Result upload
│   │   └── tray/           # System tray integration
│   └── config.example.yaml
│
├── containerClient/        # Automated testing container
│   ├── client.py           # Main application
│   ├── tests/              # Test implementations
│   └── Dockerfile
│
├── database/               # Database schema and migrations
│   ├── schema.sql          # Complete schema
│   └── seeds/              # Seed data
│
├── docs/                   # Documentation
│   ├── API.md              # API documentation
│   ├── USAGE.md            # User guide
│   ├── INSTALLATION.md     # Installation guide
│   ├── CONTRIBUTING.md     # This file
│   └── ARCHITECTURE.md     # Architecture overview
│
├── docker-compose.yml      # Production compose file
├── docker-compose.dev.yml  # Development compose file
└── .env.example            # Environment variables template
```

---

## Coding Standards

Following consistent coding standards makes the codebase easier to maintain and review.

### Go Code Standards

**Formatting**:
```bash
# Always run before committing
go fmt ./...
go vet ./...

# Optional: Use golangci-lint for advanced linting
golangci-lint run
```

**Style Guidelines**:
- Follow the [Effective Go](https://golang.org/doc/effective_go.html) guidelines
- Use descriptive variable names (avoid single letters except for short-lived variables)
- Comment all exported functions, types, and constants
- Group related code with blank lines
- Keep functions short and focused (prefer multiple small functions)
- Use early returns to reduce nesting

**Example**:
```go
// TestHTTP executes an HTTP performance test against the target URL.
// It returns detailed timing metrics including DNS lookup, TCP connect,
// TLS handshake, and total request time.
func TestHTTP(req HTTPTestRequest) (*HTTPTestResult, error) {
    if req.Target == "" {
        return nil, fmt.Errorf("target URL is required")
    }

    // Create HTTP client with timeout
    client := &http.Client{
        Timeout: time.Duration(req.Timeout) * time.Second,
    }

    // Execute request and measure timing
    start := time.Now()
    resp, err := client.Get(req.Target)
    if err != nil {
        return nil, fmt.Errorf("request failed: %w", err)
    }
    defer resp.Body.Close()

    elapsed := time.Since(start)

    return &HTTPTestResult{
        StatusCode: resp.StatusCode,
        LatencyMS:  float64(elapsed.Milliseconds()),
        Success:    resp.StatusCode >= 200 && resp.StatusCode < 300,
    }, nil
}
```

**Error Handling**:
- Always check and handle errors
- Wrap errors with context using `fmt.Errorf` with `%w`
- Log errors with appropriate log levels
- Return sentinel errors for expected error conditions

---

### Python Code Standards

**Formatting**:
```bash
# Use black for code formatting
black .

# Use isort for import sorting
isort .

# Use flake8 for linting
flake8 .

# Use mypy for type checking
mypy .
```

**Style Guidelines**:
- Follow [PEP 8](https://pep8.org/)
- Use type hints for function parameters and return values
- Write docstrings for all functions, classes, and modules (Google style)
- Keep functions under 50 lines when possible
- Use descriptive variable names
- Prefer list comprehensions over map/filter for simple cases

**Example**:
```python
from typing import Optional, Dict, Any
import aiohttp


async def upload_result(
    session: aiohttp.ClientSession,
    manager_url: str,
    result_data: Dict[str, Any],
    api_key: str
) -> bool:
    """Upload test result to manager server.

    Args:
        session: Async HTTP client session
        manager_url: Base URL of manager server
        result_data: Test result dictionary
        api_key: Authentication API key

    Returns:
        True if upload successful, False otherwise

    Raises:
        aiohttp.ClientError: If network error occurs
    """
    upload_url = f"{manager_url}/api/v1/results/upload"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with session.post(upload_url, json=result_data, headers=headers) as response:
            if response.status in (200, 201):
                return True

            error_text = await response.text()
            logger.error(f"Upload failed: {response.status} - {error_text}")
            return False

    except aiohttp.ClientError as e:
        logger.error(f"Network error during upload: {e}")
        raise
```

---

### TypeScript/React Code Standards

**Formatting**:
```bash
# Use ESLint and Prettier
npm run lint
npm run format
```

**Style Guidelines**:
- Use TypeScript strict mode
- Define interfaces for all props and state
- Use functional components with hooks
- Keep components small and focused
- Use meaningful component and variable names
- Separate concerns (presentation vs. logic)
- Use async/await instead of promises
- Handle errors gracefully

**Example**:
```typescript
import React, { useState, useEffect } from 'react';

interface TestResult {
  target: string;
  latency_ms: number;
  success: boolean;
  timestamp: string;
}

interface TestResultsProps {
  apiUrl: string;
  deviceSerial: string;
}

export const TestResults: React.FC<TestResultsProps> = ({ apiUrl, deviceSerial }) => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `${apiUrl}/api/v1/statistics/device/${deviceSerial}`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        setResults(data.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [apiUrl, deviceSerial]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="test-results">
      <h2>Test Results for {deviceSerial}</h2>
      <ul>
        {results.map((result, index) => (
          <li key={index}>
            {result.target}: {result.latency_ms}ms
            {result.success ? ' ✓' : ' ✗'}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

---

## Testing Requirements

All contributions must include appropriate tests. Code without tests will not be merged.

### Go Tests

```bash
# Run all tests
cd testServer
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests with race detection
go test -race ./...

# Run specific test
go test -run TestHTTPTest ./internal/protocols
```

**Test Example**:
```go
func TestHTTPTest(t *testing.T) {
    req := HTTPTestRequest{
        Target:   "https://example.com",
        Protocol: "auto",
        Timeout:  30,
    }

    result, err := TestHTTP(req)

    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Equal(t, 200, result.StatusCode)
    assert.True(t, result.Success)
    assert.Greater(t, result.LatencyMS, 0.0)
}
```

### Python Tests

```bash
# Run all tests with pytest
cd managerServer/api
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

**Test Example**:
```python
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client


def test_login_success(client):
    """Test successful login with valid credentials"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert 'user' in data
    assert data['user']['username'] == 'testuser'


def test_login_invalid_credentials(client):
    """Test login fails with invalid credentials"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpass'
    })

    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
```

### Frontend Tests

```bash
# Run tests
cd managerServer/frontend
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

### Integration Tests

Before submitting, ensure the entire stack works:

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
sleep 10

# Run integration tests
./scripts/integration-tests.sh
```

---

## Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-dns-testing` - New features
- `fix/database-connection` - Bug fixes
- `docs/api-examples` - Documentation
- `refactor/auth-module` - Code refactoring
- `test/http-protocol` - Test additions

### Commit Messages

Write clear, descriptive commit messages:

**Format**:
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: add UDP DNS query testing

Implement UDP protocol support for DNS queries with proper
timeout handling and response parsing. Includes tests for
both successful and failed queries.

Closes #123

---

fix: correct latency calculation in ICMP tests

The previous calculation included processing time which
inflated results. Now measures only network round-trip time.

Fixes #456

---

docs: add API examples for all test endpoints

Added curl examples and response formats for HTTP, TCP,
UDP, and ICMP test endpoints in API.md.
```

---

## Pull Request Process

### 1. Before Creating PR

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... code, test, commit ...

# Run tests and linting
./scripts/run-tests.sh
./scripts/run-linting.sh

# Push to your fork
git push origin feature/your-feature-name
```

### 2. Create Pull Request

1. Go to https://github.com/penguintechinc/WaddlePerf
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

```markdown
## Description
Brief description of what this PR does

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added/updated unit tests
- [ ] Added/updated integration tests
- [ ] Manually tested locally
- [ ] All tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed my code
- [ ] Commented complex code sections
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests that prove fix/feature works
- [ ] New and existing tests pass locally
```

### 3. Code Review Process

Your PR will be reviewed by maintainers who may:
- Request changes
- Ask questions
- Suggest improvements
- Approve and merge

**Responding to Reviews**:
- Address all comments
- Push additional commits (don't force-push during review)
- Mark conversations as resolved when addressed
- Be respectful and open to feedback

### 4. After Merge

```bash
# Update your local repository
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## Building and Testing

### Building Components

#### testServer (Go)
```bash
cd testServer

# Build for current platform
go build -o waddleperf-testserver ./cmd/testserver

# Build for multiple platforms
GOOS=linux GOARCH=amd64 go build -o waddleperf-testserver-linux-amd64 ./cmd/testserver
GOOS=darwin GOARCH=arm64 go build -o waddleperf-testserver-darwin-arm64 ./cmd/testserver
GOOS=windows GOARCH=amd64 go build -o waddleperf-testserver-windows-amd64.exe ./cmd/testserver

# Run tests
go test ./...

# Run with race detection
go test -race ./...
```

#### goClient
```bash
cd goClient

# Build for current platform
go build -o waddleperf ./cmd/waddleperf

# Build for multiple platforms
make build-all  # If Makefile exists

# Run tests
go test ./...
```

#### managerServer API
```bash
cd managerServer/api

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Type checking
mypy .

# Linting
flake8 .
black --check .
isort --check .
```

#### Frontends
```bash
# managerServer Frontend
cd managerServer/frontend
npm install
npm run build
npm test
npm run lint

# webClient Frontend
cd ../../webClient/frontend
npm install
npm run build
npm test
npm run lint
```

### Docker Builds

```bash
# Build individual images
docker build -t waddleperf-testserver ./testServer
docker build -t waddleperf-manager-api -f ./managerServer/api/Dockerfile.api ./managerServer/api
docker build -t waddleperf-manager-frontend -f ./managerServer/frontend/Dockerfile.frontend ./managerServer/frontend

# Build all with docker-compose
docker-compose build

# Build and run
docker-compose up -d
```

---

## Documentation

Documentation is crucial for users and developers.

### Updating Documentation

When making changes that affect:
- **API endpoints**: Update `docs/API.md`
- **User interfaces**: Update `docs/USAGE.md`
- **Installation process**: Update `docs/INSTALLATION.md`
- **Architecture**: Update `docs/ARCHITECTURE.md`
- **Code structure**: Update code comments and this file

### Writing Good Documentation

**Do**:
- Write clear, concise explanations
- Include working examples
- Use proper markdown formatting
- Add screenshots for UI features
- Keep examples up-to-date
- Test all code examples

**Don't**:
- Use vague language ("might", "could", "maybe")
- Include outdated information
- Write overly technical jargon
- Leave placeholders or TODOs
- Copy-paste without testing

### Example Documentation

```markdown
## Running HTTP Tests

To execute an HTTP performance test, send a POST request to the test endpoint:

### Request

\`\`\`bash
curl -X POST http://localhost:8080/api/v1/test/http \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://www.google.com",
    "protocol": "auto",
    "timeout": 30
  }'
\`\`\`

### Response

\`\`\`json
{
  "status_code": 200,
  "latency_ms": 45.23,
  "ttfb_ms": 42.15,
  "success": true
}
\`\`\`

### Parameters

- `target` (required): URL to test
- `protocol` (optional): HTTP version (default: "auto")
- `timeout` (optional): Timeout in seconds (default: 30)
```

---

## License

By contributing to WaddlePerf, you agree that your contributions will be licensed under the same license as the project (see LICENSE.md).

### Copyright Notice

All contributions must include the following copyright notice in file headers:

```go
// Copyright © 2025 Penguin Technologies Inc.
// SPDX-License-Identifier: SEE LICENSE IN LICENSE.md
```

```python
# Copyright © 2025 Penguin Technologies Inc.
# SPDX-License-Identifier: SEE LICENSE IN LICENSE.md
```

```typescript
/**
 * Copyright © 2025 Penguin Technologies Inc.
 * SPDX-License-Identifier: SEE LICENSE IN LICENSE.md
 */
```

---

## Getting Help

**Questions?**
- GitHub Discussions: https://github.com/penguintechinc/WaddlePerf/discussions
- Discord: https://discord.gg/penguintech
- Email: opensource@penguintech.com

**Found a Bug?**
- Check existing issues: https://github.com/penguintechinc/WaddlePerf/issues
- Create a new issue with:
  - Clear description
  - Steps to reproduce
  - Expected vs. actual behavior
  - Screenshots/logs if applicable

**Feature Request?**
- Open an issue labeled `enhancement`
- Describe the use case
- Explain why it benefits users
- Consider contributing the implementation!

---

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Significant contributors may be invited to join the core maintainers team.

---

**Thank you for contributing to WaddlePerf!**

**Copyright © 2025 Penguin Technologies Inc.**
