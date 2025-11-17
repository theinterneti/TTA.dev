#!/bin/bash
# Git Branch Cleanup Script for TTA.dev
# Safe, interactive cleanup of stale branches

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_DIR="/home/thein/repos/TTA.dev"
MAIN_REMOTE="TTA.dev"
BACKUP_PREFIX="backup/cleanup-$(date +%Y%m%d_%H%M%S)"

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Change to repo directory
cd "$REPO_DIR" || exit 1

print_header "Git Branch Cleanup - TTA.dev"

# Step 1: Safety backup
print_header "Step 1: Creating Safety Backup"

echo "Creating backup branch: $BACKUP_PREFIX"
git branch "$BACKUP_PREFIX"
print_success "Backup branch created"

# Step 2: Fetch and prune
print_header "Step 2: Fetching Updates & Pruning"

git fetch --all --prune
print_success "Fetched all remotes and pruned stale references"

# Step 3: Remote configuration
print_header "Step 3: Remote Configuration"

echo "Current remotes:"
git remote -v

if git remote | grep -q "^origin$"; then
    print_warning "Found 'origin' remote pointing to copilot fork"
    echo "Current origin: $(git remote get-url origin)"
    
    if confirm "Rename 'origin' to 'copilot-fork'?"; then
        git remote rename origin copilot-fork
        print_success "Renamed origin -> copilot-fork"
    elif confirm "Remove 'origin' remote entirely?"; then
        git remote remove origin
        print_success "Removed origin remote"
    else
        print_warning "Keeping origin as-is"
    fi
fi

# Step 4: List stale copilot sub-PR branches
print_header "Step 4: Copilot Sub-PR Branches (Remote)"

echo "Finding stale copilot/sub-pr-* branches..."
COPILOT_BRANCHES=$(git branch -r | grep "TTA.dev/copilot/sub-pr-" | sed 's/.*TTA.dev\///' || true)

if [ -z "$COPILOT_BRANCHES" ]; then
    print_success "No copilot sub-PR branches found"
else
    echo "Found $(echo "$COPILOT_BRANCHES" | wc -l) copilot sub-PR branches:"
    echo "$COPILOT_BRANCHES" | sed 's/^/  - /'
    
    if confirm "Delete ALL these remote branches?"; then
        echo "$COPILOT_BRANCHES" | while IFS= read -r branch; do
            echo "Deleting: $branch"
            git push "$MAIN_REMOTE" --delete "$branch" 2>/dev/null || print_warning "Failed to delete $branch (may already be gone)"
        done
        print_success "Deleted copilot sub-PR branches"
    else
        print_warning "Skipped deleting copilot sub-PR branches"
    fi
fi

# Step 5: Local merged branches
print_header "Step 5: Local Merged Branches"

echo "Checking for branches merged to main..."
MERGED_BRANCHES=$(git branch --merged main | grep -v "^\*" | grep -v "main" | grep -v "backup/" || true)

if [ -z "$MERGED_BRANCHES" ]; then
    print_success "No merged branches to clean up"
else
    echo "Found merged branches:"
    echo "$MERGED_BRANCHES" | sed 's/^/  - /'
    
    if confirm "Delete these merged local branches?"; then
        echo "$MERGED_BRANCHES" | xargs git branch -d
        print_success "Deleted merged branches"
    else
        print_warning "Skipped deleting merged branches"
    fi
fi

# Step 6: Review fix branches
print_header "Step 6: Fix Branches Review"

FIX_BRANCHES=$(git branch | grep "fix/" || true)

if [ -z "$FIX_BRANCHES" ]; then
    print_success "No fix branches found"
else
    echo "Found fix branches:"
    echo "$FIX_BRANCHES" | sed 's/^/  /'
    
    echo -e "\n${YELLOW}Review these branches manually:${NC}"
    echo "  - Check if fixes are merged"
    echo "  - Close related PRs if complete"
    echo "  - Delete branches with: git branch -d <branch-name>"
fi

# Step 7: Review experimental branches
print_header "Step 7: Experimental Branches Review"

EXP_BRANCHES=$(git branch | grep -E "experiment/|feature/keploy|feature/primitive-testing|feature/webhook" || true)

if [ -z "$EXP_BRANCHES" ]; then
    print_success "No experimental branches found"
else
    echo "Found experimental/old branches:"
    echo "$EXP_BRANCHES" | sed 's/^/  /'
    
    echo -e "\n${YELLOW}Review these branches manually:${NC}"
    echo "  - Check if work is complete"
    echo "  - Archive if needed"
    echo "  - Delete with: git branch -d <branch-name>"
fi

# Step 8: Summary
print_header "Summary"

echo "Current branch counts:"
echo "  Local branches: $(git branch | wc -l)"
echo "  Remote branches (TTA.dev): $(git branch -r | grep "TTA.dev/" | wc -l)"
echo "  Worktrees: $(git worktree list | wc -l)"

echo -e "\nBackup branch created: ${GREEN}$BACKUP_PREFIX${NC}"
echo "To remove backup after verification: ${YELLOW}git branch -d $BACKUP_PREFIX${NC}"

print_header "Cleanup Complete!"

print_warning "Next steps:"
echo "  1. Review fix branches manually"
echo "  2. Review experimental branches manually"
echo "  3. Test all worktrees still work"
echo "  4. Remove backup branch after verification"

echo -e "\nFor detailed analysis, see: ${BLUE}GIT_WORKTREE_BRANCH_ANALYSIS.md${NC}"
