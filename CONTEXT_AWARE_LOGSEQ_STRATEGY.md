# Context-Aware Logseq Organization Strategy

**Date:** 2025-10-30
**Status:** ✅ **DOCUMENTED** - Ready for implementation
**Purpose:** Maintain focus when working in different repository contexts

---

## 🎯 Problem Solved

When working in TTA.dev, you want TTA.dev-related Logseq pages to be **prominent and easily accessible**, while pages from other repositories (other TTA projects, personal notes) should be **available but not create noise or clutter**.

---

## ✅ Solution: Hybrid Multi-Graph Architecture

**Recommended Approach:** Use **separate Logseq graphs per repository** with **cross-graph linking** and **bidirectional sync**.

### Architecture

```
~/repos/
├── TTA.dev/
│   └── logseq/                    # Local TTA.dev graph (gitignored)
│       ├── pages/                 # TTA.dev-specific pages ONLY
│       └── config.edn             # TTA.dev-focused configuration
│
├── TTA-notes/                     # Central knowledge base
│   └── logseq/
│       ├── pages/
│       │   ├── TTA.dev/          # Synced from TTA.dev
│       │   ├── TTA-other/        # Synced from other repos
│       │   └── Personal/         # Personal notes
│       └── config.edn             # Unified graph configuration
```

---

## 🏗️ Three Strategies Documented

### Strategy 1: Dual-Graph Workflow ⭐ (Recommended)

**Concept:** Maintain two separate Logseq graphs:
1. **Local graph** in each repository (TTA.dev/logseq/) - Context-focused
2. **Central graph** in TTA-notes - Unified knowledge base

**Benefits:**
- ✅ Perfect context isolation
- ✅ No noise from other repos
- ✅ Full access when needed
- ✅ Cross-graph linking
- ✅ Flexible workflow

**When to use:**
- Daily work in specific repositories
- Need perfect focus on one project
- Want zero clutter from other content

### Strategy 2: Single Graph with Smart Queries

**Concept:** Use one unified graph (TTA-notes) with Logseq queries to filter by namespace.

**Benefits:**
- ✅ Maximum flexibility
- ✅ All content in one place
- ✅ Powerful cross-repo queries
- ✅ Single source of truth

**When to use:**
- Unified knowledge management
- Frequent cross-repo work
- Prefer single graph simplicity

### Strategy 3: Hybrid Approach ⭐⭐ (Best of Both)

**Concept:** Combine dual-graph and smart queries for maximum flexibility.

**Benefits:**
- ✅ Perfect focus when working in TTA.dev
- ✅ Full knowledge base access when needed
- ✅ No noise or clutter
- ✅ Flexible workflow
- ✅ Easy to maintain

**When to use:**
- Best of both worlds
- Daily work + knowledge management
- **This is the recommended approach**

---

## 📋 Implementation Guide

### Step 1: Keep Local TTA.dev Graph

**Already exists and is gitignored** ✅

```bash
cd ~/repos/TTA.dev

# Configure for TTA.dev focus
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

### Step 2: Configure TTA-notes as Unified Graph

**Already created** ✅

```bash
cd ~/repos/TTA-notes

# Configure for unified view
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

### Step 3: Create Index Page in TTA-notes

```bash
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

---

## 🔄 Daily Workflow

### Morning: Sync All Repos

```bash
cd ~/repos/TTA-notes
./scripts/sync-from-tta-dev.sh
# Future: ./scripts/sync-from-other-repos.sh
```

### During Work: Use Local Graph

```bash
cd ~/repos/TTA.dev
logseq  # Opens TTA.dev/logseq/

# You see ONLY TTA.dev pages
# No noise from other repos
# Perfect focus for TTA.dev work
```

### When You Need Unified View

```bash
cd ~/repos/TTA-notes
logseq  # Opens TTA-notes/logseq/

