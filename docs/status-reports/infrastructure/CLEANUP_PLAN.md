# Repository Cleanup Plan - Post TasksPrimitive Sprint

**Date:** November 4, 2025
**Sprint:** TasksPrimitive Days 8-9 + Real-World Validation
**Status:** Analysis Complete

---

## 📊 Repository Assessment

### What Changed This Sprint

**Major Additions:**
- ✅ TasksPrimitive implementation (1,052 lines)
- ✅ Comprehensive test suite (1,070 lines, 36 tests)
- ✅ 5 working examples (221 lines)
- ✅ Real-world validation experiments (3 scenarios, 51 tasks)
- ✅ Documentation (SPECKIT_DAY8_9_COMPLETE.md, RESULTS.md, EXECUTIVE_SUMMARY.md)
- ✅ Extensive Logseq knowledge base updates

**Current Git Status:**
- Modified files: 6
- Deleted files: 5 (old example files)
- New files: ~150+ (experiments, docs, Logseq pages, SpecKit implementation)

---

## 🎯 Cleanup Categories

### 1. Example Output Directories (KEEP AS ARTIFACTS)

**Location:** `examples/{features,plan_output,tasks_output}/`

**Status:** Generated during example runs
- `examples/features/` - 40KB (auth, notifications, payments specs)
- `examples/plan_output/` - 36KB (generated plans from examples)
- `examples/tasks_output/` - 88KB (5 example task outputs)

**Recommendation:** ✅ **KEEP** - These are valuable reference artifacts
- Shows example outputs from SpecKit workflow
- Useful for testing and validation
- Should be in `.gitignore` but preserved locally

**Action:**
```bash
# Add to .gitignore to exclude from commits
echo "examples/features/" >> .gitignore
echo "examples/plan_output/" >> .gitignore
echo "examples/tasks_output/" >> .gitignore
```

---

### 2. Experiment Outputs (KEEP, ORGANIZE)

**Location:** `experiments/tasks-real-world/`

**Contents:**
```
experiments/tasks-real-world/
├── README.md                    # Framework doc
├── RESULTS.md                   # Validation results
├── EXECUTIVE_SUMMARY.md         # Quick reference
├── run_experiments.py           # Reproducible script
├── exp1-monitoring-dashboard/   # 19 tasks
├── exp2-observability-refactor/ # 12 tasks
└── exp3-data-primitives/        # 20 tasks
```

**Recommendation:** ✅ **KEEP AND COMMIT** - Production validation proof
- Demonstrates real-world value (51 tasks, 87% time savings)
- Should be committed as evidence
- Shows TasksPrimitive production readiness

**Action:** Commit all experiment files

---

### 3. Documentation Files (ORGANIZE)

**Current Location:** Multiple places

**Files to Organize:**

**SpecKit Documentation:**
- `docs/SPECKIT_DAY8_9_COMPLETE.md` ✅ (main completion doc)
- `docs/planning/SPECKIT_DAY1_COMPLETE.md`
- `docs/planning/SPECKIT_DAY3_COMPLETE.md`
- `docs/planning/SPECKIT_DAY5_COMPLETE.md`
- `docs/planning/SPECKIT_DAY6_COMPLETE.md`
- `docs/planning/SPECKIT_DAY6_7_PLAN.md`
- `docs/planning/SPECKIT_DAY8_9_PLAN.md`
- `docs/planning/SPECKIT_IMPLEMENTATION_PLAN.md`

**Recommendation:** ✅ **ORGANIZE INTO ARCHIVE**
- These are historical planning docs (Days 1-7)
- Day 8-9 completion doc should stay in `docs/`
- Planning docs should move to `archive/speckit-planning/`

**Action:**
```bash
mkdir -p archive/speckit-planning
mv docs/planning/SPECKIT_*.md archive/speckit-planning/
# Keep SPECKIT_DAY8_9_COMPLETE.md in docs/ as the main reference
```

---

### 4. Session Reports (ORGANIZE)

**Location:** `local/session-reports/`

**Files:**
- `2025-01-16-docker-expert-complete.md`
- `2025-11-04-docker-expert-complete.md`

