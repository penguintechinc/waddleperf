# WaddlePerf Testing Guide

Comprehensive testing documentation for WaddlePerf's multi-tier testing strategies, performance monitoring, and network diagnostic testing across all components.

## Overview

WaddlePerf implements a three-tier testing strategy to balance speed, coverage, and comprehensiveness:

| Test Level | Purpose | Speed | Coverage | Tier |
|-----------|---------|-------|----------|------|
| **Smoke Tests** | Build, run, health checks, page loads | <2 min | Core functionality, basic connectivity | Tier 1 |
| **Unit Tests** | Isolated protocol/metric testing | <2 min | Protocol handlers, calculation logic | Tier 1 |
| **Integration Tests** | Component interaction, database ops | 2-5 min | Multi-service flows, API contracts | Tier 2 |
| **Network Tests** | Real-world test scenarios | 3-10 min | Network diagnostics, protocol testing | Tier 2 |
| **Performance Tests** | Load testing, multi-client scenarios | 5-15 min | Scalability, throughput, latency | Tier 3 |
| **Cross-Architecture Tests** | Multi-platform validation | 10-20 min | ARM64/AMD64 compatibility | Tier 3 |

---

## Mock Data Scripts

### Purpose

Mock data scripts populate the development database with realistic test data, enabling:
- Rapid local development without manual data entry
- Consistent test scenarios across the development team
- Documentation of expected data structure and relationships
- Quick feature iteration with pre-populated databases

### Location & Structure

```
scripts/mock-data/
├── seed-all.py             # Orchestrator: runs all seeders in order
├── seed-users.py           # 3-4 users with different roles/permissions
├── seed-test-configs.py    # 3-4 test configurations (HTTP, TCP, UDP, ICMP)
├── seed-test-results.py    # 3-4 sample results from different test runs
├── seed-devices.py         # 3-4 client devices (goClient, containerClient)
├── seed-[feature].py       # Additional feature-specific seeders
└── README.md               # Instructions for running mock data
```

### Scope: 3-4 Items Per Feature

Each seeder should create **exactly 3-4 representative items** to test all feature variations:

**Example (Test Configurations)**:
```python
# seed-test-configs.py
items = [
    {"name": "HTTP Speed Test", "protocol": "http", "enabled": True, "tier": 1},
    {"name": "TCP Latency Test", "protocol": "tcp", "enabled": True, "tier": 2},
    {"name": "UDP Packet Loss", "protocol": "udp", "enabled": True, "tier": 2},
    {"name": "ICMP Traceroute", "protocol": "icmp", "enabled": False, "tier": 3},
]
```

**Example (Test Results)**:
```python
# seed-test-results.py
items = [
    {"test_id": 1, "status": "passed", "latency_ms": 25, "jitter_ms": 2, "packet_loss": 0},
    {"test_id": 2, "status": "passed", "latency_ms": 150, "jitter_ms": 15, "packet_loss": 1},
    {"test_id": 3, "status": "failed", "latency_ms": 500, "jitter_ms": 100, "packet_loss": 5},
    {"test_id": 4, "status": "timeout", "latency_ms": None, "jitter_ms": None, "packet_loss": 100},
]
```

### Execution

**Seed all test data**:
```bash
make seed-mock-data          # Via Makefile
python scripts/mock-data/seed-all.py  # Direct execution
```

**Seed specific feature**:
```bash
python scripts/mock-data/seed-test-configs.py
python scripts/mock-data/seed-test-results.py
python scripts/mock-data/seed-devices.py
```

### Implementation Pattern

**Python (PyDAL)**:
```python
#!/usr/bin/env python3
"""Seed mock data for test configurations."""

import os
import sys
from dal import DAL

def seed_test_configs():
    db = DAL('mysql://root:password@localhost/waddleperf_dev')

    configs = [
        {"name": "HTTP Speed Test", "protocol": "http", "enabled": True},
        {"name": "TCP Test", "protocol": "tcp", "enabled": True},
        {"name": "UDP Test", "protocol": "udp", "enabled": True},
        {"name": "ICMP Test", "protocol": "icmp", "enabled": False},
    ]

    for config in configs:
        db.test_configs.insert(**config)

    print(f"✓ Seeded {len(configs)} test configurations")

if __name__ == "__main__":
    seed_test_configs()
```

