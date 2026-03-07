# TTA-notes Quick Start Guide

**Get your centralized knowledge base up and running in 15 minutes**

---

## Prerequisites

- ✅ TTA repository cloned at `/home/thein/recovered-tta-storytelling`
- ✅ TTA-notes private repository (Logseq graph)
- ✅ Logseq installed and configured
- ✅ Python 3.12+ with UV package manager

---

## Step 1: Verify TTA-notes Location (2 minutes)

**Find your TTA-notes repository:**

```bash
# List all repos in home directory
ls -la /home/thein/ | grep -i "tta\|logseq\|notes"

# Common locations:
# /home/thein/TTA-notes
# /home/thein/logseq-notes
# /home/thein/private-notes
```

**If TTA-notes doesn't exist yet:**

```bash
# Create new private repo on GitHub
# Then clone it:
cd /home/thein
git clone git@github.com:theinterneti/TTA-notes.git

# Initialize Logseq structure
cd TTA-notes
mkdir -p pages logseq
touch logseq/config.edn
```

**Set the path** (replace with your actual path):

```bash
export TTA_NOTES_PATH="/home/thein/TTA-notes"
```

---

## Step 2: Create KB Directory Structure (1 minute)

**In TTA repository:**

```bash
cd /home/thein/recovered-tta-storytelling

# Create KB namespace directories
mkdir -p .augment/kb/{Architecture,Components,Workflows,References,Status,Research,Testing}

# Verify structure
tree .augment/kb -L 1
```

**Expected output:**
```
.augment/kb
├── Architecture
├── Components
├── Workflows
├── References
├── Status
├── Research
└── Testing
```

---

## Step 3: Create Symlink to TTA-notes (1 minute)

**Create symlink from TTA-notes to TTA KB:**

```bash
# Navigate to TTA-notes pages directory
cd $TTA_NOTES_PATH/pages

# Create symlink (adjust path if TTA is elsewhere)
ln -s /home/thein/recovered-tta-storytelling/.augment/kb TTA

# Verify symlink
ls -la TTA
# Should show: TTA -> /home/thein/recovered-tta-storytelling/.augment/kb
```

**Test in Logseq:**

1. Open Logseq
2. Open TTA-notes graph
3. Navigate to `TTA/` in sidebar
4. Should see 7 namespace folders (empty for now)

---

## Step 4: Scan Documentation (2 minutes)

**Run the scanner to catalog all docs:**

```bash
cd /home/thein/recovered-tta-storytelling

# Scan all markdown files and categorize them
uv run python scripts/migrate-to-kb.py scan
```

**Expected output:**
```
🔍 Scanning repository for documentation...
✅ Scanned 2054 files

📊 Scan Results:
   Total files: 2054
   Scanned: 2054
   Priority 1 (Core): 6
   Priority 2 (Architecture): ~50
   Priority 3 (Components): ~100
   Priority 4 (Workflows): ~30
   Priority 5 (Status): ~50
   Priority 6 (References): ~40
   Priority 7 (Archive): ~1700+
```

**Scan results saved to:** `.augment/migration-status.json`

---

## Step 5: Review Migration Plan (2 minutes)

**Preview what will be migrated:**

```bash
# Show Priority 1 migration plan
uv run python scripts/migrate-to-kb.py plan --priority 1

# Show all priorities
uv run python scripts/migrate-to-kb.py plan
```

**Example output:**
```
📋 Migration Plan (Priority 1):

## References (6 files)
   📝 Pending AGENTS.md
      → .augment/kb/References/AGENTS.md
   📝 Pending .augment/TODO-AUDIT.md
      → .augment/kb/Status/TODO-Network.md
   📝 Pending CROSS-REPO-GUIDE.md
      → .augment/kb/References/Cross-Repo-Workflow.md
   ...
```

---

## Step 6: Test Migration (Dry Run) (2 minutes)

**Test without making changes:**

```bash
# Dry run for Priority 1
uv run python scripts/migrate-to-kb.py migrate --priority 1 --dry-run
```

**Expected output:**
```
📦 Migrating 6 documents...
🔍 DRY RUN - No files will be modified

📄 AGENTS.md
   → .augment/kb/References/Agent-Context.md
   ✅ Converted successfully

📄 .augment/TODO-AUDIT.md
   → .augment/kb/Status/TODO-Network.md
   ✅ Converted successfully

...

📊 Migration complete:
   ✅ Migrated: 6
   ❌ Failed: 0
```

