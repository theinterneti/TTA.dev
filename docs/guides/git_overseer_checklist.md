# Git Overseer Checklist (TTA.dev)

Concise daily and weekly loop for keeping branches, PRs, and worktrees healthy using existing scripts and VS Code tasks.

---

## 🕑 Daily Loop (10–20 minutes)

### 1. Git repo health snapshot

```bash
# From repo root
python scripts/git_manager.py status
```

**What to look for:**
- Current branch (e.g. `agent/augment`)
- Ahead/behind remote
- Untracked / modified / staged files
- Stashes and experimental branches summary

**Actions:**
- If there are untracked files you care about → stage or add to `.gitignore`.
- If there are stashes → decide whether to apply or drop within 1–2 days.
- If behind remote → plan a pull (after tests are green).

---

### 2. Worktree coordination status

```bash
python scripts/worktree/coordination-status.py
```

**What it shows:** active worktrees/branches, last sync, pending patterns, integration queue.

**Actions:**
- Confirm which worktrees are active (e.g. `augment → agent/augment`, `cline → experimental/issue-collaboration`).
- Note any pending patterns or integration-queue items you should prioritize.

Optional but recommended (once per day, usually after focused work):

```bash
python scripts/worktree/sync-learnings.py --sync-all
```

- Sync local agent patterns (`.worktree/local-patterns/` + Logseq `#ready-to-share`) into orchestrator coordination.

---

### 3. Quality Check (All)

In VS Code: `Task: Run Task → Quality Check (All)`

```bash
uv run ruff format . && \
uv run ruff check . --fix && \
uvx pyright platform/ apps/ && \
uv run pytest -v
```

**Goal:** Keep `agent/augment` and other active branches always "green".

**Actions:**
- Fix any new lint/type/test failures before starting branch/PR triage.
- If failures are unrelated to your branch, note them for follow-up issues.

---

### 4. Quick PR and branch triage (daily pass)

#### PR dashboard (high-level)

```bash
python scripts/pr_manager.py dashboard
python scripts/pr_manager.py health-check
```

**Scan for:**
- Failing-but-approved PRs that should be fixed or closed.
- Long-lived drafts that should be updated or converted to issues.
- Anything touching `agent/augment`, `experimental/issue-collaboration`, or `feature/logseq-github-todos`.

#### Branch view (local + remote)

Use `git_manager` + plain git:

```bash
python scripts/git_manager.py status   # branch & ahead/behind
python scripts/git_manager.py backup   # optional safety net

git branch --all --verbose --sort=-committerdate
```

**Decide for each active branch:**
- **Keep (active):** You are still iterating, or PR is open.
- **Keep (protected):** `main`, primary feature branches, or coordination branches.
- **Delete (local-only):** Fully merged or superseded branches.
- **Mark for cleanup:** Experimental branches that will be cleaned up weekly.

> **Rule of thumb:** Never delete a branch without either a merged PR or a recent backup (`python scripts/git_manager.py backup`).

Record any ambiguous cases as TODOs in Logseq with links to the relevant branch/PR.

---

## 📅 Weekly Loop (30–45 minutes)

Run this at least once per week (e.g. Friday afternoon or Monday morning).

### 1. Full PR analytics + triage

```bash
python scripts/pr_manager.py analyze
python scripts/pr_manager.py triage
python scripts/pr_manager.py recommend
```

**Decisions to make:**
- **Merge:** Small, green, and approved PRs.
- **Close:** Stale experimental PRs or spikes that are already integrated.
- **Convert to issue:** Explorations that uncovered work but should not be merged as-is.

Especially review:
- `experimental/issue-collaboration` PRs.
- Anything referencing `feature/logseq-github-todos`.
- All `agent/*` branches and associated PRs.

Document key outcomes in Logseq under the current journal date, tagging with `#dev-todo` where follow-ups are needed.

---

### 2. Branch hygiene (merged / stale cleanup)

Use `GitManager` helpers plus raw git for precision.

```bash
# See branches merged into main
python -m scripts.git_manager cleanup --dry-run  # or use git directly

git branch --merged main
git branch --no-merged main
```

**Process:**
1. For each non-protected branch in `git branch --merged main`:
   - Confirm the associated PR is merged.
   - If confirmed and no unique local work → safe to delete local branch.
2. For branches not merged but inactive for 30+ days:
   - Decide: close PR + delete branch, or convert to an issue.
   - If unsure, add a Logseq TODO to investigate and leave branch in place.

Use the interactive cleanup if you want a guided pass:

```bash
python scripts/git_manager.py cleanup
```

Always create a backup before aggressive cleanup:

```bash
python scripts/git_manager.py backup
```

---

### 3. Worktree coordination review

```bash
python scripts/worktree/coordination-status.py
python scripts/worktree/sync-learnings.py --sync-all
```

**Decide:**
- Which patterns from `agent/augment` and `experimental/issue-collaboration` should move into `.worktree/coordination/integration-queue/`.
- Which integrated patterns should be documented in `logseq/shared/pages/Worktree Patterns/`.

Move files and update Logseq pages accordingly.

---

### 4. Structural follow-ups → GitHub issues

From weekly findings, create or update a small set of GitHub issues, for example:
- "Expand pytest testpaths to cover observability primitives & scripts".
- "Add missing tests around git/worktree coordination scripts".
- "Codify agent worktree coordination patterns in docs + CI checks".

Keep these issues small and actionable; link to relevant branches, PRs, and Logseq pages.

---

## 🔁 Minimal Checklist Summary

**Daily:**
1. `git_manager status` → fix local noise.
2. `coordination-status` → know which worktrees/branches are hot.
3. `Quality Check (All)` task → keep tests/lint green.
4. `pr_manager dashboard/health-check` → quick PR scan.
5. Light branch triage (protect vs active vs delete-later).

**Weekly:**
1. `pr_manager analyze/triage/recommend` → heavy PR decisions.
2. Branch hygiene using merged/stale analysis + backups.
3. Worktree sync + pattern promotion.
4. Open/update 2–3 GitHub issues capturing structural work.


---
**Logseq:** [[TTA.dev/Docs/Guides/Git_overseer_checklist]]
