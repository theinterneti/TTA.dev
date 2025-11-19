# PR #26 Extraction Plan

**Date:** November 17, 2025
**PR:** #26 (feature/keploy-framework)
**Total Size:** 29,622 additions across 135 files
**Analysis Result:** 89% genuinely new content (3,192 lines)

---

## Executive Summary

PR #26 contains **comprehensive infrastructure** added on October 29, 2025. Analysis shows:

- ✅ **89% new content** (3,192 lines) - worth extracting
- ⚠️ **5 modified files** (380 lines) - need manual review
- ❌ **1 duplicate file** (9 lines) - already implemented

**Recommendation:** Extract valuable pieces into **7 focused PRs** and close original PR #26.

---

## Analysis Results

### Overall Status
- ✅ Already Implemented: 1 file (9 lines, 0.3%)
- 🆕 New Files: 27 files (3,192 lines, 89%)
- ⚠️ Modified Files: 5 files (380 lines, 11%)

### By Category

| Category | New Files | Total Lines | Value |
|----------|-----------|-------------|-------|
| **Observability** | 11 files | 1,498 lines | ⭐⭐⭐ High |
| **Memory** | 5 files | 749 lines | ⭐⭐⭐ High |
| **Docs** | 4 files | 733 lines | ⭐⭐ Medium |
| **Infrastructure** | 2 files | 131 lines | ⭐⭐ Medium |
| **Config** | 1 file | 81 lines | ⭐ Low |
| **Testing** | 1 file | 0 lines* | ⭐ Low |
| **Other** | 3 files | 0 lines* | ⭐ Low |

*Note: Files showing 0 additions likely contain code but not shown in truncated API response

---

## Extraction Strategy

### Phase 1: High-Value Infrastructure (Do First)

#### PR #1: Observability Platform (1,498 lines)
**Files:**
```
packages/tta-dev-primitives/dashboards/alertmanager/
  ├── README.md (355 lines)
  ├── alertmanager.yaml (223 lines)
  └── tta-alerts.yaml (226 lines)

packages/tta-dev-primitives/dashboards/grafana/
  ├── README.md (281 lines)
  ├── cost-tracking.json (413 lines)
  ├── slo-tracking.json
  └── workflow-overview.json

packages/tta-dev-primitives/src/tta_dev_primitives/observability/
  ├── enhanced_metrics.py
  └── instrumented_primitive.py

packages/tta-dev-primitives/tests/observability/
  ├── test_enhanced_metrics.py
  └── test_instrumented_primitives.py
```

**Value Proposition:**
- Complete Grafana dashboards for cost tracking, SLO monitoring
- 20+ AlertManager rules for primitive failures
- Enhanced metrics collection
- Production-ready observability

**Effort:** 2-3 hours (straightforward extraction)

---

#### PR #2: Memory Management System (749 lines)
**Files:**
```
.universal-instructions/memory-management/
  ├── README.md (308 lines)
  ├── context-engineering.md (441 lines)
  ├── session-management.md
  ├── memory-hierarchy.md
  └── paf-guidelines.md

packages/tta-dev-primitives/src/tta_dev_primitives/
  ├── memory_workflow.py
  ├── paf_memory.py
  └── session_group.py
```

**Value Proposition:**
- 4-layer memory architecture documentation
- Working primitives for conversational memory
- PAF (Permanent Architectural Facts) integration
- Session group management

**Effort:** 3-4 hours (complex system, needs validation)

---

### Phase 2: Supporting Infrastructure

#### PR #3: UV Workflow Foundation (733 lines)
**Files:**
```
packages/python-pathway/instructions/
  ├── UV_WORKFLOW_FOUNDATION.md (590 lines)
  ├── quality.md (34 lines)
  ├── testing.md (68 lines)
  └── tooling.md (41 lines)
```

**Value Proposition:**
- Complete `uv` integration guide
- Quality standards for Python pathway
- Testing patterns with pytest
- Tooling best practices

**Effort:** 1-2 hours (documentation only)

---

#### PR #4: Keploy API Testing (131 lines)
**Files:**
```
.github/workflows/api-testing.yml (131 lines)
.github/benchmarks/baseline.json (81 lines)
```

**Value Proposition:**
- Automated API testing workflow
- Performance baseline tracking
- Keploy framework integration

**Effort:** 2 hours (workflow + validation)

---

### Phase 3: Manual Review Required

#### PR #5: Workflow Enhancements (380 lines) ⚠️
**Modified Files (need diff comparison):**
```
.augment/rules/package-source.instructions.md (+51 lines)
.augment/rules/scripts.instructions.md (+31 lines)
.augment/rules/tests.instructions.md (+73 lines)
.github/workflows/ci.yml (+97 lines)
.github/workflows/quality-check.yml (+128 lines)
```

**Action Required:**
1. Fetch raw file contents from PR #26 branch
2. Compare against current main
3. Extract only the valuable changes
4. Discard obsolete/conflicting changes

**Effort:** 3-4 hours (requires careful review)

---

### Phase 4: Low-Priority Additions

#### PR #6: Additional Observability Tools
**Files with 0 additions shown (need content fetch):**
```
packages/tta-dev-primitives/src/tta_dev_primitives/
  ├── workflow_hub.py
  ├── observability/context_propagation.py
  └── observability/enhanced_collector.py

packages/tta-dev-primitives/tests/observability/
  └── test_context_propagation.py
```

**Action:** Fetch actual file contents to assess value

---

