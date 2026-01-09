---
title: TTA Environment Setup Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/environments/ENVIRONMENT_SETUP_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Environment Setup Guide]]

## Overview

The TTA project supports separate **Development** and **Staging** environments that can run simultaneously on your homelab machine. This guide explains how to set up, configure, and switch between these environments.

## Environment Architecture

### Development Environment
- **Purpose:** Active development, experimentation, rapid iteration
- **Ports:** Standard ports (7474, 7687, 6379, 8080, 3000, 9090)
- **Security:** Relaxed settings for ease of development
- **Logging:** DEBUG level, verbose output
- **Data:** Development data, can be reset frequently

### Staging Environment
- **Purpose:** Production-like testing, validation, multi-user testing
- **Ports:** Offset ports (7475, 7688, 6380, 8081, 3001, 9091)
- **Security:** Production-like settings
- **Logging:** INFO level, structured output
- **Data:** Staging data, more persistent

## Quick Start

### 1. Initial Setup

```bash
# Navigate to project root
cd /home/thein/recovered-tta-storytelling

# Create development environment file
cp .env.dev.example .env.dev

# Create staging environment file
cp .env.staging.example .env.staging

# Edit environment files and set your actual values
nano .env.dev      # Set development credentials
nano .env.staging  # Set staging credentials
```

### 2. Start Development Environment

```bash
# Start all development services
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Check status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### 3. Start Staging Environment

```bash
# Start all staging services
docker-compose -f docker-compose.staging-homelab.yml --env-file .env.staging up -d

# Check status
docker-compose -f docker-compose.staging-homelab.yml ps

# View logs
docker-compose -f docker-compose.staging-homelab.yml logs -f
```

### 4. Run Both Simultaneously

```bash
# Start development
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Start staging (different ports, no conflicts)
docker-compose -f docker-compose.staging-homelab.yml --env-file .env.staging up -d

# Check both
./scripts/switch-environment.sh --both
```

## Environment Configuration

### Development (.env.dev)

Key settings for development:

```bash
# Environment identification
ENVIRONMENT=development
CONTAINER_PREFIX=tta-dev

# Database ports (standard)
NEO4J_URI=bolt://localhost:7687
REDIS_PORT=6379
POSTGRES_PORT=5432

# API configuration
API_PORT=8080
API_DEBUG=true
API_LOG_LEVEL=DEBUG

# Security (relaxed for development)
JWT_SECRET_KEY=dev_jwt_secret_key_not_for_production
```

### Staging (.env.staging)

Key settings for staging:

```bash
# Environment identification
ENVIRONMENT=staging
CONTAINER_PREFIX=tta-staging

# Database ports (offset to avoid conflicts)
NEO4J_URI=bolt://localhost:7688
REDIS_PORT=6380
POSTGRES_PORT=5433

# API configuration
API_PORT=8081
API_DEBUG=false
API_LOG_LEVEL=INFO

# Security (production-like)
JWT_STAGING_SECRET_KEY=staging_jwt_secret_key_secure_change_me
```

## VS Code Workspace Integration

### Development Workspace

Open the development workspace:

```bash
code TTA-Development.code-workspace
```

Features:
- Pre-configured tasks for starting/stopping dev services
- Debug configurations for development
- Quick access to dev service URLs
- Development-specific settings

### Staging Workspace

Open the staging workspace:

```bash
code TTA-Staging.code-workspace
```

Features:
- Pre-configured tasks for starting/stopping staging services
- Integration test configurations
- Quick access to staging service URLs
- Production-like settings

## Using the Environment Switcher

The `switch-environment.sh` script provides convenient environment management:

```bash
# Show help
./scripts/switch-environment.sh --help

# Switch to development
./scripts/switch-environment.sh dev

# Switch to staging
./scripts/switch-environment.sh staging

# Show status of both environments
./scripts/switch-environment.sh --both

