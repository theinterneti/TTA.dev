---
applyTo:
  - "docker/**"
  - "docker-compose*.yml"
  - "Dockerfile*"
  - ".dockerignore"
tags: ['general']
priority: critical
instruction_type: "infrastructure"
auto_trigger: "true"
applies_to: "["docker", "docker-compose", "dockerfile", "container", "infrastructure"]"
related_files:
  - "docker-compose.dev.yml"
  - "docker-compose.test.yml"
  - "docker-compose.staging.yml"
  - ".env.dev"
  - ".env.test"
  - ".env.staging"
---

# Docker Architecture Review & Improvement Recommendations

## Executive Summary

**Current State**: 42 docker-compose files, 62+ Dockerfiles, 56 volumes, fragmented approach
**Assessment**: 🟡 **Functional but needs consolidation and standardization**
**Priority**: Implement improvements before production deployment

---

## Critical Issues Identified

### 1. File Proliferation ⚠️ HIGH PRIORITY

**Problem**: 42 docker-compose files scattered across the repository
- Main environments: `dev.yml`, `test.yml`, `staging.yml`
- Special purposes: `hotreload.yml`, `phase2a.yml`, `analytics.yml`, `homelab.yml`
- Service-specific: `neo4j-staging.yml`
- Templates in `/templates/`
- Monitoring in `/monitoring/`
- Old backups containing compose files
- `.devcontainer` with duplicate configs

**Impact**:
- Configuration drift between environments
- Difficult to maintain consistency
- Unclear which file is authoritative
- Onboarding friction for new developers

**Recommendation**: **Consolidate using Docker Compose override pattern**

```
# Proposed structure:
docker-compose.yml              # Base services (shared across all envs)
docker-compose.dev.yml          # Development overrides
docker-compose.test.yml         # Testing overrides
docker-compose.staging.yml      # Staging overrides
docker-compose.prod.yml         # Production configuration (NEW)
docker-compose.override.yml     # Local developer overrides (gitignored)

# Archive or delete:
- docker-compose.hotreload.yml  → Integrate into dev.yml
- docker-compose.phase2a.yml    → Archive to /archive/
- docker-compose.neo4j-staging.yml → Merge into staging.yml
- templates/**/docker-compose.yml → Delete (use main files)
```

### 2. Image Version Pinning 🔒 SECURITY

**Problem**: Using `:latest` and unpinned versions
```yaml
# Current (BAD):
image: grafana/grafana:latest
image: redis:7-alpine
image: neo4j:5-community

# Recommended (GOOD):
image: grafana/grafana:10.2.3
image: redis:7.2.4-alpine3.19
image: neo4j:5.26.1-community
```

**Impact**:
- Unpredictable builds
- Security vulnerabilities
- Breaking changes without notice
- Cannot rollback reliably

**Action Items**:
- [ ] Pin all image versions to specific tags
- [ ] Document version update process
- [ ] Create Dependabot/Renovate config for automated updates
- [ ] Test version upgrades in dev/test before staging/prod

### 3. Obsolete Version Declaration 📛

**Problem**: All compose files use `version: '3.8'`
```
WARN[0000] docker-compose.yml: the attribute `version` is obsolete
```

**Fix**: Remove `version:` line from all compose files (Docker Compose v2 ignores it)

### 4. Volume Naming Inconsistency 🗂️

**Problem**: Multiple volume naming conventions cause warnings
```
WARN: volume "tta_neo4j_test_data" created for project "tta-test"
      but now expected by project "recovered-tta-storytelling"
```

**Current naming**:
- `tta_neo4j_dev_data`
- `recovered-tta-storytelling_neo4j_data`
- `tta-dev_neo4j-data`

**Recommended**: Standardize on one pattern:
```yaml
volumes:
  neo4j_dev_data:
    name: tta_neo4j_dev_data
    external: false  # Explicitly managed by compose

  # OR use external for manually created volumes
  neo4j_dev_data:
    external: true
    name: tta_neo4j_dev_data
```

**Action**:
- [ ] Choose naming convention: `tta_{service}_{env}_data`
- [ ] Migrate existing volumes or mark as external
- [ ] Document volume lifecycle in data-separation-strategy.md

### 5. Secrets Management 🔐 CRITICAL

**Problem**: Hard-coded credentials in compose files
```yaml
environment:
  - NEO4J_AUTH=neo4j/tta_dev_password_2024  # Visible in compose
  - GF_SECURITY_ADMIN_PASSWORD=admin        # Default password!
```

