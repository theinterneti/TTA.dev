# TTA.dev Knowledge Base Cleanup Plan

**Date:** 2026-01-08
**Repository:** /home/thein/repos/TTA.dev
**Current Size:** 2.3GB
**Target Size:** ~2GB (-300MB, -13%)

---

## 📊 Current State

### Critical Issues
```
_archive/                     295MB (!) - 98% of cleanup target
├── packages/                 193MB  ⚠️ CRITICAL
├── packages-under-review/    91MB   ⚠️ CRITICAL
├── nested_copies/            7.7MB  ⚠️ HIGH
├── logseq_backup_20251220/   2.4MB
├── status-reports-2025/      716KB
├── logseq_backup/            620KB
├── reports/                  580KB
├── status-reports/           360KB
├── legacy-tta-game/          252KB
└── ...17 more directories
```

### Documentation Structure
```
docs/                         4.7MB (343 files)
├── planning/                 748KB (26 files)
├── status-reports/           708KB (55 files)
├── guides/                   580KB
├── architecture/             436KB
└── ...23 more subdirectories

platform/documentation/       688KB (49 files)
logseq/                       76KB (11 files)
platform/*/docs/              176KB (11 files)
```

---

## 🎯 Cleanup Strategy

### Phase 1: Archive Purge (Priority: CRITICAL)
**Target: Remove 290MB+ from _archive/**

#### Actions

1. **Remove package archives (284MB)**
   ```bash
   rm -rf _archive/packages              # 193MB - Old package versions
   rm -rf _archive/packages-under-review # 91MB  - Obsolete reviews
   rm -rf _archive/packages_backup       # 124KB - Duplicate
   ```
   **Rationale:** All in git history, no need for manual backup

2. **Remove duplicate artifacts (8MB)**
   ```bash
   rm -rf _archive/nested_copies         # 7.7MB - Duplicate nested files
   rm -rf _archive/logseq_backup*        # 3MB   - Multiple logseq backups
   ```

3. **Remove obsolete projects (252KB)**
   ```bash
   rm -rf _archive/legacy-tta-game       # 252KB - Old game project
   ```

4. **Consolidate status reports (1.6MB)**
   ```bash
   # Archive has 3 status report directories!
   rm -rf _archive/status-reports        # 360KB
   rm -rf _archive/status-reports-2025   # 716KB
   rm -rf _archive/status-reports-docs   # 104KB
   rm -rf _archive/reports               # 580KB
   ```
   **Rationale:** Redundant with docs/status-reports/

5. **Remove planning duplicates (352KB)**
   ```bash
   rm -rf _archive/planning              # 208KB
   rm -rf _archive/speckit-planning      # 144KB
   ```

**Expected Savings: ~295MB (99% of archive)**

---

### Phase 2: Documentation Consolidation (Priority: HIGH)

#### Keep Only Recent Status Reports
```bash
# Move old status reports to compressed archive
cd docs/status-reports
mkdir -p ../../_archive/historical
tar -czf ../../_archive/historical/status-reports-pre-2025.tar.gz \
  $(find . -name "*.md" -not -newermt "2025-01-01")
find . -name "*.md" -not -newermt "2025-01-01" -delete
```
**Expected Savings: ~500KB**

#### Consolidate Planning Docs
```bash
# Review and archive completed plans
cd docs/planning
# Manual review: Which are active? Which are done?
# Archive completed plans
```
**Expected Savings: ~400KB**

---

### Phase 3: Structure Normalization (Priority: MEDIUM)

#### Decision: Logseq Sync Direction

**Current Situation:**
- TTA-notes has 6 minimal pages
- TTA.dev/logseq/ has 9 pages
- Unclear which is source of truth

**Recommendation:**
```
TTA-notes/              ← PRIMARY personal KB
  ├── pages/
  └── journals/
       ↓ (sync)
TTA.dev/logseq/        ← MIRROR (read-only)
  ├── pages/           (synced FROM TTA-notes)
  └── journals/        (synced FROM TTA-notes)
```

**Action:**
```bash
# Update sync scripts to be one-way: TTA-notes → TTA.dev
# Document in README: TTA-notes is source, TTA.dev is mirror
```

#### Consolidate Platform Documentation

**Current:**
- platform/documentation/ (688KB)
- platform/*/docs/ (176KB per package)
- Unclear relationship

**Recommendation:**
```
platform/
├── primitives/
│   └── docs/              # Package-specific docs only
├── agent-context/
│   └── docs/
└── documentation/         # REMOVE - merge into main docs/
    └── logseq/            # REMOVE - use root logseq/
```

---

### Phase 4: Git Cleanup (Priority: LOW)

```bash
git gc --aggressive --prune=now
git reflog expire --expire=now --all
```

---

## 📋 Execution Plan

### Pre-Flight Safety
```bash
cd /home/thein/repos/TTA.dev

# 1. Ensure clean git state
git status

# 2. Create safety backup
tar -czf ~/TTA.dev-backup-$(date +%Y%m%d-%H%M%S).tar.gz .

# 3. Verify git history
git log --oneline | head -5
```

