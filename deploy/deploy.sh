#!/bin/bash
# Production-grade deployment script for Mortgage Agents System
# Deploys to OpenShift using existing container images

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
IMAGE_NAME="mortgage-agents" 
IMAGE_TAG="${IMAGE_TAG:-v1.0.0}"
REGISTRY="quay.io/rbrhssa"
NAMESPACE="${NAMESPACE:-mortgage-agents}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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

# Function to check deployment prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check OpenShift CLI
    if ! command -v oc &> /dev/null; then
        log_error "OpenShift CLI (oc) is not installed or not in PATH"
        log_info "Install from: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html"
        exit 1
    fi
    
    # Check if logged into OpenShift
    if ! oc whoami &> /dev/null; then
        log_error "Not logged into OpenShift cluster"
        log_info "Please run: oc login <cluster-url>"
        exit 1
    fi
    
    # Check cluster connection
    if ! oc cluster-info &> /dev/null; then
        log_error "Cannot connect to OpenShift cluster"
        exit 1
    fi
    
    # Verify deployment manifests exist
    local required_files=("rbac.yaml" "configmap.yaml" "secret.yaml" "storage.yaml" "deployment.yaml")
    for file in "${required_files[@]}"; do
        if [[ ! -f "${SCRIPT_DIR}/${file}" ]]; then
            log_error "Required deployment file not found: ${file}"
            exit 1
        fi
    done
    
    log_success "Deployment prerequisites check passed"
}

# Function to create/verify namespace
setup_namespace() {
    log_info "Setting up namespace: ${NAMESPACE}"
    
    if ! oc get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Creating new namespace: ${NAMESPACE}"
        oc new-project "${NAMESPACE}" \
            --description="Mortgage Agents AI System - ${ENVIRONMENT}" \
            --display-name="Mortgage Agents (${ENVIRONMENT})"
        
        # Label namespace for monitoring and network policies
        oc label namespace "${NAMESPACE}" \
            "name=${NAMESPACE}" \
            "environment=${ENVIRONMENT}" \
            "app=mortgage-agents"
            
        log_success "Namespace created: ${NAMESPACE}"
    else
        oc project "${NAMESPACE}"
        log_info "Using existing namespace: ${NAMESPACE}"
    fi
    
    # Verify we're in the correct namespace
    local current_namespace
    current_namespace=$(oc project -q)
    if [[ "${current_namespace}" != "${NAMESPACE}" ]]; then
        log_error "Failed to switch to namespace: ${NAMESPACE}"
        exit 1
    fi
}

# Function to update image references
update_image_references() {
    log_info "Updating image references to: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    cd "${SCRIPT_DIR}"
    
    # Update kustomization.yaml if using kustomize
    if [[ -f "kustomization.yaml" ]] && command -v kustomize &> /dev/null; then
        # Use kustomize to update image
        kustomize edit set image "mortgage-agents=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        log_success "Updated image reference in kustomization.yaml"
    else
        # Update deployment.yaml directly
        if command -v sed &> /dev/null; then
            # Create a backup
            cp deployment.yaml deployment.yaml.bak
            
            # Update image in deployment
            sed -i.tmp "s|image: mortgage-agents:.*|image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" deployment.yaml
            rm -f deployment.yaml.tmp
            
            log_success "Updated image reference in deployment.yaml"
        else
            log_warning "Cannot update image reference automatically. Please update deployment.yaml manually."
        fi
    fi
}

# Function to deploy RBAC resources
deploy_rbac() {
    log_info "Deploying RBAC resources..."
    
    if oc apply -f rbac.yaml; then
        log_success "RBAC resources deployed"
    else
        log_error "Failed to deploy RBAC resources"
        exit 1
    fi
}

