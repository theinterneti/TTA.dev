---
applyTo:
  - "docker/**"
  - "docker-compose*.yml"
  - ".env*"
  - "scripts/**"
tags: ['general']
priority: 8
instruction_type: "infrastructure"
auto_trigger: "true"
applies_to: "["docker", "environment", "data separation", "redis", "neo4j", "database"]"
related_files:
  - "docker-compose.dev.yml"
  - "docker-compose.test.yml"
  - "docker-compose.staging.yml"
  - ".env.dev"
  - ".env.test"
  - ".env.staging"
---

# TTA Data Separation Strategy

## Problem Statement

**Concern**: "I don't want our memories from the dev process clogging up TTA's agents."

Development data (test scenarios, debugging artifacts, experimental agent memories) must be completely isolated from testing, staging, and production environments to prevent:
- Development noise contaminating AI agent learning
- Test data leaking into production workflows
- Staging snapshots polluting real user experiences
- Debugging traces appearing in therapeutic sessions

## Current State Analysis

### ✅ Good Separation (Volume Level)

**Named Volumes** - Each environment has isolated storage:
```
Dev:     tta_neo4j_dev_data, tta_redis_dev_data
Test:    tta_neo4j_test_data, tta_redis_test_data
Staging: tta_neo4j_staging_data, tta_redis_staging_data (needs verification)
Prod:    (not yet configured)
```

**Container Names** - Prevent runtime conflicts:
```
Dev:     tta-dev-neo4j, tta-dev-redis
Test:    tta-test-neo4j, tta-test-redis
Staging: tta-staging-neo4j, tta-staging-redis
```

**Networks** - Isolated container communication:
```
Dev:     tta-dev-network
Test:    tta-test-network
Staging: tta-staging-network
```

**Credentials** - Different passwords per environment:
```
Dev:     neo4j/tta_dev_password_2024
Test:    neo4j/tta_test_password_2024
Staging: (needs verification)
Prod:    (secrets management required)
```

### ⚠️ Problems (Data Level)

**1. Redis Database Overlap**
- All environments use same Redis DB number (0)
- Keys can collide if instances run on same port
- No namespace prefixing strategy

**2. Neo4j Database Naming**
- All environments use database name "neo4j"
- Labels/nodes not prefixed with environment
- Multi-database feature not utilized

**3. Port Conflicts**
- All compose files expose same ports (7687, 7474, 6379)
- Cannot run dev + test simultaneously
- Manual port changes required

**4. Agent Memory Contamination Risk**
```
Current Redis keys (from dev):
- username:alice → Could be dev test data
- user:123 → Could be staging user
- email:test@example.com → Could be from any environment

No way to distinguish!
```

## Comprehensive Solution

### 1. Port Strategy - Environment-Specific Ports

**Development** (docker-compose.dev.yml):
```yaml
services:
  neo4j:
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
  redis:
    ports:
      - "6379:6379"
```

**Testing** (docker-compose.test.yml):
```yaml
services:
  neo4j:
    ports:
      - "8474:7474"  # HTTP (+1000)
      - "8687:7687"  # Bolt (+1000)
  redis:
    ports:
      - "7379:6379"  # (+1000)
```

**Staging** (docker-compose.staging.yml):
```yaml
services:
  neo4j:
    ports:
      - "9474:7474"  # HTTP (+2000)
      - "9687:7687"  # Bolt (+2000)
  redis:
    ports:
      - "8379:6379"  # (+2000)
```

**Production** (docker-compose.prod.yml):
```yaml
# No external ports exposed - internal network only
# Access via reverse proxy/load balancer
```

### 2. Redis Database Numbers

**Option A: Separate Instances (RECOMMENDED)**
```yaml
# Each environment runs own Redis instance on different port
# Pros: Complete isolation, easy backup/restore
# Cons: More resource usage

Dev:     localhost:6379 (any DB number)
Test:    localhost:7379 (any DB number)
Staging: localhost:8379 (any DB number)
```

**Option B: Shared Instance with DB Numbers**
```yaml
# Single Redis instance, different DB numbers
# Pros: Lower resource usage
# Cons: Shared memory limits, harder cleanup

Dev:     localhost:6379/0
Test:    localhost:6379/1
Staging: localhost:6379/2
Prod:    localhost:6379/3
```

**Decision**: Use **Option A** for full isolation.

### 3. Neo4j Multi-Database Strategy

Neo4j Community Edition supports multiple databases (since 4.0):

```cypher
-- Create environment-specific databases
CREATE DATABASE tta_dev;
CREATE DATABASE tta_test;
CREATE DATABASE tta_staging;
CREATE DATABASE tta_prod;
```

