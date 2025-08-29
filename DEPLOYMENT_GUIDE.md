# AI Manager - Private Repository Deployment Guide

This guide provides comprehensive instructions for setting up the AI Manager system in a private repository with full CI/CD pipeline, security scanning, and production deployment capabilities.

## 🔒 Private Repository Setup

### 1. Repository Configuration

#### Create Private Repository
```bash
# Using GitHub CLI
gh repo create your-org/ai-manager --private --description "AI-powered task management and execution system"

# Clone and push existing code
git remote add origin https://github.com/your-org/ai-manager.git
git branch -M main
git push -u origin main
```

#### Repository Settings
- **Visibility**: Private
- **Branch Protection**: Enable for `main` and `develop` branches
- **Required Reviews**: Minimum 1 review for production deployments
- **Status Checks**: Require CI/CD pipeline to pass
- **Signed Commits**: Recommended for security

### 2. Required Secrets Configuration

Set up the following secrets in your GitHub repository:

#### Core Application Secrets
```bash
# GitHub Repository Secrets (Settings > Secrets and variables > Actions)

# Container Registry Access
GHCR_USERNAME=your-github-username
GHCR_TOKEN=ghp_your_personal_access_token

# AI Provider API Keys
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database Credentials
POSTGRES_PASSWORD=secure-postgres-password
REDIS_PASSWORD=secure-redis-password

# Application Security
SECRET_KEY=super-secret-application-key-min-32-chars
JWT_SECRET_KEY=jwt-signing-key-for-authentication

# Cloud Provider Credentials (for deployment)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-west-2

# Monitoring and Alerting
GRAFANA_PASSWORD=secure-grafana-admin-password
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_SECURITY_WEBHOOK=https://hooks.slack.com/services/SECURITY/WEBHOOK

# Security Scanning
SNYK_TOKEN=your-snyk-api-token
CODECOV_TOKEN=your-codecov-token

# Backup Configuration
BACKUP_S3_BUCKET=ai-manager-backups-your-org
```

### 3. Environment-Specific Configuration

#### Production Environment Variables
Create these as environment secrets for production deployment:

```bash
# Production-specific secrets
PRODUCTION_DATABASE_URL=postgresql://user:pass@prod-db:5432/ai_manager
PRODUCTION_REDIS_URL=redis://:pass@prod-redis:6379/0
PRODUCTION_DOMAIN=yourdomain.com
SSL_CERT_PATH=/etc/ssl/certs/yourdomain.com.crt
SSL_KEY_PATH=/etc/ssl/private/yourdomain.com.key
```

#### Staging Environment Variables
```bash
# Staging-specific secrets  
STAGING_DATABASE_URL=postgresql://user:pass@staging-db:5432/ai_manager_staging
STAGING_REDIS_URL=redis://:pass@staging-redis:6379/1
STAGING_DOMAIN=staging.yourdomain.com
```

## 🚀 CI/CD Pipeline Overview

### Pipeline Stages

1. **Security Scanning** (All branches)
   - Secret detection (GitLeaks, TruffleHog)
   - Dependency vulnerabilities (Safety, pip-audit)
   - SAST analysis (Bandit, Semgrep)
   - Container scanning (Trivy, Snyk)
   - License compliance
   - Infrastructure as Code security (Checkov)

2. **Code Quality** (All branches)
   - Linting (Black, isort, flake8)
   - Type checking (mypy)
   - Code analysis (pylint)

3. **Testing** (All branches)
   - Unit tests (pytest)
   - Integration tests
   - System tests
   - Performance testing (locust)
   - Coverage reporting (codecov)

4. **Build & Package** (main, develop)
   - Multi-stage Docker builds
   - Container registry push (GHCR)
   - Build artifacts

5. **Deployment** (Environment-specific)
   - Staging: Automatic on `develop` branch
   - Production: Manual approval required on `main` branch

### Pipeline Triggers

- **Push to any branch**: Security scanning, quality checks, testing
- **Pull Request**: Full pipeline including build
- **Push to develop**: Deploy to staging
- **Push to main**: Deploy to production (with approval)
- **Schedule**: Daily security scans
- **Manual**: Deploy to specific environment

## 🏗️ Infrastructure Setup

### Prerequisites

1. **Kubernetes Cluster**
   - Production: Managed Kubernetes (EKS, GKE, AKS)
   - Staging: Can use smaller cluster or local setup
   - Required addons: Ingress controller, cert-manager, monitoring

2. **Container Registry**
   - GitHub Container Registry (ghcr.io) - included with GitHub
   - Private repository access required

