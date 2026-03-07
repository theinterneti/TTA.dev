---
title: TTA Component Maturity Workflow Instructions
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .augment/instructions/component-maturity.instructions.md
created: 2025-11-01
updated: 2025-11-01
---

# [[TTA/Components/TTA Component Maturity Workflow Instructions]]

## Overview

TTA uses a systematic component maturity workflow where individual components progress independently through three stages: **Development**, **Staging**, and **Production**. Each stage has specific quality gates and promotion criteria that must be met before advancement.

## Maturity Stages

### Development Stage

**Purpose:** Initial implementation and unit testing

**Entry Criteria:**
- Component specification created (`specs/<component>.md`)
- Basic implementation started
- Initial unit tests written

**Quality Gates:**
- ✅ All unit tests pass
- ✅ Test coverage ≥60%
- ✅ Linting clean (ruff)
- ✅ Type checking clean (pyright)
- ✅ No security issues (detect-secrets)

**Exit Criteria:**
- All quality gates pass
- Component functionality complete per spec
- Unit tests comprehensive
- Documentation complete (README.md)
- Code review approved

**Typical Duration:** 1-2 weeks

---

### Staging Stage

**Purpose:** Integration testing and validation with other components

**Entry Criteria:**
- All development stage criteria met
- Integration tests written
- Component integrated with dependencies

**Quality Gates:**
- ✅ All integration tests pass
- ✅ Test coverage ≥70%
- ✅ All development gates pass
- ✅ Integration with other components validated
- ✅ Performance acceptable (no regressions)

**Exit Criteria:**
- All quality gates pass
- Integration tests comprehensive
- Performance validated
- Multi-component workflows tested
- Staging deployment successful
- 7-day stability period (no critical bugs)

**Typical Duration:** 1-2 weeks

---

### Production Stage

**Purpose:** Production deployment and live usage

**Entry Criteria:**
- All staging stage criteria met
- End-to-end tests written
- Security review complete
- Monitoring configured
- Rollback procedure tested

**Quality Gates:**
- ✅ All end-to-end tests pass
- ✅ Test coverage ≥80%
- ✅ All staging gates pass
- ✅ 7-day uptime ≥99.5%
- ✅ Security review complete
- ✅ Monitoring configured
- ✅ Rollback procedure tested

**Exit Criteria:**
- All quality gates pass
- Production deployment successful
- Monitoring active and alerting
- Documentation complete (user-facing)
- Runbook created for operations
- Post-deployment validation complete

**Typical Duration:** Ongoing (continuous improvement)

---

## Component Promotion Process

### 1. Create Component Specification

Before starting development, create a specification:

```bash
# Use template
cp specs/templates/component.spec.template.md specs/<component>.md

# Fill in specification
# - Overview
# - Requirements (functional/non-functional)
# - API design
# - Implementation plan
# - Acceptance criteria
# - Maturity targets
```

### 2. Implement Component (Development Stage)

```bash
# Create component directory
mkdir -p src/<component>

# Implement component
# - Core functionality
# - Unit tests
# - Documentation

# Run workflow to validate
python scripts/workflow/spec_to_production.py \
    --spec specs/<component>.md \
    --component <component> \
    --target development
```

### 3. Promote to Staging

**Prerequisites:**
- All development quality gates pass
- Integration tests written
- Component integrated with dependencies

**Process:**
```bash
# Run workflow for staging
python scripts/workflow/spec_to_production.py \
    --spec specs/<component>.md \
    --component <component> \
    --target staging

# If successful, create promotion issue
gh issue create \
    --title "Promote <component> to staging" \
    --label "component:<component>,target:staging" \
    --body "Component ready for staging promotion. All quality gates passed."
```

**Validation:**
- Review workflow report: `workflow_report_<component>.json`
- Check quality gate results
- Verify integration tests pass
- Confirm no regressions

### 4. Promote to Production