# Check environment configuration
./scripts/switch-environment.sh --check dev
./scripts/switch-environment.sh --check staging
```

## Service Access URLs

### Development Environment

| Service | URL | Purpose |
|---------|-----|---------|
| Neo4j Browser | http://localhost:7474 | Graph database UI |
| API Server | http://localhost:8080 | Backend API |
| Frontend | http://localhost:3000 | Web interface |
| Grafana | http://localhost:3000 | Monitoring dashboard |
| Prometheus | http://localhost:9090 | Metrics collection |
| Redis Commander | http://localhost:8081 | Redis management |

### Staging Environment

| Service | URL | Purpose |
|---------|-----|---------|
| Neo4j Browser | http://localhost:7475 | Graph database UI |
| API Server | http://localhost:8081 | Backend API |
| Frontend | http://localhost:3001 | Web interface |
| Grafana | http://localhost:3002 | Monitoring dashboard |
| Prometheus | http://localhost:9091 | Metrics collection |
| Redis Commander | http://localhost:8082 | Redis management |
| Health Check | http://localhost:8090 | Service health |

## Common Workflows

### Daily Development

```bash
# Morning: Start development environment
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Open development workspace
code TTA-Development.code-workspace

# Work on features...

# Evening: Stop development environment
docker-compose -f docker-compose.dev.yml down
```

### Testing in Staging

```bash
# Start staging environment
docker-compose -f docker-compose.staging-homelab.yml --env-file .env.staging up -d

# Open staging workspace
code TTA-Staging.code-workspace

# Run integration tests
ENVIRONMENT=staging uv run pytest tests/integration/ -v

# Run E2E tests
ENVIRONMENT=staging uv run pytest tests/e2e/ -v

# Stop staging when done
docker-compose -f docker-compose.staging-homelab.yml down
```

### Parallel Development and Testing

```bash
# Start both environments
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
docker-compose -f docker-compose.staging-homelab.yml --env-file .env.staging up -d

# Develop in dev environment (port 8080)
# Test in staging environment (port 8081)

# Check status of both
./scripts/switch-environment.sh --both
```

## Troubleshooting

### Port Conflicts

If you see port conflict errors:

```bash
# Check what's using the ports
sudo lsof -i :7474  # Neo4j dev
sudo lsof -i :7475  # Neo4j staging
sudo lsof -i :6379  # Redis dev
sudo lsof -i :6380  # Redis staging

# Stop conflicting services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.staging-homelab.yml down
```

### Environment File Issues

If environment variables aren't loading:

```bash
# Verify environment file exists
ls -la .env.dev .env.staging

# Check environment file syntax
cat .env.dev | grep -v '^#' | grep -v '^$'

# Recreate from template if needed
cp .env.dev.example .env.dev
```

### Database Connection Issues

```bash
# Check database containers are running
docker ps | grep neo4j
docker ps | grep redis
docker ps | grep postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs neo4j
docker-compose -f docker-compose.staging-homelab.yml logs neo4j-staging

# Restart databases
docker-compose -f docker-compose.dev.yml restart neo4j redis
```

## Best Practices

1. **Keep Environments Separate**
   - Use different API keys for dev and staging
   - Use different passwords for databases
   - Don't mix development and staging data

2. **Regular Cleanup**
   - Stop unused environments to free resources
   - Clean up old Docker volumes periodically
   - Review and update environment files regularly

3. **Security**
   - Never commit .env.dev or .env.staging files
   - Use strong passwords in staging (production-like)
   - Rotate credentials regularly

4. **Testing**
   - Test in development first
   - Validate in staging before production
   - Run full test suite in staging environment

5. **Monitoring**
   - Check Grafana dashboards regularly
   - Review logs for errors
   - Monitor resource usage

## Next Steps

- [[TTA/Workflows/PORT_REFERENCE|Port Reference Guide]] - Detailed port allocation
- [[TTA/Workflows/SWITCHING_ENVIRONMENTS|Switching Environments]] - Advanced switching techniques
- [[TTA/Workflows/TESTING_GUIDE|Testing Guide]] - Running tests in each environment
- [[TTA/Workflows/PRODUCTION_DEPLOYMENT_GUIDE|Deployment Guide]] - Production deployment

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs: `docker-compose -f <compose-file> logs`
3. Check environment configuration: `./scripts/switch-environment.sh --check <env>`
4. Consult the main [[TTA/Workflows/README|README.md]]


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs environments environment setup guide document]]