### Execute Cleanup
```bash
#!/bin/bash
set -euo pipefail

cd /home/thein/repos/TTA.dev

echo "=== TTA.dev Cleanup Script ==="
echo "Date: $(date)"
echo

# Phase 1: Remove _archive bloat
echo "Phase 1: Purging archive (295MB)..."

echo "  Removing package archives (284MB)..."
rm -rf _archive/packages
rm -rf _archive/packages-under-review
rm -rf _archive/packages_backup

echo "  Removing duplicate artifacts (8MB)..."
rm -rf _archive/nested_copies
rm -rf _archive/logseq_backup
rm -rf _archive/logseq_backup_20251220

echo "  Removing obsolete projects (252KB)..."
rm -rf _archive/legacy-tta-game

echo "  Removing duplicate status reports (1.6MB)..."
rm -rf _archive/status-reports
rm -rf _archive/status-reports-2025
rm -rf _archive/status-reports-docs
rm -rf _archive/reports

echo "  Removing duplicate planning (352KB)..."
rm -rf _archive/planning
rm -rf _archive/speckit-planning

echo "  ✓ Phase 1 complete: ~295MB removed"
echo

# Phase 2: Archive old status reports
echo "Phase 2: Archiving old status reports..."
cd docs/status-reports
mkdir -p ../../_archive/historical
if find . -name "*.md" -not -newermt "2025-01-01" | grep -q .; then
    tar -czf ../../_archive/historical/status-reports-pre-2025.tar.gz \
      $(find . -name "*.md" -not -newermt "2025-01-01")
    find . -name "*.md" -not -newermt "2025-01-01" -delete
    echo "  ✓ Old status reports archived"
else
    echo "  ✓ No old status reports to archive"
fi
cd ../..
echo

# Phase 3: Git cleanup
echo "Phase 3: Git maintenance..."
git add -A
git status --short
echo
read -p "Commit changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "cleanup: Remove 295MB of redundant archive files

- Remove packages/ (193MB) and packages-under-review/ (91MB)
- Remove nested_copies/ (7.7MB) and logseq backups (3MB)
- Remove duplicate status report directories (1.6MB)
- Remove duplicate planning directories (352KB)
- Archive old status reports to compressed tarball

Total reduction: ~295MB (13% of repository size)
All removed files are in git history and recoverable if needed."

    echo
    echo "Running git gc --aggressive..."
    git gc --aggressive --prune=now
    git reflog expire --expire=now --all
fi

echo
echo "=== Cleanup Complete ==="
du -sh .
echo
```

---

## 🎯 Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total Size** | 2.3GB | ~2GB | -300MB (13%) |
| **_archive/** | 295MB | <5MB | -290MB (98%) |
| **docs/status-reports/** | 708KB | ~200KB | -500KB (70%) |
| **Structure Clarity** | Low | High | Normalized |

---

## ⚠️ Safety & Validation

### Backup Strategy
```bash
# Full backup before cleanup
tar -czf ~/TTA.dev-backup-20260108.tar.gz /home/thein/repos/TTA.dev

# After cleanup, verify
du -sh /home/thein/repos/TTA.dev
git status
git log --oneline | head -5
```

### Recovery Plan
If something goes wrong:
```bash
# From git history
git reflog
git reset --hard <commit-hash>

# From backup
cd /home/thein/repos
rm -rf TTA.dev
tar -xzf ~/TTA.dev-backup-20260108.tar.gz
```

---

## 📝 Post-Cleanup Tasks

### 1. Update Documentation
```markdown
# README.md or DOCUMENTATION.md

## Documentation Structure

- `docs/` - Main documentation hub
  - `guides/` - User and developer guides
  - `architecture/` - System architecture
  - `status-reports/` - Recent status reports (last 12 months)
  - `planning/` - Active planning documents
- `logseq/` - Personal KB (synced FROM TTA-notes)
- `platform/*/docs/` - Package-specific documentation
```

### 2. Document Logseq Sync
```bash
# In scripts/sync-to-tta-dev.sh or similar
# Add comment:
# NOTE: TTA-notes is the SOURCE of truth
# TTA.dev/logseq/ is a READ-ONLY mirror
# Only sync FROM TTA-notes → TTA.dev
```

### 3. Create Maintenance Script
```bash
# scripts/cleanup-archives.sh
# Monthly cron job to prevent archive bloat
```

---

## 🚦 Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Delete needed files | Low | High | Full backup + git history |
| Git corruption | Very Low | High | git fsck before/after |
| Status report loss | Low | Medium | Compressed archive kept |
| Sync confusion | Medium | Low | Document in README |

---

## ✅ Success Criteria

- [ ] Repository size < 2GB
- [ ] _archive/ < 5MB
- [ ] No duplicate status report directories
- [ ] Clear documentation structure
- [ ] Logseq sync direction documented
- [ ] All changes committed to git
- [ ] Safety backup created

---

## 🎓 Lessons Learned

### Archive Anti-Patterns to Avoid
1. **Manual backups in _archive/** - Use git history instead
2. **Multiple status report directories** - Keep one location
3. **Nested copies** - Indicates sync/copy errors
4. **Obsolete project directories** - Remove or compress

### Best Practices Going Forward
1. **Rely on git history** - No manual _archive/ needed
2. **Regular cleanup** - Monthly review of docs/
3. **Single source of truth** - Clear sync direction
4. **Compress long-term archives** - Use .tar.gz for old reports

---

**Ready to execute?**
```bash
cd /home/thein/repos/TTA.dev
bash docs/TTA_DEV_CLEANUP_PLAN.md  # (extract script section)
```

**Generated:** 2026-01-08
**Author:** GitHub Copilot (Claude Sonnet 4.5)
