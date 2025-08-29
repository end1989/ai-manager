@echo off
setlocal enabledelayedexpansion

echo 🚀 AI Manager Private Repository Setup
echo ==================================================

REM Check prerequisites
echo [1/6] Checking prerequisites...

where git >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed
    echo Install it from: https://git-scm.com/
    pause
    exit /b 1
)

where gh >nul 2>&1
if errorlevel 1 (
    echo ❌ GitHub CLI is not installed
    echo Install it from: https://cli.github.com/
    pause
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed
    echo Install it from: https://docker.com/get-started
    pause
    exit /b 1
)

echo ✅ All prerequisites installed

REM Get repository details
echo.
echo [2/6] Repository configuration...

set /p GITHUB_ORG="Enter your GitHub organization/username: "
set /p REPO_NAME="Enter repository name (default: ai-manager): "
if "%REPO_NAME%"=="" set REPO_NAME=ai-manager

set REPO_FULL_NAME=%GITHUB_ORG%/%REPO_NAME%

echo ✅ Will create repository: %REPO_FULL_NAME%

REM Create GitHub repository
echo.
echo [3/6] Creating private repository...

gh repo view "%REPO_FULL_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Repository %REPO_FULL_NAME% already exists
    set /p CONTINUE="Continue with existing repository? (y/N): "
    if /i not "!CONTINUE!"=="y" exit /b 1
) else (
    echo Creating private repository...
    gh repo create "%REPO_FULL_NAME%" --private --description "AI-powered task management and execution system with enterprise CI/CD" --gitignore Python --license MIT
    echo ✅ Repository created successfully
)

REM Update configuration files
echo.
echo [4/6] Updating configuration files...

if exist ".github\workflows\ci.yml" (
    powershell -Command "(Get-Content '.github\workflows\ci.yml') -replace 'your-org', '%GITHUB_ORG%' | Set-Content '.github\workflows\ci.yml'"
    echo ✅ Updated CI workflow
)

if exist "k8s\ai-manager.yaml" (
    powershell -Command "(Get-Content 'k8s\ai-manager.yaml') -replace 'your-org', '%GITHUB_ORG%' | Set-Content 'k8s\ai-manager.yaml'"
    echo ✅ Updated Kubernetes manifests
)

if exist "Dockerfile" (
    powershell -Command "(Get-Content 'Dockerfile') -replace 'your-org', '%GITHUB_ORG%' | Set-Content 'Dockerfile'"
    echo ✅ Updated Dockerfile
)

echo ✅ Configuration files updated

REM Set up git remote
echo.
echo [5/6] Configuring git remote...

git remote get-url origin >nul 2>&1
if not errorlevel 1 (
    echo Updating existing remote...
    git remote set-url origin "https://github.com/%REPO_FULL_NAME%.git"
) else (
    echo Adding new remote...
    git remote add origin "https://github.com/%REPO_FULL_NAME%.git"
)

echo ✅ Git remote configured

REM Initial commit and push
echo.
echo [6/6] Pushing code to repository...

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

Ready for production deployment! 🎯"

git branch -M main
git push -u origin main

echo ✅ Code pushed to repository

REM Success message
echo.
echo 🎉 SUCCESS! Your AI Manager private repository is ready!
echo ==================================================
echo Repository URL: https://github.com/%REPO_FULL_NAME%
echo Next steps:
echo 1. Go to repository Settings ^> Secrets and variables ^> Actions
echo 2. Add the required secrets (see QUICK_START_DEPLOYMENT.md)
echo 3. Watch the CI/CD pipeline run in the Actions tab
echo 4. Start local development with: docker-compose up -d
echo.
echo 📚 Documentation:
echo • QUICK_START_DEPLOYMENT.md - 15-minute setup guide  
echo • DEPLOYMENT_GUIDE.md - Complete deployment manual
echo • SECURITY.md - Security policies and procedures
echo.
echo Your AI Manager system is production-ready! 🚀

REM Open repository in browser
set /p OPEN_BROWSER="Open repository in browser? (Y/n): "
if /i not "!OPEN_BROWSER!"=="n" (
    gh repo view "%REPO_FULL_NAME%" --web
)

pause