**Recommendation:** ✅ **KEEP IN local/**
- These are session-specific reports
- Good for historical reference
- Already in `local/` which is appropriate

**Action:** No change needed

---

### 5. Atomic DevOps Documentation (VERIFY RELEVANCE)

**Files:**
- `docs/ATOMIC_DEVOPS_PROGRESS.md`
- `docs/ATOMIC_DEVOPS_SUMMARY.md`
- `docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`
- `docs/guides/ATOMIC_DEVOPS_QUICKSTART.md`

**Status:** From earlier work, may not be part of current TasksPrimitive sprint

**Recommendation:** ⚠️ **VERIFY THEN COMMIT OR ARCHIVE**
- If relevant to current TTA.dev: Commit
- If experimental/superseded: Move to `archive/atomic-devops/`

**Action:** User decision needed

---

### 6. Cache Files (__pycache__)

**Location:** Throughout repo

**Status:** Standard Python cache files

**Recommendation:** ✅ **ALREADY IN .gitignore**
- No action needed
- Can clean locally if desired: `find . -type d -name __pycache__ -exec rm -rf {} +`

---

### 7. Logseq Pages (KEEP, VERIFY GITIGNORE)

**Location:** `logseq/`

**Status:**
- ~100+ new Logseq pages
- Comprehensive knowledge base
- TODO system implementation

**Recommendation:** ⚠️ **DECISION NEEDED**

**Options:**

A. **Commit to Git** (Share knowledge base with team)
   - Pros: Team can use Logseq KB, version controlled
   - Cons: Many files, may be personal notes

B. **Add to .gitignore** (Keep personal)
   - Pros: Personal knowledge base, cleaner repo
   - Cons: Not shared with team
   - Already has `logseq/.gitignore` created

C. **Selective Commit** (Best of both)
   - Commit: Public pages (TTA.dev architecture, guides, TODO system)
   - Ignore: Personal journals, experimental pages
   - Add to `.gitignore`:
     ```
     logseq/journals/
     logseq/logseq/
     logseq/pages/AI\ Research.md
     # Keep architecture and guide pages
     ```

**Recommendation:** Option C - Selective commit of public knowledge

**Action:** User decision needed

---

### 8. Root-Level Orphan Files

**Files:**
- `tasks_github.json` (in root)

**Status:** Likely test output from TasksPrimitive

**Recommendation:** ✅ **MOVE OR DELETE**
- If needed: Move to `examples/tasks_output/`
- If test artifact: Delete

**Action:**
```bash
# Check content first
cat tasks_github.json
# Then either:
mv tasks_github.json examples/tasks_output/test-output.json
# OR
rm tasks_github.json
```

---

### 9. SpecKit Package Structure

**Location:** `platform/primitives/`

**New Files:**
```
src/tta_dev_primitives/speckit/
├── __init__.py
├── clarify_primitive.py
├── plan_primitive.py
├── specify_primitive.py
├── tasks_primitive.py
└── validation_gate_primitive.py

examples/
├── speckit_clarify_example.py
├── speckit_plan_example.py
├── speckit_specify_example.py
├── speckit_tasks_example.py
└── speckit_validation_gate_example.py

tests/speckit/
└── (36 test files)
```

**Recommendation:** ✅ **COMMIT ALL** - Core implementation
- This is production code
- Fully tested (361/361 passing)
- Ready for use

**Action:** Commit all SpecKit files

---

## 🚀 Recommended Cleanup Actions

### Priority 1: Immediate (Before Commit)

1. **Update .gitignore for example outputs:**
   ```bash
   echo "" >> .gitignore
   echo "# SpecKit example outputs" >> .gitignore
   echo "examples/features/" >> .gitignore
   echo "examples/plan_output/" >> .gitignore
   echo "examples/tasks_output/" >> .gitignore
   ```

2. **Clean up root orphan files:**
   ```bash
   # Inspect and decide
   cat tasks_github.json
   # Then delete if test artifact
   rm tasks_github.json
   ```

3. **Organize SpecKit planning docs:**
   ```bash
   mkdir -p archive/speckit-planning
   mv docs/planning/SPECKIT_DAY1_COMPLETE.md archive/speckit-planning/
   mv docs/planning/SPECKIT_DAY3_COMPLETE.md archive/speckit-planning/
   mv docs/planning/SPECKIT_DAY5_COMPLETE.md archive/speckit-planning/
   mv docs/planning/SPECKIT_DAY6_COMPLETE.md archive/speckit-planning/
   mv docs/planning/SPECKIT_DAY6_7_PLAN.md archive/speckit-planning/
   mv docs/planning/SPECKIT_DAY8_9_PLAN.md archive/speckit-planning/
   mv docs/planning/SPECKIT_IMPLEMENTATION_PLAN.md archive/speckit-planning/
   ```

### Priority 2: Decision Points

1. **Logseq Knowledge Base:**
   - Decision: Commit all, ignore all, or selective?
   - Recommendation: Selective (public architecture/guides, ignore journals)

2. **Atomic DevOps Documentation:**
   - Decision: Keep or archive?
   - Action: Review relevance to current project

### Priority 3: Optional Cleanup

1. **Clean Python cache files:**
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
   find . -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null
   ```

2. **Remove HTML coverage reports (if committed):**
   ```bash
   rm -rf htmlcov/
   ```

---

## 📝 Git Commit Strategy

### Recommended Commits

**Commit 1: SpecKit Core Implementation**
```bash
git add platform/primitives/src/tta_dev_primitives/speckit/
git add platform/primitives/tests/speckit/
git add platform/primitives/examples/speckit_*.py
git commit -m "feat(speckit): Add TasksPrimitive with Days 8-9 implementation

- Implement TasksPrimitive (1,052 lines)
- Add comprehensive test suite (36 tests, 95% coverage)
- Add 5 working examples (221 lines)
- All 361 tests passing

Closes #<issue-number> if applicable"
```

**Commit 2: Real-World Validation**
```bash
git add experiments/tasks-real-world/
git commit -m "docs(speckit): Add real-world validation experiments

- 3 realistic TTA.dev scenarios tested
- 51 actionable tasks generated
- 87% time savings proven
- Production readiness validated

Includes RESULTS.md and EXECUTIVE_SUMMARY.md"
```

**Commit 3: Documentation**
```bash
git add docs/SPECKIT_DAY8_9_COMPLETE.md
git add .gitignore  # with example outputs excluded
git commit -m "docs(speckit): Add completion documentation and cleanup

- Add comprehensive Day 8-9 completion summary
- Update .gitignore for example outputs
- Archive historical planning docs"
```

**Commit 4: Logseq Knowledge Base (if committing)**
```bash
# Selective commit of public pages
git add "logseq/pages/TTA.dev*"
git add "logseq/pages/TODO*.md"
git add logseq/ADVANCED_FEATURES.md
# Exclude journals
echo "logseq/journals/" >> .gitignore
git commit -m "docs(kb): Add Logseq knowledge base architecture

- Add TTA.dev architecture pages
- Add TODO management system
- Add advanced features documentation"
```

---

## ✅ Verification Checklist

After cleanup:

- [ ] No unnecessary files in staging area
- [ ] `.gitignore` updated for example outputs
- [ ] Historical planning docs archived
- [ ] Root directory clean (no orphan files)
- [ ] All tests still passing: `uv run pytest -v`
- [ ] Documentation accessible and organized
- [ ] Experiments committed with validation proof
- [ ] Git status shows only intended changes

---

## 📊 Expected Final Structure

```
TTA.dev/
├── packages/
│   └── tta-dev-primitives/
│       ├── src/tta_dev_primitives/speckit/  # ✅ Committed
│       ├── tests/speckit/                    # ✅ Committed
│       └── examples/speckit_*.py             # ✅ Committed
├── experiments/
│   └── tasks-real-world/                     # ✅ Committed (validation)
│       ├── README.md
│       ├── RESULTS.md
│       ├── EXECUTIVE_SUMMARY.md
│       ├── run_experiments.py
│       └── exp{1,2,3}-*/
├── docs/
│   ├── SPECKIT_DAY8_9_COMPLETE.md           # ✅ Committed
│   └── planning/                             # Cleaned up
├── archive/
│   └── speckit-planning/                     # ✅ Historical docs
│       ├── SPECKIT_DAY1_COMPLETE.md
│       ├── SPECKIT_DAY3_COMPLETE.md
│       └── ... (Days 1-7 planning)
├── examples/
│   ├── features/                             # ❌ Ignored (outputs)
│   ├── plan_output/                          # ❌ Ignored (outputs)
│   └── tasks_output/                         # ❌ Ignored (outputs)
└── logseq/                                   # ⚠️ Decision needed
    ├── journals/                             # Recommend ignore
    └── pages/                                # Recommend selective commit
```

---

## 🎯 Next Steps

1. **Review this plan** and make decisions on:
   - Logseq KB commit strategy
   - Atomic DevOps docs relevance

2. **Execute cleanup actions** (Priority 1)

3. **Run verification** checklist

4. **Commit changes** using recommended strategy

5. **Update ROADMAP.md** to reflect TasksPrimitive completion

---

**Generated by:** Repository cleanup analysis
**Sprint:** TasksPrimitive Days 8-9 + Validation
**Date:** November 4, 2025


---
**Logseq:** [[TTA.dev/Docs/Status-reports/Infrastructure/Cleanup_plan]]
