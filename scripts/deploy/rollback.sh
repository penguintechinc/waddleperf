#!/bin/bash
#
# Rollback Kubernetes deployments
# Usage: ./rollback.sh [deployment] [namespace]
#

set -e

# Configuration
DEPLOYMENT="${1:-unified-api}"
NAMESPACE="${2:-waddleperf}"
KUBECONFIG="${KUBECONFIG:-${HOME}/.kube/config}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [deployment] [namespace]

Arguments:
  deployment  Deployment name to rollback (default: unified-api)
  namespace   Kubernetes namespace (default: waddleperf)

Special deployments:
  all         Rollback all deployments in the namespace

Examples:
  $0                              # Rollback unified-api in waddleperf
  $0 unified-api waddleperf       # Explicit rollback
  $0 all waddleperf               # Rollback all deployments
  $0 --help                       # Show this help

Commands:
  --history [deployment]          Show rollout history
  --help                          Show this help
EOF
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

# Check for special commands
if [ "$DEPLOYMENT" = "--help" ] || [ "$DEPLOYMENT" = "-h" ]; then
    show_usage
    exit 0
fi

if [ "$DEPLOYMENT" = "--history" ]; then
    HISTORY_DEPLOYMENT="${NAMESPACE:-unified-api}"
    HISTORY_NAMESPACE="${2:-waddleperf}"

    log_section "Rollout History for $HISTORY_DEPLOYMENT"
    if kubectl rollout history deployment/"$HISTORY_DEPLOYMENT" -n "$HISTORY_NAMESPACE"; then
        exit 0
    else
        log_error "Failed to get rollout history"
        exit 1
    fi
fi

log_section "Kubernetes Deployment Rollback"
log_info "Namespace: $NAMESPACE"
log_info "Deployment: $DEPLOYMENT"

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    log_error "Unable to connect to Kubernetes cluster. Check kubeconfig."
    exit 1
fi
log_info "Connected to Kubernetes cluster"

# Function to rollback a single deployment
rollback_deployment() {
    local deploy=$1
    local ns=$2

    log_info "Checking deployment: $deploy"

    # Check if deployment exists
    if ! kubectl get deployment "$deploy" -n "$ns" &> /dev/null; then
        log_error "Deployment '$deploy' not found in namespace '$ns'"
        return 1
    fi

    # Show current rollout history
    log_info "Current rollout history for '$deploy':"
    if ! kubectl rollout history deployment/"$deploy" -n "$ns"; then
        log_error "Failed to get rollout history"
        return 1
    fi

    # Confirm rollback
    echo ""
    read -p "Rollback deployment '$deploy' in namespace '$ns'? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled for '$deploy'"
        return 0
    fi

    # Perform rollback
    log_info "Rolling back deployment '$deploy'..."
    if kubectl rollout undo deployment/"$deploy" -n "$ns"; then
        log_info "Rollback initiated for '$deploy'"

        # Wait for rollout to complete
        log_info "Waiting for rollout to complete..."
        if kubectl rollout status deployment/"$deploy" -n "$ns" --timeout=5m; then
            log_info "Deployment '$deploy' rolled back successfully"
            return 0
        else
            log_error "Rollback for deployment '$deploy' failed to complete"
            return 1
        fi
    else
        log_error "Failed to rollback deployment '$deploy'"
        return 1
    fi
}

# Function to rollback all deployments
rollback_all_deployments() {
    local ns=$1

    log_info "Getting all deployments in namespace '$ns'..."
    DEPLOYMENTS=$(kubectl get deployments -n "$ns" -o jsonpath='{.items[*].metadata.name}')

    if [ -z "$DEPLOYMENTS" ]; then
        log_warn "No deployments found in namespace '$ns'"
        return 0
    fi

    log_info "Found deployments: $DEPLOYMENTS"
    echo ""
    read -p "Rollback ALL deployments in namespace '$ns'? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        return 0
    fi

    FAILED_DEPLOYMENTS=()
    SUCCESSFUL_DEPLOYMENTS=()

    for deployment in $DEPLOYMENTS; do
        if rollback_deployment "$deployment" "$ns"; then
            SUCCESSFUL_DEPLOYMENTS+=("$deployment")
        else
            FAILED_DEPLOYMENTS+=("$deployment")
        fi
    done

    log_section "Rollback Summary"
    log_info "Successful: ${#SUCCESSFUL_DEPLOYMENTS[@]}"
    for deploy in "${SUCCESSFUL_DEPLOYMENTS[@]}"; do
        log_info "  ✓ $deploy"
    done

    if [ ${#FAILED_DEPLOYMENTS[@]} -gt 0 ]; then
        log_error "Failed: ${#FAILED_DEPLOYMENTS[@]}"
        for deploy in "${FAILED_DEPLOYMENTS[@]}"; do
            log_error "  ✗ $deploy"
        done
        return 1
    fi

    return 0
}

# Main logic
if [ "$DEPLOYMENT" = "all" ]; then
    if rollback_all_deployments "$NAMESPACE"; then
        exit 0
    else
        exit 1
    fi
else
    if rollback_deployment "$DEPLOYMENT" "$NAMESPACE"; then
        exit 0
    else
        exit 1
    fi
fi

log_section "Rollback Complete"
log_info "Namespace: $NAMESPACE"
log_info "To check status: kubectl get deployments -n $NAMESPACE"
log_info "To view logs: kubectl logs -n $NAMESPACE <pod-name>"
