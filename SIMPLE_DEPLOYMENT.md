# Simple Deployment Guide

## Minimal GitHub Repository Secrets

You only need to add **2 required secrets** to your GitHub repository:

### Required Secrets

Go to: https://github.com/end1989/ai-manager/settings/secrets/actions

1. **`GHCR_USERNAME`**: Your GitHub username (e.g., `end1989`)
2. **`GHCR_TOKEN`**: Your GitHub Personal Access Token
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `write:packages` permission
   - Copy the token value

### Optional Secrets (will use defaults if not provided)

- `SECRET_KEY`: Production secret key (auto-generated if not provided)
- `JWT_SECRET_KEY`: JWT secret key (auto-generated if not provided)
- `OPENAI_API_KEY`: OpenAI API key (will use mock if not provided)
- `ANTHROPIC_API_KEY`: Anthropic API key (will use mock if not provided)

## Quick Start

1. **Add the 2 required secrets** to your repository
2. **Push any change** to trigger the CI/CD pipeline:
   ```bash
   git add .
   git commit -m "trigger deployment"
   git push origin main
   ```

3. **Monitor deployment** at:
   - Actions: https://github.com/end1989/ai-manager/actions
   - Packages: https://github.com/end1989/ai-manager/pkgs/container/ai-manager

## Local Testing

The system is already running locally at:
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Simple Docker Deployment

If you want to run with Docker locally:
```bash
# Build and run with simple configuration
docker-compose -f docker-compose.simple.yml up --build
```

This uses:
- SQLite database (no PostgreSQL needed)
- No Redis (falls back gracefully)
- Minimal configuration
- Single container deployment

## Production Features Available

Even with this simple setup, you get:
- AI-powered task management
- 14 advanced project templates
- Real-time dashboard
- REST API with OpenAPI docs
- Automated CI/CD pipeline
- Security scanning
- Docker containerization
- Health monitoring

## Database

Uses SQLite by default:
- No external database server needed
- Data persisted in Docker volume
- Automatic schema creation
- Perfect for single-node deployment

## What's Next

Once the basic deployment works, you can optionally add:
- External PostgreSQL for multi-node scaling
- Redis for improved caching
- Custom AI provider API keys
- Advanced monitoring with Prometheus/Grafana
- Kubernetes deployment