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

## 🎯 Context-Aware Organization Strategy

### Problem Statement

When working in TTA.dev, you want TTA.dev-related Logseq pages to be prominent and easily accessible, while pages from other repositories (other TTA projects, personal notes) should be available but not create noise or clutter.

### Solution: Multi-Graph Architecture with Smart Linking

**Recommended Approach:** Use **separate Logseq graphs per repository** with **cross-graph linking** via file paths.

#### Architecture

```
~/repos/
├── TTA.dev/
│   └── logseq/                    # Local TTA.dev graph (gitignored)
│       ├── pages/                 # TTA.dev-specific pages
│       └── config.edn             # TTA.dev-specific config
│
├── TTA-notes/                     # Central knowledge base
│   └── logseq/
│       ├── pages/
│       │   ├── TTA.dev/          # Synced from TTA.dev
│       │   ├── TTA-other/        # Synced from other repos
│       │   └── Personal/         # Personal notes
│       └── config.edn             # Unified graph config
│
└── wsl-projects/
    └── TTA-notes/                 # Submodule or symlink
```

### Strategy 1: Dual-Graph Workflow (Recommended)

**Concept:** Maintain two separate Logseq graphs:

1. **Local graph** in each repository (TTA.dev/logseq/) - Context-focused
2. **Central graph** in TTA-notes - Unified knowledge base

#### Benefits

✅ **Perfect context isolation** - Only see TTA.dev pages when working in TTA.dev
✅ **No noise** - Other repo pages don't clutter the interface
✅ **Full access when needed** - Switch to TTA-notes for unified view
✅ **Cross-graph linking** - Link between graphs via file paths
✅ **Flexible workflow** - Choose the right graph for the task

#### Implementation

**Step 1: Keep Local TTA.dev Graph**

```bash
# TTA.dev/logseq/ already exists and is gitignored
# This is your context-focused graph
cd ~/repos/TTA.dev

# Logseq configuration for TTA.dev graph
cat > logseq/config.edn << 'EOF'
{:meta/version 1
 :feature/enable-journals? true
 :default-home {:page "TTA.dev"}
 :preferred-format :markdown

 ;; TTA.dev-specific settings
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}

 ;; Favorites for quick access
 :favorites ["TTA.dev" "TTA Primitives" "Architecture" "Guides"]}
EOF
```

**Step 2: Configure TTA-notes as Unified Graph**

```bash
# TTA-notes has all pages from all repos
cd ~/repos/TTA-notes

# Logseq configuration for unified graph
cat > logseq/config.edn << 'EOF'
{:meta/version 1
 :feature/enable-journals? true
 :default-home {:page "Index"}
 :preferred-format :markdown

 ;; Unified graph settings
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}

 ;; Organize by namespace
 :favorites ["Index" "TTA.dev/" "Personal/" "Daily/"]}
EOF
```

**Step 3: Create Index Page in TTA-notes**

```bash
# Create index page for navigation
cat > ~/repos/TTA-notes/logseq/pages/Index.md << 'EOF'
type:: [[Navigation]]
category:: [[Hub]]

---

# Knowledge Base Index

## 🏗️ TTA Projects

- [[TTA.dev/]] - Main development toolkit
- [[TTA-other-project/]] - Other TTA repositories

## 📝 Personal

- [[Personal/]] - Personal notes and ideas
- [[Daily/]] - Daily journal entries

## 🔍 Quick Access

### TTA.dev
- [[TTA.dev/Architecture/]]
- [[TTA.dev/Primitives/]]
- [[TTA.dev/Guides/]]

### Recent
- [[TTA.dev/Migration Dashboard]]
- [[TTA.dev/MCP/README]]
EOF
```

#### Workflow

**When working in TTA.dev:**

```bash
# Open Logseq with TTA.dev graph
cd ~/repos/TTA.dev
logseq  # Points to TTA.dev/logseq/

# You see ONLY TTA.dev pages
# No noise from other repos
# Perfect focus for TTA.dev work
```

**When you need unified view:**

```bash
# Open Logseq with TTA-notes graph
cd ~/repos/TTA-notes
logseq  # Points to TTA-notes/logseq/

# You see ALL pages from all repos
# Full knowledge base access
# Cross-repo linking and queries
```

**Syncing between graphs:**

```bash
# After editing in TTA.dev graph
cd ~/repos/TTA-notes
./scripts/sync-from-tta-dev.sh  # Pull changes

# After editing in TTA-notes graph
cd ~/repos/TTA-notes
./scripts/sync-to-tta-dev.sh    # Push TTA.dev changes back
```

### Strategy 2: Single Graph with Smart Queries (Alternative)

**Concept:** Use one unified graph (TTA-notes) with Logseq queries to filter by namespace.

#### Custom Queries for Context Filtering

```clojure
;; In TTA-notes/logseq/config.edn
{:default-queries
 {:journals
  [{:title "📅 Recent Journal Entries"
    :query [:find (pull ?p [*])
            :where
            [?p :block/journal? true]
            [?p :block/journal-day ?d]]
    :result-transform (fn [result]
                        (sort-by (fn [r] (get r :block/journal-day)) > result))
    :collapsed? false}]

  :pages
  [{:title "🏗️ TTA.dev Pages"
    :query [:find (pull ?p [*])
            :where
            [?p :block/name ?name]
            [(clojure.string/starts-with? ?name "tta.dev/")]]
    :collapsed? false}

   {:title "📝 Personal Pages"
    :query [:find (pull ?p [*])
            :where
            [?p :block/name ?name]
            [(clojure.string/starts-with? ?name "personal/")]]
    :collapsed? true}

   {:title "🔗 Other Projects"
    :query [:find (pull ?p [*])
            :where
            [?p :block/name ?name]
            [(clojure.string/starts-with? ?name "tta-")]]
    :collapsed? true}]}}
```

