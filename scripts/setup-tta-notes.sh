#!/bin/bash
# Setup script for TTA-notes repository
# Creates the repository structure and initial sync

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 TTA-notes Repository Setup${NC}"
echo "================================"
echo ""

# Configuration
TTA_NOTES_DIR="$HOME/repos/TTA-notes"
TTA_DEV_DIR="$HOME/repos/TTA.dev"

# Step 1: Check if TTA-notes already exists
if [ -d "$TTA_NOTES_DIR" ]; then
    echo -e "${YELLOW}⚠️  TTA-notes directory already exists at $TTA_NOTES_DIR${NC}"
    read -p "Do you want to reinitialize it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting setup."
        exit 1
    fi
    rm -rf "$TTA_NOTES_DIR"
fi

# Step 2: Create TTA-notes directory
echo -e "${BLUE}📁 Creating TTA-notes directory structure...${NC}"
mkdir -p "$TTA_NOTES_DIR"
cd "$TTA_NOTES_DIR"

# Initialize git repository
git init
git branch -M main

# Step 3: Create Logseq structure
echo -e "${BLUE}📝 Creating Logseq structure...${NC}"
mkdir -p logseq/pages/TTA.dev
mkdir -p logseq/journals
mkdir -p scripts

# Step 4: Create Logseq config
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
 
 ;; Enable namespace support for multi-repo structure
 :feature/enable-block-timestamps? false
 :feature/enable-search-remove-accents? true
 
 ;; Configure page references
 :ref/default-open-blocks-level 2
 :ref/linked-references-collapsed-threshold 50
 
 ;; Graph settings
 :graph/settings {:journal/page-title-format "yyyy-MM-dd"
                  :builtin-pages-hidden? false}}
EOF

# Step 5: Create README
cat > README.md << 'EOF'
# TTA-notes

**Private knowledge base for TTA projects**

This repository contains Logseq documentation synced from multiple TTA-related repositories.

## 🏗️ Structure

```
TTA-notes/
├── logseq/
│   ├── pages/
│   │   ├── TTA.dev/        # Synced from TTA.dev repository
│   │   └── Personal/       # Personal notes (not synced)
│   ├── journals/           # Daily notes
│   └── config.edn          # Logseq configuration
├── scripts/
│   ├── sync-from-tta-dev.sh   # Sync TTA.dev → TTA-notes
│   └── sync-to-tta-dev.sh     # Sync TTA-notes → TTA.dev
└── README.md
```

## 🔄 Sync Workflow

### Pull Latest Knowledge
```bash
./scripts/sync-from-tta-dev.sh
```

### Push Changes Back to TTA.dev
```bash
./scripts/sync-to-tta-dev.sh
```

## 📝 Usage

1. Open Logseq and add this directory as a graph
2. Edit pages in `logseq/pages/`
3. Run sync scripts to keep repositories in sync

## 🔗 Related Repositories

- [TTA.dev](https://github.com/theinterneti/TTA.dev) - Main development toolkit
- [wsl-projects](https://github.com/theinterneti/wsl-projects) - Personal workspace

---

**Created:** 2025-10-30
**Sync Strategy:** See `TTA_NOTES_ARCHITECTURE.md` in TTA.dev repository
EOF

# Step 6: Create sync scripts
cat > scripts/sync-from-tta-dev.sh << 'EOF'
#!/bin/bash
# Sync Logseq pages from TTA.dev to TTA-notes

set -e

SOURCE_DIR="$HOME/repos/TTA.dev/logseq/pages"
TARGET_DIR="$HOME/repos/TTA-notes/logseq/pages/TTA.dev"

echo "🔄 Syncing TTA.dev → TTA-notes..."

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: TTA.dev logseq directory not found at $SOURCE_DIR"
    exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Sync files (preserving timestamps)
rsync -av --delete "$SOURCE_DIR/" "$TARGET_DIR/"

# Commit changes
cd "$HOME/repos/TTA-notes"
git add logseq/pages/TTA.dev/

if git diff --staged --quiet; then
    echo "✅ No changes to commit"
else
    git commit -m "sync: Update TTA.dev knowledge base from source"
    echo "✅ Sync complete and committed"
fi
EOF

cat > scripts/sync-to-tta-dev.sh << 'EOF'
#!/bin/bash
# Sync TTA.dev pages back to source repository

set -e

SOURCE_DIR="$HOME/repos/TTA-notes/logseq/pages/TTA.dev"
TARGET_DIR="$HOME/repos/TTA.dev/logseq/pages"

echo "🔄 Syncing TTA-notes → TTA.dev..."

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: TTA-notes TTA.dev directory not found at $SOURCE_DIR"
    exit 1
fi

# Sync files
rsync -av --delete "$SOURCE_DIR/" "$TARGET_DIR/"

# Commit in TTA.dev
cd "$HOME/repos/TTA.dev"
git add logseq/pages/

if git diff --staged --quiet; then
    echo "✅ No changes to commit"
else
    git commit -m "docs(logseq): Sync updates from TTA-notes"
    echo "✅ Reverse sync complete and committed"
fi
EOF

chmod +x scripts/sync-from-tta-dev.sh
chmod +x scripts/sync-to-tta-dev.sh

# Step 7: Create .gitignore
cat > .gitignore << 'EOF'
# Logseq
.recycle/
logseq/.recycle/
logseq/bak/
logseq/version-files/

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
*.swo
*~
EOF

# Step 8: Initial commit
echo -e "${BLUE}📦 Creating initial commit...${NC}"
git add .
git commit -m "feat: Initialize TTA-notes knowledge base structure

- Set up Logseq directory structure
- Add sync scripts for TTA.dev integration
- Configure Logseq for multi-repo knowledge base
- Add comprehensive README"

# Step 9: Sync from TTA.dev
echo -e "${BLUE}🔄 Running initial sync from TTA.dev...${NC}"
./scripts/sync-from-tta-dev.sh

echo ""
echo -e "${GREEN}✅ TTA-notes setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Create GitHub repository: https://github.com/new"
echo "   - Name: TTA-notes"
echo "   - Visibility: Private"
echo "   - Do NOT initialize with README"
echo ""
echo "2. Push to GitHub:"
echo "   cd $TTA_NOTES_DIR"
echo "   git remote add origin https://github.com/theinterneti/TTA-notes.git"
echo "   git push -u origin main"
echo ""
echo "3. Open Logseq and add graph:"
echo "   - Open Logseq"
echo "   - Add graph: $TTA_NOTES_DIR"
echo "   - Verify all pages are visible"
echo ""
echo "4. (Optional) Add to wsl-projects as submodule:"
echo "   cd ~/repos/wsl-projects"
echo "   git submodule add https://github.com/theinterneti/TTA-notes.git TTA-notes"
echo ""

