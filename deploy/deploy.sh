#!/bin/bash

# AI Manager Deployment Script
# Usage: ./deploy.sh [environment] [action]
# Environment: staging, production
# Action: deploy, rollback, status, logs

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="ai-manager"
APP_NAME="ai-manager"

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
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed. Please install helm first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed. Please install docker first."
        exit 1
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Function to set environment
set_environment() {
    local env=$1
    
    case $env in
        staging)
            KUBECONFIG="$HOME/.kube/staging-config"
            ENV_FILE="$PROJECT_ROOT/.env.staging"
            IMAGE_TAG="staging"
            ;;
        production)
            KUBECONFIG="$HOME/.kube/production-config"
            ENV_FILE="$PROJECT_ROOT/.env.production"
            IMAGE_TAG="latest"
            ;;
        *)
            log_error "Invalid environment: $env. Use 'staging' or 'production'"
            exit 1
            ;;
    esac
    
    export KUBECONFIG
    log_info "Environment set to: $env"
    log_info "Using kubeconfig: $KUBECONFIG"
}

# Function to create namespace and secrets
setup_namespace() {
    log_info "Setting up namespace and secrets..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets and configmaps
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml"
    
    # Create Docker registry secret for private images
    if [ ! -z "$GHCR_TOKEN" ]; then
        kubectl create secret docker-registry ghcr-secret \
            --namespace=$NAMESPACE \
            --docker-server=ghcr.io \
            --docker-username=$GHCR_USERNAME \
            --docker-password=$GHCR_TOKEN \
            --docker-email=$GHCR_EMAIL \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    log_success "Namespace and secrets configured"
}

# Function to deploy database
deploy_database() {
    log_info "Deploying PostgreSQL database..."
    
    kubectl apply -f "$PROJECT_ROOT/k8s/postgres.yaml"
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l app=ai-manager-postgres -n $NAMESPACE --timeout=300s
    
    log_success "Database deployment completed"
}

# Function to deploy Redis
deploy_redis() {
    log_info "Deploying Redis cache..."
    
    kubectl apply -f "$PROJECT_ROOT/k8s/redis.yaml"
    
    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=ai-manager-redis -n $NAMESPACE --timeout=300s
    
    log_success "Redis deployment completed"
}

# Function to deploy application
deploy_application() {
    log_info "Deploying AI Manager application..."
    
    # Update image tag in deployment
    sed "s|ghcr.io/your-org/ai-manager:latest|ghcr.io/$GITHUB_REPOSITORY:$IMAGE_TAG|g" \
        "$PROJECT_ROOT/k8s/ai-manager.yaml" > /tmp/ai-manager-deploy.yaml
    
    kubectl apply -f /tmp/ai-manager-deploy.yaml
    
    # Wait for deployment to be ready
    log_info "Waiting for application to be ready..."
    kubectl wait --for=condition=available deployment/ai-manager-app -n $NAMESPACE --timeout=600s
    
    log_success "Application deployment completed"
}

# Function to deploy ingress
deploy_ingress() {
    log_info "Deploying ingress configuration..."
    
    kubectl apply -f "$PROJECT_ROOT/k8s/ingress.yaml"
    
    log_success "Ingress deployment completed"
}

# Function to run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Get service endpoint
    local service_ip=$(kubectl get svc ai-manager-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$service_ip" ]; then
        service_ip=$(kubectl get svc ai-manager-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
        log_warning "Using ClusterIP for testing: $service_ip"
    fi
    
    # Test health endpoint
    if kubectl run smoke-test --rm -i --restart=Never --image=curlimages/curl -- \
        curl -f "http://$service_ip/health" --max-time 30; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Test API documentation endpoint
    if kubectl run smoke-test-docs --rm -i --restart=Never --image=curlimages/curl -- \
        curl -f "http://$service_ip/docs" --max-time 30; then
        log_success "API documentation check passed"
    else
        log_warning "API documentation check failed (non-critical)"
    fi
    
    log_success "Smoke tests completed"
}

# Function to show deployment status
show_status() {
    log_info "Deployment Status:"
    
    echo
    echo "=== Namespace ==="
    kubectl get namespace $NAMESPACE
    
    echo
    echo "=== Deployments ==="
    kubectl get deployments -n $NAMESPACE
    
    echo
    echo "=== StatefulSets ==="
    kubectl get statefulsets -n $NAMESPACE
    
    echo
    echo "=== Services ==="
    kubectl get services -n $NAMESPACE
    
    echo
    echo "=== Ingress ==="
    kubectl get ingress -n $NAMESPACE
    
    echo
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE -o wide
    
    echo
    echo "=== Persistent Volume Claims ==="
    kubectl get pvc -n $NAMESPACE
}

# Function to show logs
show_logs() {
    local component=$1
    
    case $component in
        app|application)
            kubectl logs -f deployment/ai-manager-app -n $NAMESPACE
            ;;
        db|database|postgres)
            kubectl logs -f statefulset/ai-manager-postgres -n $NAMESPACE
            ;;
        redis|cache)
            kubectl logs -f deployment/ai-manager-redis -n $NAMESPACE
            ;;
        *)
            log_info "Available log components: app, db, redis"
            log_info "Usage: $0 [environment] logs [component]"
            ;;
    esac
}

# Function to rollback deployment
rollback_deployment() {
    log_warning "Rolling back to previous version..."
    
    kubectl rollout undo deployment/ai-manager-app -n $NAMESPACE
    
    # Wait for rollback to complete
    kubectl rollout status deployment/ai-manager-app -n $NAMESPACE --timeout=600s
    
    log_success "Rollback completed"
}

# Function to cleanup resources
cleanup() {
    log_warning "Cleaning up deployment resources..."
    
    read -p "Are you sure you want to delete all resources in namespace '$NAMESPACE'? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main deployment function
deploy() {
    local env=$1
    
    log_info "Starting deployment to $env environment..."
    
    check_prerequisites
    set_environment $env
    setup_namespace
    deploy_database
    deploy_redis
    deploy_application
    deploy_ingress
    
    log_info "Waiting for all services to be fully ready..."
    sleep 30
    
    run_smoke_tests
    
    log_success "Deployment to $env completed successfully!"
    
    # Show final status
    show_status
    
    log_info "Access your application at:"
    if [ "$env" = "production" ]; then
        echo "  https://yourdomain.com"
    else
        echo "  https://staging.yourdomain.com"
    fi
}

# Main script logic
main() {
    local environment=${1:-"staging"}
    local action=${2:-"deploy"}
    
    case $action in
        deploy)
            deploy $environment
            ;;
        status)
            set_environment $environment
            show_status
            ;;
        logs)
            set_environment $environment
            show_logs $3
            ;;
        rollback)
            set_environment $environment
            rollback_deployment
            ;;
        cleanup)
            set_environment $environment
            cleanup
            ;;
        *)
            echo "Usage: $0 [environment] [action] [options]"
            echo "Environment: staging, production (default: staging)"
            echo "Actions:"
            echo "  deploy    - Deploy the application (default)"
            echo "  status    - Show deployment status"
            echo "  logs      - Show logs (specify component: app, db, redis)"
            echo "  rollback  - Rollback to previous version"
            echo "  cleanup   - Remove all resources (destructive)"
            echo
            echo "Examples:"
            echo "  $0 production deploy"
            echo "  $0 staging status"
            echo "  $0 production logs app"
            echo "  $0 staging rollback"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"