**Recommendation**: Use Docker secrets or environment variables from secure source

**Implementation**:

```yaml
# docker-compose.prod.yml
services:
  neo4j:
    environment:
      - NEO4J_AUTH_FILE=/run/secrets/neo4j_auth
    secrets:
      - neo4j_auth

secrets:
  neo4j_auth:
    file: ./secrets/neo4j_auth.txt  # Gitignored
    # OR external: true (from secrets manager)
```

**For Production**:
- Use AWS Secrets Manager / HashiCorp Vault / Azure Key Vault
- Inject secrets at runtime, never commit
- Rotate credentials regularly
- Use separate secrets per environment

**Action Items**:
- [ ] Create secrets/ directory (add to .gitignore)
- [ ] Move all passwords to secrets files
- [ ] Update compose files to use secrets
- [ ] Document secret rotation procedure
- [ ] Implement secrets management in CI/CD

### 6. Resource Limits Missing ⚙️

**Problem**: Only staging has resource limits
```yaml
# Staging (GOOD):
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M

# Dev/Test (BAD):
# No limits - can consume all host resources
```

**Recommendation**: Add limits to all environments

```yaml
# Development (generous for debugging):
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 512M

# Test (constrained for CI):
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 2G
    reservations:
      cpus: '0.25'
      memory: 256M

# Production (right-sized per service):
# Based on actual usage metrics
```

### 7. Health Check Dependencies 🏥

**Problem**: Services depend on databases but don't wait for health
```yaml
redis-commander:
  depends_on:
    - redis  # Starts after, but doesn't wait for healthy
```

**Recommendation**: Use health-check-based dependencies

```yaml
redis-commander:
  depends_on:
    redis:
      condition: service_healthy  # Wait for health check to pass
```

**Action**: Update all depends_on to use condition: service_healthy

### 8. Build Context Issues 🏗️

**Problem**: Staging builds from local source code
```yaml
# Current:
shared-components:
  build:
    context: ./web-interfaces/shared
    dockerfile: Dockerfile.staging
  volumes:
    - ./web-interfaces/shared:/app  # Development mount in staging!
```

**Issues**:
- Slow staging startup (rebuilds every time)
- Inconsistent with production (should use pre-built images)
- Development volumes mounted in staging environment

**Recommendation**: Multi-stage approach

```yaml
# Development: Fast iteration with hot reload
shared-components:
  build:
    context: ./web-interfaces/shared
    target: development
  volumes:
    - ./web-interfaces/shared:/app
    - /app/node_modules

# Staging/Production: Pre-built immutable images
shared-components:
  image: registry.tta-platform.com/shared-components:${IMAGE_TAG}
  # No build, no volumes - pure deployment
```

**Multi-stage Dockerfile**:
```dockerfile
# Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS development
ENV NODE_ENV=development
CMD ["npm", "run", "dev"]

FROM base AS build
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
ENV NODE_ENV=production
CMD ["node", "dist/index.js"]
```

### 9. Missing Production Configuration 🚀

**Problem**: No docker-compose.prod.yml

**Create**: Production-ready configuration with:
- No external ports (reverse proxy only)
- Secrets management
- Resource limits based on production sizing
- Read-only file systems where possible
- No privileged containers
- Automated backups
- Log aggregation
- Metrics exporters

### 10. Network Redundancy 🌐

**Problem**: Multiple networks with similar purposes
```
tta-dev-network
tta-dev_tta-staging  # Hybrid name?
tta-test-network
```

**Recommendation**: Clear network strategy

```yaml
# Development: bridge network (default)
networks:
  default:
    name: tta-dev-network

# Production: Multiple networks for security
networks:
  frontend:  # Public-facing services
  backend:   # Internal services (databases, queues)
  monitoring:  # Observability stack
```

---

## Recommended Architecture

### Proposed File Structure

