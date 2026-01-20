#!/bin/bash
# tests/smoke/k8s-beta-test.sh
#
# Kubernetes Beta Test Suite
# Tests deployed services in the waddleperf namespace

# Note: Don't use set -e to allow all tests to run even if one fails

NAMESPACE="${NAMESPACE:-waddleperf}"
DEPLOYMENT="${DEPLOYMENT:-unified-api}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

echo "=============================================="
echo "    Kubernetes Beta Test Suite"
echo "=============================================="
echo ""
echo "Namespace: $NAMESPACE"
echo "Deployment: $DEPLOYMENT"
echo ""

# Test 1: Check deployment exists and is ready
echo "----------------------------------------------"
echo "[1/6] Verifying deployment exists and is ready"
echo "----------------------------------------------"

if kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" &>/dev/null; then
    READY=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    DESIRED=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.replicas}')

    if [ "$READY" = "$DESIRED" ] && [ "$READY" -gt 0 ]; then
        echo -e "    ${GREEN}✓${NC} Deployment is ready ($READY/$DESIRED replicas)"
        ((TESTS_PASSED++))
    else
        echo -e "    ${RED}✗${NC} Deployment not ready ($READY/$DESIRED replicas)"
        ((TESTS_FAILED++))
    fi
else
    echo -e "    ${RED}✗${NC} Deployment not found"
    ((TESTS_FAILED++))
fi
echo ""

# Test 2: Check pods are running
echo "----------------------------------------------"
echo "[2/6] Verifying pods are running"
echo "----------------------------------------------"

POD_COUNT=$(kubectl get pods -n "$NAMESPACE" -l "app=$DEPLOYMENT" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

if [ "$POD_COUNT" -gt 0 ]; then
    echo -e "    ${GREEN}✓${NC} $POD_COUNT pod(s) running"
    ((TESTS_PASSED++))
else
    echo -e "    ${RED}✗${NC} No running pods found"
    ((TESTS_FAILED++))
fi
echo ""

# Test 3: Health endpoint test
echo "----------------------------------------------"
echo "[3/6] Testing health endpoint"
echo "----------------------------------------------"

HEALTH_RESPONSE=$(kubectl exec -n "$NAMESPACE" deployment/"$DEPLOYMENT" -- curl -s http://localhost:5000/health 2>/dev/null || echo "{}")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "unknown"' 2>/dev/null)

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "    ${GREEN}✓${NC} Health endpoint returns healthy status"
    echo "    Response: $(echo "$HEALTH_RESPONSE" | jq -c .)"
    ((TESTS_PASSED++))
else
    echo -e "    ${RED}✗${NC} Health endpoint failed (status: $HEALTH_STATUS)"
    ((TESTS_FAILED++))
fi
echo ""

# Test 4: Socket.IO handshake test
echo "----------------------------------------------"
echo "[4/6] Testing Socket.IO handshake"
echo "----------------------------------------------"

SOCKETIO_RESPONSE=$(kubectl exec -n "$NAMESPACE" deployment/"$DEPLOYMENT" -- curl -s "http://localhost:5000/socket.io/?EIO=4&transport=polling" 2>/dev/null || echo "")

if echo "$SOCKETIO_RESPONSE" | grep -q '"sid"'; then
    SID=$(echo "$SOCKETIO_RESPONSE" | grep -o '"sid":"[^"]*"' | cut -d'"' -f4)
    echo -e "    ${GREEN}✓${NC} Socket.IO handshake successful"
    echo "    Session ID: $SID"
    ((TESTS_PASSED++))
else
    echo -e "    ${RED}✗${NC} Socket.IO handshake failed"
    echo "    Response: $SOCKETIO_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 5: WebSocket upgrade available
echo "----------------------------------------------"
echo "[5/6] Verifying WebSocket upgrade support"
echo "----------------------------------------------"

if echo "$SOCKETIO_RESPONSE" | grep -q '"websocket"'; then
    echo -e "    ${GREEN}✓${NC} WebSocket upgrade available"
    ((TESTS_PASSED++))
else
    echo -e "    ${RED}✗${NC} WebSocket upgrade not available"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Check service and ingress configuration
echo "----------------------------------------------"
echo "[6/6] Verifying service and ingress"
echo "----------------------------------------------"

SERVICE_EXISTS=$(kubectl get service "$DEPLOYMENT" -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
INGRESS_EXISTS=$(kubectl get ingress "$DEPLOYMENT" -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)

if [ "$SERVICE_EXISTS" -gt 0 ]; then
    SERVICE_IP=$(kubectl get service "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    echo -e "    ${GREEN}✓${NC} Service exists (ClusterIP: $SERVICE_IP)"
    ((TESTS_PASSED++))
else
    echo -e "    ${RED}✗${NC} Service not found"
    ((TESTS_FAILED++))
fi

if [ "$INGRESS_EXISTS" -gt 0 ]; then
    INGRESS_HOST=$(kubectl get ingress "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
    echo -e "    ${GREEN}✓${NC} Ingress exists (Host: $INGRESS_HOST)"

    # Check if Socket.IO path is configured
    if kubectl get ingress "$DEPLOYMENT" -n "$NAMESPACE" -o yaml | grep -q "path: /socket.io"; then
        echo -e "    ${GREEN}✓${NC} Socket.IO ingress path configured"
    else
        echo -e "    ${YELLOW}⚠${NC} Socket.IO ingress path not found"
    fi
else
    echo -e "    ${RED}✗${NC} Ingress not found"
fi
echo ""

# Summary
echo "=============================================="
echo "               Test Summary"
echo "=============================================="
echo ""
echo -e "  ${GREEN}Passed${NC}:  $TESTS_PASSED"
echo -e "  ${RED}Failed${NC}:  $TESTS_FAILED"
echo ""

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}=============================================="
    echo "    All $TOTAL tests passed!"
    echo -e "==============================================${NC}"
    exit 0
else
    echo -e "${RED}=============================================="
    echo "    $TESTS_FAILED of $TOTAL tests failed"
    echo -e "==============================================${NC}"
    exit 1
fi
