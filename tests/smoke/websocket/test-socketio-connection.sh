#!/bin/bash
# tests/smoke/websocket/test-socketio-connection.sh
#
# Smoke test for Socket.IO WebSocket connectivity
# Verifies that the Socket.IO server is reachable and responds correctly

set -e

# Configuration
API_URL="${API_URL:-http://localhost:5000}"
TIMEOUT="${TIMEOUT:-10}"

echo "=== Socket.IO Connection Smoke Test ==="
echo "API URL: $API_URL"

# Test 1: Check if Socket.IO handshake endpoint is available
echo ""
echo "[1/3] Testing Socket.IO handshake endpoint..."
SOCKETIO_URL="${API_URL}/socket.io/?EIO=4&transport=polling"

RESPONSE=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$SOCKETIO_URL" 2>/dev/null || echo "CURL_FAILED")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "    ✓ Socket.IO handshake endpoint responded (HTTP $HTTP_CODE)"
else
    echo "    ✗ Socket.IO handshake endpoint failed (HTTP $HTTP_CODE)"
    echo "    Response: $(echo "$RESPONSE" | head -n -1)"
    exit 1
fi

# Test 2: Verify Socket.IO response contains session ID (sid)
echo ""
echo "[2/3] Verifying Socket.IO session response..."
BODY=$(echo "$RESPONSE" | head -n -1)

# Socket.IO response format: 0{"sid":"...","upgrades":["websocket"],...}
if echo "$BODY" | grep -q '"sid"'; then
    echo "    ✓ Socket.IO returned session ID (sid)"
else
    echo "    ✗ Socket.IO response missing session ID"
    echo "    Response: $BODY"
    exit 1
fi

# Test 3: Verify WebSocket upgrade is available
echo ""
echo "[3/3] Verifying WebSocket upgrade availability..."
if echo "$BODY" | grep -q '"websocket"'; then
    echo "    ✓ WebSocket transport is available"
else
    echo "    ⚠ WebSocket transport may not be available"
    echo "    Response: $BODY"
    # Don't fail - polling fallback may still work
fi

echo ""
echo "=== Socket.IO Connection Smoke Test: PASSED ==="
exit 0
