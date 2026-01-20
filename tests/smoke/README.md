# WaddlePerf Smoke Tests

Fast verification tests (<2 minutes) that validate core functionality after code changes.

## Quick Start

```bash
# Run all smoke tests
./tests/smoke/run-all.sh

# Or via Makefile
make smoke-test
```

## Test Categories

### API Health Tests (`api/`)
- `test-unified-api-health.sh` - Verifies the unified API is running and healthy

### WebSocket/Socket.IO Tests (`websocket/`)
- `test-socketio-connection.sh` - Verifies Socket.IO handshake endpoint responds
- `test-socketio-events.py` - Verifies Socket.IO event handling works

### Build Tests (`build/`)
- Container build verification (add as needed)

### Runtime Tests (`run/`)
- Container runtime health checks (add as needed)

### WebUI Tests (`webui/`)
- Page load and tab navigation tests (add as needed)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://localhost:5000` | Unified API base URL |
| `WEBCLIENT_URL` | `http://localhost:3000` | WebClient frontend URL |
| `TIMEOUT` | `10` | Request timeout in seconds |

## Adding New Tests

1. Create a new `.sh` or `.py` file in the appropriate category directory
2. Name the file with prefix `test-` (e.g., `test-new-feature.sh`)
3. Make it executable: `chmod +x tests/smoke/<category>/test-new-feature.sh`
4. Exit with code 0 for success, non-zero for failure

### Shell Test Template

```bash
#!/bin/bash
# tests/smoke/<category>/test-new-feature.sh
set -e

echo "=== New Feature Smoke Test ==="

# Your test logic here
if curl -s http://localhost:5000/health | grep -q '"healthy"'; then
    echo "✓ Test passed"
    exit 0
else
    echo "✗ Test failed"
    exit 1
fi
```

### Python Test Template

```python
#!/usr/bin/env python3
"""tests/smoke/<category>/test-new-feature.py"""
import sys

def main():
    print("=== New Feature Smoke Test ===")
    # Your test logic here
    success = True

    if success:
        print("✓ Test passed")
        return 0
    else:
        print("✗ Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Integration with CI/CD

Smoke tests run automatically:
- On every PR (must pass to merge)
- Before full test suite execution
- As part of pre-commit checklist

## Dependencies

For Python Socket.IO tests:
```bash
pip install python-socketio[asyncio_client]
```
