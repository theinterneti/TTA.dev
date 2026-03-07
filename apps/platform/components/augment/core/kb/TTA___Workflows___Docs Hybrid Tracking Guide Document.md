---
title: Hybrid Task Tracking Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/HYBRID_TRACKING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Hybrid Task Tracking Guide]]

**Quick reference for managing work across Task List and GitHub Issues**

---

## When to Use Each Tool

### Task List (AI Agent)
✅ **Use For:**
- Breaking down work into actionable steps
- Tracking progress during active work sessions
- Quick status updates
- Adjusting priorities on the fly
- Planning and brainstorming

❌ **Don't Use For:**
- Long-term tracking (>1 week)
- Cross-team collaboration
- PR integration
- Permanent record keeping

### GitHub Issues
✅ **Use For:**
- Multi-day/week work tracking
- PR integration and review
- Cross-repository coordination
- Team collaboration
- Permanent record and discussion
- Milestone tracking

❌ **Don't Use For:**
- Minute-by-minute progress
- Temporary planning notes
- Quick brainstorming

---

## Workflow

### Starting a New Phase

1. **Create GitHub Issue**
   ```bash
   # Use issue template
   gh issue create --template memory-system-extraction.md \
     --title "[EXTRACTION] Extract tta-agent-coordination package" \
     --label "enhancement,packaging,tta.dev-migration"
   ```

2. **Break Down in Task List**
   - Use AI agent to create sub-tasks
   - Track immediate progress
   - Update as you work

3. **Link Them Together**
   - Add GitHub issue number to task description
   - Reference task list in GitHub issue comments

### During Active Work

1. **Update Task List** (Real-time)
   ```
   Mark task as IN_PROGRESS when starting
   Mark task as COMPLETE when done
   Add new tasks as needed
   ```

2. **Update GitHub Issue** (Daily)
   ```markdown
   ## Progress Update - 2025-10-28

   ✅ Completed:
   - Fixed workspace configuration
   - Standardized Python version

   🔄 In Progress:
   - Adding version constraints

   ⏭️ Next:
   - Validate workspace configuration
   ```

### Completing a Phase

1. **Mark All Tasks Complete** in task list
2. **Update GitHub Issue** with final summary
3. **Close GitHub Issue** with completion comment
4. **Link to PR** if applicable

---

## Example: Phase 0 Workflow

### Step 1: Create GitHub Issue

```bash
cd ~/recovered-tta-storytelling

# Create issue from template
gh issue create \
  --template packaging-fixes.md \
  --title "[PACKAGING] Fix workspace configuration and Python version" \
  --label "bug,packaging,critical" \
  --assignee @me
```

**Result:** Issue #123 created

### Step 2: Update Task List

```
Tell AI agent:
"I've created GitHub issue #123 for Phase 0.
Let's start with the first task: Fix workspace configuration."
```

**AI marks task as IN_PROGRESS**

### Step 3: Do the Work

```bash
# Fix workspace configuration
vim pyproject.toml

# Add missing packages to workspace members
[tool.uv.workspace]
members = [
    "packages/tta-ai-framework",
    "packages/tta-narrative-engine",
    "packages/ai-dev-toolkit",           # ADDED
    "packages/universal-agent-context",  # ADDED
]

# Validate
uv sync --all-extras
```

### Step 4: Update Task List

```
Tell AI agent:
"Workspace configuration is fixed. Mark the task as complete."
```

**AI marks task as COMPLETE**

### Step 5: Update GitHub Issue

```bash
gh issue comment 123 --body "✅ Fixed workspace configuration
- Added ai-dev-toolkit to workspace members
- Added universal-agent-context to workspace members
- Validated with \`uv sync --all-extras\`
- All packages resolve correctly"
```

### Step 6: Repeat for Remaining Tasks

Continue this pattern for each sub-task in Phase 0.

### Step 7: Complete Phase

```bash
# When all tasks done
gh issue close 123 --comment "✅ Phase 0 Complete

All packaging fixes implemented:
- ✅ Workspace configuration fixed
- ✅ Python version standardized to 3.12+
- ✅ Version constraints added
- ✅ Workspace validated

Ready to proceed with Phase 1."
```

---

