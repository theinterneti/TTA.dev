# TTA-notes: Multi-Repository Knowledge Base Architecture

**Date:** 2025-10-30
**Status:** 🚧 Implementation Plan
**Purpose:** Centralized Logseq knowledge base syncing from multiple TTA repositories

---

## 🎯 Vision

Create a unified knowledge graph that:
- Syncs Logseq documentation from multiple TTA-related repositories
- Maintains separation between public docs (in repos) and private knowledge (in TTA-notes)
- Enables cross-repository linking and querying in Logseq
- Integrates personal knowledge base with professional work

---

## 🏗️ Architecture Overview

```
TTA-notes (Central Knowledge Base)
├── logseq/
│   ├── pages/
│   │   ├── TTA.dev/           # Synced from TTA.dev repo
│   │   ├── TTA-other-project/ # Synced from other TTA repos
│   │   └── Personal/          # Personal notes (not synced)
│   ├── journals/              # Daily notes
│   └── config.edn             # Logseq configuration
├── .git/                      # Git repository
└── README.md                  # Documentation

TTA.dev (Public Repository)
├── logseq/                    # Synced TO TTA-notes
│   └── pages/                 # Project-specific knowledge
├── docs/                      # Public documentation
└── .gitignore                 # Ignores logseq/

wsl-projects (Personal Repository)
└── TTA-notes/                 # Git submodule or symlink
```

---

## 📋 Implementation Plan

### Phase 1: Create TTA-notes Repository

**Step 1: Initialize Repository**
```bash
# Create new repository on GitHub
# Repository name: TTA-notes
# Visibility: Private (contains personal knowledge)
# Initialize with README

# Clone locally
cd ~/repos
git clone https://github.com/theinterneti/TTA-notes.git
cd TTA-notes
```

**Step 2: Set Up Logseq Structure**
```bash
# Create Logseq directory structure
mkdir -p logseq/pages
mkdir -p logseq/journals

# Create initial config
cat > logseq/config.edn << 'EOF'
{:meta/version 1
 :feature/enable-journals? true
 :feature/enable-whiteboards? false
 :default-home {:page "TTA.dev"}
 :preferred-format :markdown
 :preferred-workflow :now
 :hidden []
 :default-templates {:journals ""}
 :publishing/all-pages-public? false
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"}}
EOF

# Create README
cat > README.md << 'EOF'
# TTA-notes

**Private knowledge base for TTA projects**

This repository contains Logseq documentation synced from multiple TTA-related repositories.

## Structure

- `logseq/pages/TTA.dev/` - Knowledge from TTA.dev repository
- `logseq/pages/Personal/` - Personal notes (not synced)
- `logseq/journals/` - Daily notes

## Sync Strategy

See `SYNC_WORKFLOW.md` for details on syncing from source repositories.
EOF

# Initial commit
git add .
git commit -m "feat: Initialize TTA-notes knowledge base structure"
git push origin main
```

### Phase 2: Configure Sync from TTA.dev

**Option A: Git Subtree (Recommended)**

Advantages:
- No submodule complexity
- Full history in TTA-notes
- Easy to sync changes bidirectionally

```bash
# In TTA-notes repository
cd ~/repos/TTA-notes

# Add TTA.dev as a remote
git remote add tta-dev ~/repos/TTA.dev

# Pull logseq/ directory from TTA.dev
git subtree add --prefix=logseq/pages/TTA.dev tta-dev docs/logseq-migration-cleanup --squash

# To sync updates from TTA.dev later:
git subtree pull --prefix=logseq/pages/TTA.dev tta-dev docs/logseq-migration-cleanup --squash
```

**Option B: Symlink (Simpler, but less portable)**

Advantages:
- Real-time sync (no git commands needed)
- Simpler workflow
- Logseq sees changes immediately

```bash
# In TTA-notes repository
cd ~/repos/TTA-notes/logseq/pages

# Create symlink to TTA.dev logseq
ln -s ~/repos/TTA.dev/logseq/pages TTA.dev

# Commit the symlink
git add TTA.dev
git commit -m "feat: Link TTA.dev logseq pages"
```

**Option C: Sync Script (Most Flexible)**

Advantages:
- Full control over sync process
- Can filter/transform content
- Works across different filesystems

```bash
# Create sync script in TTA-notes
cat > scripts/sync-from-tta-dev.sh << 'EOF'
#!/bin/bash
# Sync Logseq pages from TTA.dev to TTA-notes

SOURCE_DIR="$HOME/repos/TTA.dev/logseq/pages"
TARGET_DIR="$HOME/repos/TTA-notes/logseq/pages/TTA.dev"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Sync files (preserving timestamps)
rsync -av --delete "$SOURCE_DIR/" "$TARGET_DIR/"

# Commit changes
cd "$HOME/repos/TTA-notes"
git add logseq/pages/TTA.dev/
git commit -m "sync: Update TTA.dev knowledge base" || echo "No changes to commit"

echo "✅ Sync complete: TTA.dev → TTA-notes"
EOF

chmod +x scripts/sync-from-tta-dev.sh

# Run sync
./scripts/sync-from-tta-dev.sh
```

