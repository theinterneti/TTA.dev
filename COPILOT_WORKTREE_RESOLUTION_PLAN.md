# Copilot Worktree Resolution Plan

**Date:** 2025-11-15
**Issue:** framework/ directory contains complete repository duplication (336,558 insertions)
**Root Cause:** agent/copilot branch created blank without basing on main

## Current State

### Copilot Worktree Status
- **Location:** `/home/thein/repos/TTA.dev-copilot`
- **Branch:** `agent/copilot`
- **Files Staged:** 1,084 files
- **Insertions:** 336,558 lines
- **Problem:** Complete repository duplication under `framework/` subdirectory

### Valuable Unique Content Identified

**framework/docs/mcp-references/** - MCP server documentation (UNIQUE, not in main repo):
```
framework/docs/mcp-references/
├── README.md
├── context7.md
├── database-toolbox.md
├── devcontext.md
├── e2b.md
├── filesystem.md
├── github.md
├── grafana.md
├── hypertool.md
├── jaeger.md
├── notebooklm.md
├── playwright.md
├── prometheus.md
├── sequential-thinking.md
└── integrations/
    ├── devcontext-integration.md
    ├── filesystem-integration.md
    ├── github-integration.md
    ├── jaeger-integration.md
    ├── prometheus-integration.md
    └── sequential-thinking-integration.md
```

### What's Being Duplicated (to be discarded)

- **framework/.github/** - Duplicate of .github/ workflows
- **framework/logseq/** - Duplicate of logseq/ knowledge base
- **framework/packages/** - Duplicate of all TTA.dev packages
- **framework/scripts/** - Duplicate of automation scripts
- **framework/tests/** - Duplicate of test suites
- **framework/docs/** - Mostly duplicates, EXCEPT mcp-references/
- Everything else in framework/

## Resolution Strategy

### Step 1: Extract Valuable Content to Main Repo

1. Switch to main repo worktree
2. Create new branch `feature/mcp-documentation`
3. Copy unique MCP documentation from copilot worktree:
   ```bash
   cp -r /home/thein/repos/TTA.dev-copilot/framework/docs/mcp-references/ \
         /home/thein/repos/TTA.dev/docs/mcp-references/
   ```
4. Commit and push:
   ```bash
   git add docs/mcp-references/
   git commit -m "docs: Add MCP server reference documentation from copilot worktree"
   git push origin feature/mcp-documentation
   ```
5. Create PR for review

### Step 2: Clean Copilot Worktree

Option A: **Hard Reset (Recommended)**
```bash
cd /home/thein/repos/TTA.dev-copilot
git reset --hard origin/main  # Reset to clean main branch
git clean -fdx  # Remove all untracked files
```

Option B: **Selective Unstaging**
```bash
cd /home/thein/repos/TTA.dev-copilot
git reset HEAD framework/  # Unstage all framework/ changes
git clean -fdx framework/  # Remove framework/ directory
```

Option C: **Branch Recreation**
```bash
cd /home/thein/repos/TTA.dev
git worktree remove TTA.dev-copilot
git branch -D agent/copilot
git checkout main
git checkout -b agent/copilot
git worktree add TTA.dev-copilot agent/copilot
```

### Step 3: Verify Clean State

```bash
cd /home/thein/repos/TTA.dev-copilot
git status  # Should show clean working directory
git log --oneline --graph -10  # Should match main repo history
```

## Execution Order

1. ✅ **Create COPILOT_WORKTREE_RESOLUTION_PLAN.md** (this file)
2. ⏳ **Extract MCP documentation** to main repo feature branch
3. ⏳ **Create PR** for MCP documentation
4. ⏳ **Clean copilot worktree** using Option A (hard reset)
5. ⏳ **Verify** clean state
6. ✅ **Document resolution** in BRANCH_ORGANIZATION_COMPLETE.md

## Risks & Mitigation

**Risk:** Losing valuable work in copilot worktree
- **Mitigation:** Extracted unique content (MCP docs) before cleanup
- **Verification:** Manually reviewed framework/ for other unique content (none found)

**Risk:** Breaking copilot worktree configuration
- **Mitigation:** Can recreate worktree using Option C if needed
- **Fallback:** Main repo worktrees (augment, cline) unaffected

**Risk:** Losing commit history
- **Mitigation:** Commit history preserved in remote (not being rewritten)
- **Note:** agent/copilot branch history shows the duplication issue for future reference

## Success Criteria

- [ ] MCP documentation extracted to main repo
- [ ] PR created for MCP documentation
- [ ] Copilot worktree shows clean working directory
- [ ] No framework/ directory in copilot worktree
- [ ] agent/copilot branch based on main (no more blank branch)
- [ ] All worktrees remain functional

## Post-Resolution Actions

1. Update COPILOT_WORKTREE_INVESTIGATION.md with resolution outcome
2. Add resolution summary to BRANCH_ORGANIZATION_COMPLETE.md
3. Consider adding git hook to prevent blank branch creation in future
4. Document lesson learned: Always base worktree branches on main

---

**Created by:** AI Agent (GitHub Copilot)
**User Approval Required:** Before executing Step 2 (cleanup)
