---
title: Top 3 Priority Components for Staging Promotion
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/TOP_3_PRIORITIES.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Top 3 Priority Components for Staging Promotion]]

**Last Updated**: 2025-10-13 (CORRECTED)
**Planning Horizon**: Next 2 weeks (2025-10-14 to 2025-10-27)

---

## ⚠️ CORRECTION NOTICE

**Previous Version Error**: This document previously stated Narrative Arc Orchestrator had 70.3% coverage. This was **INCORRECT** based on unverified/outdated data.

**Verified Current Coverage** (per GitHub Issue #42): **42.9%**

The priorities have been **reordered** to reflect accurate data and component readiness.

---

## Executive Summary

Based on the comprehensive component maturity assessment with **CORRECTED** coverage data, the following 3 components are prioritized for staging promotion over the next 2 weeks:

| Priority | Component | Coverage | Effort | Target Date | Status |
|----------|-----------|----------|--------|-------------|--------|
| **P0** | **Carbon** | **70.6% ✅** | **Immediate** | **2025-10-14** | **🟢 READY NOW** |
| **P1** | Model Management | 100% ✅ | 2-3 days | 2025-10-17 | 🔴 Code quality issues |
| **P1** | Gameplay Loop | 100% ✅ | 2-3 days | 2025-10-17 | 🔴 Code quality issues |

**Total Estimated Effort**: 2-3 days (Carbon ready immediately)
**Expected Outcome**: 3 additional components in staging by 2025-10-17

---

## Priority 1: Carbon ⭐ **READY NOW**

### Status
🟢 **READY FOR IMMEDIATE STAGING PROMOTION**

### Why This Component First?
- ✅ **Already exceeds 70% coverage threshold (70.6%)**
- ✅ **ZERO blockers** - all quality checks passing
- ✅ No code changes required
- ✅ Immediate deployment possible
- ✅ Quick win to validate promotion workflow
- ✅ Low risk (no external dependencies)

### Current Metrics
- **Test Coverage**: 70.6% ✅ (exceeds 70% requirement by 0.6%)
- **Tests Passing**: ✅ All passing
- **Core Features**: ✅ Complete
- **Linting**: ✅ 0 issues
- **Type Checking**: ✅ Passing
- **Security**: ✅ Passing
- **Documentation**: ✅ README exists

### Blockers
**NONE** ✅ - Component is ready for immediate promotion

### Action Plan
**Timeline**: Can be promoted **TODAY** (2025-10-14)

**Steps**:
```bash
# 1. Verify current status (should all pass)
uvx ruff check src/components/carbon_component.py
uvx pyright src/components/carbon_component.py
uvx bandit -r src/components/carbon_component.py -ll
uv run pytest tests/ --cov=src/components/carbon_component.py

# 2. Create promotion issue
gh issue create \
  --title "Promote Carbon Component to Staging" \
  --label "component-promotion,P0" \
  --body "Carbon component meets all staging criteria (70.6% coverage, all checks passing, zero blockers)"

# 3. Deploy to staging
./scripts/deploy-staging.sh --component carbon

# 4. Begin 7-day observation period
# Monitor metrics, integration tests, performance
```

### Success Criteria
- ✅ All quality checks verified passing
- ✅ Promotion issue created
- ✅ Deployed to staging environment
- ✅ 7-day observation period initiated
- ✅ Monitoring dashboards configured

### Next Steps After Promotion
1. Monitor staging deployment for 7 days (until 2025-10-21)
2. Run integration tests daily
3. Collect performance metrics
4. Consider production promotion after successful observation period

---

## Priority 2: Model Management

### Status
🔴 **DEVELOPMENT** (needs code quality fixes)

### Why This Component Second?
- ✅ Already at 100% test coverage
- ✅ Only needs code quality fixes (no new tests required)
- ✅ Critical for LLM integration
- ⚠️ Has security issue that needs addressing

### Current Metrics
- **Test Coverage**: 100% ✅ (exceeds 70% requirement)
- **Tests Passing**: ✅ All passing
- **Core Features**: ✅ Complete
- **Security**: ⚠️ Medium severity issue (B615)

### Blockers (2 total)
1. ❌ **664 linting issues**
2. ❌ **Security: B615** (Hugging Face unsafe download)

### Action Plan
**Estimated Effort**: 2-3 days
**Target Deployment**: 2025-10-17

**Phase 1: Linting (1 day)**
```bash
# Scan for issues
uvx ruff check src/components/model_management/ > model_mgmt_linting.txt

# Auto-fix
uvx ruff check --fix src/components/model_management/

# Verify
uvx ruff check src/components/model_management/
```

**Phase 2: Type Checking (1 day)**
```bash
# Scan for errors
uvx pyright src/components/model_management/ > model_mgmt_types.txt

# Fix manually (add type hints, null checks)
# ...

# Verify
uvx pyright src/components/model_management/
```

**Phase 3: Security (4 hours)**
```bash
# Scan for security issues
uvx bandit -r src/components/model_management/ -ll

# Fix B615: Use safe download methods for Hugging Face
# Replace unsafe download with verified download
# ...

# Verify
uvx bandit -r src/components/model_management/ -ll
```

**Phase 4: Validation (1 hour)**
```bash
# Run all checks
uvx ruff check src/components/model_management/
uvx pyright src/components/model_management/
uvx bandit -r src/components/model_management/ -ll
uv run pytest tests/test_model_management_component.py --cov=src/components/model_management
```

### Success Criteria
- ✅ All linting issues resolved (0 errors)
- ✅ All type checking errors resolved (0 errors)
- ✅ Security issue B615 resolved
- ✅ Test coverage maintained at 100%
- ✅ All tests passing
- ✅ Deployed to staging environment

### Next Steps
1. Create promotion issue
2. Document blockers
3. Execute action plan
4. Deploy to staging
5. Monitor for 7 days

---

## Priority 3: Gameplay Loop

### Status
🔴 **DEVELOPMENT** (needs code quality fixes)

### Why This Component Third?
- ✅ Already at 100% test coverage
- ✅ Only needs code quality fixes (no new tests required)
- ✅ **Critical for player experience** (P0 priority)
- ⚠️ Has significant linting issues (1,247 issues)

### Current Metrics
- **Test Coverage**: 100% ✅ (exceeds 70% requirement)
- **Tests Passing**: ✅ All passing
- **Core Features**: ✅ Complete
- **Security**: ✅ Passing

### Blockers (3 total)
1. ❌ **1,250 linting issues** (Issue #22)
2. ❌ **Type checking errors**
3. ❌ **Missing README**

### Action Plan
**Estimated Effort**: 2-3 days
**Target Deployment**: 2025-10-17
**Blocker Issue**: #22

**Phase 1: Linting (1-2 days)**
```bash
# Scan for issues (already documented in Issue #22)
uvx ruff check src/components/gameplay_loop/ > gameplay_linting.txt

# Auto-fix (will resolve ~80% of issues)
uvx ruff check --fix src/components/gameplay_loop/

# Manual fixes for remaining issues
# ...

# Verify
uvx ruff check src/components/gameplay_loop/
```

**Phase 2: Type Checking (1 day)**
```bash
# Scan for errors
uvx pyright src/components/gameplay_loop/ > gameplay_types.txt

# Fix manually (add type hints, null checks)
# ...

# Verify
uvx pyright src/components/gameplay_loop/
```

**Phase 3: README (2 hours)**
```bash
# Copy template
cp src/components/carbon/README.md src/components/gameplay_loop/README.md

# Edit with component-specific details
nano src/components/gameplay_loop/README.md
```

**Phase 4: Validation (1 hour)**
```bash
# Run all checks
uvx ruff check src/components/gameplay_loop/
uvx pyright src/components/gameplay_loop/
uvx bandit -r src/components/gameplay_loop/ -ll
uv run pytest tests/test_gameplay_loop_component.py --cov=src/components/gameplay_loop
```

### Success Criteria
- ✅ All 1,250 linting issues resolved (0 errors)
- ✅ All type checking errors resolved (0 errors)
- ✅ README created with all required sections
- ✅ Test coverage maintained at 100%
- ✅ All tests passing
- ✅ Deployed to staging environment

### Next Steps
1. Update Issue #22 with action plan
2. Execute action plan
3. Deploy to staging
4. Monitor for 7 days
5. Consider production promotion (critical for player experience)

---

## Timeline Summary

### Week 1: 2025-10-14 to 2025-10-20

**Monday 2025-10-14**
- ✅ Carbon: Verify readiness, create promotion issue, deploy to staging
- ✅ Begin 7-day observation period for Carbon

**Tuesday 2025-10-15**
- ✅ Monitor Carbon staging deployment
- ✅ Model Management: Begin linting fixes (664 issues)

**Wednesday 2025-10-16**
- ✅ Model Management: Complete linting, address security issue (B615)
- ✅ Gameplay Loop: Begin linting fixes (1,250 issues)

**Thursday 2025-10-17**
- ✅ Model Management: Validate and deploy to staging
- ✅ Gameplay Loop: Continue linting fixes

**Friday 2025-10-18**
- ✅ Gameplay Loop: Complete linting, begin type checking
- ✅ Monitor Carbon and Model Management in staging

### Week 2: 2025-10-21 to 2025-10-27

**Monday 2025-10-21**
- ✅ Gameplay Loop: Complete type checking, create README
- ✅ Carbon: Complete 7-day observation (ready for production consideration)

**Tuesday 2025-10-22**
- ✅ Gameplay Loop: Validate and deploy to staging
- ✅ Monitor all 3 components in staging

**Wednesday-Friday 2025-10-23 to 2025-10-25**
- ✅ Continue monitoring staging deployments
- ✅ Begin work on Narrative Arc Orchestrator test coverage improvement
- ✅ Begin work on next priority components (LLM, Docker, Player Experience)

---

## Success Metrics

### By 2025-10-17 (End of Week 1)
- ✅ 3 components promoted to staging
- ✅ 6 total components in staging (50% of total)
- ✅ Promotion workflow validated with 3 successful promotions

### By 2025-10-27 (End of Week 2)
- ✅ All 3 components stable in staging
- ✅ Integration tests passing
- ✅ Performance metrics collected
- ✅ Ready to begin production promotions

---

## Risk Mitigation

### Risk 1: Linting Fixes Take Longer Than Expected
**Mitigation**: Use auto-fix for 80% of issues, focus manual effort on critical issues only

### Risk 2: Type Checking Reveals Architectural Issues
**Mitigation**: Document issues, create follow-up tasks, don't block promotion for non-critical issues

### Risk 3: Security Issue (B615) Requires Significant Refactoring
**Mitigation**: Implement safe download wrapper, defer full refactoring to post-staging

### Risk 4: Staging Deployment Failures
**Mitigation**: Test deployment in dev environment first, have rollback plan ready

---

## Related Documentation

- **Component Maturity Status**: `docs/component-promotion/COMPONENT_MATURITY_STATUS.md`
- **Narrative Arc Orchestrator Blockers**: `docs/component-promotion/NARRATIVE_ARC_ORCHESTRATOR_BLOCKERS.md`
- **Promotion Script**: `scripts/promote-narrative-arc-orchestrator.sh`
- **Promotion Issues**: #45 (Narrative Arc Orchestrator), #22 (Gameplay Loop)
- **Status Report**: Issue #42

---

## Appendix: Narrative Arc Orchestrator Status

**Previous Priority**: P0 (INCORRECT - based on false 70.3% coverage data)
**Current Priority**: P2 (CORRECTED - based on verified 42.9% coverage)

### Why Deprioritized?

**Actual Coverage**: 42.9% (verified via GitHub Issue #42)
**Coverage Gap**: 27.1% (need to reach 70% threshold)
**Estimated Effort**: 1-2 weeks of focused test development

### Test Coverage Improvement Plan

**Priority Areas**:
1. **scale_manager.py** (currently 53.39%)
   - Add tests for event creation logic (lines 119-133)
   - Add tests for scale window calculations (lines 184-202)
   - Add tests for conflict resolution (lines 207-224)
   - Add tests for async initialization (lines 245-252)
   - **Estimated gain**: +10-12%

2. **impact_analysis.py** (currently 53.44%)
   - Add tests for null checks and edge cases
   - Add tests for error handling paths
   - **Estimated gain**: +8-10%

3. **causal_graph.py** (currently 42.86%)
   - Add tests for graph validation (lines 25-29)
   - Add tests for cycle detection (line 16)
   - **Estimated gain**: +5-7%

**Target Completion**: 2025-10-27 (not 2025-10-15 as previously stated)

### Quality Checks (Already Passing)
- ✅ Linting: 0 issues
- ✅ Type checking: Passing
- ✅ Security: Passing
- ✅ Documentation: README exists

---

**Last Updated**: 2025-10-13 (CORRECTED)
**Next Review**: 2025-10-14
**Maintained By**: @theinterneti


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion top 3 priorities document]]