**If successful, proceed to actual migration.**

---

## Step 7: Execute Priority 1 Migration (2 minutes)

**Migrate core context files:**

```bash
# Real migration (no --dry-run)
uv run python scripts/migrate-to-kb.py migrate --priority 1
```

**What happens:**

1. **Converts** documents to Logseq format (adds frontmatter)
2. **Moves** to `.augment/kb/` appropriate namespace
3. **Creates stub** in original location pointing to new KB location
4. **Updates** migration-status.json

**Verify in Logseq:**

1. Refresh Logseq graph (Ctrl+R / Cmd+R)
2. Navigate to `TTA/References/Agent-Context`
3. Should see AGENTS.md content with Logseq metadata
4. Check linked references work

---

## Step 8: Configure Logseq (3 minutes)

**Update TTA-notes Logseq config:**

```bash
# Copy template config to TTA-notes
cp /home/thein/recovered-tta-storytelling/.augment/logseq/config.edn \
   $TTA_NOTES_PATH/logseq/config.edn
```

**Or manually add to `TTA-notes/logseq/config.edn`:**

```clojure
{:meta/version 1

 :default-home {:page "TTA/References/Agent-Context"}

 :preferred-format :markdown

 :graph/namespace-configuration
 {:TTA {:color "#3B82F6" :icon "🎮"}}

 :default-queries
 {:journals [
   {:title "🔥 High Priority TODOs"
    :query [:find (pull ?b [*])
           :where
           [?b :block/marker "TODO"]
           [?b :block/priority "A"]
           [?b :block/page ?p]
           [?p :block/name ?n]
           [(str/starts-with? ?n "tta/")]]}
   ]}
}
```

**Restart Logseq** to apply config changes.

---

## Step 9: Validate Setup (1 minute)

**Run validation:**

```bash
uv run python scripts/migrate-to-kb.py validate
```

**Expected output:**
```
🔍 Validating KB structure...
   ✅ Architecture: 0 files
   ✅ Components: 0 files
   ✅ Workflows: 0 files
   ✅ References: 6 files
   ✅ Status: 1 file
   ✅ Research: 0 files
   ✅ Testing: 0 files

✅ Validation complete
```

**Test in Logseq:**

1. Search for `[[TTA/References/Agent-Context]]`
2. Open page
3. Check tags: should have `#TTA` tag
4. Verify links work
5. Try Logseq queries (if configured)

---

## Step 10: Review Migration Report (1 minute)

**Generate full report:**

```bash
uv run python scripts/migrate-to-kb.py report
```

**Example output:**
```
📊 Migration Report

Total documents: 2054
Migrated: 6 (0.3%)
Pending: 2048 (99.7%)

By Priority:
   Priority 1: 6/6 migrated
   Priority 2: 0/50 migrated
   Priority 3: 0/100 migrated
   Priority 4: 0/30 migrated
   Priority 5: 0/50 migrated
   Priority 6: 0/40 migrated
   Priority 7: 0/1700+ migrated

By Category:
   Architecture: 0/50 migrated
   Components: 0/100 migrated
   References: 6/46 migrated
   Status: 1/51 migrated
   ...
```

---

## ✅ Success! You're Ready to Use the KB

### What You Have Now

1. **`.augment/kb/`** - Local KB directory with 7 namespaces
2. **TTA-notes symlink** - Logseq can access TTA content directly
3. **6 core docs migrated** - AGENTS.md, TODO-AUDIT.md, etc.
4. **Migration automation** - Script ready for future migrations
5. **Logseq configured** - TTA namespace, queries, and templates

### Quick Access

**In Logseq:**
- `TTA/References/Agent-Context` - AI agent context (was AGENTS.md)
- `TTA/Status/TODO-Network` - Central TODO tracking (was TODO-AUDIT.md)
- `TTA/References/Cross-Repo-Workflow` - Multi-repo coordination

**In Terminal:**
```bash
# View KB directly
cd /home/thein/recovered-tta-storytelling/.augment/kb
tree -L 2

# Check migration status
cat .augment/migration-status.json | jq '.docs[] | select(.migrated==true)'
```

---

## Next Steps

### Continue Migration (Recommended Order)

**Week 1:**
```bash
# Priority 2: Architecture docs (~50 files)
uv run python scripts/migrate-to-kb.py migrate --priority 2 --dry-run
uv run python scripts/migrate-to-kb.py migrate --priority 2
```

