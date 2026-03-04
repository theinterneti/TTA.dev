# TTA.dev Branch Cleanup Plan

**Date:** November 7, 2025
**Current Status:** 22 local branches, 47 remote branches
**Goal:** Establish clean branching strategy and remove stale branches

## 🎯 Branch Cleanup Strategy

### Branches to Delete (Merged)

These branches are merged into main and can be safely deleted:

```bash
# Local merged branches
git branch -d feat/add-observability-integration-package-clean
git branch -d feat/add-workflow-primitives-package
git branch -d feat/professional-setup-with-mcp-integration
git branch -d feature/observability-phase-2-primitive-instrumentation
git branch -d test/gemini-write-capabilities-demo
```

### Branches to Evaluate

#### Copilot Branches (Likely Stale)
- `copilot/sub-pr-28-again` - Sub-PR work, likely complete
- `copilot/sub-pr-28-please-work` - Sub-PR work, likely complete

#### Fix Branches (Check Status)
- `fix/gemini-api-key-secret-name` - Gemini CLI fix
- `fix/gemini-cli-auth-config` - Gemini CLI fix
- `fix/gemini-cli-write-permissions` - Gemini CLI fix
- `fix/update-mcp-server-to-v0.20.1` - MCP update
- `fix/use-ai-studio-not-vertex-ai` - Gemini configuration

#### Feature Branches (Check Relevance)
- `feature/keploy-framework` - Package now archived
- `feature/observability-phase-1-trace-context` - Observability work
- `feature/observability-phase-2-core-instrumentation` - Observability work
- `feature/speckit-days-8-9` - Speckit work

#### Test/Experimental
- `test/gemini-cli-diagnostics` - Diagnostic work
- `experiment/ace-integration` - **CURRENT BRANCH** - ACE integration work

### Proposed Branching Strategy

#### Branch Types
- `main` - Production ready code
- `feature/` - New features (e.g., `feature/new-primitive`)
- `fix/` - Bug fixes (e.g., `fix/cache-memory-leak`)
- `docs/` - Documentation updates (e.g., `docs/api-reference`)
- `refactor/` - Code refactoring (e.g., `refactor/observability-cleanup`)

#### Branch Lifecycle
1. **Create** from main with descriptive name
2. **Develop** with focused commits
3. **PR** to main with comprehensive review
4. **Merge** using squash merge for clean history
5. **Delete** branch immediately after merge

#### Naming Conventions
- Use lowercase with hyphens
- Include issue number if applicable: `fix/memory-leak-issue-123`
- Keep names descriptive but concise
- Avoid generic names like `test` or `experiment`

## 🧹 Cleanup Actions

### Phase 1: Delete Merged Branches ✅ SAFE

```bash
git branch -d feat/add-observability-integration-package-clean
git branch -d feat/add-workflow-primitives-package
git branch -d feat/professional-setup-with-mcp-integration
git branch -d feature/observability-phase-2-primitive-instrumentation
git branch -d test/gemini-write-capabilities-demo
```

### Phase 2: Evaluate and Clean Stale Branches

#### Archive Package-Related Branches
Since we archived keploy-framework package:
```bash
git branch -D feature/keploy-framework  # Force delete
```

#### Clean Up Copilot Sub-PR Branches
After verifying they're complete:
```bash
git branch -D copilot/sub-pr-28-again
git branch -D copilot/sub-pr-28-please-work
```

#### Consolidate Fix Branches
Many Gemini CLI fixes can likely be cleaned up:
```bash
# After verifying fixes are applied
git branch -D fix/gemini-cli-auth-config
git branch -D fix/gemini-cli-write-permissions
git branch -D fix/use-ai-studio-not-vertex-ai
```

### Phase 3: Remote Branch Cleanup

Many remote branches likely mirror local ones and can be cleaned:
```bash
# Delete remote branches that are merged
git push origin --delete feat/add-observability-integration-package-clean
git push origin --delete feat/add-workflow-primitives-package
# ... etc
```

## 📊 Expected Results

### Before Cleanup
- 22 local branches
- 47 remote branches
- Confusing branch naming
- Stale work branches

### After Cleanup
- ~8-10 active local branches
- ~15-20 active remote branches
- Clear naming conventions
- Only active work branches

## 🛡️ Safety Measures

1. **Backup** current branch state before cleanup
2. **Verify merge status** before deleting branches
3. **Check for unpushed work** on each branch
4. **Use `-d` flag** for merged branches (safe)
5. **Use `-D` flag** only for confirmed stale branches

## 📋 Implementation Checklist

- [ ] Execute Phase 1 (merged branches) - SAFE
- [ ] Review each branch in Phase 2 before deletion
- [ ] Clean up remote branches to match local
- [ ] Document new branching strategy
- [ ] Update team on new conventions

---

**Next Review:** After major feature development cycles


---
**Logseq:** [[TTA.dev/Docs/Development/Branch_cleanup_plan]]
