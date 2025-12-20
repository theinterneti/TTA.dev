# Context: Deployment

**Purpose:** Quick reference for deployment procedures, environment management, and troubleshooting in TTA.

**When to Use:** When deploying components, managing environments, or troubleshooting deployment issues.

---

## Deployment Environments

### Environment Overview

| Environment | Purpose | URL | Database |
|-------------|---------|-----|----------|
| **Development** | Local development | `http://localhost:8000` | Local Docker |
| **Staging** | Pre-production testing | `https://staging.tta.example.com` | Staging cluster |
| **Production** | Live system | `https://tta.example.com` | Production cluster |

### Environment Configuration

#### Development
```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=development
```

#### Staging
```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
REDIS_URL=redis://staging-redis:6379
NEO4J_URL=bolt://staging-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${STAGING_NEO4J_PASSWORD}
```

#### Production
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
REDIS_URL=redis://prod-redis:6379
NEO4J_URL=bolt://prod-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${PROD_NEO4J_PASSWORD}
```

---

## Component Maturity Workflow

### Development → Staging Promotion

**Prerequisites:**
- All tests passing
- Coverage ≥70%
- Linting clean (ruff)
- Type checking clean (pyright)
- No security issues (detect-secrets)
- Component MATURITY.md updated

**Deployment Steps:**
```bash
# 1. Run quality gates
python scripts/workflow/spec_to_production.py \
    --spec specs/component_name.md \
    --component component_name \
    --target staging

# 2. Verify quality gates passed
cat workflow_report_component_name.json | jq '.stage_results.testing.quality_gates'

# 3. Create staging deployment PR
git checkout -b deploy/component-name-staging
git add .
git commit -m "deploy(component-name): promote to staging"
git push origin deploy/component-name-staging

# 4. Merge PR after approval

# 5. Deploy to staging
kubectl set image deployment/tta-api \
    api=tta-api:${VERSION} \
    -n tta-staging

# 6. Verify deployment
kubectl rollout status deployment/tta-api -n tta-staging
```

### Staging → Production Promotion

**Prerequisites:**
- Integration test coverage ≥80%
- All integration tests passing
- Performance meets SLAs
- 7-day uptime ≥99.5% in staging
- Security review complete
- Monitoring configured
- Rollback procedure tested

**Deployment Steps:**
```bash
# 1. Run production quality gates
python scripts/workflow/spec_to_production.py \
    --spec specs/component_name.md \
    --component component_name \
    --target production

# 2. Create production deployment PR
git checkout -b deploy/component-name-production
git add .
git commit -m "deploy(component-name): promote to production"
git push origin deploy/component-name-production

# 3. Merge PR after approval (requires 2 approvals)

# 4. Deploy to production
kubectl set image deployment/tta-api \
    api=tta-api:${VERSION} \
    -n tta-production

# 5. Verify deployment
kubectl rollout status deployment/tta-api -n tta-production

# 6. Monitor metrics
kubectl logs -f deployment/tta-api -n tta-production
```

---

## Deployment Commands

### Docker Commands

#### Build Image
```bash
# Build development image
docker build -t tta-api:dev .

# Build staging image
docker build -t tta-api:staging --build-arg ENV=staging .

# Build production image
docker build -t tta-api:prod --build-arg ENV=production .
```

#### Run Container
```bash
# Run development container
docker run -p 8000:8000 --env-file .env.development tta-api:dev

# Run with volume mount (for development)
docker run -p 8000:8000 \
    -v $(pwd)/src:/app/src \
    --env-file .env.development \
    tta-api:dev
```

#### Docker Compose
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d redis neo4j

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Kubernetes Commands

#### Deployment
```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml -n tta-staging

# Update image
kubectl set image deployment/tta-api \
    api=tta-api:v1.0.1 \
    -n tta-staging

# Scale deployment
kubectl scale deployment/tta-api --replicas=3 -n tta-staging

# Rollback deployment
kubectl rollout undo deployment/tta-api -n tta-staging
```

#### Monitoring
```bash
# Check deployment status
kubectl rollout status deployment/tta-api -n tta-staging

# View pods
kubectl get pods -n tta-staging

# View logs
kubectl logs -f deployment/tta-api -n tta-staging

# View logs for specific pod
kubectl logs -f tta-api-7d8f9c5b6-abc12 -n tta-staging

# Describe pod
kubectl describe pod tta-api-7d8f9c5b6-abc12 -n tta-staging
```

#### Debugging
```bash
# Execute command in pod
kubectl exec -it tta-api-7d8f9c5b6-abc12 -n tta-staging -- /bin/bash

# Port forward to local
kubectl port-forward deployment/tta-api 8000:8000 -n tta-staging