3. **DNS and SSL**
   - Domain configuration
   - SSL certificates (Let's Encrypt or commercial)

4. **Monitoring Stack**
   - Prometheus for metrics
   - Grafana for dashboards
   - ELK stack for logging (optional)

### Deployment Options

#### Option 1: Kubernetes (Recommended for Production)
```bash
# Deploy to staging
./deploy/deploy.sh staging deploy

# Deploy to production  
./deploy/deploy.sh production deploy

# Check status
./deploy/deploy.sh production status

# View logs
./deploy/deploy.sh production logs app
```

#### Option 2: Docker Compose (Development/Testing)
```bash
# Start all services
docker-compose up -d

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 🔐 Security Best Practices

### 1. Secrets Management

- **Never commit secrets to version control**
- Use GitHub Secrets for CI/CD variables
- Consider external secret managers (AWS Secrets Manager, Azure Key Vault)
- Rotate secrets regularly
- Use different secrets for each environment

### 2. Container Security

- Use non-root users in containers
- Minimal base images (alpine, distroless)
- Multi-stage builds to reduce attack surface
- Regular security scanning
- Read-only root filesystems

### 3. Network Security

- Private container registry
- Network policies in Kubernetes
- TLS/SSL for all communications
- VPN or private networks for management access
- Rate limiting and DDoS protection

### 4. Access Control

- Role-based access control (RBAC)
- Principle of least privilege
- Multi-factor authentication
- Regular access reviews
- Audit logging

### 5. Monitoring and Alerting

- Security event monitoring
- Failed authentication alerts
- Resource usage monitoring
- Performance anomaly detection
- Automated incident response

## 📊 Monitoring and Observability

### Metrics Collection
- Application metrics (Prometheus)
- System metrics (Node Exporter)
- Container metrics (cAdvisor)
- Custom business metrics

### Logging Strategy
- Structured logging (JSON format)
- Centralized log aggregation
- Log retention policies
- Security event correlation

### Alerting Rules
- High error rates
- Performance degradation
- Security violations
- Resource exhaustion
- Service unavailability

### Dashboards
- Application performance
- Infrastructure health
- Security metrics
- Business KPIs
- Cost monitoring

## 🔄 Backup and Disaster Recovery

### Backup Strategy
- Database backups (automated daily)
- Application data backups
- Configuration backups
- Regular backup testing
- Cross-region backup replication

### Disaster Recovery
- Recovery time objective (RTO): 4 hours
- Recovery point objective (RPO): 1 hour
- Automated failover capabilities
- Regular DR testing
- Documented recovery procedures

## 📋 Operational Procedures

### Deployment Process
1. Code review and approval
2. CI/CD pipeline validation
3. Staging deployment and testing
4. Production deployment approval
5. Health checks and monitoring
6. Rollback procedures if needed

### Incident Response
1. Automated alerting
2. Incident triage and classification
3. Investigation and containment
4. Resolution and recovery
5. Post-incident review and improvements

### Maintenance Windows
- Scheduled maintenance windows
- Rolling updates for zero-downtime
- Database maintenance procedures
- Security patching schedule

## 🧪 Testing Strategy

### Test Types
- Unit tests (90%+ coverage required)
- Integration tests
- End-to-end tests
- Security tests
- Performance tests
- Load tests

### Testing Environments
- Development: Local development
- Staging: Production-like testing
- Production: Live monitoring and testing

### Test Automation
- Automated test execution in CI/CD
- Test result reporting
- Performance regression detection
- Security vulnerability testing

## 📈 Performance Optimization

### Application Performance
- Async/await patterns
- Database query optimization
- Caching strategies
- Connection pooling
- Load balancing

### Infrastructure Performance
- Auto-scaling policies
- Resource allocation optimization
- CDN usage
- Database read replicas
- Container resource limits

## 🔧 Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Critical fixes
- `release/*`: Release preparation

### Code Quality
- Pre-commit hooks
- Automated code formatting
- Static analysis
- Dependency scanning
- License compliance

### Review Process
- Pull request reviews
- Automated checks
- Security review for sensitive changes
- Documentation updates
- Test coverage validation

## 📞 Support and Troubleshooting

### Common Issues
- Service startup failures
- Database connectivity issues
- Authentication problems
- Performance bottlenecks
- Security alerts

### Troubleshooting Tools
- Log analysis
- Metrics monitoring
- Trace analysis
- Health check endpoints
- Debug mode configuration

### Getting Help
- Internal documentation
- Runbook procedures
- Escalation contacts
- External support channels
- Community resources

---

## 🎯 Quick Start Checklist

- [ ] Create private GitHub repository
- [ ] Configure repository secrets
- [ ] Set up Kubernetes cluster
- [ ] Configure DNS and SSL certificates
- [ ] Run initial deployment to staging
- [ ] Validate all security scans pass
- [ ] Deploy to production
- [ ] Set up monitoring and alerting
- [ ] Configure backup procedures
- [ ] Document operational procedures

---

**Last Updated**: 2025-08-29  
**Version**: 1.0.0  
**Environment**: Production-Ready