---
title: 🎯 TTA Component Promotion Plan
tags: #TTA
status: Active
repo: theinterneti/TTA
path: COMPONENT_PROMOTION_PLAN.md
created: 2025-10-26
updated: 2025-10-26
---
# [[TTA/Components/🎯 TTA Component Promotion Plan]]

**Date:** 2025-10-26
**Goal:** Move components from experimental → development → staging

---

## 📊 Current State Analysis

### Component Maturity Overview
- **Total Components:** 12
- **Ready for Staging:** 1 (8%) ✅
- **Needs Work:** 11 (92%) ⚠️

### Maturity Thresholds
- **Experimental:** No requirements (0% coverage)
- **Development:** 60% test coverage + basic quality
- **Staging:** 70% test coverage + all quality gates
- **Production:** 80% test coverage + full validation

---

## ✅ Already Ready for Staging (1)

### 1. Carbon Component
- **Coverage:** 73.2% ✅
- **Blockers:** 0
- **Status:** Ready to promote immediately
- **Action:** Promote to staging

---

## 🎯 Priority 1: High-Value, Low Effort (3 components)

These have high coverage but need quality fixes:

### 2. Model Management
- **Coverage:** 100% ✅
- **Blockers:** 3 (linting, type checking, security)
- **Effort:** Low (quality fixes only)
- **Value:** High (core AI infrastructure)
- **Action Plan:**
  1. Fix linting issues (665 issues - likely auto-fixable with ruff)
  2. Fix type checking errors
  3. Address security warning (Hugging Face download pinning)
- **Estimated Time:** 2-4 hours

### 3. Gameplay Loop
- **Coverage:** 100% ✅
- **Blockers:** 3 (quality gates)
- **Effort:** Low (quality fixes only)
- **Value:** High (player experience)
- **Action Plan:**
  1. Fix linting issues
  2. Fix type checking errors
  3. Security validation
- **Estimated Time:** 2-4 hours

### 4. Narrative Coherence
- **Coverage:** 100% ✅
- **Blockers:** 3 (quality gates)
- **Effort:** Low (quality fixes only)
- **Value:** High (therapeutic content)
- **Action Plan:**
  1. Fix linting issues
  2. Fix type checking errors
  3. Security validation
- **Estimated Time:** 2-4 hours

---

## 🎯 Priority 2: Medium Coverage, Fixable (3 components)

These need coverage boost + quality fixes:

### 5. Narrative Arc Orchestrator
- **Coverage:** 47.1% (need +22.9%)
- **Blockers:** 4
- **Effort:** Medium (coverage + quality)
- **Value:** Critical (core narrative engine)
- **Action Plan:**
  1. Add tests for uncovered paths (focus on main workflows)
  2. Fix linting issues
  3. Fix type checking errors
  4. Security validation
- **Estimated Time:** 6-8 hours

### 6. LLM Component
- **Coverage:** 28.2% (need +41.8%)
- **Blockers:** 2
- **Effort:** Medium
- **Value:** Critical (AI infrastructure)
- **Action Plan:**
  1. Add integration tests for LLM calls
  2. Mock external dependencies
  3. Fix quality gates
- **Estimated Time:** 6-8 hours

### 7. Neo4j Component
- **Coverage:** 27.2% (need +42.8%)
- **Blockers:** 2
- **Effort:** Medium
- **Value:** Critical (data infrastructure)
- **Action Plan:**
  1. Add integration tests (with test database)
  2. Fix linting issues (14 issues)
  3. Test connection handling, transactions
- **Estimated Time:** 6-8 hours

---

## 🎯 Priority 3: Zero Coverage (4 components)

These need test creation from scratch:

### 8. Character Arc Manager
- **Coverage:** 0% (need +70%)
- **Blockers:** 3
- **Effort:** High (new tests needed)
- **Value:** High (player engagement)
- **Status:** Currently experimental
- **Action Plan:**
  1. Write comprehensive test suite
  2. Focus on character state management
  3. Test arc progression logic
  4. Fix quality gates
