#!/bin/bash
# Production-grade build script for Mortgage Agents System
# Builds and pushes container images using Podman

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="mortgage-agents"
IMAGE_TAG="${IMAGE_TAG:-v1.0.0}"
REGISTRY="quay.io/rbrhssa"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-podman}"
BUILD_CONTEXT="${BUILD_CONTEXT:-${SCRIPT_DIR}}"
GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking build prerequisites..."
    
    # Check container runtime
    if ! command -v "${CONTAINER_RUNTIME}" &> /dev/null; then
        log_error "${CONTAINER_RUNTIME} is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Containerfile exists
    if [[ ! -f "${BUILD_CONTEXT}/Containerfile" ]]; then
        log_error "Containerfile not found in ${BUILD_CONTEXT}"
        exit 1
    fi
    
    # Check if requirements.txt exists
    if [[ ! -f "${BUILD_CONTEXT}/requirements.txt" ]]; then
        log_error "requirements.txt not found in ${BUILD_CONTEXT}"
        exit 1
    fi
    
    log_success "Build prerequisites check passed"
}

# Function to validate project structure
validate_project_structure() {
    log_info "Validating project structure..."
    
    local required_paths=(
        "app/"
        "app/graph.py"
        "app/agents/"
        "app/utils/"
        "requirements.txt"
        "Containerfile"
    )
    
    for path in "${required_paths[@]}"; do
        if [[ ! -e "${BUILD_CONTEXT}/${path}" ]]; then
            log_error "Required path not found: ${path}"
            exit 1
        fi
    done
    
    log_success "Project structure validation passed"
}

# Function to build container image
build_image() {
    log_info "Building container image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    cd "${BUILD_CONTEXT}"
    
    # Build arguments - build directly with registry path
    local full_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    local latest_image_name="${REGISTRY}/${IMAGE_NAME}:latest"
    
    local build_args=(
        --file "Containerfile"
        --tag "${full_image_name}"
        --tag "${latest_image_name}"
        --label "version=${IMAGE_TAG}"
        --label "build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        --label "git-commit=${GIT_COMMIT}"
        --label "description=Mortgage Agents AI System"
        --label "maintainer=mortgage-team"
    )
    
    # Add build-time environment variables
    build_args+=(
        --build-arg "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        --build-arg "VERSION=${IMAGE_TAG}"
        --build-arg "GIT_COMMIT=${GIT_COMMIT}"
    )
    
    # Execute build
    if ${CONTAINER_RUNTIME} build "${build_args[@]}" .; then
        log_success "Container image built successfully: ${full_image_name}"
    else
        log_error "Container build failed"
        exit 1
    fi
}

# Function to test image
test_image() {
    log_info "Testing built image..."
    
    local full_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Basic image inspection
    if ${CONTAINER_RUNTIME} inspect "${full_image_name}" > /dev/null; then
        log_success "Image inspection passed"
    else
        log_error "Image inspection failed"
        exit 1
    fi
    
    # Test image can start (quick test)
    log_info "Running quick smoke test..."
    if ${CONTAINER_RUNTIME} run --rm --entrypoint="" "${full_image_name}" python -c "import sys; print(f'Python version: {sys.version}')"; then
        log_success "Smoke test passed - Python runtime works"
    else
        log_warning "Smoke test failed - image may have issues"
    fi
}

# Function to tag images for registry
tag_for_registry() {
    log_info "Images already built with registry tags: ${REGISTRY}"
    
    local full_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    local latest_image_name="${REGISTRY}/${IMAGE_NAME}:latest"
    
    log_success "Images ready for registry push"
    log_info "  Available: ${full_image_name}"
    log_info "  Available: ${latest_image_name}"
}

# Function to push images to registry
push_image() {
    log_info "Pushing images to registry..."
    
    local full_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    local latest_image_name="${REGISTRY}/${IMAGE_NAME}:latest"
    
    # Push versioned image
    if ${CONTAINER_RUNTIME} push "${full_image_name}"; then
        log_success "Pushed: ${full_image_name}"
    else
        log_error "Failed to push: ${full_image_name}"
        exit 1
    fi
    
    # Push latest image
    if ${CONTAINER_RUNTIME} push "${latest_image_name}"; then
        log_success "Pushed: ${latest_image_name}"
    else
        log_warning "Failed to push latest tag (non-critical)"
    fi
}

# Function to cleanup local images (optional)
cleanup_local_images() {
    log_info "Cleaning up local build images..."
    
    # Remove untagged dangling images
    local dangling_images
    dangling_images=$(${CONTAINER_RUNTIME} images -f "dangling=true" -q 2>/dev/null || true)
    
    if [[ -n "${dangling_images}" ]]; then
        echo "${dangling_images}" | xargs ${CONTAINER_RUNTIME} rmi 2>/dev/null || true
        log_success "Cleaned up dangling images"
    else
        log_info "No dangling images to clean up"
    fi
}

# Function to show build summary
show_build_summary() {
    log_info "Build Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Image:        ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "Registry:     ${REGISTRY}"
    echo "Git Commit:   ${GIT_COMMIT}"
    echo "Build Date:   $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo "Runtime:      ${CONTAINER_RUNTIME}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show image size
    local image_size
    local full_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    image_size=$(${CONTAINER_RUNTIME} images --format "table {{.Size}}" "${full_image_name}" | tail -n1)
    echo "Image Size:   ${image_size}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Main function
main() {
    local command="${1:-build}"
    
    case "${command}" in
        "build")
            check_prerequisites
            validate_project_structure
            build_image
            test_image
            push_image
            show_build_summary
            ;;
        "build-only")
            check_prerequisites
            validate_project_structure
            build_image
            test_image
            show_build_summary
            ;;
        "push")
            check_prerequisites
            tag_for_registry
            push_image
            show_build_summary
            ;;
        "all"|"full")
            check_prerequisites
            validate_project_structure
            build_image
            test_image
            push_image
            cleanup_local_images
            show_build_summary
            ;;
        "test")
            test_image
            ;;
        "clean")
            cleanup_local_images
            ;;
        *)
            echo "Usage: $0 {build|build-only|push|all|test|clean}"
            echo
            echo "Commands:"
            echo "  build      - Build, test, and push container image (default)"
            echo "  build-only - Build and test container image locally only"
            echo "  push       - Push existing image to registry"  
            echo "  all        - Build, test, push, and cleanup (full workflow)"
            echo "  test       - Test existing image"
            echo "  clean      - Cleanup dangling local images"
            echo
            echo "Environment variables:"
            echo "  IMAGE_TAG           - Image tag (default: v1.0.0)"
            echo "  CONTAINER_RUNTIME   - Container runtime (default: podman)"
            echo "  BUILD_CONTEXT       - Build context directory (default: current dir)"
            echo "  GIT_COMMIT          - Git commit hash (auto-detected)"
            echo ""
            echo "Registry: quay.io/rbrhssa/mortgage-agents (hardcoded)"
            echo
            echo "Examples:"
            echo "  ./build.sh                                    # Build and push v1.0.0 to quay.io/rbrhssa"
            echo "  IMAGE_TAG=v1.2.0 ./build.sh build           # Build and push specific version"
            echo "  ./build.sh build-only                        # Build locally without pushing"
            echo "  CONTAINER_RUNTIME=docker ./build.sh build   # Use Docker instead of Podman"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
