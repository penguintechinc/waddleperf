#!/bin/bash
# tests/smoke/api/test-unified-api-health.sh
#
# Smoke test for unified-api health endpoint

set -e

API_URL="${API_URL:-http://localhost:5000}"
TIMEOUT="${TIMEOUT:-10}"

echo "=== Unified API Health Smoke Test ==="
echo "API URL: $API_URL"

# Test health endpoint
echo ""
echo "[1/1] Checking API health endpoint..."
HEALTH_URL="${API_URL}/health"

RESPONSE=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$HEALTH_URL" 2>/dev/null || echo "CURL_FAILED")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "    ✓ Health endpoint responded (HTTP $HTTP_CODE)"

    # Check if response contains "healthy" status
    if echo "$BODY" | grep -q '"status".*"healthy"'; then
        echo "    ✓ API reports healthy status"
    else
        echo "    ⚠ API response: $BODY"
    fi

    echo ""
    echo "=== Unified API Health Smoke Test: PASSED ==="
    exit 0
else
    echo "    ✗ Health endpoint failed (HTTP $HTTP_CODE)"
    echo "    Response: $BODY"
    echo ""
    echo "=== Unified API Health Smoke Test: FAILED ==="
    exit 1
fi