---

## Tier 1: Smoke Tests

### Purpose

Smoke tests provide fast verification that basic functionality works after code changes, preventing regressions in core features. **Tier 1 must complete in <2 minutes**.

### Requirements (Mandatory)

All components **MUST** implement smoke tests before committing:

- ✅ **Build Tests**: All containers build successfully without errors
- ✅ **Run Tests**: All containers start and remain healthy
- ✅ **API Health Checks**: All API endpoints respond with 200/healthy status
- ✅ **Page Load Tests**: All web pages load without JavaScript errors
- ✅ **Protocol Handler Tests**: All protocol implementations load correctly

### Location & Structure

```
tests/smoke/
├── build/          # Container build verification
│   ├── test-testserver-build.sh
│   ├── test-manager-build.sh
│   ├── test-webclient-build.sh
│   └── test-go-client-build.sh
├── run/            # Container runtime and health
│   ├── test-testserver-run.sh
│   ├── test-manager-run.sh
│   └── test-webclient-run.sh
├── api/            # API health endpoint validation
│   ├── test-testserver-health.sh
│   ├── test-manager-api-health.sh
│   └── test-webclient-api-health.sh
├── webui/          # Page load and tab navigation
│   ├── test-manager-ui-loads.sh
│   ├── test-webclient-ui-loads.sh
│   └── README.md
├── run-all.sh      # Execute all smoke tests
└── README.md       # Documentation
```

### Execution

**Run all smoke tests**:
```bash
make smoke-test              # Via Makefile
./tests/smoke/run-all.sh     # Direct execution
```

**Run specific test category**:
```bash
./tests/smoke/build/test-testserver-build.sh
./tests/smoke/api/test-testserver-health.sh
./tests/smoke/webui/test-manager-ui-loads.sh
```

### Implementation Examples

**Build Test (Shell)**:
```bash
#!/bin/bash
# tests/smoke/build/test-testserver-build.sh

set -e

echo "Testing testServer build..."
cd testserver

if docker build -t testserver:test .; then
    echo "✓ testServer builds successfully"
    exit 0
else
    echo "✗ testServer build failed"
    exit 1
fi
```

**Health Check Test**:
```bash
#!/bin/bash
# tests/smoke/api/test-testserver-health.sh

set -e

echo "Checking testServer health..."
HEALTH_URL="http://localhost:8080/health"

RESPONSE=$(curl -s -w "\n%{http_code}" "$HEALTH_URL")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ testServer API is healthy (HTTP $HTTP_CODE)"
    exit 0
else
    echo "✗ testServer API is unhealthy (HTTP $HTTP_CODE)"
    exit 1
fi
```

---

## Tier 2: Integration Tests

### Purpose

Integration tests verify that components work together correctly, including real database interactions and service communication. Tests are executed on feature branches and main. **Tier 2 must complete in <5 minutes**.

### Location & Structure

```
tests/integration/
├── testserver/
│   ├── test-protocol-execution.py
│   ├── test-result-storage.py
│   └── test-multi-protocol-flow.py
├── manager/
│   ├── test-auth-flow.py
│   ├── test_user_management.py
│   └── test_api_contracts.py
├── webclient/
│   ├── test_test_submission.py
│   └── test_result_retrieval.py
├── database/
│   ├── test_migrations.py
│   ├── test_galera_clustering.py
│   └── test_result_queries.py
└── multi_component/
    ├── test_end_to_end_speed_test.py
    └── test_multi_tier_escalation.py
```

### Execution

```bash
make test-integration       # All integration tests
pytest tests/integration/   # Python
go test -tags=integration ./...  # Go
npm run test:integration    # JavaScript
```