- **Estimated Time:** 12-16 hours

### 9. Therapeutic Systems
- **Coverage:** 0% (need +70%)
- **Blockers:** 3
- **Effort:** High
- **Value:** Critical (therapeutic value)
- **Status:** Currently experimental
- **Action Plan:**
  1. Write test suite for safety systems
  2. Test emotional tracking
  3. Test intervention triggers
  4. Fix quality gates
- **Estimated Time:** 12-16 hours

### 10. Docker Component
- **Coverage:** 20.1% (need +49.9%)
- **Blockers:** 3 (including 148 linting issues!)
- **Effort:** High
- **Value:** Medium (infrastructure)
- **Action Plan:**
  1. Fix massive linting issues (148!)
  2. Add container lifecycle tests
  3. Fix type checking
- **Estimated Time:** 8-10 hours

### 11. Agent Orchestration
- **Coverage:** 2% (need +68%)
- **Blockers:** 3
- **Effort:** Very High
- **Value:** Critical (core orchestration)
- **Status:** Currently experimental
- **Action Plan:**
  1. Design comprehensive test strategy
  2. Write integration tests
  3. Mock agent interactions
  4. Fix quality gates
- **Estimated Time:** 16-20 hours

### 12. Player Experience (Remaining)
- **Coverage:** Unknown
- **Blockers:** Unknown
- **Effort:** Medium
- **Value:** High
- **Action Plan:** Analyze and plan

---

## 🚀 Recommended Promotion Sequence

### Phase 1: Quick Wins (Week 1)
**Goal:** Get 4 more components to staging

1. ✅ **Carbon** - Promote immediately (already ready)
2. 🔧 **Model Management** - Fix quality gates (2-4h)
3. 🔧 **Gameplay Loop** - Fix quality gates (2-4h)
4. 🔧 **Narrative Coherence** - Fix quality gates (2-4h)

**Outcome:** 5/12 components in staging (42%)

### Phase 2: Core Infrastructure (Week 2)
**Goal:** Critical infrastructure components

5. 🔧 **Narrative Arc Orchestrator** - Coverage + quality (6-8h)
6. 🔧 **LLM Component** - Coverage + quality (6-8h)
7. 🔧 **Neo4j Component** - Coverage + quality (6-8h)

**Outcome:** 8/12 components in staging (67%)

### Phase 3: Player Systems (Weeks 3-4)
**Goal:** Player-facing components

8. 🔧 **Character Arc Manager** - Full test suite (12-16h)
9. 🔧 **Therapeutic Systems** - Full test suite (12-16h)

**Outcome:** 10/12 components in staging (83%)

### Phase 4: Remaining (Week 5)
**Goal:** Complete the migration

10. 🔧 **Agent Orchestration** - Comprehensive testing (16-20h)
11. 🔧 **Docker Component** - Fix + coverage (8-10h)

**Outcome:** 12/12 components in staging (100%)

---

## 🛠️ Automation Strategy

### Use Workflow Primitives
```bash
# Promote components using automation
python scripts/workflow/spec_to_production.py \
    --component carbon \
    --target staging

# Analyze maturity
python scripts/analyze-component-maturity.py
```

### Quality Gate Automation
```bash
# Run all quality checks
Tasks: Run Task -> ✅ Quality: Run All Checks

# Or manually:
uv run ruff format .
uv run ruff check . --fix
uvx pyright src/
```

### Test Coverage Workflow
```bash
# Run tests with coverage
Tasks: Run Task -> 🧪 Test: Run with Coverage

# Or manually:
uv run pytest tests/ --cov=src --cov-report=html
```

---

## 📋 Detailed Action Items

### For Priority 1 Components (This Week)

#### Carbon (Immediate)
```bash
# Already ready - just promote
python scripts/workflow/spec_to_production.py \
    --spec specs/carbon.md \
    --component carbon \
    --target staging
```