## Files to DISCARD

### Already Implemented
```
.github/prometheus/prometheus.yml (9 lines)
  Reason: Identical file already exists in main
```

---

## Execution Plan

### Step 1: Validate Assumption (30 minutes)
```bash
# Fetch actual file contents for "0 additions" files
# Use GitHub API to get raw content

# Files to check:
- packages/tta-dev-primitives/dashboards/grafana/slo-tracking.json
- packages/tta-dev-primitives/dashboards/grafana/workflow-overview.json
- packages/tta-dev-primitives/src/tta_dev_primitives/memory_workflow.py
- packages/tta-dev-primitives/src/tta_dev_primitives/paf_memory.py
- packages/tta-dev-primitives/src/tta_dev_primitives/session_group.py
- packages/tta-dev-primitives/src/tta_dev_primitives/workflow_hub.py
- packages/tta-dev-primitives/src/tta_dev_primitives/observability/enhanced_metrics.py
- packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py
- packages/tta-dev-primitives/src/tta_dev_primitives/observability/prometheus_exporter.py
- packages/tta-dev-primitives/src/tta_dev_primitives/observability/context_propagation.py
- packages/tta-dev-primitives/src/tta_dev_primitives/observability/enhanced_collector.py
- All test files
```

### Step 2: Create Focused PRs (1-2 weeks)

**Priority Order:**
1. **PR #1: Observability Platform** (Day 1-2)
   - Extract dashboards + alerts
   - Validate with docker-compose
   - Test with tta-observability-integration

2. **PR #2: Memory Management** (Day 3-4)
   - Extract documentation first
   - Add primitives
   - Write integration tests

3. **PR #3: UV Workflow Foundation** (Day 5)
   - Extract docs
   - Update existing python-pathway

4. **PR #4: Keploy Testing** (Day 6-7)
   - Extract workflow
   - Validate in CI

5. **PR #5: Workflow Enhancements** (Day 8-9) ⚠️
   - Manual diff review
   - Cherry-pick valuable changes

6. **PR #6: Additional Observability** (Day 10)
   - After content validation
   - If valuable

### Step 3: Close Original PR #26 (Day 11)

**Close with comment:**
```markdown
## PR #26 Closure Plan

This PR contained valuable infrastructure but was too broad (135 files).

### What We Extracted
✅ Observability Platform → PR #XXX
✅ Memory Management → PR #XXX
✅ UV Workflow Foundation → PR #XXX
✅ Keploy Testing → PR #XXX
✅ Workflow Enhancements → PR #XXX

### What We Discarded
❌ .github/prometheus/prometheus.yml - already implemented
❌ Obsolete workflow changes - superseded by current main

### Total Impact
- **New Features:** 5 focused PRs
- **Lines Added:** ~3,500 (vs 29,622 original)
- **Maintainability:** ⭐⭐⭐⭐⭐ (small, focused PRs)

Closing this PR in favor of extracted, focused PRs above.
```

---

## Next Actions

### Immediate (Today)
1. ✅ Run analysis script (`python3 scripts/analyze_pr_26.py`) - **DONE**
2. ⬜ Fetch file contents for "0 additions" files
3. ⬜ Validate actual content exists
4. ⬜ Update this plan with findings

### This Week
1. ⬜ Create PR #1 (Observability Platform)
2. ⬜ Create PR #2 (Memory Management)
3. ⬜ Create PR #3 (UV Workflow)

### Next Week
1. ⬜ Create PR #4 (Keploy Testing)
2. ⬜ Manual review PR #5 (Workflow Enhancements)
3. ⬜ Close original PR #26

---

## Risk Assessment

### High Risk
- ⚠️ **Modified workflow files** - May conflict with current CI
  - Mitigation: Manual diff, cherry-pick changes
  
- ⚠️ **Memory primitives** - Complex integration
  - Mitigation: Comprehensive integration tests

### Medium Risk
- ⚠️ **Grafana dashboards** - May need schema updates
  - Mitigation: Test with docker-compose before merging

### Low Risk
- ✅ **Documentation** - Safe to extract
- ✅ **Test files** - Easy to validate

---

## Success Criteria

### For Each Extracted PR
- [ ] All files exist and compile
- [ ] Tests pass (100% coverage for new code)
- [ ] Documentation complete
- [ ] No conflicts with current main
- [ ] CI/CD passes
- [ ] Manual QA complete

### For Overall Extraction
- [ ] All valuable content extracted
- [ ] Obsolete content discarded
- [ ] Original PR #26 closed with explanation
- [ ] Team understands new features
- [ ] Documentation updated

---

## Estimated Timeline

- **Analysis & Planning:** 1 day (Today)
- **Extraction Work:** 10 days (2 weeks)
- **Review & Merge:** 3 days (distributed)
- **Total:** ~2.5 weeks

---

## Notes

### Why 7 PRs Instead of 1?
1. **Easier Review** - Reviewers can understand focused changes
2. **Faster Merge** - Small PRs merge quickly
3. **Better Testing** - Isolated features easier to validate
4. **Rollback Safety** - Revert individual features if needed
5. **Clear History** - Git history shows what each feature does

### What About PR #60?
After completing PR #26 extraction, apply same strategy:
1. Analyze file overlap with current main
2. Extract valuable pieces (prompts, workflows, configs)
3. Discard obsolete content
4. Create focused PRs

---

**Status:** Ready for execution
**Last Updated:** November 17, 2025
**Next Review:** After file content validation