#### Context-Specific Home Pages

```markdown
<!-- TTA-notes/logseq/pages/TTA.dev.md -->
type:: [[Project Hub]]
category:: [[TTA Projects]]

---

# TTA.dev

**Main development toolkit for AI workflows**

## 📚 Quick Access

### Architecture
{{query (and [[TTA.dev]] [[Architecture]])}}

### Primitives
{{query (and [[TTA.dev]] [[Primitives]])}}

### Guides
{{query (and [[TTA.dev]] [[Guide]])}}

## 🔗 Related
- [[TTA.dev/Migration Dashboard]]
- [[TTA.dev/MCP/README]]
```

#### Workflow

**Focus on TTA.dev:**

- Set home page to `TTA.dev`
- Use queries to show only TTA.dev pages
- Other pages hidden but searchable

**Access other content:**

- Use search (Cmd/Ctrl+K)
- Click favorites to switch context
- Use Index page for navigation

### Strategy 3: Hybrid Approach (Best of Both)

**Concept:** Combine dual-graph and smart queries for maximum flexibility.

#### Daily Workflow

**Morning: Sync all repos to TTA-notes**

```bash
cd ~/repos/TTA-notes
./scripts/sync-from-tta-dev.sh
# Future: ./scripts/sync-from-other-repos.sh
```

**Work in TTA.dev with local graph**

```bash
cd ~/repos/TTA.dev
logseq  # Focused on TTA.dev only
```

**Evening: Sync changes back**

```bash
cd ~/repos/TTA-notes
./scripts/sync-to-tta-dev.sh
git add logseq/
git commit -m "docs: Daily knowledge updates"
git push origin main
```

### Cross-Graph Linking

**Link from TTA.dev graph to TTA-notes:**

```markdown
<!-- In TTA.dev/logseq/pages/SomePage.md -->

See also: [[../../../TTA-notes/logseq/pages/Personal/RelatedIdea.md][Personal: Related Idea]]
```

**Link from TTA-notes to TTA.dev:**

```markdown
<!-- In TTA-notes/logseq/pages/Personal/SomePage.md -->

Related to TTA.dev: [[TTA.dev/Architecture/Agent Discoverability]]
```

### Recommended Configuration

#### For TTA.dev/logseq/config.edn

```clojure
{:meta/version 1
 :feature/enable-journals? true
 :default-home {:page "TTA.dev"}
 :preferred-format :markdown
 :preferred-workflow :now

 ;; Focus on TTA.dev content
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}

 ;; Quick access to key pages
 :favorites ["TTA.dev"
             "TTA Primitives"
             "TTA.dev/Architecture/"
             "TTA.dev/Guides/"
             "TTA.dev/Migration Dashboard"]

 ;; Custom queries for TTA.dev context
 :default-queries
 {:journals
  [{:title "📅 Recent Work"
    :query [:find (pull ?p [*])
            :where
            [?p :block/journal? true]]
    :collapsed? false}]}}
```

#### For TTA-notes/logseq/config.edn

```clojure
{:meta/version 1
 :feature/enable-journals? true
 :default-home {:page "Index"}
 :preferred-format :markdown
 :preferred-workflow :now

 ;; Unified graph settings
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}

 ;; Namespace-based organization
 :favorites ["Index"
             "TTA.dev/"
             "Personal/"
             "Daily/"]

 ;; Context-aware queries
 :default-queries
 {:pages
  [{:title "🏗️ TTA.dev"
    :query [:find (pull ?p [*])
            :where
            [?p :block/name ?name]
            [(clojure.string/starts-with? ?name "tta.dev/")]]
    :collapsed? false}

   {:title "📝 Personal"
    :query [:find (pull ?p [*])
            :where
            [?p :block/name ?name]
            [(clojure.string/starts-with? ?name "personal/")]]
    :collapsed? true}]}}
```

### Decision Matrix

| Strategy | Focus | Flexibility | Complexity | Recommended For |
|----------|-------|-------------|------------|-----------------|
| **Dual-Graph** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Daily work in specific repos |
| **Single Graph + Queries** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Unified knowledge management |
| **Hybrid** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Best of both worlds |

### Final Recommendation

**Use the Hybrid Approach (Strategy 3):**

1. **Keep local TTA.dev graph** for focused work
   - Only TTA.dev pages visible
   - No noise from other repos
   - Perfect context isolation

2. **Use TTA-notes graph** for unified view
   - All repos synced
   - Cross-repo queries
   - Knowledge base management

3. **Sync bidirectionally** as needed
   - Morning: Pull from all repos
   - Evening: Push changes back
   - Automated with scripts

**Benefits:**

- ✅ Perfect focus when working in TTA.dev
- ✅ Full knowledge base access when needed
- ✅ No noise or clutter
- ✅ Flexible workflow
- ✅ Easy to maintain

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

- **Logseq Documentation:** <https://docs.logseq.com/>
- **Git Subtree Guide:** <https://www.atlassian.com/git/tutorials/git-subtree>
- **Git Submodules:** <https://git-scm.com/book/en/v2/Git-Tools-Submodules>

---

**Status:** ✅ **IMPLEMENTED** - Repository created and synced
**Next:** Configure Logseq with context-aware organization