#### Model Management (2-4 hours)
```bash
# 1. Fix linting
cd /home/thein/recovered-tta-storytelling
uv run ruff check src/components/model_management/ --fix
uv run ruff format src/components/model_management/

# 2. Fix type errors
uvx pyright src/components/model_management/

# 3. Address security
# Review: B615:huggingface_unsafe_download
# Add revision pinning to from_pretrained() calls

# 4. Verify
uv run pytest tests/test_model_management.py --cov
```

#### Gameplay Loop (2-4 hours)
```bash
# Similar process
uv run ruff check src/components/gameplay_loop/ --fix
uvx pyright src/components/gameplay_loop/
uv run pytest tests/test_gameplay_loop.py --cov
```

#### Narrative Coherence (2-4 hours)
```bash
# Similar process
uv run ruff check src/components/narrative_coherence/ --fix
uvx pyright src/components/narrative_coherence/
uv run pytest tests/test_narrative_coherence.py --cov
```

---

## 📊 Success Metrics

### Weekly Targets
- **Week 1:** 5 components in staging (42%)
- **Week 2:** 8 components in staging (67%)
- **Week 3-4:** 10 components in staging (83%)
- **Week 5:** 12 components in staging (100%)

### Quality Targets
- All components pass linting (ruff)
- All components pass type checking (pyright)
- All components pass security checks
- All components have ≥70% test coverage

### Process Targets
- Use AI workflow primitives for efficiency
- Document learnings in `.augment/memory/`
- Create reusable patterns in `.augment/workflows/`
- Maintain 100% test pass rate

---

## 🤖 AI Workflow Integration

### Use Chatmodes
```
@qa-engineer Help me write tests for the Model Management component
@backend-dev Fix the linting issues in Narrative Arc Orchestrator
@architect Review the test strategy for Agent Orchestration
```

### Use Workflows
```
Use the test-coverage-improvement workflow for Narrative Arc Orchestrator
Use the quality-gate-fix workflow for Model Management
Use the component-promotion workflow when ready
```

### Track in Memory
Document patterns in `.augment/memory/`:
- `testing-patterns.memory.md` - Effective test patterns
- `quality-improvements.memory.md` - Common fixes
- `component-promotion.memory.md` - Promotion learnings

---

## 🎯 Next Immediate Steps

### 1. Promote Carbon (5 minutes)
```bash
code TTA-AI-Workflow.code-workspace
# Run: Tasks -> ⚙️ Workflow: Component Promotion
# Select: carbon, staging
```

### 2. Fix Model Management (2-4 hours)
```bash
# Use AI assistance:
@qa-engineer Review Model Management test coverage
@backend-dev Fix linting issues in Model Management

# Run quality checks:
Tasks -> ✅ Quality: Run All Checks
```

### 3. Update Tracking (ongoing)
```bash
# Monitor progress
Tasks -> ⚙️ Workflow: Analyze Component Maturity

# View in Grafana
Tasks -> 🌐 Open: Grafana Dashboard
```

---

## 📚 Resources

- **Setup Guide:** `VS_CODE_AI_WORKFLOW_SETUP.md`
- **AI Primitives:** `.augment/` directory
- **Quality Gates:** `scripts/workflow/quality_gates.py`
- **Test Patterns:** `.augment/memory/testing-patterns.memory.md`
- **Promotion Script:** `scripts/workflow/spec_to_production.py`

---

## 💡 Pro Tips

1. **Start with quick wins** - Fix quality gates on 100% coverage components
2. **Use automation** - Let ruff auto-fix most linting issues
3. **Leverage AI** - Use chatmodes for test generation
4. **Document patterns** - Add learnings to memory bank
5. **Monitor progress** - Check Grafana dashboards regularly
6. **Test incrementally** - Run tests after each fix
7. **Commit frequently** - Small, focused commits

---

**Ready to start with Carbon promotion and Model Management fixes!** 🚀

Would you like to:
1. Promote Carbon to staging now?
2. Start fixing Model Management?
3. Review a specific component in detail?


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___component promotion plan document]]
