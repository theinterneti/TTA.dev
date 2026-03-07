---
title: TTA Component Promotion Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/COMPONENT_PROMOTION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/TTA Component Promotion Guide]]

## Overview

This guide provides step-by-step instructions for promoting TTA components through maturity stages. Follow this guide when you're ready to promote a component from Development → Staging or Staging → Production.

---

## Quick Reference

| Promotion | Min Duration | Test Coverage | Key Requirements |
|-----------|--------------|---------------|------------------|
| Dev → Staging | N/A | ≥70% unit tests | Core features, API docs, code quality |
| Staging → Production | 7 days | ≥80% integration tests | Performance, security, monitoring, rollback |

---

## Pre-Promotion Checklist

Before starting the promotion process, verify:

- [ ] Component MATURITY.md file is up-to-date
- [ ] All promotion criteria are met
- [ ] All blocker issues are resolved
- [ ] Documentation is complete and accurate
- [ ] All tests pass locally
- [ ] Dependencies are at equal or higher maturity stage

---

## Development → Staging Promotion

### Prerequisites

1. **Core Features Complete**: 80%+ of planned functionality implemented
2. **Unit Tests**: ≥70% coverage, all passing
3. **API Documentation**: Complete API documentation
4. **Code Quality**: Passes ruff, pyright, bandit
5. **Component README**: Usage examples and setup instructions
6. **Dependencies**: All dependencies identified and stable
7. **Integration**: Works with dependent components in dev environment

### Step-by-Step Process

#### Step 1: Verify Criteria

```bash
# Run tests
uvx pytest tests/test_<component>.py --cov=src/components/<component> --cov-report=term

# Check code quality
uvx ruff check src/components/<component>/
uvx pyright src/components/<component>/

# Security scan
uvx bandit -r src/components/<component>/
```

**Expected Results**:
- ✅ Test coverage ≥70%
- ✅ All tests passing
- ✅ No linting errors
- ✅ No type errors
- ✅ No critical security issues

#### Step 2: Update MATURITY.md

Update `src/components/<component>/MATURITY.md`:

```markdown
**Current Stage**: Staging (promoted from Development on YYYY-MM-DD)
**Last Updated**: YYYY-MM-DD

### Development → Staging
- [x] Core features complete (80%+)
- [x] Unit tests passing (≥70% coverage)
- [x] API documented
- [x] Code quality checks passing
- [x] Component README complete
- [x] Dependencies stable
- [x] Integration validated

**Status**: 7/7 criteria met ✅
```

#### Step 3: Create Promotion Request

1. Go to https://github.com/theinterneti/TTA/issues/new/choose
2. Select **"🚀 Component Promotion Request"**
3. Fill out the form:

**Component Name**: Select your component

**Current Stage**: Development

**Target Stage**: Staging

**Functional Group**: Select appropriate group

**Promotion Justification**:
```markdown
Component is ready for staging promotion:
- All core features implemented and tested
- Unit test coverage: XX%
- API documentation complete
- Code quality checks passing
- Successfully integrates with [list dependencies]
```

**Development → Staging Criteria**: Check all boxes

**Test Results**:
```markdown
**Unit Tests**: XX% coverage, YY/YY passing
**Test Command**: `uvx pytest tests/test_<component>.py --cov`
**Test Report**: [link to CI run or local results]
```

**Documentation Links**:
```markdown
- Component README: src/components/<component>/README.md
- API Documentation: [link if applicable]
```

**Dependencies**:
```markdown
- Neo4j (Production)
- Redis (Production)
```

**Known Blockers**: None (or list any)

4. Add labels:
   - `component:<component-name>`
   - `target:staging`
   - `promotion:requested`

5. Submit the issue

#### Step 4: Automated Validation

Wait for CI/CD to run automated checks. The system will:
- Run component tests
- Check code quality
- Perform security scan
- Validate coverage
- Post results as comment

Review the results and address any issues.

#### Step 5: Deploy to Staging

```bash
# Update environment configuration
cp .env.staging.example .env.staging
# Edit .env.staging with staging-specific values

# Deploy to staging environment
docker-compose -f docker-compose.staging-homelab.yml up -d <component>

# Verify deployment
docker-compose -f docker-compose.staging-homelab.yml ps
docker-compose -f docker-compose.staging-homelab.yml logs <component>
```

