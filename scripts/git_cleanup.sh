#!/bin/bash
# TTA.dev Git Intelligent Cleanup
# Automated cleanup based on current repository analysis

set -e  # Exit on error

echo "======================================================================="
echo "🧹 TTA.dev Git Repository Intelligent Cleanup"
echo "======================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create backup first
BACKUP_BRANCH="backup/cleanup-$(date +%Y%m%d_%H%M%S)"
echo -e "${BLUE}📦 Creating backup branch: ${BACKUP_BRANCH}${NC}"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✅ Backup created${NC}"
echo ""

# Phase 1: Sync with remote
echo -e "${BLUE}🔄 Phase 1: Syncing with remote${NC}"
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
read -p "Pull latest changes from TTA.dev remote? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git pull TTA.dev "$(git rev-parse --abbrev-ref HEAD)" || {
        echo -e "${RED}❌ Pull failed. You may need to resolve conflicts.${NC}"
        echo "Backup branch available: $BACKUP_BRANCH"
        exit 1
    }
    echo -e "${GREEN}✅ Synced with remote${NC}"
fi
echo ""

# Phase 2: Handle untracked files
echo -e "${BLUE}📄 Phase 2: Untracked Files${NC}"
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED" ]; then
    echo "Found untracked files:"
    echo "$UNTRACKED"
    echo ""
    
    # Check specific files
    if [ -f ".github/workflows/auto-lazy-dev-setup.yml" ]; then
        echo -e "${YELLOW}📄 .github/workflows/auto-lazy-dev-setup.yml${NC}"
        read -p "Add this new lazy dev workflow? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .github/workflows/auto-lazy-dev-setup.yml
            echo -e "${GREEN}✅ Added${NC}"
        fi
    fi
    
    if [ -f "scripts/git_manager.py" ]; then
        echo -e "${YELLOW}📄 scripts/git_manager.py${NC}"
        read -p "Add this new git management tool? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add scripts/git_manager.py
            echo -e "${GREEN}✅ Added${NC}"
        fi
    fi
    
    if [ -f "GIT_CLEANUP_PLAN.md" ]; then
        echo -e "${YELLOW}📄 GIT_CLEANUP_PLAN.md${NC}"
        read -p "Add this cleanup plan? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add GIT_CLEANUP_PLAN.md
            echo -e "${GREEN}✅ Added${NC}"
        fi
    fi
    
    # Commit staged files
    if ! git diff --cached --quiet; then
        read -p "Commit staged files? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git commit -m "feat: Add git management tools and cleanup documentation"
            echo -e "${GREEN}✅ Changes committed${NC}"
        fi
    fi
else
    echo "No untracked files"
fi
echo ""

# Phase 3: Review and clean stashes
echo -e "${BLUE}💾 Phase 3: Stashes${NC}"
STASH_COUNT=$(git stash list | wc -l)
if [ "$STASH_COUNT" -gt 0 ]; then
    echo "Found $STASH_COUNT stash(es)"
    git stash list
    echo ""
    
    # Check stash@{1} - likely obsolete merge conflict
    if git stash list | grep -q "stash@{1}"; then
        echo -e "${YELLOW}Stash@{1}: WIP on docs/mcp-references (merge conflicts)${NC}"
        read -p "Drop this old merge conflict stash? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash drop stash@{1}
            echo -e "${GREEN}✅ Dropped stash@{1}${NC}"
        fi
    fi
    
    # Review stash@{0}
    if git stash list | grep -q "stash@{0}"; then
        echo -e "${YELLOW}Stash@{0}: Documentation reorganization${NC}"
        read -p "Show contents? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash show -p stash@{0} | head -100
            echo ""
            read -p "Apply this stash? (y)es, (d)rop, (k)eep: " -n 1 -r
            echo
            case "$REPLY" in
                [Yy])
                    git stash apply stash@{0}
                    echo -e "${GREEN}✅ Applied stash@{0}${NC}"
                    ;;
                [Dd])
                    git stash drop stash@{0}
                    echo -e "${GREEN}✅ Dropped stash@{0}${NC}"
                    ;;
                *)
                    echo "Keeping stash@{0}"
                    ;;
            esac
        fi
    fi
else
    echo "No stashes found"
fi
echo ""

# Phase 4: Clean merged branches
echo -e "${BLUE}🌿 Phase 4: Merged Branches${NC}"
MERGED=$(git branch --merged main | grep -v "^\*\|main\|develop\|master" || true)
if [ -n "$MERGED" ]; then
    echo "Branches merged into main:"
    echo "$MERGED"
    echo ""
    read -p "Delete all merged branches? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$MERGED" | xargs -r git branch -d
        echo -e "${GREEN}✅ Deleted merged branches${NC}"
    fi
else
    echo "No merged branches to clean"
fi
echo ""

# Phase 5: Clean experimental branches
echo -e "${BLUE}🧪 Phase 5: Experimental Branches${NC}"
EXPERIMENTAL=$(git branch | grep "copilot/sub-pr-" || true)
if [ -n "$EXPERIMENTAL" ]; then
    EXPERIMENT_COUNT=$(echo "$EXPERIMENTAL" | wc -l)
    echo "Found $EXPERIMENT_COUNT experimental copilot/sub-pr-* branches"
    echo "(Showing first 5)"
    echo "$EXPERIMENTAL" | head -5
    echo ""
    read -p "Delete all copilot/sub-pr-* branches? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$EXPERIMENTAL" | xargs -r git branch -D
        echo -e "${GREEN}✅ Deleted experimental branches${NC}"
    fi
else
    echo "No experimental branches to clean"
fi
echo ""

# Final status
echo "======================================================================="
echo -e "${GREEN}🎉 Cleanup Complete!${NC}"
echo "======================================================================="
echo ""
echo "Final status:"
python scripts/git_manager.py status || {
    echo "Repository Status:"
    git status --short
    echo ""
    echo "Branches: $(git branch | wc -l) local"
    echo "Stashes: $(git stash list | wc -l)"
}
echo ""
echo -e "${BLUE}📦 Backup branch:${NC} $BACKUP_BRANCH"
echo ""
echo "Next steps:"
echo "1. Review changes with: git status"
echo "2. If issues, restore from backup: git checkout $BACKUP_BRANCH"
echo "3. Continue work on your feature branch"
echo ""