```
📁 TTA Repository Root/
├── docker/
│   ├── dockerfiles/
│   │   ├── api/
│   │   │   ├── Dockerfile          # Multi-stage (dev, prod targets)
│   │   │   └── .dockerignore
│   │   ├── frontend/
│   │   │   ├── Dockerfile
│   │   │   └── .dockerignore
│   │   ├── services/
│   │   │   ├── neo4j/
│   │   │   │   └── Dockerfile.custom  # If custom Neo4j needed
│   │   │   └── redis/
│   │   │       ├── Dockerfile.custom
│   │   │       └── redis.conf
│   │   └── testing/
│   │       └── Dockerfile.e2e
│   │
│   ├── compose/
│   │   ├── docker-compose.yml       # Base services
│   │   ├── docker-compose.dev.yml   # Development overrides
│   │   ├── docker-compose.test.yml  # CI/Testing overrides
│   │   ├── docker-compose.staging.yml
│   │   ├── docker-compose.prod.yml
│   │   └── docker-compose.monitoring.yml  # Optional monitoring stack
│   │
│   ├── scripts/
│   │   ├── build.sh                 # Build all images
│   │   ├── push.sh                  # Push to registry
│   │   ├── deploy-dev.sh
│   │   ├── deploy-staging.sh
│   │   └── health-check.sh
│   │
│   └── configs/
│       ├── neo4j/
│       │   └── neo4j.conf
│       ├── redis/
│       │   └── redis.conf
│       ├── grafana/
│       │   └── datasources.yml
│       └── prometheus/
│           └── prometheus.yml
│
├── .env.example                     # Template
├── .env.dev                         # Development defaults
├── .env.test                        # Test defaults
├── .env.staging                     # Staging (no secrets)
├── secrets/                         # .gitignored
│   ├── .gitkeep
│   ├── neo4j_dev_auth.txt
│   ├── redis_dev_password.txt
│   └── README.md                    # How to set up secrets
│
└── .dockerignore                    # Root .dockerignore
```

### Base Compose Pattern

```yaml
# docker/compose/docker-compose.yml
# Base configuration - shared across all environments

services:
  neo4j:
    image: neo4j:${NEO4J_VERSION:-5.26.1}-community
    container_name: ${CONTAINER_PREFIX:-tta}-neo4j
    # Ports NOT exposed here - per environment
    environment:
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_security_procedures_unrestricted: "apoc.*,gds.*"
      NEO4J_dbms_security_procedures_allowlist: "apoc.*,gds.*"
      NEO4J_dbms_connector_bolt_listen__address: "0.0.0.0:7687"
      NEO4J_dbms_connector_http_listen__address: "0.0.0.0:7474"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:7474 || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 40s
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - backend

  redis:
    image: redis:${REDIS_VERSION:-7.2.4}-alpine3.19
    container_name: ${CONTAINER_PREFIX:-tta}-redis
    command: >
      redis-server
      --appendonly yes
      --maxmemory ${REDIS_MAX_MEMORY:-512mb}
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - backend

volumes:
  neo4j_data:
    name: ${CONTAINER_PREFIX:-tta}_neo4j_${ENVIRONMENT:-dev}_data
  neo4j_logs:
    name: ${CONTAINER_PREFIX:-tta}_neo4j_${ENVIRONMENT:-dev}_logs
  redis_data:
    name: ${CONTAINER_PREFIX:-tta}_redis_${ENVIRONMENT:-dev}_data

networks:
  backend:
    name: ${CONTAINER_PREFIX:-tta}-${ENVIRONMENT:-dev}-backend
    driver: bridge
```

```yaml
# docker/compose/docker-compose.dev.yml
# Development overrides

services:
  neo4j:
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-tta_dev_password_2024}
      NEO4J_dbms_memory_heap_initial__size: 1G
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_logs_debug_level: ${LOG_LEVEL:-INFO}
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 512M

  redis:
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  redis-commander:
    image: rediscommander/redis-commander:0.8.1
    container_name: ${CONTAINER_PREFIX:-tta}-redis-commander
    ports:
      - "8081:8081"
    environment:
      REDIS_HOSTS: local:redis:6379
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - backend
    profiles:
      - tools
```

```yaml
# docker/compose/docker-compose.test.yml
# CI/Testing overrides

services:
  neo4j:
    ports:
      - "8474:7474"
      - "8687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-tta_test_password_2024}
      NEO4J_dbms_memory_heap_initial__size: 512m
      NEO4J_dbms_memory_heap_max__size: 1G
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  redis:
    ports:
      - "7379:6379"
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

```yaml
# docker/compose/docker-compose.prod.yml
# Production configuration

services:
  neo4j:
    # NO external ports - internal network only
    environment:
      NEO4J_AUTH_FILE: /run/secrets/neo4j_auth
      NEO4J_dbms_memory_heap_initial__size: ${NEO4J_HEAP_INITIAL:-2G}
      NEO4J_dbms_memory_heap_max__size: ${NEO4J_HEAP_MAX:-4G}
      NEO4J_dbms_logs_debug_level: WARN
    secrets:
      - neo4j_auth
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    # NO external ports
    command: >
      redis-server
      /usr/local/etc/redis/redis.conf
    configs:
      - source: redis_config
        target: /usr/local/etc/redis/redis.conf
    secrets:
      - redis_password
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G