### Examples

**Test testServer → Database Flow**:
```python
# tests/integration/testserver/test_result_storage.py
import pytest
from testserver import TestServer
from dal import DAL

def test_http_result_storage():
    """Verify HTTP test results are stored correctly."""
    server = TestServer()
    db = DAL('mysql://root:password@localhost/waddleperf_dev')

    # Execute test
    result = server.run_http_test("example.com", 443)

    # Verify result stored in database
    stored = db(db.test_results.test_id == result['id']).select()[0]
    assert stored.status == 'passed'
    assert stored.latency_ms > 0
```

**Test Multi-Component Flow**:
```python
# tests/integration/multi_component/test_end_to_end_speed_test.py
def test_speed_test_flow():
    """Test complete speed test from WebUI → API → testServer → DB."""

    # 1. Authenticate with manager API
    token = auth_manager_api()

    # 2. Create speed test via WebClient API
    test_id = create_test(token, test_type='speed_test')

    # 3. Poll testServer for results
    results = get_test_results(test_id)

    # 4. Verify results stored in database
    assert results['download_mbps'] > 0
    assert results['latency_ms'] >= 0
```

---

## Tier 3: Comprehensive Tests

### Purpose

Comprehensive tests validate scalability, throughput, resource usage under load, and cross-platform compatibility. Tests run nightly or pre-release. **Tier 3 runs 5-15 minutes**.

### Location & Structure

```
tests/performance/
├── load-tests/
│   ├── concurrent-tests.js
│   ├── sustained-load.js
│   └── spike-testing.js
├── stress-tests/
│   ├── database-stress.py
│   ├── protocol-stress.go
│   └── connection-pool-stress.py
├── profile-reports/
│   ├── cpu-profile.py
│   ├── memory-profile.py
│   └── network-profile.sh
└── cross-platform/
    ├── test-arm64-build.sh
    ├── test-amd64-build.sh
    └── test-compatibility.sh
```

### Execution

```bash
make test-performance         # All performance tests
npm run test:performance      # Load testing
go test -bench ./...          # Go benchmarks
./tests/cross-platform/test-arm64-build.sh  # ARM64 validation
```

### Performance Testing Example

**Load Test - Concurrent Speed Tests**:
```javascript
// tests/performance/load-tests/concurrent-tests.js
const http = require('http');

async function runConcurrentTests(numClients = 50) {
    const results = [];
    const startTime = Date.now();

    for (let i = 0; i < numClients; i++) {
        results.push(
            new Promise((resolve) => {
                http.get('http://localhost:8080/api/v1/tests/speed', (res) => {
                    resolve({ status: res.statusCode, time: Date.now() - startTime });
                });
            })
        );
    }

    const responses = await Promise.all(results);
    const successCount = responses.filter(r => r.status === 200).length;
    const avgLatency = responses.reduce((a, b) => a + b.time, 0) / responses.length;

    console.log(`✓ ${successCount}/${numClients} concurrent tests succeeded`);
    console.log(`✓ Average latency: ${avgLatency.toFixed(2)}ms`);

    return { successCount, avgLatency };
}
```

---

## Network Test Implementation

### Protocol Testing

**TCP Test Example**:
```python
# tests/integration/testserver/test_tcp_protocol.py
def test_tcp_latency_measurement():
    """Verify TCP latency measurement accuracy."""
    from testserver.protocols import TCPTest

    test = TCPTest(host='example.com', port=443, timeout=10)
    result = test.run()

    assert result['status'] == 'success'
    assert 0 < result['latency_ms'] < 1000
    assert 'jitter_ms' in result
    assert 'packets_lost' in result
```

**UDP Test Example**:
```go
// testserver/protocols/udp_test.go
func TestUDPPacketLoss(t *testing.T) {
    test := NewUDPTest("8.8.8.8", 53, 1000)
    result := test.Run()

    assert.Equal(t, "success", result.Status)
    assert.Greater(t, int64(0), result.PacketsLost)
    assert.Greater(t, result.PacketsReceived, int64(0))
}
```