# Function to deploy configuration
deploy_config() {
    log_info "Deploying configuration resources..."
    
    # Apply ConfigMap
    if oc apply -f configmap.yaml; then
        log_success "ConfigMap deployed"
    else
        log_error "Failed to deploy ConfigMap"
        exit 1
    fi
    
    # Check if secret already exists
    if oc get secret mortgage-agents-secrets &> /dev/null; then
        log_warning "Secret already exists - skipping secret creation"
        log_info "To update secret, delete it first: oc delete secret mortgage-agents-secrets"
    else
        # Apply Secret (only if it doesn't exist)
        if oc apply -f secret.yaml; then
            log_success "Secret deployed"
            log_warning "Remember to update secret values with production credentials!"
        else
            log_error "Failed to deploy Secret"
            exit 1
        fi
    fi
}

# Function to deploy storage
deploy_storage() {
    log_info "Deploying storage and networking resources..."
    
    if oc apply -f storage.yaml; then
        log_success "Storage and networking resources deployed"
    else
        log_error "Failed to deploy storage resources"
        exit 1
    fi
    
    # Wait for PVC to be bound
    log_info "Waiting for PVC to be bound..."
    if oc wait --for=condition=Bound pvc/mortgage-agents-data-pvc --timeout=60s; then
        log_success "PVC bound successfully"
    else
        log_warning "PVC binding timeout - continuing with deployment"
    fi
}

# Function to deploy application
deploy_application() {
    log_info "Deploying application..."
    
    if [[ -f "kustomization.yaml" ]] && command -v kustomize &> /dev/null; then
        # Use kustomize for deployment
        if kustomize build . | oc apply -f -; then
            log_success "Application deployed using kustomize"
        else
            log_error "Failed to deploy application with kustomize"
            exit 1
        fi
    else
        # Deploy deployment.yaml directly
        if oc apply -f deployment.yaml; then
            log_success "Application deployment applied"
        else
            log_error "Failed to deploy application"
            exit 1
        fi
    fi
}

# Function to wait for deployment rollout
wait_for_rollout() {
    log_info "Waiting for deployment rollout..."
    
    # Wait for deployment to be ready
    if oc rollout status deployment/mortgage-agents --timeout=600s; then
        log_success "Deployment rollout completed successfully"
    else
        log_error "Deployment rollout failed or timed out"
        
        # Show pod status for debugging
        log_info "Pod status for debugging:"
        oc get pods -l app=mortgage-agents
        
        # Show recent events
        log_info "Recent events:"
        oc get events --sort-by='.lastTimestamp' | tail -10
        
        exit 1
    fi
}