# You see ALL pages from all repos
# Full knowledge base access
# Cross-repo linking and queries
```

### Evening: Sync Changes Back

```bash
cd ~/repos/TTA-notes
./scripts/sync-to-tta-dev.sh
git add logseq/
git commit -m "docs: Daily knowledge updates"
git push origin main
```

---

## 🔗 Cross-Graph Linking

### Link from TTA.dev to TTA-notes

```markdown
<!-- In TTA.dev/logseq/pages/SomePage.md -->

See also: [[../../../TTA-notes/logseq/pages/Personal/RelatedIdea.md][Personal: Related Idea]]
```

### Link from TTA-notes to TTA.dev

```markdown
<!-- In TTA-notes/logseq/pages/Personal/SomePage.md -->

Related to TTA.dev: [[TTA.dev/Architecture/Agent Discoverability]]
```

---

## 📊 Decision Matrix

| Strategy | Focus | Flexibility | Complexity | Recommended For |
|----------|-------|-------------|------------|-----------------|
| **Dual-Graph** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Daily work in specific repos |
| **Single Graph + Queries** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Unified knowledge management |
| **Hybrid** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Best of both worlds** ⭐ |

---

## ✅ Benefits of Hybrid Approach

### Perfect Focus
- ✅ Only see TTA.dev pages when working in TTA.dev
- ✅ No noise from personal notes or other projects
- ✅ Clean, distraction-free interface

### Full Access
- ✅ Switch to TTA-notes for unified view
- ✅ All repos synced in one place
- ✅ Cross-repo queries and insights

### Flexible Workflow
- ✅ Choose the right graph for the task
- ✅ Easy to switch between contexts
- ✅ Bidirectional sync keeps everything in sync

### Easy Maintenance
- ✅ Automated sync scripts
- ✅ Git version control
- ✅ Clear separation of concerns

---

## 🎯 Next Steps

### Immediate

1. **Configure TTA.dev Graph**
   ```bash
   cd ~/repos/TTA.dev
   # Update logseq/config.edn with TTA.dev-focused settings
   ```

2. **Configure TTA-notes Graph**
   ```bash
   cd ~/repos/TTA-notes
   # Update logseq/config.edn with unified settings
   # Create Index.md page
   ```

3. **Test Workflow**
   - Open Logseq in TTA.dev (focused view)
   - Open Logseq in TTA-notes (unified view)
   - Verify sync scripts work

### Optional

4. **Add Custom Queries**
   - Context-specific queries in TTA-notes
   - Namespace-based filtering
   - Cross-repo insights

5. **Set Up Automation**
   - Cron job for auto-sync
   - Git hooks for sync on commit
   - Backup strategy

---

## 📚 Documentation

**Full details:** See `TTA_NOTES_ARCHITECTURE.md` section "Context-Aware Organization Strategy"

**Related:**
- `TTA_NOTES_SETUP_COMPLETE.md` - Setup verification
- `MIGRATION_COMPLETE.md` - Migration summary
- `scripts/sync-from-tta-dev.sh` - Pull sync script
- `scripts/sync-to-tta-dev.sh` - Push sync script

---

## 🎓 Key Insights

### Why Dual-Graph Works

1. **Logseq is file-based** - Each graph is just a directory
2. **No conflicts** - Separate graphs = separate namespaces
3. **Easy switching** - Just open different directory in Logseq
4. **Sync is simple** - rsync or git handles file copying

### Why Hybrid is Best

1. **Focus when you need it** - Local graph for daily work
2. **Access when you need it** - Central graph for knowledge management
3. **No compromises** - Get benefits of both approaches
4. **Easy to maintain** - Scripts handle the complexity

### Why This Solves Your Problem

1. **No noise** - TTA.dev graph only shows TTA.dev pages
2. **Full access** - TTA-notes graph shows everything
3. **Discoverability** - Search works across both graphs
4. **Flexibility** - Choose the right tool for the job

---

**Status:** ✅ **READY FOR IMPLEMENTATION**

**Recommended:** Start with Hybrid Approach (Strategy 3)

**Next:** Configure Logseq graphs and test workflow