#### Step 6: Verify in Staging

```bash
# Run integration tests in staging
uvx pytest tests/integration/test_<component>_integration.py

# Check health endpoint (if applicable)
curl http://localhost:<staging-port>/health

# Monitor logs
docker-compose -f docker-compose.staging-homelab.yml logs -f <component>
```

#### Step 7: Update Tracking

1. Update GitHub Project:
   - Move component card to "🧪 Staging" column
   - Update "Current Stage" field to "Staging"
   - Update "Last Updated" field

2. Update promotion issue:
   - Add label `promotion:completed`
   - Close the issue

3. Create next milestone (optional):
   - Create milestone: "<Component> → Production Promotion"
   - Set target date (minimum 7 days from now)

---

## Staging → Production Promotion

### Prerequisites

1. **Integration Tests**: ≥80% coverage, all passing
2. **Performance**: Meets defined SLAs
3. **Security**: No critical vulnerabilities
4. **Reliability**: 7-day uptime ≥99.5% in staging
5. **Documentation**: Complete user docs, API reference, troubleshooting guide
6. **Monitoring**: Health checks, metrics, alerts configured
7. **Rollback**: Rollback procedure documented and tested
8. **Load Testing**: Handles expected production load

### Step-by-Step Process

#### Step 1: Verify Staging Performance

```bash
# Monitor staging for 7 days
# Check uptime
docker-compose -f docker-compose.staging-homelab.yml ps <component>

# Check logs for errors
docker-compose -f docker-compose.staging-homelab.yml logs <component> | grep -i error

# Review metrics (if Grafana is set up)
# Navigate to Grafana dashboard and review component metrics
```

**Required Metrics**:
- ✅ Uptime ≥99.5% over 7 days
- ✅ No critical errors
- ✅ Performance within SLA targets

#### Step 2: Run Integration Tests

```bash
# Run full integration test suite
uvx pytest tests/integration/ --cov=src/components/<component> --cov-report=term

# Run E2E tests (if applicable)
uvx pytest tests/e2e/ -k <component>
```

**Expected Results**:
- ✅ Integration test coverage ≥80%
- ✅ All integration tests passing
- ✅ E2E tests passing (if applicable)

#### Step 3: Performance Validation

```bash
# Run load tests (if applicable)
# Example using locust or similar tool
locust -f tests/load/test_<component>_load.py --headless -u 100 -r 10 --run-time 5m
```

**Validate**:
- ✅ Response times within SLA
- ✅ Throughput meets requirements
- ✅ Resource usage acceptable
- ✅ No performance degradation under load

#### Step 4: Security Review

```bash
# Run security scans
uvx bandit -r src/components/<component>/
uvx safety check

# Check for dependency vulnerabilities
uv pip list --outdated
```

**Validate**:
- ✅ No critical vulnerabilities
- ✅ All dependencies up-to-date
- ✅ Security best practices followed

#### Step 5: Document Rollback Procedure

Create `docs/operations/<component>_ROLLBACK.md`:

```markdown
# <Component> Rollback Procedure

## Quick Rollback

1. Revert to previous Docker image:
   ```bash
   docker-compose down <component>
   docker-compose up -d <component>:<previous-tag>
   ```

2. Verify health:
   ```bash
   curl http://localhost:<port>/health
   ```

## Full Rollback

1. Stop component
2. Restore database backup (if schema changed)
3. Revert environment variables
4. Start component with previous version
5. Verify all health checks pass
6. Monitor for 1 hour

## Rollback Validation

- [ ] Component starts successfully
- [ ] Health checks pass
- [ ] Integration tests pass
- [ ] No errors in logs
- [ ] Performance metrics normal
```

#### Step 6: Test Rollback Procedure

```bash
# In staging environment, test the rollback
# 1. Note current version
# 2. Deploy previous version
# 3. Verify rollback works
# 4. Redeploy current version
```

#### Step 7: Create Promotion Request