**Prerequisites:**
- All staging quality gates pass
- 7-day stability period complete
- Security review complete
- Monitoring configured
- Rollback procedure tested

**Process:**
```bash
# Run workflow for production
python scripts/workflow/spec_to_production.py \
    --spec specs/<component>.md \
    --component <component> \
    --target production

# If successful, create promotion issue
gh issue create \
    --title "Promote <component> to production" \
    --label "component:<component>,target:production" \
    --body "Component ready for production promotion. All quality gates passed."
```

**Validation:**
- Review workflow report
- Check all quality gates
- Verify end-to-end tests pass
- Confirm monitoring active
- Validate rollback procedure

---

## Tracking Component Maturity

### GitHub Projects

Use GitHub Projects to track component maturity:

**Columns:**
- **Backlog:** Components planned but not started
- **Development:** Components in development stage
- **Staging:** Components in staging stage
- **Production:** Components in production stage
- **Deprecated:** Components being phased out

**Moving Cards:**
- Move component card when quality gates pass
- Add notes about promotion blockers
- Link to workflow reports

### GitHub Issues

Create issues for promotion blockers:

```markdown
Title: [Component] Staging Promotion Blocker: Low Test Coverage

Labels: component:<component>, target:staging, blocker

Description:
Component: <component>
Target Stage: staging
Current Coverage: 65%
Required Coverage: 70%

Blocker Details:
- Missing tests for error handling
- Edge cases not covered
- Integration tests incomplete

Action Items:
- [ ] Add error handling tests
- [ ] Test edge cases
- [ ] Complete integration tests
- [ ] Re-run workflow to validate
```

### Component Labels

Use labels to track component status:

- `component:<name>` - Component identifier
- `target:development` - Targeting development stage
- `target:staging` - Targeting staging stage
- `target:production` - Targeting production stage
- `blocker` - Promotion blocker
- `quality-gate-failure` - Quality gate failure

### TODO Comments

Link TODO comments to GitHub issues:

```python
# TODO(#123): Increase test coverage to 70% for staging promotion
def incomplete_function():
    pass

# TODO(#124): Add integration tests for database persistence
def database_operation():
    pass
```

---

## Quality Gate Thresholds by Stage

### Test Coverage

| Stage | Threshold | Rationale |
|-------|-----------|-----------|
| Development | ≥60% | Basic coverage for unit tests |
| Staging | ≥70% | Comprehensive coverage including integration |
| Production | ≥80% | High coverage for production reliability |

### Test Types

| Stage | Required Tests |
|-------|----------------|
| Development | Unit tests |
| Staging | Unit + Integration tests |
| Production | Unit + Integration + E2E tests |

### Code Quality

| Gate | Development | Staging | Production |
|------|-------------|---------|------------|
| Linting | ✅ Required | ✅ Required | ✅ Required |
| Type Checking | ✅ Required | ✅ Required | ✅ Required |
| Security Scan | ✅ Required | ✅ Required | ✅ Required |

---

## Component Dependencies

### Dependency Management

Track component dependencies in specifications:

```markdown
## Dependencies

### Required Components
- `orchestration` (staging) - For agent coordination
- `player_experience` (development) - For player interaction

### Optional Components
- `analytics` (production) - For usage tracking
```

### Promotion Constraints

**Rule:** A component cannot be promoted to a stage higher than its dependencies.

**Example:**
- If `component_a` depends on `component_b`
- And `component_b` is in development
- Then `component_a` cannot be promoted to staging

**Validation:**
```python
def validate_dependency_maturity(
    component: str,
    target_stage: str,
    dependencies: list[tuple[str, str]]
) -> bool:
    """Validate component dependencies meet maturity requirements."""
    stage_order = ["development", "staging", "production"]
    target_index = stage_order.index(target_stage)

    for dep_component, dep_stage in dependencies:
        dep_index = stage_order.index(dep_stage)
        if dep_index < target_index:
            return False

    return True
```

---

## Rollback Procedures

### Development Stage