secrets:
  neo4j_auth:
    external: true  # From secrets manager
  redis_password:
    external: true

configs:
  redis_config:
    file: ../configs/redis/redis.conf
```

---

## Implementation Roadmap

### Phase 1: Immediate Fixes (This Week)
- [ ] Remove `version: '3.8'` from all compose files
- [ ] Pin all image versions
- [ ] Add resource limits to dev and test environments
- [ ] Update depends_on to use `condition: service_healthy`
- [ ] Document current architecture

### Phase 2: Consolidation (Next Sprint)
- [ ] Create base docker-compose.yml
- [ ] Migrate dev, test, staging to override pattern
- [ ] Archive/delete obsolete compose files
- [ ] Centralize Dockerfiles in /docker/dockerfiles/
- [ ] Create .dockerignore files
- [ ] Clean up orphaned Docker volumes

### Phase 3: Security Hardening (Following Sprint)
- [ ] Implement secrets management
- [ ] Move all credentials out of compose files
- [ ] Create secrets/ directory (gitignored)
- [ ] Add read-only file systems where possible
- [ ] Audit and harden security options

### Phase 4: Production Ready (Pre-Launch)
- [ ] Create docker-compose.prod.yml
- [ ] Implement CI/CD image building
- [ ] Set up image registry
- [ ] Add automated backup procedures
- [ ] Implement log aggregation
- [ ] Add metrics and monitoring
- [ ] Load testing and resource sizing
- [ ] Disaster recovery planning

---

## Best Practices Checklist

### Images
- [ ] All images use specific version tags (no `:latest`)
- [ ] Multi-stage Dockerfiles for size optimization
- [ ] .dockerignore files minimize build context
- [ ] Images scanned for vulnerabilities (Trivy/Snyk)
- [ ] Images built in CI, not at runtime

### Security
- [ ] No secrets in compose files or Dockerfiles
- [ ] `security_opt: no-new-privileges:true` on all services
- [ ] `read_only: true` where possible
- [ ] Non-root users in containers
- [ ] Minimal base images (alpine, distroless)

### Configuration
- [ ] Environment variables externalized
- [ ] Secrets management implemented
- [ ] Resource limits on all services
- [ ] Health checks on all services
- [ ] Proper logging configuration

### Operations
- [ ] Automated backups configured
- [ ] Volume lifecycle documented
- [ ] Cleanup scripts for development
- [ ] Monitoring and alerting set up
- [ ] Rollback procedures documented

### Development Experience
- [ ] Single command to start environment
- [ ] Clear documentation for local setup
- [ ] Fast iteration with hot reload
- [ ] Easy data reset procedures
- [ ] VS Code integration maintained

---

## Migration Commands

### Clean Up Orphaned Resources

```bash
# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Remove unused images
docker image prune -a -f

# Comprehensive cleanup
docker system prune -a --volumes -f
```

### Test New Compose Structure

```bash
# Validate compose files
docker compose -f docker/compose/docker-compose.yml \
  -f docker/compose/docker-compose.dev.yml \
  config

# Start with new structure
docker compose -f docker/compose/docker-compose.yml \
  -f docker/compose/docker-compose.dev.yml \
  up -d

# Check health
docker compose ps
docker compose logs -f
```

---

## Metrics & Success Criteria

### Before (Current State)
- 42 docker-compose files
- 62+ Dockerfiles
- 56 Docker volumes
- Inconsistent naming
- Hard-coded secrets
- No production config

### After (Target State)
- 5 docker-compose files (base + 4 environments)
- ~15 Dockerfiles (consolidated, multi-stage)
- Clean volumes (only active environments)
- Consistent naming: `tta_{service}_{env}_data`
- Secrets externalized
- Production-ready configuration
- CI/CD integrated
- Automated testing
- Monitoring dashboards

---

## Related Documentation

- **Data Separation**: `.github/instructions/data-separation-strategy.md`
- **Security Standards**: `.github/instructions/safety.instructions.md`
- **Testing Battery**: `.github/instructions/testing-battery.instructions.md`
- **Environment Ports**: `.vscode/ENVIRONMENT_PORTS_REFERENCE.md`

---

**Last Updated**: 2025-10-26
**Status**: Draft - Awaiting Review
**Priority**: Critical for production readiness
**Owner**: Infrastructure Team