**Environment Variables**:
```bash
# .env.dev
NEO4J_DATABASE=tta_dev

# .env.test
NEO4J_DATABASE=tta_test

# .env.staging
NEO4J_DATABASE=tta_staging

# .env.prod
NEO4J_DATABASE=tta_prod
```

### 4. Namespace Prefixing (Defense in Depth)

Even with separate instances/databases, use prefixes for clarity:

**Redis Keys**:
```python
# src/common/redis_config.py
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
REDIS_KEY_PREFIX = f"{ENVIRONMENT}:"

def make_key(key: str) -> str:
    """Prefix all Redis keys with environment."""
    return f"{REDIS_KEY_PREFIX}{key}"

# Usage
redis.set(make_key("user:123"), data)  # Becomes "development:user:123"
```

**Neo4j Labels/Properties**:
```python
# src/common/neo4j_config.py
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENV_LABEL = ENVIRONMENT.capitalize()  # Development, Test, Staging, Production

def add_env_label(labels: list[str]) -> list[str]:
    """Add environment label to all nodes."""
    return labels + [ENV_LABEL]

# Usage in Cypher
CREATE (s:Session:Development {id: $id})  # Automatic environment tagging
MATCH (s:Session:Production) RETURN s     # Query only production sessions
```

### 5. Data Cleanup Scripts

**Development Data Wipe** (safe to run anytime):
```bash
#!/bin/bash
# scripts/cleanup/wipe-dev-data.sh

echo "⚠️  This will DELETE ALL development data!"
read -p "Type 'DELETE DEV DATA' to confirm: " confirm

if [ "$confirm" != "DELETE DEV DATA" ]; then
    echo "Cancelled."
    exit 1
fi

# Stop dev containers
docker-compose -f docker-compose.dev.yml down

# Remove dev volumes
docker volume rm tta_neo4j_dev_data tta_neo4j_dev_logs tta_redis_dev_data

# Recreate containers
docker-compose -f docker-compose.dev.yml up -d

echo "✅ Development data wiped clean!"
```

**Test Data Reset** (for CI/CD):
```bash
#!/bin/bash
# scripts/cleanup/reset-test-data.sh

docker-compose -f docker-compose.test.yml down -v  # -v removes volumes
docker-compose -f docker-compose.test.yml up -d
echo "✅ Test environment reset!"
```

**Staging Data Snapshot** (backup before wipe):
```bash
#!/bin/bash
# scripts/cleanup/snapshot-staging.sh

timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/staging/$timestamp

# Backup Neo4j
docker exec tta-staging-neo4j neo4j-admin database dump tta_staging \
    --to=/backups/tta_staging_$timestamp.dump

# Backup Redis
docker exec tta-staging-redis redis-cli --rdb /data/dump_$timestamp.rdb

echo "✅ Staging snapshot created: backups/staging/$timestamp"
```

**NEVER** wipe staging/prod without explicit backup confirmation.

### 6. VS Code Database Configuration

**.vscode/settings.json**:
```json
{
  "redis.database": [
    {
      "name": "TTA Dev Redis",
      "host": "localhost",
      "port": 6379,
      "db": 0,
      "label": "🟢 DEV"
    },
    {
      "name": "TTA Test Redis",
      "host": "localhost",
      "port": 7379,
      "db": 0,
      "label": "🟡 TEST"
    },
    {
      "name": "TTA Staging Redis",
      "host": "localhost",
      "port": 8379,
      "db": 0,
      "label": "🟠 STAGING"
    }
  ]
}
```

**.vscode/database-connections.json** (reference):
```json
[
  {
    "name": "🟢 TTA Dev Neo4j",
    "host": "localhost",
    "port": 7687,
    "username": "neo4j",
    "password": "tta_dev_password_2024",  // pragma: allowlist secret
    "database": "tta_dev"
  },
  {
    "name": "🟡 TTA Test Neo4j",
    "host": "localhost",
    "port": 8687,
    "username": "neo4j",
    "password": "tta_test_password_2024",  // pragma: allowlist secret
    "database": "tta_test"
  },
  {
    "name": "🟠 TTA Staging Neo4j",
    "host": "localhost",
    "port": 9687,
    "username": "neo4j",
    "password": "tta_staging_password_2024",  // pragma: allowlist secret
    "database": "tta_staging"
  }
]
```

### 7. Environment Variable Standards

**.env.dev**:
```bash
ENVIRONMENT=development
CONTAINER_PREFIX=tta-dev
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=tta_dev_password_2024
NEO4J_DATABASE=tta_dev
REDIS_URL=redis://localhost:6379/0
```

**.env.test**:
```bash
ENVIRONMENT=test
CONTAINER_PREFIX=tta-test
NEO4J_URI=bolt://localhost:8687
NEO4J_PASSWORD=tta_test_password_2024
NEO4J_DATABASE=tta_test
REDIS_URL=redis://localhost:7379/0
```