**Rollback:** Revert commits
```bash
git revert <commit-hash>
git push origin main
```

### Staging Stage

**Rollback:** Revert deployment + database migration
```bash
# Revert code
git revert <commit-hash>
git push origin main

# Revert database migration (if applicable)
python scripts/db/rollback_migration.py --migration <migration-id>

# Verify rollback
python scripts/workflow/spec_to_production.py \
    --spec specs/<component>.md \
    --component <component> \
    --target staging
```

### Production Stage

**Rollback:** Full rollback procedure
```bash
# 1. Notify stakeholders
echo "Production rollback initiated for <component>"

# 2. Revert code
git revert <commit-hash>
git push origin main

# 3. Revert database migration
python scripts/db/rollback_migration.py --migration <migration-id>

# 4. Clear caches
python scripts/cache/clear_component_cache.py --component <component>

# 5. Verify rollback
python scripts/workflow/spec_to_production.py \
    --spec specs/<component>.md \
    --component <component> \
    --target production

# 6. Monitor for issues
python scripts/monitoring/check_component_health.py --component <component>

# 7. Document rollback
gh issue create \
    --title "Production rollback: <component>" \
    --label "component:<component>,rollback,incident" \
    --body "Rollback reason: <reason>\nRollback time: <time>\nImpact: <impact>"
```

---

## Monitoring and Observability

### Development Stage

**Metrics:**
- Test execution time
- Test pass rate
- Code coverage
- Linting issues

**Tools:**
- Workflow reports (`workflow_report_<component>.json`)
- Metrics dashboard (`workflow_dashboard_<component>.html`)

### Staging Stage

**Metrics:**
- Integration test pass rate
- API response times
- Error rates
- Resource usage

**Tools:**
- Application logs
- Metrics dashboard
- Integration test reports

### Production Stage

**Metrics:**
- Uptime (target: ≥99.5%)
- Response times (p50, p95, p99)
- Error rates
- User engagement
- Resource utilization

**Tools:**
- Production monitoring dashboard
- Alerting system
- Log aggregation
- Performance profiling

---

## Best Practices

### Component Design

✅ **DO:**
- Design components with clear boundaries
- Minimize dependencies between components
- Use interfaces for component communication
- Document component APIs
- Version component interfaces

❌ **DON'T:**
- Create tightly coupled components
- Skip dependency documentation
- Change interfaces without versioning
- Deploy components with unmet dependencies

### Promotion Strategy

✅ **DO:**
- Promote components incrementally
- Validate quality gates before promotion
- Test rollback procedures
- Document promotion decisions
- Track promotion blockers

❌ **DON'T:**
- Skip quality gates
- Promote without testing
- Ignore rollback procedures
- Rush promotions
- Promote components with failing dependencies

### Quality Assurance

✅ **DO:**
- Write comprehensive tests
- Test integration points
- Validate performance
- Review security implications
- Monitor component health

❌ **DON'T:**
- Skip integration tests
- Ignore performance regressions
- Deploy without security review
- Disable monitoring
- Lower quality gates to pass

---

## Component Maturity Checklist

### Development → Staging

- [ ] All unit tests pass
- [ ] Test coverage ≥60%
- [ ] Linting clean
- [ ] Type checking clean
- [ ] No security issues
- [ ] Integration tests written
- [ ] Component integrated with dependencies
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Workflow report reviewed

### Staging → Production

- [ ] All integration tests pass
- [ ] Test coverage ≥70%
- [ ] All development gates pass
- [ ] Performance validated
- [ ] 7-day stability period complete
- [ ] End-to-end tests written
- [ ] Security review complete
- [ ] Monitoring configured
- [ ] Rollback procedure tested
- [ ] User documentation complete
- [ ] Runbook created
- [ ] Workflow report reviewed

---

**Last Updated:** 2025-10-20
**Status:** Active
**Applies To:** All components in `src/` directory


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___.augment instructions component maturity.instructions]]
