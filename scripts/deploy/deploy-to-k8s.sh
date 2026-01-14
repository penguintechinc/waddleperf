#!/bin/bash
#
# Deploy WaddlePerf services to Kubernetes
# Usage: ./deploy-to-k8s.sh [namespace] [environment]
#

set -e

# Configuration
NAMESPACE="${1:-waddleperf}"
ENVIRONMENT="${2:-dev}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
K8S_MANIFESTS_DIR="${PROJECT_ROOT}/infrastructure/k8s"
KUBECONFIG="${KUBECONFIG:-${HOME}/.kube/config}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${GREEN}=== $1 ===${NC}"
    echo ""
}

# Verify kubectl is installed
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Verify kubeconfig exists
if [ ! -f "$KUBECONFIG" ]; then
    log_error "kubeconfig not found at $KUBECONFIG"
    exit 1
fi

log_section "WaddlePerf Kubernetes Deployment"
log_info "Namespace: $NAMESPACE"
log_info "Environment: $ENVIRONMENT"
log_info "Manifests directory: $K8S_MANIFESTS_DIR"

# Check cluster connectivity
log_section "Verifying Kubernetes Cluster Access"
if ! kubectl cluster-info &> /dev/null; then
    log_error "Unable to connect to Kubernetes cluster. Check kubeconfig."
    exit 1
fi
log_info "Connected to Kubernetes cluster"

# Create namespace if it doesn't exist
log_section "Creating Namespace"
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log_info "Namespace '$NAMESPACE' already exists"
else
    log_info "Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
    log_info "Namespace created"
fi

# Verify secrets exist
log_section "Verifying Secrets"
REQUIRED_SECRETS=(
    "registry-credentials"
    "database-credentials"
)

MISSING_SECRETS=0
for secret in "${REQUIRED_SECRETS[@]}"; do
    if kubectl get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
        log_info "Secret '$secret' exists"
    else
        log_warn "Secret '$secret' not found in namespace '$NAMESPACE'"
        ((MISSING_SECRETS++))
    fi
done

if [ $MISSING_SECRETS -gt 0 ]; then
    log_warn "Some required secrets are missing. Deployment may fail if they are needed."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 1
    fi
fi

# Apply Kubernetes manifests
log_section "Applying Kubernetes Manifests"
if [ ! -d "$K8S_MANIFESTS_DIR" ]; then
    log_error "K8s manifests directory not found: $K8S_MANIFESTS_DIR"
    exit 1
fi

# Find all YAML files and apply them
MANIFEST_COUNT=0
while IFS= read -r manifest_file; do
    log_info "Applying: $manifest_file"
    kubectl apply -f "$manifest_file" -n "$NAMESPACE"
    ((MANIFEST_COUNT++))
done < <(find "$K8S_MANIFESTS_DIR" -type f \( -name "*.yaml" -o -name "*.yml" \) | sort)

if [ $MANIFEST_COUNT -eq 0 ]; then
    log_warn "No manifest files found in $K8S_MANIFESTS_DIR"
else
    log_info "Applied $MANIFEST_COUNT manifest(s)"
fi

# Wait for rollout
log_section "Waiting for Deployments to Roll Out"
DEPLOYMENTS=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

if [ -z "$DEPLOYMENTS" ]; then
    log_warn "No deployments found in namespace '$NAMESPACE'"
else
    for deployment in $DEPLOYMENTS; do
        log_info "Waiting for deployment '$deployment' to roll out..."
        if kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=5m; then
            log_info "Deployment '$deployment' rolled out successfully"
        else
            log_error "Deployment '$deployment' failed to roll out"
            exit 1
        fi
    done
fi

# Display service URLs
log_section "Deployed Services"
SERVICES=$(kubectl get services -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,TYPE:.spec.type,IP:.status.loadBalancer.ingress[0].ip,PORT:.spec.ports[0].port --no-headers 2>/dev/null)

if [ -z "$SERVICES" ]; then
    log_warn "No services found"
else
    echo "$SERVICES"
fi

# Display ingress URLs
log_section "Ingress URLs"
INGRESSES=$(kubectl get ingress -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,HOST:.spec.rules[0].host,PATH:.spec.rules[0].http.paths[0].path --no-headers 2>/dev/null)

if [ -z "$INGRESSES" ]; then
    log_info "No ingress resources found"
else
    echo "$INGRESSES"
fi

log_section "Deployment Complete"
log_info "Namespace: $NAMESPACE"
log_info "Environment: $ENVIRONMENT"
log_info ""
log_info "To view pod status: kubectl get pods -n $NAMESPACE"
log_info "To view logs: kubectl logs -n $NAMESPACE <pod-name>"
log_info "To describe deployment: kubectl describe deployment -n $NAMESPACE <deployment-name>"