---

## Multi-Tier Escalation Testing

### Test Escalation Flow

```python
# tests/integration/multi_component/test_multi_tier_escalation.py
def test_tier_1_to_tier_3_escalation():
    """Test automatic escalation from Tier 1 through Tier 3."""

    # Tier 1: Basic connectivity test (30 seconds)
    tier1_result = run_tier1_test("example.com")

    if tier1_result['status'] == 'failed':
        # Escalate to Tier 2
        tier2_result = run_tier2_test("example.com")

        if tier2_result['status'] == 'failed':
            # Escalate to Tier 3
            tier3_result = run_tier3_test("example.com")
            assert tier3_result['comprehensive_analysis'] is not None

    assert tier1_result['tier'] == 1
```

---

## Cross-Architecture Testing

### Purpose

Cross-architecture testing ensures components build and run correctly on both amd64 and arm64 architectures, preventing platform-specific bugs.

### Setup (First Time)

Enable Docker buildx for multi-architecture builds:

```bash
docker buildx create --name multiarch --driver docker-container
docker buildx use multiarch
```

### Single Architecture Build

```bash
# Test current architecture (native, fast)
docker build -t testserver:test testserver/

# Or explicitly specify architecture
docker build --platform linux/amd64 -t testserver:test testserver/
```

### Cross-Architecture Build

```bash
# Test alternate architecture (uses QEMU emulation)
docker buildx build --platform linux/arm64 -t testserver:test testserver/

# Test both simultaneously
docker buildx build --platform linux/amd64,linux/arm64 \
  -t testserver:test testserver/
```

### Multi-Architecture Test Script

```bash
#!/bin/bash
# tests/cross-platform/test-multiarch.sh

set -e

SERVICES=("testserver" "manager" "webclient")
ARCHITECTURES=("linux/amd64" "linux/arm64")

for service in "${SERVICES[@]}"; do
    echo "Testing $service on multiple architectures..."

    for arch in "${ARCHITECTURES[@]}"; do
        echo "  → Building for $arch..."
        docker buildx build \
            --platform "$arch" \
            -t "waddleperf-$service:multiarch-test" \
            "$service/" || {
            echo "✗ Build failed for $service on $arch"
            exit 1
        }
    done

    echo "✓ $service builds successfully on amd64 and arm64"
done

echo "✓ All services passed multi-architecture testing"
```

---

## Test Execution Order (Pre-Commit)

Follow this order for efficient testing before commits:

1. **Linters** (fast, <1 min)
   - Python: flake8, black, isort, mypy
   - Go: golangci-lint
   - JavaScript: eslint, prettier

2. **Security scans** (fast, <1 min)
   - Python: bandit, safety check
   - Go: gosec
   - Node.js: npm audit

3. **Secrets check** (fast, <1 min)
   - No API keys, passwords, tokens in code

4. **Build & Run** (5-10 min)
   - Build all containers
   - Verify runtime health

5. **Smoke tests** (fast, <2 min) ← **Gates further testing**
   - All containers build
   - API health checks pass
   - UI pages load

6. **Unit tests** (1-2 min)
   - Protocol handler tests
   - Calculation logic tests

7. **Integration tests** (2-5 min)
   - Component interaction
   - Database operations

8. **Network tests** (optional, 3-10 min)
   - Real test scenarios
   - Protocol validation

9. **Cross-architecture build** (optional, slow 10-20 min)
   - ARM64/AMD64 compatibility

---

## CI/CD Integration

All tests run automatically in GitHub Actions:

- **On PR**: Smoke + Unit + Integration tests
- **On main merge**: All tests + Performance tests
- **Nightly**: Performance + Cross-architecture tests
- **Release**: Full suite + Manual sign-off

See [Workflows](WORKFLOWS.md) for detailed CI/CD configuration.

---

**Last Updated**: 2026-01-06
**Maintained by**: Penguin Tech Inc
