# Mortgage Agents Deployment Guide

This directory contains production-grade deployment configurations and scripts for the Mortgage Agents AI System.

## Architecture Overview

The system is designed for containerized deployment using:
- **Red Hat UBI 9** base image with Python 3.11
- **OpenShift** as the target platform with proper SCC handling
- **Podman** as the container runtime
- **Production-grade** configuration management with external secrets

## Directory Structure

```
deploy/
├── README.md              # This deployment guide
├── configmap.yaml         # Application configuration
├── secret.yaml           # Sensitive configuration (credentials)
├── rbac.yaml              # Service accounts, roles, and permissions
├── storage.yaml           # Persistent storage, services, and routes
├── deployment.yaml        # Main application deployment
├── kustomization.yaml     # Kustomize configuration
└── deploy.sh             # Deployment automation script
```

## Prerequisites

1. **OpenShift CLI** (`oc`) installed and configured
2. **Podman** installed for container operations
3. **Active OpenShift login**: `oc login <your-cluster-url>`
4. **Container registry** access (e.g., Quay.io)

## Quick Start

### 1. Build Container Image

From the project root directory:

```bash
# Build and test locally
./build.sh build

# Build and push to registry
REGISTRY=quay.io/rbrhssa IMAGE_TAG=v1.0.0 ./build.sh all
```

### 2. Configure Production Settings

Edit `deploy/secret.yaml` with your production values:

```yaml
stringData:
  # Replace with your actual LLM endpoint
  LLM_BASE_URL: "https://your-llm-endpoint.com/v1"
  LLM_API_KEY: "your-api-key"
  
  # Replace with your Neo4j credentials
  NEO4J_URI: "bolt://your-neo4j:7687"
  NEO4J_PASSWORD: "your-production-password"
```

### 3. Deploy to OpenShift

```bash
cd deploy/

# Full deployment
REGISTRY=quay.io/rbrhssa IMAGE_TAG=v1.0.0 ./deploy.sh deploy

# Update existing deployment with new image
IMAGE_TAG=v1.1.0 ./deploy.sh update
```

## Build Script (`build.sh`)

Located in the project root, handles container image lifecycle:

### Commands

```bash
./build.sh build    # Build container image locally
./build.sh push     # Push existing image to registry
./build.sh all      # Build, test, push, and cleanup
./build.sh test     # Test existing local image
./build.sh clean    # Cleanup dangling images
```

### Environment Variables

```bash
IMAGE_TAG=v1.2.0              # Image version (default: v1.0.0)
REGISTRY=quay.io/rbrhssa      # Container registry
CONTAINER_RUNTIME=docker      # Use Docker instead of Podman
BUILD_CONTEXT=/path/to/src    # Custom build context
```

### Example Usage

```bash
# Build for development
./build.sh build

# Build and push production image
REGISTRY=quay.io/rbrhssa IMAGE_TAG=v2.1.0 ./build.sh all
```

## Deploy Script (`deploy.sh`)

Located in the `deploy/` directory, handles OpenShift deployment:

### Commands

```bash
./deploy.sh deploy     # Full deployment (new environment)
./deploy.sh update     # Update application only (new image)
./deploy.sh status     # Show deployment status
./deploy.sh health     # Run health checks
./deploy.sh rollback   # Rollback to previous version
./deploy.sh cleanup    # Delete all resources
./deploy.sh logs       # Show application logs
```

### Environment Variables

```bash
IMAGE_TAG=v1.2.0                    # Image version to deploy
REGISTRY=quay.io/rbrhssa            # Container registry
NAMESPACE=mortgage-agents           # OpenShift namespace
ENVIRONMENT=production              # Environment label
```

### Example Usage

```bash
# Deploy to production
REGISTRY=quay.io/rbrhssa IMAGE_TAG=v1.0.0 ./deploy.sh deploy

# Deploy to staging
NAMESPACE=mortgage-staging IMAGE_TAG=v1.1.0-rc1 ENVIRONMENT=staging ./deploy.sh deploy

# Update production with new version
IMAGE_TAG=v1.0.1 ./deploy.sh update

# Check status
./deploy.sh status
```

## Production Workflow

### 1. Development Build