1. Go to https://github.com/theinterneti/TTA/issues/new/choose
2. Select **"🚀 Component Promotion Request"**
3. Fill out the form (similar to Dev → Staging, but with production criteria)

**Staging → Production Criteria**: Check all boxes

**Performance Metrics**:
```markdown
**Response Time**: p50: XXms, p95: XXms, p99: XXms
**Throughput**: XX req/s
**Resource Usage**: CPU: XX%, Memory: XXMB
**Uptime**: 99.X% over 7 days

Performance report: [link to Grafana dashboard or test results]
```

**Security Review**:
```markdown
**Security Scan**: No critical vulnerabilities
**Dependency Audit**: All dependencies up-to-date
**Secrets Management**: All secrets properly managed via environment variables

Security report: [link to scan results]
```

**Rollback Plan**:
```markdown
See docs/operations/<component>_ROLLBACK.md

Rollback tested in staging: [date]
Rollback time estimate: X minutes
```

4. Add labels:
   - `component:<component-name>`
   - `target:production`
   - `promotion:requested`

5. Submit the issue

#### Step 8: Deploy to Production

```bash
# Backup current state
./scripts/backup-production.sh

# Update production environment
cp .env.production.example .env.production
# Edit .env.production with production values

# Deploy to production
docker-compose -f docker-compose.yml up -d <component>

# Verify deployment
docker-compose ps
docker-compose logs <component>
```

#### Step 9: Post-Deployment Validation

```bash
# Run smoke tests
uvx pytest tests/smoke/test_<component>_smoke.py

# Check health endpoint
curl https://production-domain.com/health

# Monitor metrics
# Check Grafana dashboard for anomalies

# Monitor logs
docker-compose logs -f <component> | grep -i error
```

**Monitor for 24 hours**:
- ✅ No critical errors
- ✅ Performance within SLA
- ✅ No user-reported issues

#### Step 10: Update Tracking

1. Update MATURITY.md:
```markdown
**Current Stage**: Production (promoted from Staging on YYYY-MM-DD)

## Promotion History
- 2025-XX-XX: Promoted to Development
- 2025-XX-XX: Promoted to Staging (Issue #XXX)
- 2025-XX-XX: Promoted to Production (Issue #YYY)
```

2. Update GitHub Project:
   - Move to "🚀 Production" column
   - Update "Current Stage" to "Production"

3. Close promotion issue:
   - Add label `promotion:completed`
   - Close issue

---

## Handling Promotion Blockers

If you encounter blockers during promotion:

### Step 1: Create Blocker Issue

1. Go to https://github.com/theinterneti/TTA/issues/new/choose
2. Select **"🚧 Component Promotion Blocker"**
3. Fill out the form with blocker details
4. Link to promotion request issue

### Step 2: Resolve Blocker

1. Work on resolving the blocker
2. Update blocker issue with progress
3. Close blocker issue when resolved

### Step 3: Update Promotion Request

1. Update promotion request with blocker resolution
2. Re-run validation
3. Proceed with promotion

---

## Rollback After Promotion

If issues are discovered after promotion:

### Immediate Rollback

```bash
# Follow documented rollback procedure
# See docs/operations/<component>_ROLLBACK.md

# Verify rollback successful
# Monitor for stability
```

### Post-Rollback

1. Create incident report
2. Identify root cause
3. Fix issues
4. Re-test in lower environment
5. Create new promotion request when ready

---

## Tips and Best Practices

1. **Promote During Low-Traffic Periods**: Schedule production promotions during maintenance windows
2. **Monitor Closely**: Watch metrics closely for 24-48 hours after promotion
3. **Have Rollback Ready**: Always have rollback procedure tested and ready
4. **Communicate**: Notify team of promotion schedule
5. **Document Everything**: Keep detailed notes of promotion process
6. **Learn from Issues**: Update this guide with lessons learned

---

## Related Documentation

- [[TTA/Components/COMPONENT_MATURITY_WORKFLOW|Component Maturity Workflow]]
- [[TTA/Components/COMPONENT_LABELS_GUIDE|Component Labels Guide]]
- [[TTA/Components/ENVIRONMENT_SETUP_GUIDE|Environment Setup Guide]]


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs development component promotion guide document]]
