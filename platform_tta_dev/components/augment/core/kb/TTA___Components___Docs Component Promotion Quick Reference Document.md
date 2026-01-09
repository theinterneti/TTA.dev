---
title: Component Promotion Quick Reference
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/QUICK_REFERENCE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Component Promotion Quick Reference]]

**Last Updated**: 2025-10-13

---

## 🚀 Narrative Arc Orchestrator - Ready for Staging

### Status
🟡 **READY** (after blocker resolution)
**Coverage**: 70.3% ✅
**Promotion Issue**: #45
**Target Date**: 2025-10-15

### Quick Start

```bash
# Run automated promotion script
./scripts/promote-narrative-arc-orchestrator.sh

# Or run phases individually
./scripts/promote-narrative-arc-orchestrator.sh --phase 1  # Linting (2-3 hours)
./scripts/promote-narrative-arc-orchestrator.sh --phase 2  # Type checking (3-4 hours)
./scripts/promote-narrative-arc-orchestrator.sh --phase 3  # README (1-2 hours)
./scripts/promote-narrative-arc-orchestrator.sh --phase 4  # Validate (1 hour)
```

### Blockers (3 total, 6-9 hours)
- ❌ 150 linting issues (2-3 hours)
- ❌ 21 type checking errors (3-4 hours)
- ❌ Missing README (1-2 hours)

---

## 📋 Key Files

### Documentation
- **Promotion Issue**: [#45](https://github.com/theinterneti/TTA/issues/45)
- **Blocker Tracking**: `docs/component-promotion/NARRATIVE_ARC_ORCHESTRATOR_BLOCKERS.md`
- **Maturity Status**: `docs/component-promotion/COMPONENT_MATURITY_STATUS.md`
- **Top 3 Priorities**: `docs/component-promotion/TOP_3_PRIORITIES.md`
- **Execution Summary**: `docs/component-promotion/PROMOTION_EXECUTION_SUMMARY.md`

### Scripts
- **Promotion Script**: `scripts/promote-narrative-arc-orchestrator.sh`

### Component Files
- **Component Path**: `src/components/narrative_arc_orchestrator/`
- **Test Path**: `tests/test_narrative_arc_orchestrator_component.py`
- **MATURITY.md**: `src/components/narrative_arc_orchestrator/MATURITY.md`

---

## ⚡ Quick Commands

### Validation
```bash
# Linting
uvx ruff check src/components/narrative_arc_orchestrator/

# Type checking
uvx pyright src/components/narrative_arc_orchestrator/

# Security
uvx bandit -r src/components/narrative_arc_orchestrator/ -ll

# Tests
uv run pytest tests/test_narrative_arc_orchestrator_component.py \
    --cov=src/components/narrative_arc_orchestrator \
    --cov-report=term
```

### Fixes
```bash
# Auto-fix linting
uvx ruff check --fix src/components/narrative_arc_orchestrator/

# Create README
cp src/components/carbon/README.md src/components/narrative_arc_orchestrator/README.md
nano src/components/narrative_arc_orchestrator/README.md
```

### Deployment
```bash
# Deploy to staging
docker-compose -f docker-compose.staging-homelab.yml up -d narrative-arc-orchestrator

# Verify
docker-compose -f docker-compose.staging-homelab.yml ps
docker-compose -f docker-compose.staging-homelab.yml logs narrative-arc-orchestrator
```

---

## 📊 Component Status Summary

### Staging (3)
- ✅ Carbon (73.2%)
- ✅ Narrative Coherence (100%)
- ✅ Neo4j (0%)

### Ready for Staging (1)
- 🟡 Narrative Arc Orchestrator (70.3%)

### Development - High Priority (2)
- 🔴 Model Management (100%, code quality issues)
- 🔴 Gameplay Loop (100%, code quality issues)

### Development - Medium Priority (3)
- 🔴 LLM Component (28.2%, needs +41.8%)
- 🔴 Docker Component (20.1%, needs +49.9%)
- 🔴 Player Experience (17.3%, needs +52.7%)

### Development - Low Priority (3)
- 🔴 Agent Orchestration (2.0%, needs +68%)
- 🔴 Character Arc Manager (0%, needs +70%)
- 🔴 Therapeutic Systems (0%, needs +70%)

---

## 📅 Timeline

### This Week (2025-10-14 to 2025-10-20)
- **Mon**: Narrative Arc Orchestrator - Fix linting + type checking
- **Tue**: Narrative Arc Orchestrator - README + deploy to staging ✅
- **Wed**: Model Management - Begin linting fixes
- **Thu**: Model Management - Type checking + security
- **Fri**: Gameplay Loop - Begin linting fixes

### Next Week (2025-10-21 to 2025-10-27)
- **Mon**: Gameplay Loop - Type checking + README
- **Tue**: Gameplay Loop - Deploy to staging ✅
- **Wed-Fri**: Monitor staging, begin next wave

---

## ✅ Success Criteria

### Narrative Arc Orchestrator
- ✅ All linting issues resolved (0 errors)
- ✅ All type checking errors resolved (0 errors)
- ✅ README created
- ✅ Coverage ≥70% maintained
- ✅ All tests passing
- ✅ Deployed to staging

### Overall
- ✅ 6/12 components in staging by 2025-10-17 (50%)
- ✅ 9/12 components in staging by 2025-10-31 (75%)

---

## 🔗 Related Issues

- **#45**: Narrative Arc Orchestrator promotion
- **#42**: Component status report
- **#22**: Gameplay Loop blockers
- **#23**: Narrative Coherence blockers
- **#24**: Carbon promotion (closed)
- **#43, #44**: Neo4j promotion (closed)

---

## 📞 Quick Help

### Common Issues

**Q: Linting auto-fix doesn't resolve all issues?**
A: Some issues require manual fixes. Review remaining issues and fix manually.

**Q: Type checking errors persist after fixes?**
A: Ensure all null checks are in place. Pattern: `if metadata and 'key' in metadata:`

**Q: README template doesn't fit component?**
A: Customize sections as needed. Focus on: Overview, Features, Usage, API, Testing.

**Q: Deployment fails?**
A: Check Docker logs, verify environment variables, ensure dependencies are available.

### Getting Help

1. Review blocker tracking: `docs/component-promotion/NARRATIVE_ARC_ORCHESTRATOR_BLOCKERS.md`
2. Check promotion issue: #45
3. Review execution summary: `docs/component-promotion/PROMOTION_EXECUTION_SUMMARY.md`
4. Run validation commands to identify specific issues

---

**Next Action**: Run `./scripts/promote-narrative-arc-orchestrator.sh` to begin promotion process.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion quick reference document]]