```bash
# Build and test locally
./build.sh build
./build.sh test
```

### 2. CI/CD Pipeline Build

```bash
# In your CI pipeline
export IMAGE_TAG="${GIT_TAG:-${GIT_COMMIT:0:7}}"
export REGISTRY="quay.io/rbrhssa"

./build.sh all
```

### 3. Staging Deployment

```bash
cd deploy/
export IMAGE_TAG="v1.2.0"
export NAMESPACE="mortgage-staging"
export ENVIRONMENT="staging"

./deploy.sh deploy
./deploy.sh health
```

### 4. Production Deployment

```bash
cd deploy/
export IMAGE_TAG="v1.2.0"
export NAMESPACE="mortgage-agents"
export ENVIRONMENT="production"

./deploy.sh deploy
./deploy.sh health
```

## Security Features

### OpenShift Security Context Constraints (SCC)

The deployment includes a custom SCC that:
- Runs as non-root user (UID 1001)
- Uses restricted capabilities
- Enables proper volume access
- Follows OpenShift security best practices

### RBAC (Role-Based Access Control)

- **Service Account**: `mortgage-agents-sa`
- **Minimal Permissions**: Only required access to ConfigMaps, Secrets, and PVCs
- **Namespace Isolation**: Permissions scoped to application namespace

### Configuration Management

- **Secrets**: Stored in OpenShift Secrets (not in container)
- **Configuration**: External ConfigMaps (not baked into image)
- **Environment Variables**: Sourced from Secrets at runtime

## Monitoring and Health Checks

### Health Endpoints

- **Liveness**: `/health` - Container health check
- **Readiness**: `/ready` - Service readiness check
- **Startup**: Initial container startup probe

### Resource Monitoring

- **CPU Limits**: 1000m (1 core) with 250m requests
- **Memory Limits**: 2Gi with 512Mi requests
- **Horizontal Pod Autoscaling**: 2-10 replicas based on CPU/Memory

### Logging

```bash
# View recent logs
./deploy.sh logs

# Stream live logs
oc logs -l app=mortgage-agents -f

# Debug specific pod
oc logs <pod-name> -c mortgage-agents
```

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   # Check image exists in registry
   podman pull quay.io/rbrhssa/mortgage-agents:v1.0.0
   
   # Verify image reference in deployment
   oc describe deployment mortgage-agents
   ```

2. **Pod Start Failures**
   ```bash
   # Check pod events
   oc describe pod <pod-name>
   
   # Check application logs
   oc logs <pod-name>
   ```

3. **Configuration Issues**
   ```bash
   # Verify ConfigMap
   oc describe configmap mortgage-agents-config
   
   # Check Secret (without revealing values)
   oc describe secret mortgage-agents-secrets
   ```

### Debug Commands

```bash
# Get all resources
oc get all -l app=mortgage-agents

# Check pod details
oc describe pod -l app=mortgage-agents

# Check service endpoints
oc get endpoints mortgage-agents-service

# Test service connectivity
oc port-forward svc/mortgage-agents-service 8080:8000
```

## Backup and Recovery

### Data Backup

The system uses a PersistentVolumeClaim for data storage:

```bash
# Backup PVC data
oc rsync <pod-name>:/opt/app-root/src/mortgage-agents/data ./backup/

# Restore from backup
oc rsync ./backup/ <pod-name>:/opt/app-root/src/mortgage-agents/data
```

### Configuration Backup

```bash
# Export configuration
oc get configmap mortgage-agents-config -o yaml > config-backup.yaml
oc get secret mortgage-agents-secrets -o yaml > secret-backup.yaml
```

## Performance Tuning

### Resource Optimization

Edit `deployment.yaml` to adjust:
- CPU/Memory requests and limits
- HPA thresholds
- Replica counts

### Database Connections

Configure in `configmap.yaml`:
- Neo4j connection pool settings
- Database timeout values
- Connection retry logic

## Support

For deployment issues:
1. Check logs: `./deploy.sh logs`
2. Verify status: `./deploy.sh status` 
3. Run health checks: `./deploy.sh health`
4. Review OpenShift events: `oc get events --sort-by='.lastTimestamp'`
