# TTA.dev Branch Organization Plan

**Date:** November 16, 2025  
**Current Status:** Changes stashed, organizing into logical branches  
**Worktree Location:** Main repo on `feature/phase5-apm-integration`, copilot worktree on `agent/copilot`

---

## 📋 Overview

We have two sets of changes to organize:

1. **Main Worktree Changes** (stashed in `stash@{0}`)
2. **Copilot Worktree Changes** (massive `framework/` directory structure - already staged)

---

## 🗂️ Main Worktree Changes Organization

### Category 1: Native Observability Migration ✅
**Branch:** `feature/phase5-apm-integration` (CURRENT - keep these staged)  
**Files:**
- `.hypertool/BASELINE_TEST_RESULTS.md`
- `.hypertool/NATIVE_LINUX_OBSERVABILITY_SETUP.md`
- `.hypertool/OBSERVABILITY_ALTERNATIVES.md`
- `.hypertool/instrumentation/GRAFANA_CLOUD_SETUP.md`
- `.hypertool/instrumentation/check_grafana_config.py`
- `.hypertool/instrumentation/config/__init__.py`
- `.hypertool/instrumentation/config/prometheus_remote_write.py`
- `.hypertool/instrumentation/config/tempo_exporter.py`
- `.hypertool/instrumentation/simple_dashboard.py`
- `docs/guides/DOCKER_FREE_OBSERVABILITY_MIGRATION.md`
- `docs/guides/LINUX_NATIVE_OBSERVABILITY.md`
- `docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md`
- `docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md`
- `docs/guides/OBSERVABILITY_MIGRATION_COMPLETE.md`
- `scripts/setup-native-observability.sh`

**Additional Files to Add:**
- `config.alloy.new` → Move to `.hypertool/instrumentation/config/alloy.new`
- `test_observability.py` → Move to `scripts/test_observability.py`
- `test_real_workflow.py` → Move to `scripts/test_real_workflow.py`
- `docs/OBSERVABILITY_SETUP_COMPLETE.md`
- `docs/guides/UNIFIED_OBSERVABILITY_ARCHITECTURE.md`

**Action:**
1. Pop stash selectively
2. Add observability-related untracked files
3. Commit to `feature/phase5-apm-integration`
4. Create PR: "Phase 5: Native Observability Migration Complete"

---

### Category 2: CLI Architecture & Planning 🆕
**Branch:** `feature/tta-dev-cli-architecture` (NEW)  
**Files:**
- `docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md`
- `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md`
- `docs/planning/TTA_DEV_CLI_IMPLEMENTATION_PLAN.md`

**Action:**
1. Create new branch from `main`
2. Cherry-pick files from stash
3. Commit architecture docs
4. Create PR: "Architecture: TTA-dev CLI Design & Planning"

**Next Steps:**
- This branch sets the foundation for the CLI implementation
- Implementation will happen in `feature/tta-dev-cli-mvp` (from Architecture doc)

---

### Category 3: Documentation Reorganization 🆕
**Branch:** `feature/docs-reorganization` (NEW)  
**Files:**
- `docs/quickstart/` (entire directory)
- `docs/sessions/` (entire directory)
- `docs/troubleshooting/` (entire directory)

**Action:**
1. Create new branch from `main`
2. Add new documentation directories
3. Commit with structure explanation
4. Create PR: "Docs: Add quickstart, sessions, and troubleshooting directories"

---

### Category 4: Modified Files (Need Review)
**Files:**
- `docs/guides/README.md` (both staged and unstaged changes - CONFLICT)
- `packages/tta-dev-integrations/pyproject.toml`
- `uv.lock`

**Action:**
1. Review `docs/guides/README.md` changes separately
   - Staged changes likely from observability work
   - Unstaged changes might be from other sessions
2. Check pyproject.toml and uv.lock for dependencies added
3. Decide which branch these belong to

---

## 🗂️ Copilot Worktree Changes Organization

### Current Status
**Worktree:** `/home/thein/repos/TTA.dev-copilot`  
**Branch:** `agent/copilot`  
**Changes:** MASSIVE `framework/` directory structure (all staged)

