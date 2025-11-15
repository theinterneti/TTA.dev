#!/bin/bash
# Repository Cleanup Script - Post TasksPrimitive Sprint
# Date: November 4, 2025

set -e  # Exit on error

echo "=========================================="
echo "TTA.dev Repository Cleanup"
echo "TasksPrimitive Sprint Completion"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check we're in the right directory
if [ ! -f "AGENTS.md" ] || [ ! -d "packages/tta-dev-primitives" ]; then
    echo -e "${RED}Error: Must run from TTA.dev root directory${NC}"
    exit 1
fi

echo "Step 1: Update .gitignore for example outputs"
echo "----------------------------------------------"
if ! grep -q "examples/features/" .gitignore; then
    echo "" >> .gitignore
    echo "# SpecKit example outputs (generated during development)" >> .gitignore
    echo "examples/features/" >> .gitignore
    echo "examples/plan_output/" >> .gitignore
    echo "examples/tasks_output/" >> .gitignore
    echo -e "${GREEN}✓ Added example outputs to .gitignore${NC}"
else
    echo -e "${YELLOW}○ Example outputs already in .gitignore${NC}"
fi
echo ""

echo "Step 2: Check for orphan files in root"
echo "---------------------------------------"
if [ -f "tasks_github.json" ]; then
    echo -e "${YELLOW}Found: tasks_github.json${NC}"
    echo "Contents preview:"
    head -5 tasks_github.json
    echo "..."
    read -p "Delete this file? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm tasks_github.json
        echo -e "${GREEN}✓ Deleted tasks_github.json${NC}"
    else
        echo -e "${YELLOW}○ Kept tasks_github.json${NC}"
    fi
else
    echo -e "${GREEN}✓ No orphan files found${NC}"
fi
echo ""

echo "Step 3: Archive historical SpecKit planning docs"
echo "------------------------------------------------"
mkdir -p archive/speckit-planning
PLANNING_DOCS=(
    "docs/planning/SPECKIT_DAY1_COMPLETE.md"
    "docs/planning/SPECKIT_DAY3_COMPLETE.md"
    "docs/planning/SPECKIT_DAY5_COMPLETE.md"
    "docs/planning/SPECKIT_DAY6_COMPLETE.md"
    "docs/planning/SPECKIT_DAY6_7_PLAN.md"
    "docs/planning/SPECKIT_DAY8_9_PLAN.md"
    "docs/planning/SPECKIT_IMPLEMENTATION_PLAN.md"
)

moved_count=0
for doc in "${PLANNING_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        basename_file=$(basename "$doc")
        mv "$doc" "archive/speckit-planning/$basename_file"
        echo -e "${GREEN}✓ Moved $basename_file to archive${NC}"
        ((moved_count++))
    fi
done

if [ $moved_count -eq 0 ]; then
    echo -e "${YELLOW}○ No planning docs to move${NC}"
else
    echo -e "${GREEN}✓ Archived $moved_count planning documents${NC}"
fi
echo ""

echo "Step 4: Clean Python cache files (optional)"
echo "-------------------------------------------"
read -p "Clean __pycache__ and .pyc files? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null || true
    echo -e "${GREEN}✓ Cleaned Python cache files${NC}"
else
    echo -e "${YELLOW}○ Skipped Python cache cleanup${NC}"
fi
echo ""

echo "Step 5: Verify test suite still passes"
echo "---------------------------------------"
read -p "Run test suite to verify? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    if uv run pytest -v --tb=short -q; then
        echo -e "${GREEN}✓ All tests passing!${NC}"
    else
        echo -e "${RED}✗ Tests failed! Review changes before committing${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}○ Skipped test verification${NC}"
    echo -e "${YELLOW}  Remember to run: uv run pytest -v${NC}"
fi
echo ""

echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
echo ""
echo "Completed actions:"
echo "  • Updated .gitignore for example outputs"
echo "  • Checked for orphan files"
echo "  • Archived historical planning docs"
echo "  • Optional: Cleaned Python cache"
echo "  • Optional: Verified tests"
echo ""
echo "Next steps:"
echo "  1. Review git status: git status"
echo "  2. Stage changes: git add <files>"
echo "  3. Commit in logical groups (see docs/CLEANUP_PLAN.md)"
echo "  4. Consider Logseq KB commit strategy"
echo ""
echo -e "${GREEN}Cleanup complete!${NC}"
echo ""
echo "For detailed commit strategy, see:"
echo "  docs/CLEANUP_PLAN.md"
