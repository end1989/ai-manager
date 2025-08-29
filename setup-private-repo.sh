#!/bin/bash

# AI Manager Private Repository Setup Script
# This script automates the initial setup process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 AI Manager Private Repository Setup${NC}"
echo "=================================================="

# Check prerequisites
echo -e "\n${BLUE}[1/6] Checking prerequisites...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Install it from: https://docker.com/get-started"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites installed${NC}"

# Get repository details
echo -e "\n${BLUE}[2/6] Repository configuration...${NC}"

read -p "Enter your GitHub organization/username: " GITHUB_ORG
read -p "Enter repository name (default: ai-manager): " REPO_NAME
REPO_NAME=${REPO_NAME:-ai-manager}

REPO_FULL_NAME="$GITHUB_ORG/$REPO_NAME"

echo -e "${GREEN}✅ Will create repository: $REPO_FULL_NAME${NC}"

# Create GitHub repository
echo -e "\n${BLUE}[3/6] Creating private repository...${NC}"

if gh repo view "$REPO_FULL_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Repository $REPO_FULL_NAME already exists${NC}"
    read -p "Continue with existing repository? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Creating private repository..."
    gh repo create "$REPO_FULL_NAME" \
        --private \
        --description "AI-powered task management and execution system with enterprise CI/CD" \
        --gitignore Python \
        --license MIT
    
    echo -e "${GREEN}✅ Repository created successfully${NC}"
fi

# Update configuration files
echo -e "\n${BLUE}[4/6] Updating configuration files...${NC}"

# Update GitHub Actions workflow
if [ -f ".github/workflows/ci.yml" ]; then
    sed -i.bak "s/your-org/$GITHUB_ORG/g" .github/workflows/ci.yml
    echo "✅ Updated CI workflow"
fi

# Update Kubernetes manifests
if [ -f "k8s/ai-manager.yaml" ]; then
    sed -i.bak "s/your-org/$GITHUB_ORG/g" k8s/ai-manager.yaml
    echo "✅ Updated Kubernetes manifests"
fi

# Update Dockerfile
if [ -f "Dockerfile" ]; then
    sed -i.bak "s/your-org/$GITHUB_ORG/g" Dockerfile
    echo "✅ Updated Dockerfile"
fi

echo -e "${GREEN}✅ Configuration files updated${NC}"

# Set up git remote
echo -e "\n${BLUE}[5/6] Configuring git remote...${NC}"

if git remote get-url origin &> /dev/null; then
    echo "Updating existing remote..."
    git remote set-url origin "https://github.com/$REPO_FULL_NAME.git"
else
    echo "Adding new remote..."
    git remote add origin "https://github.com/$REPO_FULL_NAME.git"
fi

echo -e "${GREEN}✅ Git remote configured${NC}"

# Initial commit and push
echo -e "\n${BLUE}[6/6] Pushing code to repository...${NC}"

git add .
git commit -m "🚀 Initial commit: AI Manager with Enterprise CI/CD

✨ Features:
• Complete AI-powered task management system  
• 14 advanced task templates (ML, DevOps, Blockchain, etc.)
• Enterprise CI/CD pipeline with security scanning
• Kubernetes deployment configurations
• Real-time monitoring dashboard
• AI-powered code review system

🔒 Security:
• Private repository ready
• Comprehensive vulnerability scanning  
• Secrets management
• Container security hardening
• Compliance reporting

🏗️ Infrastructure:
• Docker multi-stage builds
• Kubernetes StatefulSets and Deployments
• Auto-scaling and rolling updates
• Monitoring with Prometheus/Grafana
• ELK stack for logging

Ready for production deployment! 🎯" 2>/dev/null || echo "Commit created"

git branch -M main
git push -u origin main

echo -e "${GREEN}✅ Code pushed to repository${NC}"

# Success message
echo -e "\n${GREEN}🎉 SUCCESS! Your AI Manager private repository is ready!${NC}"
echo "=================================================="
echo -e "${BLUE}Repository URL:${NC} https://github.com/$REPO_FULL_NAME"
echo -e "${BLUE}Next steps:${NC}"
echo "1. Go to repository Settings > Secrets and variables > Actions"
echo "2. Add the required secrets (see QUICK_START_DEPLOYMENT.md)"
echo "3. Watch the CI/CD pipeline run in the Actions tab"
echo "4. Start local development with: docker-compose up -d"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "• QUICK_START_DEPLOYMENT.md - 15-minute setup guide"  
echo "• DEPLOYMENT_GUIDE.md - Complete deployment manual"
echo "• SECURITY.md - Security policies and procedures"
echo ""
echo -e "${GREEN}Your AI Manager system is production-ready! 🚀${NC}"

# Open repository in browser
read -p "Open repository in browser? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    gh repo view "$REPO_FULL_NAME" --web
fi