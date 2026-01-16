#!/bin/bash
#
# Build and push Docker images to registry
# Usage: ./build-and-push.sh [service] [version]
#

set -e

# Configuration
SERVICE="${1:-unified-api}"
VERSION="${2:-latest}"
REGISTRY="registry-dal2.penguintech.io"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICES_DIR="${PROJECT_ROOT}/services"

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
Usage: $0 [service] [version]

Services:
  - unified-api (default)
  - testserver
  - frontends
  - all (build all services)

Version: Tag for docker image (default: latest)

Examples:
  $0 unified-api v1.0.0
  $0 all beta-20250113
  $0 frontends latest
EOF
}

# Verify docker is installed
if ! command -v docker &> /dev/null; then
    log_error "docker is not installed. Please install Docker first."
    exit 1
fi

# Verify docker buildx is available
if ! docker buildx version &> /dev/null; then
    log_error "docker buildx is not available. Please install Docker with buildx support."
    exit 1
fi

log_section "Docker Build and Push Configuration"
log_info "Registry: $REGISTRY"
log_info "Service: $SERVICE"
log_info "Version: $VERSION"
log_info "Project root: $PROJECT_ROOT"

# Function to build and push a service
build_and_push_service() {
    local service_name=$1
    local version=$2
    local service_path="${SERVICES_DIR}/${service_name}"

    if [ ! -d "$service_path" ]; then
        log_error "Service directory not found: $service_path"
        return 1
    fi

    log_section "Building and Pushing: $service_name"

    # Check if Dockerfile exists
    if [ ! -f "${service_path}/Dockerfile" ]; then
        log_error "Dockerfile not found: ${service_path}/Dockerfile"
        return 1
    fi

    log_info "Service path: $service_path"
    log_info "Building multi-arch image (amd64, arm64)..."

    local image_name="${REGISTRY}/waddleperf/${service_name}"
    local tags=(
        "${image_name}:${version}"
        "${image_name}:latest"
    )

    local build_args="--platform linux/amd64,linux/arm64 --push"
    for tag in "${tags[@]}"; do
        build_args="${build_args} -t ${tag}"
    done

    # Add build context
    build_args="${build_args} ."

    log_info "Building with: docker buildx build $build_args"
    log_info "Platforms: linux/amd64, linux/arm64"

    cd "$service_path"
    if docker buildx build --platform linux/amd64,linux/arm64 --push \
        -t "${image_name}:${version}" \
        -t "${image_name}:latest" \
        .; then
        log_info "Successfully built and pushed: ${image_name}:${version}"
        cd - > /dev/null
        return 0
    else
        log_error "Failed to build and push: ${image_name}:${version}"
        cd - > /dev/null
        return 1
    fi
}

# Main logic
if [ "$SERVICE" = "all" ]; then
    log_section "Building all services"

    FAILED_SERVICES=()
    SUCCESSFUL_SERVICES=()

    # Find all service directories
    if [ ! -d "$SERVICES_DIR" ]; then
        log_error "Services directory not found: $SERVICES_DIR"
        exit 1
    fi

    for service_dir in "${SERVICES_DIR}"/*; do
        if [ -d "$service_dir" ] && [ -f "${service_dir}/Dockerfile" ]; then
            service_name=$(basename "$service_dir")
            if build_and_push_service "$service_name" "$VERSION"; then
                SUCCESSFUL_SERVICES+=("$service_name")
            else
                FAILED_SERVICES+=("$service_name")
            fi
        fi
    done

    log_section "Build Summary"
    log_info "Successful: ${#SUCCESSFUL_SERVICES[@]}"
    for svc in "${SUCCESSFUL_SERVICES[@]}"; do
        log_info "  ✓ $svc"
    done

    if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
        log_error "Failed: ${#FAILED_SERVICES[@]}"
        for svc in "${FAILED_SERVICES[@]}"; do
            log_error "  ✗ $svc"
        done
        exit 1
    fi
elif [ "$SERVICE" = "--help" ] || [ "$SERVICE" = "-h" ]; then
    show_usage
    exit 0
else
    if build_and_push_service "$SERVICE" "$VERSION"; then
        log_section "Build Complete"
        log_info "Image: ${REGISTRY}/waddleperf/${SERVICE}:${VERSION}"
        exit 0
    else
        exit 1
    fi
fi

log_section "All Operations Complete"
log_info "Registry: $REGISTRY"
log_info "To deploy: ./deploy-to-k8s.sh"
