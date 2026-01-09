---
title: Agentic Workflow: Component Promotion
tags: #TTA
status: Active
repo: theinterneti/TTA
path: packages/universal-agent-context/.augment/workflows/component-promotion.prompt.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Agentic Workflow: Component Promotion]]

**Purpose:** Promote a TTA component through maturity stages (dev → staging → production)

**When to Use:**
- Component ready for next maturity stage
- All quality gates pass for current stage
- Need to validate promotion criteria
- Preparing for deployment

---

## Workflow Description

This workflow guides the systematic promotion of a TTA component through maturity stages, ensuring all quality gates and criteria are met before advancement.

**Maturity Stages:**
1. **Development:** Initial implementation, ≥60% coverage
2. **Staging:** Integration testing, ≥70% coverage
3. **Production:** Production-ready, ≥80% coverage

---

## Input Requirements

### Required Inputs
- **Component Name:** Name of component to promote (e.g., `agent_orchestration`, `player_experience`)
- **Current Stage:** Current maturity stage (`development`, `staging`)
- **Target Stage:** Target maturity stage (`staging`, `production`)
- **Specification File:** Path to component specification (e.g., `specs/agent_orchestration.md`)

### Optional Inputs
- **Skip Quality Gates:** Boolean (default: false) - Only use for testing
- **Dry Run:** Boolean (default: false) - Validate without promoting

---

## Step-by-Step Process

### Step 1: Validate Current State

**Goal:** Verify component is ready for promotion

**Actions:**
1. Check component exists
2. Verify current stage matches expected
3. Confirm specification file exists
4. Review component status

**Commands:**
```bash
# Check component structure
ls -la src/{component_name}/

# Check tests
ls -la tests/{component_name}/

# Review specification
cat specs/{component_name}.md
```

**Validation Criteria:**
- [ ] Component directory exists
- [ ] Tests directory exists
- [ ] Specification file exists
- [ ] Current stage documented

---

### Step 2: Run Quality Gates

**Goal:** Ensure all quality gates pass for target stage

**Actions:**
1. Run integrated workflow
2. Check all quality gate results
3. Review any failures
4. Fix issues if needed

**Commands:**
```bash
# Run workflow for target stage
python scripts/workflow/spec_to_production.py \
    --spec specs/{component_name}.md \
    --component {component_name} \
    --target {target_stage}

# Check results
cat workflow_report_{component_name}.json | jq '.stage_results'

# View dashboard
open workflow_dashboard_{component_name}.html
```

**Quality Gate Thresholds:**

**Development → Staging:**
- [ ] Test coverage ≥70%
- [ ] All tests passing (100%)
- [ ] Linting clean (ruff)
- [ ] Type checking clean (pyright)
- [ ] No security issues (detect-secrets)
- [ ] Integration tests exist

**Staging → Production:**
- [ ] Test coverage ≥80%
- [ ] All integration tests passing
- [ ] Performance meets SLAs
- [ ] 7-day uptime ≥99.5%
- [ ] Security review complete
- [ ] Monitoring configured
- [ ] Rollback procedure tested

---

### Step 3: Review Promotion Criteria

**Goal:** Verify component meets all promotion criteria

**Development → Staging Criteria:**
- [ ] Core functionality complete
- [ ] Unit tests comprehensive
- [ ] Integration tests written
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Documentation complete
- [ ] Code review approved

**Staging → Production Criteria:**
- [ ] All staging criteria met
- [ ] E2E tests passing
- [ ] Performance validated
- [ ] Security audit complete
- [ ] Monitoring dashboards created
- [ ] Runbook documented
- [ ] Rollback tested
- [ ] Stakeholder approval

**Commands:**
```bash
# Check coverage details
uv run pytest tests/{component_name}/ \
    --cov=src/{component_name} \
    --cov-report=html

# Open coverage report
open htmlcov/index.html

# Check integration tests
uv run pytest tests/integration/ -v -m integration

# Check E2E tests (for production)
uv run pytest tests/e2e/ -v -m e2e
```

---

### Step 4: Update Tracking

**Goal:** Document promotion in GitHub

**Actions:**
1. Create promotion issue
2. Update component labels
3. Move in GitHub Projects
4. Document decision

**GitHub Issue Template:**
```markdown
## Component Promotion: {component_name}

**Current Stage:** {current_stage}
**Target Stage:** {target_stage}
**Date:** {date}

### Quality Gates
- [x] Test coverage: {coverage}%
- [x] All tests passing
- [x] Linting clean
- [x] Type checking clean
- [x] Security scan clean

### Promotion Criteria
- [x] {criterion_1}
- [x] {criterion_2}
- [ ] {criterion_3} (if any pending)

### Blockers
{list any blockers or none}

### Approval
- [ ] Tech lead approval
- [ ] QA approval
- [ ] Security approval (for production)

### Rollback Plan
{describe rollback procedure}
```

**Commands:**
```bash
# Create GitHub issue
gh issue create \
    --title "Promote {component_name} to {target_stage}" \
    --label "component:{component_name}" \
    --label "target:{target_stage}" \
    --body-file promotion_issue.md

# Update project board
gh project item-move \
    --project "TTA Component Maturity" \
    --column "{target_stage}"
```

---

### Step 5: Execute Promotion

**Goal:** Promote component to target stage

**Actions:**
1. Update component metadata
2. Update documentation
3. Deploy to target environment
4. Verify deployment
5. Update AI context

**Update Component Metadata:**
```python
# src/{component_name}/__init__.py
"""
{Component Name}

Maturity Stage: {target_stage}
Coverage: {coverage}%
Last Updated: {date}
"""

__version__ = "{version}"
__maturity__ = "{target_stage}"
```