### Phase 3: Integrate with wsl-projects

**Option A: Git Submodule**
```bash
# In wsl-projects repository
cd ~/repos/wsl-projects

# Add TTA-notes as submodule
git submodule add https://github.com/theinterneti/TTA-notes.git TTA-notes

# Initialize and update
git submodule init
git submodule update

# Commit
git add .gitmodules TTA-notes
git commit -m "feat: Add TTA-notes knowledge base as submodule"
```

**Option B: Symlink**
```bash
# In wsl-projects repository
cd ~/repos/wsl-projects

# Create symlink to TTA-notes
ln -s ~/repos/TTA-notes TTA-notes

# Add to .gitignore (don't commit symlink)
echo "TTA-notes" >> .gitignore
```

---

## 🔄 Sync Workflow

### Daily Workflow

**Morning: Pull Latest Knowledge**
```bash
# Update TTA-notes from all sources
cd ~/repos/TTA-notes
./scripts/sync-from-tta-dev.sh
git pull origin main
```

**During Work: Edit in Logseq**
```bash
# Open Logseq
# Point to ~/repos/TTA-notes
# Edit pages as needed
# Logseq auto-saves to disk
```

**Evening: Push Changes**
```bash
# Commit changes in TTA-notes
cd ~/repos/TTA-notes
git add logseq/
git commit -m "docs: Daily knowledge updates"
git push origin main

# Optionally: Sync changes back to TTA.dev
# (if you edited TTA.dev-specific pages)
cd ~/repos/TTA.dev
# Manual copy or reverse sync script
```

### Syncing Changes Back to TTA.dev

**If you edit TTA.dev pages in TTA-notes:**
```bash
# Reverse sync script
cat > ~/repos/TTA-notes/scripts/sync-to-tta-dev.sh << 'EOF'
#!/bin/bash
# Sync TTA.dev pages back to source repository

SOURCE_DIR="$HOME/repos/TTA-notes/logseq/pages/TTA.dev"
TARGET_DIR="$HOME/repos/TTA.dev/logseq/pages"

# Sync files
rsync -av --delete "$SOURCE_DIR/" "$TARGET_DIR/"

# Commit in TTA.dev
cd "$HOME/repos/TTA.dev"
git add logseq/pages/
git commit -m "docs(logseq): Sync updates from TTA-notes" || echo "No changes"

echo "✅ Reverse sync complete: TTA-notes → TTA.dev"
EOF

chmod +x ~/repos/TTA-notes/scripts/sync-to-tta-dev.sh
```

---

## 📝 Logseq Configuration

### Enable Cross-Repository Linking

**In `logseq/config.edn`:**
```clojure
{:meta/version 1
 :feature/enable-journals? true
 :preferred-format :markdown
 
 ;; Enable namespace support for multi-repo structure
 :feature/enable-block-timestamps? false
 :feature/enable-search-remove-accents? true
 
 ;; Configure page references
 :ref/default-open-blocks-level 2
 :ref/linked-references-collapsed-threshold 50
 
 ;; Enable graph view across all pages
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}}
```

### Namespace Organization

**Recommended page naming:**
- `TTA.dev/Architecture/Agent Discoverability` - From TTA.dev repo
- `TTA.dev/Primitives/RouterPrimitive` - From TTA.dev repo
- `Personal/Ideas/New Feature` - Personal notes
- `Daily/2025-10-30` - Journal entries

**Benefits:**
- Clear source attribution
- Easy filtering in queries
- Prevents naming conflicts

---

## 🎯 Next Steps

### Immediate Actions

1. **Create TTA-notes Repository**
   ```bash
   # On GitHub: Create new private repository "TTA-notes"
   # Clone locally
   cd ~/repos
   git clone https://github.com/theinterneti/TTA-notes.git
   ```

2. **Initialize Structure**
   ```bash
   cd ~/repos/TTA-notes
   mkdir -p logseq/pages logseq/journals scripts
   # Copy config.edn and README.md from above
   git add .
   git commit -m "feat: Initialize TTA-notes structure"
   git push origin main
   ```

3. **Sync TTA.dev Logseq**
   ```bash
   # Choose sync method (recommend Option C: Sync Script)
   # Create and run sync script
   ./scripts/sync-from-tta-dev.sh
   ```

4. **Configure Logseq**
   ```bash
   # Open Logseq
   # Add graph: ~/repos/TTA-notes
   # Verify all pages are visible
   ```

### Future Enhancements

- [ ] Add sync scripts for other TTA repositories
- [ ] Set up automated sync (cron job or git hooks)
- [ ] Create Logseq queries for cross-repo insights
- [ ] Document backup strategy
- [ ] Add CI/CD for validation (optional)

---

## 📚 References

- **Logseq Documentation:** https://docs.logseq.com/
- **Git Subtree Guide:** https://www.atlassian.com/git/tutorials/git-subtree
- **Git Submodules:** https://git-scm.com/book/en/v2/Git-Tools-Submodules

---

**Status:** 🚧 Ready for implementation
**Next:** Create TTA-notes repository and run initial sync

