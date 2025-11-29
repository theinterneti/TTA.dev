#!/bin/bash
# Git Diff Review and Enhancement with Cline CLI
#
# Get AI-powered code review before committing changes.
#
# Usage:
#   ./scripts/cline/review-diff.sh [SCOPE]
#
#   SCOPE:
#     (empty)        - Review uncommitted changes (default)
#     staged         - Review staged changes only
#     <branch-name>  - Review diff between main and branch
#     <commit-hash>  - Review specific commit
#
# Examples:
#   ./scripts/cline/review-diff.sh                    # Review working directory
#   ./scripts/cline/review-diff.sh staged             # Review staged changes
#   ./scripts/cline/review-diff.sh feature-branch     # Review branch vs main
#   ./scripts/cline/review-diff.sh HEAD~1             # Review last commit

SCOPE=${1:-working}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check cline
if ! command -v cline &> /dev/null; then
  echo -e "${RED}❌ Cline CLI not found${NC}"
  echo "Install: npm install -g @cline/cli"
  exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Cline CLI: Git Diff Review & Enhancement                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get diff based on scope
case "$SCOPE" in
  working)
    DIFF=$(git diff)
    SCOPE_DESC="uncommitted changes"
    ;;
  staged)
    DIFF=$(git diff --cached)
    SCOPE_DESC="staged changes"
    ;;
  *)
    # Check if it's a branch
    if git show-ref --verify --quiet refs/heads/$SCOPE; then
      DIFF=$(git diff main..$SCOPE)
      SCOPE_DESC="branch: $SCOPE vs main"
    # Check if it's a commit hash
    elif git cat-file -e $SCOPE^{commit} 2>/dev/null; then
      DIFF=$(git show $SCOPE)
      SCOPE_DESC="commit: $SCOPE"
    else
      echo -e "${RED}❌ Invalid scope: $SCOPE${NC}"
      echo "Valid scopes: working, staged, <branch-name>, <commit-hash>"
      exit 1
    fi
    ;;
esac

# Check if there are changes
if [ -z "$DIFF" ]; then
  echo -e "${GREEN}ℹ️  No changes to review ($SCOPE_DESC)${NC}"
  exit 0
fi

# Count lines changed
LINES_CHANGED=$(echo "$DIFF" | wc -l)
FILES_CHANGED=$(echo "$DIFF" | grep -E "^diff --git" | wc -l)

echo -e "${CYAN}📊 Diff Stats:${NC}"
echo "  Scope: $SCOPE_DESC"
echo "  Files changed: $FILES_CHANGED"
echo "  Lines in diff: $LINES_CHANGED"
echo ""

# Save diff
TEMP_FILE="/tmp/diff-review-$(date +%s).txt"
echo "$DIFF" > "$TEMP_FILE"

# Preview
echo -e "${CYAN}📝 Diff preview:${NC}"
echo "$DIFF" | head -n 20
if [ $LINES_CHANGED -gt 20 ]; then
  echo "... ($(($LINES_CHANGED - 20)) more lines)"
fi
echo ""

# Determine review depth based on size
if [ $LINES_CHANGED -lt 50 ]; then
  REVIEW_TYPE="detailed"
  REVIEW_DESC="Detailed review (small change)"
elif [ $LINES_CHANGED -lt 200 ]; then
  REVIEW_TYPE="standard"
  REVIEW_DESC="Standard review (medium change)"
else
  REVIEW_TYPE="summary"
  REVIEW_DESC="Summary review (large change)"
fi

echo -e "${CYAN}🤖 Review type: $REVIEW_DESC${NC}"
echo ""
read -p "Proceed with Cline review? (y/n) " -n 1 -r
echo
if [[ ! $RRESPONSE =~ ^[Yy]$ ]]; then
  echo "Cancelled. Diff saved to: $TEMP_FILE"
  exit 0
fi

echo ""
echo -e "${CYAN}🔍 Cline is reviewing your changes...${NC}"
echo ""

# Build review prompt based on size
if [ "$REVIEW_TYPE" = "detailed" ]; then
  REVIEW_PROMPT="Provide detailed code review for this diff ($SCOPE_DESC):

$(cat $TEMP_FILE)

DETAILED REVIEW CHECKLIST:
- [ ] Tests included for new code?
- [ ] Tests updated for changed code?
- [ ] Docstrings complete and accurate?
- [ ] Type hints correct (use 'str | None' not 'Optional[str]')?
- [ ] Follows TTA.dev patterns (.clinerules)?
- [ ] No hardcoded values?
- [ ] Error handling present?
- [ ] No breaking changes?
- [ ] Performance implications?
- [ ] Security concerns?

For each file:
1. Overall assessment
2. Specific issues (with line numbers)
3. Improvement suggestions
4. Code quality score (1-10)

Final recommendation: APPROVE / CHANGES_NEEDED / REJECT"

elif [ "$REVIEW_TYPE" = "standard" ]; then
  REVIEW_PROMPT="Review this diff ($SCOPE_DESC):

$(cat $TEMP_FILE)

STANDARD REVIEW:
1. Check for common issues:
   - Missing tests
   - Missing/incorrect type hints
   - Documentation gaps
   - TTA.dev pattern violations
   - Potential bugs

2. Provide:
   - Summary of changes
   - Key concerns (if any)
   - Suggestions for improvement
   - Overall quality assessment

Recommendation: APPROVE / CHANGES_NEEDED / REJECT"

else
  REVIEW_PROMPT="Quick review of this large diff ($SCOPE_DESC):

Stats: $FILES_CHANGED files, $LINES_CHANGED lines

$(cat $TEMP_FILE)

SUMMARY REVIEW:
1. High-level assessment of changes
2. Critical issues only (must fix)
3. Major concerns (should fix)
4. General observations

Focus on:
- Obvious bugs or errors
- Breaking changes
- Security issues
- Major pattern violations

Quick recommendation: APPROVE / NEEDS_REVIEW / CONCERNS"
fi

# Send to Cline
echo "$REVIEW_PROMPT" | cline

echo ""
echo -e "${GREEN}✅ Review complete${NC}"
echo ""
echo -e "${CYAN}📋 Next steps:${NC}"

case "$SCOPE" in
  working)
    echo "  1. Address any issues Cline identified"
    echo "  2. Stage changes: git add -p"
    echo "  3. Review staged: ./scripts/cline/review-diff.sh staged"
    echo "  4. Commit: git commit"
    ;;
  staged)
    echo "  1. Address any issues Cline identified"
    echo "  2. Update staged changes: git add -p"
    echo "  3. Commit: git commit"
    ;;
  *)
    echo "  1. Address any issues Cline identified"
    echo "  2. Make changes to your branch/commit"
    echo "  3. Re-review if needed"
    ;;
esac

echo ""
echo -e "${CYAN}📄 Diff saved to: $TEMP_FILE${NC}"