## Daily Workflow

### Morning (Start of Work Session)

1. **Check GitHub Issues**
   ```bash
   gh issue list --assignee @me --state open
   ```

2. **Review Task List**
   ```
   Ask AI: "Show me the current task list and what's in progress"
   ```

3. **Plan Today's Work**
   ```
   Tell AI: "I want to work on [TASK]. Break it down into steps."
   ```

### During Work

1. **Update Task List** as you complete steps
2. **Take notes** in GitHub issue comments
3. **Commit frequently** with semantic messages

### End of Day

1. **Update GitHub Issue** with progress summary
2. **Review Task List** with AI
3. **Plan Tomorrow** - What's next?

---

## Best Practices

### Task List
- ✅ Keep tasks small and actionable (1-4 hours each)
- ✅ Update in real-time as you work
- ✅ Use for planning and breaking down work
- ✅ Mark tasks IN_PROGRESS when starting
- ✅ Mark tasks COMPLETE when done

### GitHub Issues
- ✅ Create one issue per major phase
- ✅ Update daily with progress summary
- ✅ Use checklists for sub-tasks
- ✅ Link related issues and PRs
- ✅ Close with summary when complete

### Synchronization
- ✅ Reference GitHub issue # in task descriptions
- ✅ Reference task list in GitHub issue comments
- ✅ Keep both updated (task list real-time, issues daily)
- ✅ Use consistent terminology across both

---

## Templates

### GitHub Issue Progress Update
```markdown
## Progress Update - [DATE]

### ✅ Completed
- Task 1 description
- Task 2 description

### 🔄 In Progress
- Task 3 description (50% complete)

### ⏭️ Next Steps
- Task 4 description
- Task 5 description

### 🚧 Blockers
- None / [Describe blocker]

### 📊 Metrics
- Tests: X/Y passing
- Coverage: Z%
- Time spent: N hours
```

### Task List Update Request
```
AI, please update the task list:
- Mark "[TASK_NAME]" as COMPLETE
- Mark "[TASK_NAME]" as IN_PROGRESS
- Add new task: "[TASK_NAME]" under Phase X
```

---

## Troubleshooting

### Task List and GitHub Out of Sync

**Problem:** Task list shows different status than GitHub issue

**Solution:**
1. Decide which is correct (usually task list for current state)
2. Update GitHub issue to match
3. Add comment explaining the sync

### Too Many Tasks in Task List

**Problem:** Task list becoming overwhelming

**Solution:**
1. Focus on current phase only
2. Mark future phases as NOT_STARTED
3. Expand sub-tasks only when ready to work on them

### GitHub Issue Too Detailed

**Problem:** Issue has too much detail, hard to read

**Solution:**
1. Use collapsible sections in markdown
2. Move detailed notes to separate documents
3. Keep issue focused on high-level progress

---

## Quick Commands

### GitHub CLI
```bash
# List your open issues
gh issue list --assignee @me --state open

# Create issue from template
gh issue create --template [TEMPLATE_NAME].md

# Update issue
gh issue comment [NUMBER] --body "[MESSAGE]"

# Close issue
gh issue close [NUMBER] --comment "[MESSAGE]"

# View issue
gh issue view [NUMBER]
```

### Task List (AI Agent)
```
# View current tasks
"Show me the current task list"

# Update task status
"Mark task [NAME] as COMPLETE"
"Mark task [NAME] as IN_PROGRESS"

# Add new task
"Add a new task: [DESCRIPTION] under Phase X"

# Break down task
"Break down [TASK_NAME] into smaller steps"
```

---

## Success Metrics

### Good Hybrid Tracking
✅ Task list updated in real-time
✅ GitHub issues updated daily
✅ Both tools reference each other
✅ Clear progress visibility
✅ No duplicate work tracking

### Poor Hybrid Tracking
❌ Task list and GitHub out of sync
❌ GitHub issues not updated for days
❌ No cross-references between tools
❌ Unclear what's actually done
❌ Duplicate tracking effort

---

**Remember:** Task list for **doing**, GitHub issues for **tracking**.

---

**Last Updated:** 2025-10-28
**Maintained By:** @theinterneti


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs hybrid tracking guide document]]
