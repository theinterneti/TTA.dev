# Deployment Best Practices

Tags: #best-practices, #deployment, #stage-deployment, #tta-dev

## Overview

Best practices for deploying TTA.dev applications to production.

## When to Apply

- **Stage:** DEPLOYMENT
- **Priority:** HIGH
- **Audience:** DevOps, SREs, Deployment engineers

## Key Principles

### 1. Automate Everything

Use CI/CD pipelines for consistent, repeatable deployments.

**TTA.dev GitHub Actions workflow:**

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run deployment script
        run: ./scripts/deploy.sh
```

### 2. Blue-Green Deployments

Never deploy directly to production. Use blue-green pattern:

1. Deploy to "green" environment
2. Run smoke tests on green
3. Switch traffic from blue → green
4. Keep blue as rollback target

### 3. Health Checks

Every service must expose health endpoints:

```python
from tta_dev_primitives.lifecycle import StageManager, Stage

async def health_check():
    """Check service health."""
    # Verify stage is PRODUCTION
    if current_stage != Stage.PRODUCTION:
        return {"status": "unhealthy", "reason": "Not in production"}

    # Check dependencies
    # Check database connectivity
    # Verify observability pipeline

    return {"status": "healthy"}
```

### 4. Observability First

Deploy observability before code:

```python
from observability_integration import initialize_observability

# Initialize BEFORE starting service
success = initialize_observability(
    service_name="my-service",
    enable_prometheus=True
)

if not success:
    raise RuntimeError("Observability initialization failed")
```

### 5. Rollback Plan

Always have a rollback plan:

- Keep previous version running
- Document rollback steps
- Test rollback in staging first
- Set rollback time limit (e.g., 15 minutes to decide)

## Deployment Checklist

Before deploying to PRODUCTION:

- [ ] All tests pass in CI
- [ ] Staging deployment successful
- [ ] Smoke tests pass on staging
- [ ] Performance benchmarks acceptable
- [ ] Security scan complete
- [ ] Observability verified working
- [ ] Rollback procedure documented
- [ ] On-call engineer notified
- [ ] Deployment window approved
- [ ] Database migrations tested

## Anti-Patterns

### ❌ Don't Deploy on Friday

Weekend deployments = difficult rollbacks

### ❌ Don't Skip Staging

"Works on my machine" is not sufficient

### ❌ Don't Deploy Without Observability

Can't fix what you can't see

## Related Pages

- [[TTA.dev/Common Mistakes/Deployment Pitfalls]]
- [[TTA.dev/Examples/Deployment Pipeline]]
- [[TTA.dev/Stage Guides/Deployment Stage]]

## References

- Blue-Green Deployments: <https://martinfowler.com/bliki/BlueGreenDeployment.html>
- Observability integration: `platform/observability/README.md`