**Update Documentation:**
```markdown
# Component: {component_name}

**Status:** {target_stage}
**Coverage:** {coverage}%
**Last Promoted:** {date}

## Quality Metrics
- Test Coverage: {coverage}%
- Integration Tests: {count}
- E2E Tests: {count}
- Performance: {metrics}
```

**Deploy to Environment:**
```bash
# For staging
kubectl apply -f k8s/staging/{component_name}.yaml

# For production
kubectl apply -f k8s/production/{component_name}.yaml

# Verify deployment
kubectl rollout status deployment/{component_name} -n tta-{target_stage}
```

**Update AI Context:**
```bash
python .augment/context/cli.py add integrated-workflow-2025-10-20 \
    "Component {component_name} promoted from {current_stage} to {target_stage}. Coverage: {coverage}%. All quality gates passed." \
    --importance 1.0
```

---

### Step 6: Post-Promotion Validation

**Goal:** Verify promotion was successful

**Actions:**
1. Run smoke tests
2. Check monitoring
3. Verify metrics
4. Monitor for issues

**Smoke Tests:**
```bash
# Run smoke tests for target environment
uv run pytest tests/smoke/ \
    --env={target_stage} \
    -v

# Check health endpoint
curl https://{target_stage}.tta.dev/health

# Check component status
curl https://{target_stage}.tta.dev/api/v1/status/{component_name}
```

**Monitoring:**
```bash
# Check metrics
open https://grafana.tta.dev/d/{component_name}

# Check logs
kubectl logs -f deployment/{component_name} -n tta-{target_stage}

# Check error rate
kubectl top pods -n tta-{target_stage}
```

**Validation Criteria:**
- [ ] Smoke tests pass
- [ ] Health checks pass
- [ ] No errors in logs
- [ ] Metrics within normal range
- [ ] Performance acceptable

---

## Validation Criteria

### Overall Success Criteria
- [ ] All quality gates pass
- [ ] All promotion criteria met
- [ ] GitHub tracking updated
- [ ] Component deployed successfully
- [ ] Post-promotion validation passes
- [ ] No rollback needed within 24 hours

### Failure Criteria (Rollback Triggers)
- Any quality gate fails
- Critical bug discovered
- Performance degradation >20%
- Error rate >1%
- Security vulnerability found

---

## Output/Deliverables

### 1. Promotion Report
```json
{
  "component": "{component_name}",
  "from_stage": "{current_stage}",
  "to_stage": "{target_stage}",
  "date": "{date}",
  "quality_gates": {
    "coverage": "{coverage}%",
    "tests_passing": true,
    "linting": "clean",
    "type_checking": "clean",
    "security": "clean"
  },
  "promotion_criteria": {
    "all_met": true,
    "details": [...]
  },
  "deployment": {
    "success": true,
    "environment": "{target_stage}",
    "version": "{version}"
  },
  "validation": {
    "smoke_tests": "passed",
    "health_checks": "passed",
    "monitoring": "normal"
  }
}
```

### 2. Updated Documentation
- Component README updated with new stage
- Specification updated with promotion date
- Runbook updated (for production)

### 3. GitHub Tracking
- Promotion issue created
- Project board updated
- Labels updated

### 4. AI Context Update
- Promotion recorded in AI context session
- Learnings documented

---

## Integration with Primitives

### AI Context Management
```python
# Track promotion decision
context_manager.add_message(
    session_id="integrated-workflow-2025-10-20",
    role="user",
    content=f"Promoting {component_name} from {current_stage} to {target_stage}",
    importance=1.0
)

# Track quality gate results
context_manager.add_message(
    session_id="integrated-workflow-2025-10-20",
    role="assistant",
    content=f"Quality gates passed: coverage={coverage}%, tests=100%",
    importance=0.9
)
```

### Error Recovery
```python
# Automatic retry for transient failures
@with_retry(RetryConfig(max_retries=3, base_delay=1.0))
async def deploy_component(component_name: str, target_stage: str):
    # Deployment with automatic retry
    pass

# Rollback on persistent failure
if deployment_failed:
    await rollback_component(component_name, current_stage)
```

### Development Observability
```python
# Track promotion metrics
@track_execution("component_promotion")
async def promote_component(component_name: str, target_stage: str):
    # Promotion tracked automatically
    pass

# View promotion metrics
# Dashboard shows: promotion time, success rate, rollback rate
```

---

## Rollback Procedure

### When to Rollback
- Quality gates fail post-deployment
- Critical bug discovered
- Performance degradation
- Security issue found

### Rollback Steps
1. Stop traffic to new version
2. Revert to previous version
3. Verify rollback successful
4. Document rollback reason
5. Create issue for fix

**Commands:**
```bash
# Rollback deployment
kubectl rollout undo deployment/{component_name} -n tta-{target_stage}

# Verify rollback
kubectl rollout status deployment/{component_name} -n tta-{target_stage}

# Update tracking
gh issue create \
    --title "Rollback {component_name} from {target_stage}" \
    --label "rollback" \
    --label "component:{component_name}"
```

---

## Resources

### TTA Documentation
- Component Maturity: `.augment/instructions/component-maturity.instructions.md`
- Quality Gates: `.augment/instructions/quality-gates.instructions.md`
- Workflow Learnings: `.augment/memory/workflow-learnings.memory.md`

### Tools
- Integrated Workflow: `scripts/workflow/spec_to_production.py`
- AI Context: `.augment/context/cli.py`
- GitHub CLI: `gh`

---

**Note:** Always validate promotion criteria before executing promotion. Rollback is easier than fixing production issues.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___universal agent context .augment workflows component promotion.prompt]]