# Function to run health checks
run_health_checks() {
    log_info "Running post-deployment health checks..."
    
    # Check pod status
    local ready_pods
    ready_pods=$(oc get pods -l app=mortgage-agents -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o True | wc -l)
    local total_pods
    total_pods=$(oc get pods -l app=mortgage-agents --no-headers | wc -l)
    
    if [[ "${ready_pods}" -eq "${total_pods}" ]] && [[ "${total_pods}" -gt 0 ]]; then
        log_success "All pods are ready (${ready_pods}/${total_pods})"
    else
        log_warning "Some pods may not be ready (${ready_pods}/${total_pods})"
    fi
    
    # Check service endpoints
    if oc get endpoints mortgage-agents-service &> /dev/null; then
        local endpoint_count
        endpoint_count=$(oc get endpoints mortgage-agents-service -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
        if [[ "${endpoint_count}" -gt 0 ]]; then
            log_success "Service endpoints available: ${endpoint_count}"
        else
            log_warning "No service endpoints available"
        fi
    fi
    
    # Test application endpoint if route is available
    local route_host
    route_host=$(oc get route mortgage-agents-route -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    if [[ -n "${route_host}" ]]; then
        log_info "Testing application endpoint: https://${route_host}/health"
        if curl -f -s --max-time 30 "https://${route_host}/health" > /dev/null; then
            log_success "Application health endpoint responding"
        else
            log_warning "Application health endpoint not responding (may still be starting)"
        fi
    fi
}

# Function to show deployment status
show_deployment_status() {
    log_info "Deployment Status Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Namespace:    ${NAMESPACE}"
    echo "Image:        ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "Environment:  ${ENVIRONMENT}"
    echo "Deployed:     $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo
    log_info "Pods:"
    oc get pods -l app=mortgage-agents -o wide
    
    echo
    log_info "Services:"
    oc get services -l app=mortgage-agents
    
    echo
    log_info "Routes:"
    oc get routes -l app=mortgage-agents
    
    # Show application URL
    local route_host
    route_host=$(oc get route mortgage-agents-route -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    if [[ -n "${route_host}" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_success "🌐 Application URL: https://${route_host}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
}

# Function to rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    if oc rollout undo deployment/mortgage-agents; then
        log_success "Rollback initiated"
        
        # Wait for rollback to complete
        if oc rollout status deployment/mortgage-agents --timeout=300s; then
            log_success "Rollback completed successfully"
        else
            log_error "Rollback failed or timed out"
            exit 1
        fi
    else
        log_error "Failed to initiate rollback"
        exit 1
    fi
}

# Function to cleanup deployment
cleanup_deployment() {
    log_warning "This will delete all mortgage-agents resources in ${NAMESPACE}"
    read -p "Are you sure? (yes/no): " -r
    
    if [[ "${REPLY}" == "yes" ]]; then
        log_info "Cleaning up deployment..."
        
        # Delete in reverse order
        oc delete -f deployment.yaml --ignore-not-found=true
        oc delete -f storage.yaml --ignore-not-found=true
        oc delete -f secret.yaml --ignore-not-found=true
        oc delete -f configmap.yaml --ignore-not-found=true
        oc delete -f rbac.yaml --ignore-not-found=true
        
        log_success "Deployment cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main function
main() {
    local command="${1:-deploy}"
    
    case "${command}" in
        "deploy")
            check_prerequisites
            setup_namespace
            update_image_references
            deploy_rbac
            deploy_config
            deploy_storage
            deploy_application
            wait_for_rollout
            run_health_checks
            show_deployment_status
            ;;
        "update")
            check_prerequisites
            oc project "${NAMESPACE}"
            update_image_references
            deploy_application
            wait_for_rollout
            run_health_checks
            show_deployment_status
            ;;
        "status")
            check_prerequisites
            oc project "${NAMESPACE}"
            show_deployment_status
            ;;
        "health")
            check_prerequisites
            oc project "${NAMESPACE}"
            run_health_checks
            ;;
        "rollback")
            check_prerequisites
            oc project "${NAMESPACE}"
            rollback_deployment
            show_deployment_status
            ;;
        "cleanup"|"delete")
            check_prerequisites
            oc project "${NAMESPACE}"
            cleanup_deployment
            ;;
        "logs")
            check_prerequisites
            oc project "${NAMESPACE}"
            log_info "Showing recent logs for mortgage-agents pods..."
            oc logs -l app=mortgage-agents --tail=50 -f
            ;;
        *)
            echo "Usage: $0 {deploy|update|status|health|rollback|cleanup|logs}"
            echo
            echo "Commands:"
            echo "  deploy   - Full deployment (RBAC, config, storage, application)"
            echo "  update   - Update only the application (new image version)"
            echo "  status   - Show deployment status and URLs"
            echo "  health   - Run health checks"
            echo "  rollback - Rollback to previous deployment version"
            echo "  cleanup  - Delete all resources (destructive!)"
            echo "  logs     - Show application logs"
            echo
            echo "Environment variables:"
            echo "  IMAGE_TAG    - Image tag to deploy (default: v1.0.0)"
            echo "  NAMESPACE    - OpenShift namespace (default: mortgage-agents)"
            echo "  ENVIRONMENT  - Environment name (default: production)"
            echo ""
            echo "Registry: quay.io/rbrhssa/mortgage-agents (hardcoded)"
            echo
            echo "Examples:"
            echo "  IMAGE_TAG=v1.2.0 NAMESPACE=mortgage-dev ./deploy.sh deploy"
            echo "  IMAGE_TAG=v1.2.1 ./deploy.sh update"
            echo "  NAMESPACE=mortgage-staging ./deploy.sh status"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