**.env.staging**:
```bash
ENVIRONMENT=staging
CONTAINER_PREFIX=tta-staging
NEO4J_URI=bolt://localhost:9687
NEO4J_PASSWORD=tta_staging_password_2024
NEO4J_DATABASE=tta_staging
REDIS_URL=redis://localhost:8379/0
```

**.env.prod** (secrets manager):
```bash
ENVIRONMENT=production
CONTAINER_PREFIX=tta-prod
# Secrets loaded from vault/secrets manager
# No external ports exposed
```

## Implementation Checklist

### Phase 1: Immediate Fixes (This PR)
- [ ] Update `docker-compose.test.yml` with ports 8474/8687/7379
- [ ] Update `docker-compose.staging.yml` with ports 9474/9687/8379
- [ ] Create `.env.test` with test-specific configuration
- [ ] Update `.env.staging` with staging-specific configuration
- [ ] Create `scripts/cleanup/wipe-dev-data.sh`
- [ ] Update `.vscode/settings.json` with port-separated Redis connections
- [ ] Update `.vscode/database-connections.json` with port-separated Neo4j

### Phase 2: Data Layer Namespacing (Next Sprint)
- [ ] Implement `RedisKeyPrefixer` utility class
- [ ] Implement `Neo4jLabelHelper` utility class
- [ ] Update all Redis operations to use prefixed keys
- [ ] Update all Neo4j operations to include environment labels
- [ ] Add migration script to prefix existing dev data
- [ ] Update documentation with namespace examples

### Phase 3: Multi-Database Migration (Following Sprint)
- [ ] Create Neo4j initialization script with database creation
- [ ] Update docker-compose health checks for specific databases
- [ ] Test multi-database workflows
- [ ] Document database switching procedures
- [ ] Create backup/restore procedures per database

### Phase 4: Production Hardening (Pre-Launch)
- [ ] Secrets management integration (HashiCorp Vault/AWS Secrets Manager)
- [ ] Remove all external ports from production compose file
- [ ] Implement reverse proxy/load balancer configuration
- [ ] Set up automated staging snapshots before deployments
- [ ] Create disaster recovery playbook
- [ ] Penetration testing of data isolation

## Testing the Separation

**Run All Environments Simultaneously**:
```bash
# Terminal 1: Development
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Testing
docker-compose -f docker-compose.test.yml up

# Terminal 3: Staging
docker-compose -f docker-compose.staging.yml up
```

**Verify Isolation**:
```bash
# Connect to dev Neo4j
cypher-shell -a bolt://localhost:7687 -u neo4j -p tta_dev_password_2024
CREATE (n:TestNode {env: "dev"}) RETURN n;

# Connect to test Neo4j
cypher-shell -a bolt://localhost:8687 -u neo4j -p tta_test_password_2024
MATCH (n:TestNode) RETURN count(n);  # Should be 0

# Confirm dev has data
cypher-shell -a bolt://localhost:7687 -u neo4j -p tta_dev_password_2024
MATCH (n:TestNode) RETURN count(n);  # Should be 1
```

## Agent Memory Contamination Prevention

**Before** (current risk):
```python
# Agent stores memory in Redis
redis.set("conversation:123", agent_memory)

# Problem: Which environment is this from?
# Dev testing? Real user session? Staging demo?
# All mixed together in redis:6379/0
```

**After** (isolated):
```python
# Development
redis = Redis(host="localhost", port=6379, db=0)
redis.set(make_key("conversation:123"), agent_memory)
# Becomes: "development:conversation:123" in localhost:6379

# Production
redis = Redis(host="prod-redis.internal", port=6379, db=0)
redis.set(make_key("conversation:123"), agent_memory)
# Becomes: "production:conversation:123" in prod-redis.internal:6379

# No overlap possible - different physical instances!
```

## Benefits

1. **Complete Data Isolation**: Physical separation via volumes + ports
2. **Simultaneous Environments**: Run dev + test + staging at same time
3. **Safe Experimentation**: Wipe dev data without fear
4. **Clear Debugging**: Know exactly which environment data came from
5. **Agent Purity**: Production agents never see dev test data
6. **Easy Backup/Restore**: Per-environment snapshots
7. **Compliance Ready**: Audit trail shows environment separation

## Related Documentation

- `.github/instructions/graph-db.instructions.md` - Neo4j usage patterns
- `.github/instructions/safety.instructions.md` - Security standards
- `.vscode/dev-database-setup.md` - Database setup guide
- `scripts/dev.sh` - Development workflow automation

---

**Last Updated**: 2025-10-26
**Status**: Draft - Pending Phase 1 implementation
**Owner**: Infrastructure Team


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.github/Instructions/Data-separation-strategy]]