### What is This?
Looking at the files, this appears to be:
- Complete Logseq knowledge base migration (`framework/logseq/`)
- Full package extraction (`framework/packages/`)
- Testing infrastructure (`framework/tests/`)
- Scripts and automation (`framework/scripts/`)
- Monitoring setup (`framework/monitoring/`)

### Questions to Answer
1. **Is this a separate "framework" extraction?**
   - Looks like TTA.dev packages being prepared for standalone distribution
   - Or a "framework mode" workspace structure?

2. **Should this be merged back to main?**
   - If yes: This is HUGE, needs careful review
   - If no: This might be an experimental branch for a framework distribution

3. **What's the relationship to main repo?**
   - Check if `framework/` already exists in main
   - Determine if this is additive or replacement

### Recommended Action (Copilot Worktree)

**PAUSE and Investigate:**

1. **Check main repo for `framework/` directory:**
   ```bash
   cd /home/thein/repos/TTA.dev
   ls -la | grep framework
   ```

2. **Review the purpose:**
   - Is this for packaging TTA.dev as a redistributable framework?
   - Is this a VS Code workspace configuration experiment?

3. **Decision paths:**

   **Option A: Framework Distribution Preparation**
   - Branch: `feature/framework-extraction`
   - Purpose: Prepare TTA.dev for npm/pip distribution
   - Action: Continue with staged changes, create massive PR

   **Option B: Experimental Workspace Structure**
   - Branch: `experiment/framework-workspace`
   - Purpose: Testing alternative repo organization
   - Action: Keep in worktree, don't merge yet

   **Option C: Logseq Migration**
   - Branch: `feature/logseq-kb-migration`
   - Purpose: Move Logseq files to `framework/logseq/`
   - Action: Extract just the Logseq changes

---

## 🎯 Recommended Execution Order

### Phase 1: Main Worktree (Today)

1. **Commit Observability Work (30 min)**
   ```bash
   cd /home/thein/repos/TTA.dev
   git stash pop stash@{0}
   # Selectively stage observability files
   git add .hypertool/instrumentation/
   git add docs/guides/*OBSERVABILITY*
   git add scripts/setup-native-observability.sh
   git commit -m "Phase 5: Native Linux observability complete"
   ```

2. **Create CLI Architecture Branch (15 min)**
   ```bash
   git checkout main
   git checkout -b feature/tta-dev-cli-architecture
   # Cherry-pick architecture docs from stash
   git add docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md
   git add docs/planning/TTA_DEV_CLI_*.md
   git commit -m "Architecture: TTA-dev CLI design and planning"
   git push origin feature/tta-dev-cli-architecture
   ```

3. **Create Docs Reorganization Branch (10 min)**
   ```bash
   git checkout main
   git checkout -b feature/docs-reorganization
   git add docs/quickstart/ docs/sessions/ docs/troubleshooting/
   git commit -m "Docs: Add quickstart, sessions, troubleshooting directories"
   git push origin feature/docs-reorganization
   ```

### Phase 2: Copilot Worktree (Investigate First)

1. **Investigate Framework Structure (30 min)**
   - Check if `framework/` exists in main
   - Review the intent behind this massive change
   - Document findings

2. **Decision Point**
   - If framework extraction: Create feature branch, careful PR
   - If experimental: Keep in worktree, don't merge
   - If Logseq migration: Extract just those files

---

## 📊 Branch Strategy Summary

### Active Branches After Reorganization

```
main
├── feature/phase5-apm-integration          # Observability (merge ready)
├── feature/tta-dev-cli-architecture        # CLI design docs (review)
├── feature/docs-reorganization             # Docs structure (merge ready)
└── agent/copilot (worktree)                # TBD based on investigation
```

### Merge Order
1. `feature/docs-reorganization` → main (simple, low risk)
2. `feature/phase5-apm-integration` → main (tested, ready)
3. `feature/tta-dev-cli-architecture` → main (architecture decision)
4. Copilot worktree: Decide after investigation

---

## ✅ Next Immediate Actions

1. **Execute Phase 1 (Main Worktree)**
   - Follow the commands above
   - Create 3 focused PRs

2. **Investigate Copilot Worktree**
   - Understand the `framework/` structure
   - Determine intent and strategy
   - Document findings

3. **Open PRs**
   - All main worktree branches get PRs
   - Review and merge in recommended order

---

**Ready to execute?** Let's start with Phase 1 - organizing the main worktree changes!
