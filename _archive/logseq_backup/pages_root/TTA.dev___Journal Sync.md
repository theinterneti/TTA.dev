# TTA.dev/Journal Sync

**Automated synchronization of journal entries across multi-agent worktrees**

type:: reference
status:: active
created:: [[2025-12-04]]

---

## Overview

The journal sync system consolidates journal entries from multiple agent worktrees into a canonical shared location. This enables:

- **Cross-agent visibility**: All agents can see each other's work logs
- **Unified history**: Single timeline of all development activity
- **TTA-notes integration**: Sync to shared brain repository

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source Directories                           │
├─────────────────────────────────────────────────────────────────┤
│  TTA.dev/logseq/journals/           → agent: main              │
│  TTA.dev-augment/logseq/journals/   → agent: augment           │
│  TTA.dev-cline/logseq/journals/     → agent: cline             │
│  TTA.dev-copilot/logseq/journals/   → agent: copilot           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ sync_journals.py
┌─────────────────────────────────────────────────────────────────┐
│                 Primary Destination                              │
│  TTA.dev/journals/                  (git-tracked, canonical)    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ --sync-to-notes
┌─────────────────────────────────────────────────────────────────┐
│                Secondary Destination                             │
│  TTA-notes/journals/                (shared brain hub)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Naming Convention

| Scenario | Format | Example |
|----------|--------|---------|
| Single agent for date | `YYYY-MM-DD.md` | `2025-11-15.md` |
| Multiple agents for date | `YYYY-MM-DD_<agent>.md` | `2025-11-20_main.md`, `2025-11-20_cline.md` |

---

## Agent Frontmatter

Each synced journal file includes metadata:

```markdown
agent:: cline
date:: [[2025-11-20]]
synced:: 2025-12-04 15:09

# Original content follows...
```

---

## Usage

### Basic Sync (to TTA.dev/journals/ only)

```bash
cd /home/thein/repos/TTA.dev
python3 scripts/sync_journals.py
```

### Full Sync (including TTA-notes)

```bash
python3 scripts/sync_journals.py --sync-to-notes
```

### Dry Run (preview changes)

```bash
python3 scripts/sync_journals.py --dry-run --verbose
```

### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without writing files |
| `--verbose`, `-v` | Show detailed output for each file |
| `--sync-to-notes` | Also sync to TTA-notes repository |

---

## Automation Options

### Manual (Recommended for now)

Run the sync script periodically:

```bash
# After a work session
python3 scripts/sync_journals.py --sync-to-notes

# Then commit and push
git add journals/
git commit -m "sync: journal entries from agents"
```

### Cron Job (Future)

```bash
# Add to crontab for daily sync at midnight
0 0 * * * cd /home/thein/repos/TTA.dev && python3 scripts/sync_journals.py --sync-to-notes
```

### Git Hook (Future)

Could be added as a post-commit hook to auto-sync after commits.

---

## Source

**Script:** `scripts/sync_journals.py`

---

## Related

- [[TTA.dev/KB Structure]] - Overall knowledge base structure
- [[TTA.dev/Code-KB Linking]] - Linking conventions

---

**Tags:** #reference #journals #sync #automation #multi-agent


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___journal sync]]