# View events
kubectl get events -n tta-staging --sort-by='.lastTimestamp'
```

---

## Rollback Procedures

### Kubernetes Rollback

#### Quick Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/tta-api -n tta-staging

# Rollback to specific revision
kubectl rollout undo deployment/tta-api --to-revision=2 -n tta-staging

# View rollout history
kubectl rollout history deployment/tta-api -n tta-staging
```

#### Manual Rollback
```bash
# 1. Identify last working version
kubectl rollout history deployment/tta-api -n tta-staging

# 2. Update to last working version
kubectl set image deployment/tta-api \
    api=tta-api:v1.0.0 \
    -n tta-staging

# 3. Verify rollback
kubectl rollout status deployment/tta-api -n tta-staging

# 4. Monitor logs
kubectl logs -f deployment/tta-api -n tta-staging
```

### Database Rollback

#### Redis Rollback
```bash
# 1. Backup current state
redis-cli --rdb /backup/redis-backup-$(date +%Y%m%d-%H%M%S).rdb

# 2. Restore from backup
redis-cli --rdb /backup/redis-backup-20251022-120000.rdb

# 3. Verify data
redis-cli ping
redis-cli dbsize
```

#### Neo4j Rollback
```bash
# 1. Stop Neo4j
neo4j stop

# 2. Restore from backup
cp -r /backup/neo4j-backup-20251022-120000/* /var/lib/neo4j/data/

# 3. Start Neo4j
neo4j start

# 4. Verify data
cypher-shell "MATCH (n) RETURN count(n)"
```

---

## Common Deployment Issues

### Issue 1: Pod CrashLoopBackOff

**Symptoms:**
- Pod status: `CrashLoopBackOff`
- Pod keeps restarting

**Debugging:**
```bash
# 1. Check pod logs
kubectl logs tta-api-7d8f9c5b6-abc12 -n tta-staging

# 2. Check previous logs
kubectl logs tta-api-7d8f9c5b6-abc12 -n tta-staging --previous

# 3. Describe pod
kubectl describe pod tta-api-7d8f9c5b6-abc12 -n tta-staging

# 4. Check events
kubectl get events -n tta-staging --sort-by='.lastTimestamp'
```

**Common Fixes:**
- Fix application startup errors
- Fix environment variables
- Fix health check endpoints
- Increase resource limits

### Issue 2: ImagePullBackOff

**Symptoms:**
- Pod status: `ImagePullBackOff`
- Cannot pull container image

**Debugging:**
```bash
# 1. Check image name
kubectl describe pod tta-api-7d8f9c5b6-abc12 -n tta-staging | grep Image

# 2. Check image exists
docker pull tta-api:v1.0.1

# 3. Check registry credentials
kubectl get secret regcred -n tta-staging -o yaml
```

**Common Fixes:**
- Fix image tag
- Fix registry credentials
- Push image to registry
- Fix image pull policy

### Issue 3: Service Unavailable

**Symptoms:**
- 503 Service Unavailable
- Cannot connect to service

**Debugging:**
```bash
# 1. Check service
kubectl get svc -n tta-staging

# 2. Check endpoints
kubectl get endpoints -n tta-staging

# 3. Check pods
kubectl get pods -n tta-staging

# 4. Test service internally
kubectl run -it --rm debug --image=busybox --restart=Never -n tta-staging -- wget -O- http://tta-api:8000/health
```

**Common Fixes:**
- Fix service selector
- Fix pod labels
- Fix health check endpoints
- Scale up pods

---

## Health Checks

### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Health Check Endpoints
```python
# /health/live - Liveness check
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

# /health/ready - Readiness check
@app.get("/health/ready")
async def readiness():
    # Check dependencies
    redis_ok = await check_redis()
    neo4j_ok = await check_neo4j()

    if redis_ok and neo4j_ok:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Not ready")
```

---

## Best Practices

### DO:
✅ Test deployments in staging first
✅ Use semantic versioning (v1.0.0)
✅ Tag images with version and commit SHA
✅ Run quality gates before deployment
✅ Monitor deployments closely
✅ Have rollback plan ready
✅ Document deployment procedures
✅ Use health checks

### DON'T:
❌ Deploy directly to production
❌ Skip quality gates
❌ Deploy without testing
❌ Use `latest` tag in production
❌ Deploy during peak hours
❌ Deploy without monitoring
❌ Deploy without rollback plan
❌ Ignore deployment errors

---

## Resources

### TTA Documentation
- Component Maturity: `docs/development/COMPONENT_MATURITY_WORKFLOW.md`
- Integrated Workflow: `docs/development/integrated-workflow-design.md`
- Quality Gates: `scripts/workflow/quality_gates.py`

### External Resources
- Docker: https://docs.docker.com/
- Kubernetes: https://kubernetes.io/docs/
- kubectl: https://kubernetes.io/docs/reference/kubectl/

---

**Note:** Always test deployments in staging before production. Monitor closely and be ready to rollback if issues arise.