**Week 2:**
```bash
# Priority 3: Component docs (~100 files)
uv run python scripts/migrate-to-kb.py migrate --priority 3 --dry-run
uv run python scripts/migrate-to-kb.py migrate --priority 3
```

**Week 3:**
```bash
# Priority 4: Workflows (~30 files)
uv run python scripts/migrate-to-kb.py migrate --priority 4 --dry-run
uv run python scripts/migrate-to-kb.py migrate --priority 4
```

### Ongoing Maintenance

**Daily/Weekly:**
```bash
# Check for new docs
uv run python scripts/migrate-to-kb.py scan

# Validate KB health
uv run python scripts/migrate-to-kb.py validate

# Generate progress report
uv run python scripts/migrate-to-kb.py report
```

---

## Troubleshooting

### Issue: Logseq doesn't see TTA namespace

**Solution:**
```bash
# Verify symlink exists
ls -la $TTA_NOTES_PATH/pages/TTA

# Should output:
# TTA -> /home/thein/recovered-tta-storytelling/.augment/kb

# If not, recreate symlink:
cd $TTA_NOTES_PATH/pages
rm -f TTA  # Remove if exists
ln -s /home/thein/recovered-tta-storytelling/.augment/kb TTA
```

**In Logseq:**
- Close and reopen the graph
- Check Settings → Files → Make sure symlinks are followed

### Issue: Migration script fails

**Solution:**
```bash
# Check Python environment
uv --version
uv run python --version  # Should be 3.12+

# Re-sync dependencies
cd /home/thein/recovered-tta-storytelling
uv sync --all-extras

# Try dry run first
uv run python scripts/migrate-to-kb.py migrate --priority 1 --dry-run
```

### Issue: Broken links after migration

**Solution:**
```bash
# Run link validation (to be built)
uv run python scripts/kb-maintenance.py check-links

# Manually fix in Logseq using Find & Replace
```

### Issue: Duplicate content

**Solution:**
- Original files become stubs pointing to KB
- Backup created at `{original}.md.backup`
- Safe to delete backups after verifying migration

---

## Common Commands Reference

```bash
# === Migration Commands ===

# Scan all docs
uv run python scripts/migrate-to-kb.py scan

# View migration plan for specific priority
uv run python scripts/migrate-to-kb.py plan --priority 1

# Dry run (no changes)
uv run python scripts/migrate-to-kb.py migrate --priority 1 --dry-run

# Execute migration
uv run python scripts/migrate-to-kb.py migrate --priority 1

# Validate KB structure
uv run python scripts/migrate-to-kb.py validate

# Generate report
uv run python scripts/migrate-to-kb.py report

# === KB Navigation ===

# View KB directory structure
tree /home/thein/recovered-tta-storytelling/.augment/kb -L 2

# Count files by namespace
find .augment/kb -name "*.md" | cut -d'/' -f4 | sort | uniq -c

# Search KB content
grep -r "search term" .augment/kb/

# === TTA-notes Management ===

# Navigate to TTA-notes
cd $TTA_NOTES_PATH

# Check symlink status
ls -la pages/TTA

# View Logseq config
cat logseq/config.edn

# Commit changes
git add .
git commit -m "Update TTA knowledge base"
git push
```

---

## Resources

- **Integration Plan:** `.augment/TTA-NOTES-INTEGRATION.md` (full details)
- **Migration Status:** `.augment/migration-status.json` (auto-updated)
- **KB Location:** `.augment/kb/` (local) → `TTA-notes/pages/TTA` (symlinked)
- **Scripts:** `scripts/migrate-to-kb.py` (migration), `scripts/kb-maintenance.py` (maintenance)

---

## Getting Help

**Documentation Issues:**
- Review original doc vs migrated version
- Check `.md.backup` files for original content
- Open issue in TTA repo if migration corrupted content

**Logseq Issues:**
- Check [Logseq documentation](https://docs.logseq.com/)
- Verify config.edn syntax
- Test with simple pages first

**Migration Script Issues:**
- Run with `--dry-run` first
- Check Python/UV versions
- Review `.augment/migration-status.json` for error details

---

**Status:** Ready to begin! Start with Step 1 to verify your TTA-notes location.

**Estimated Total Time:** 15 minutes for initial setup + Priority 1 migration

**Next Action:** Verify TTA-notes repository location and proceed to Step 1.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Tta-notes-quick-start]]
