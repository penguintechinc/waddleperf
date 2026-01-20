#!/bin/bash
# tests/smoke/run-all.sh
#
# Main smoke test runner for WaddlePerf
# Executes all smoke tests and reports results
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration (can be overridden by environment variables)
export API_URL="${API_URL:-http://localhost:5000}"
export WEBCLIENT_URL="${WEBCLIENT_URL:-http://localhost:3000}"
export TIMEOUT="${TIMEOUT:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

echo "=============================================="
echo "       WaddlePerf Smoke Test Suite"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  API URL:       $API_URL"
echo "  WebClient URL: $WEBCLIENT_URL"
echo "  Timeout:       ${TIMEOUT}s"
echo ""

# Function to run a single test
run_test() {
    local test_name="$1"
    local test_script="$2"

    echo "----------------------------------------------"
    echo "Running: $test_name"
    echo "----------------------------------------------"

    if [ ! -f "$test_script" ]; then
        echo -e "${YELLOW}SKIPPED${NC}: Test script not found: $test_script"
        ((TESTS_SKIPPED++))
        return
    fi

    if [ ! -x "$test_script" ]; then
        chmod +x "$test_script"
    fi

    if "$test_script"; then
        echo -e "${GREEN}PASSED${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAILED${NC}: $test_name"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Function to run a Python test
run_python_test() {
    local test_name="$1"
    local test_script="$2"

    echo "----------------------------------------------"
    echo "Running: $test_name"
    echo "----------------------------------------------"

    if [ ! -f "$test_script" ]; then
        echo -e "${YELLOW}SKIPPED${NC}: Test script not found: $test_script"
        ((TESTS_SKIPPED++))
        return
    fi

    if python3 "$test_script"; then
        echo -e "${GREEN}PASSED${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAILED${NC}: $test_name"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# ============================================
# API Health Tests
# ============================================
echo ""
echo "=============================================="
echo "           API Health Tests"
echo "=============================================="

run_test "Unified API Health Check" "$SCRIPT_DIR/api/test-unified-api-health.sh"

# ============================================
# WebSocket/Socket.IO Tests
# ============================================
echo ""
echo "=============================================="
echo "         WebSocket/Socket.IO Tests"
echo "=============================================="

run_test "Socket.IO Connection Test" "$SCRIPT_DIR/websocket/test-socketio-connection.sh"
run_python_test "Socket.IO Events Test" "$SCRIPT_DIR/websocket/test-socketio-events.py"

# ============================================
# Build Tests (if containers need verification)
# ============================================
if [ -d "$SCRIPT_DIR/build" ] && [ -n "$(ls -A "$SCRIPT_DIR/build" 2>/dev/null)" ]; then
    echo ""
    echo "=============================================="
    echo "             Build Tests"
    echo "=============================================="

    for test in "$SCRIPT_DIR/build"/*.sh; do
        if [ -f "$test" ]; then
            test_name=$(basename "$test" .sh | sed 's/test-//' | sed 's/-/ /g')
            run_test "Build: $test_name" "$test"
        fi
    done
fi

# ============================================
# Runtime Tests
# ============================================
if [ -d "$SCRIPT_DIR/run" ] && [ -n "$(ls -A "$SCRIPT_DIR/run" 2>/dev/null)" ]; then
    echo ""
    echo "=============================================="
    echo "            Runtime Tests"
    echo "=============================================="

    for test in "$SCRIPT_DIR/run"/*.sh; do
        if [ -f "$test" ]; then
            test_name=$(basename "$test" .sh | sed 's/test-//' | sed 's/-/ /g')
            run_test "Runtime: $test_name" "$test"
        fi
    done
fi

# ============================================
# WebUI Tests
# ============================================
if [ -d "$SCRIPT_DIR/webui" ] && [ -n "$(ls -A "$SCRIPT_DIR/webui" 2>/dev/null)" ]; then
    echo ""
    echo "=============================================="
    echo "             WebUI Tests"
    echo "=============================================="

    for test in "$SCRIPT_DIR/webui"/*.sh; do
        if [ -f "$test" ]; then
            test_name=$(basename "$test" .sh | sed 's/test-//' | sed 's/-/ /g')
            run_test "WebUI: $test_name" "$test"
        fi
    done
fi

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "               Test Summary"
echo "=============================================="
echo ""
echo -e "  ${GREEN}Passed${NC}:  $TESTS_PASSED"
echo -e "  ${RED}Failed${NC}:  $TESTS_FAILED"
echo -e "  ${YELLOW}Skipped${NC}: $TESTS_SKIPPED"
echo ""

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}=============================================="
    echo "      All $TOTAL smoke tests passed!"
    echo -e "==============================================${NC}"
    exit 0
else
    echo -e "${RED}=============================================="
    echo "      $TESTS_FAILED of $TOTAL smoke tests failed"
    echo -e "==============================================${NC}"
    exit 1
fi
