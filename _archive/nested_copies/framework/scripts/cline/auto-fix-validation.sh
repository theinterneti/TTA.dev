#!/bin/bash
# Auto-Fix Package Validation Issues with Cline CLI
#
# This script runs TTA.dev package validation and pipes the output
# to Cline CLI for automated fixing.
#
# Usage:
#   ./scripts/cline/auto-fix-validation.sh <package-name>
#   ./scripts/cline/auto-fix-validation.sh tta-dev-primitives
#
# What it does:
#   1. Runs ./scripts/validate-package.sh
#   2. Captures validation output
#   3. If issues found, sends to Cline CLI
#   4. Cline analyzes and fixes issues
#   5. Human reviews changes

set -e  # Exit on error

PACKAGE=$1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Usage check
if [ -z "$PACKAGE" ]; then
  echo -e "${RED}❌ Usage: $0 <package-name>${NC}"
  echo ""
  echo "Examples:"
  echo "  $0 tta-dev-primitives"
  echo "  $0 tta-observability-integration"
  echo "  $0 universal-agent-context"
  exit 1
fi

# Check package exists
if [ ! -d "packages/$PACKAGE" ]; then
  echo -e "${RED}❌ Package not found: packages/$PACKAGE${NC}"
  exit 1
fi

# Check cline CLI is installed
if ! command -v cline &> /dev/null; then
  echo -e "${RED}❌ Cline CLI not found${NC}"
  echo ""
  echo "Install with: npm install -g @cline/cli"
  echo "Or use: npx @cline/cli ..."
  exit 1
fi

# Check cline is configured
if ! cline config list &> /dev/null; then
  echo -e "${YELLOW}⚠️  Cline CLI not configured${NC}"
  echo ""
  echo "Configure with:"
  echo "  cline config set api-provider openrouter"
  echo "  cline config set api-key sk-or-v1-YOUR_KEY"
  echo "  cline config set api-model-id mistralai/mistral-small-3.2"
  exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Cline CLI: Auto-Fix Package Validation Issues            ║${NC}"
echo -e "${BLUE}║  Package: ${PACKAGE}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run validation
echo -e "${CYAN}🔍 Step 1: Running validation...${NC}"
VALIDATION_OUTPUT=$(./scripts/validate-package.sh $PACKAGE 2>&1 || true)

# Check if already valid
if echo "$VALIDATION_OUTPUT" | grep -q "✅ All validations passed"; then
  echo -e "${GREEN}✅ Package already passes all validations!${NC}"
  echo ""
  echo "$VALIDATION_OUTPUT"
  exit 0
fi

# Save output to temp file for reference
TEMP_FILE="/tmp/validation-${PACKAGE}-$(date +%s).txt"
echo "$VALIDATION_OUTPUT" > "$TEMP_FILE"

echo -e "${YELLOW}⚠️  Validation issues found${NC}"
echo ""
echo "Preview of issues:"
echo "$VALIDATION_OUTPUT" | head -n 30
echo ""
echo -e "${CYAN}📄 Full validation report saved to: $TEMP_FILE${NC}"
echo ""

# Ask for confirmation
echo -e "${CYAN}🤖 Step 2: Send to Cline for automated fixing?${NC}"
echo ""
echo "Cline will:"
echo "  - Analyze validation errors"
echo "  - Fix issues following TTA.dev standards (.clinerules)"
echo "  - Run validation after each fix"
echo "  - Show you diffs for review"
echo ""
read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ ! $RRESPONSE =~ ^[Yy]$ ]]; then
  echo "Cancelled. Validation report in: $TEMP_FILE"
  exit 0
fi

# Send to Cline
echo ""
echo -e "${CYAN}🚀 Step 3: Cline is analyzing and fixing issues...${NC}"
echo ""

cat "$TEMP_FILE" | cline "Fix all validation issues for packages/$PACKAGE shown in this report.

CONTEXT:
- Package: $PACKAGE
- Package path: packages/$PACKAGE
- Follow TTA.dev standards from .clinerules file
- This is a monorepo (use 'uv' not 'pip')

VALIDATION REPORT:
$(cat)

INSTRUCTIONS:
1. Read the validation report carefully
2. Categorize issues:
   - Missing docstrings
   - Type hint issues
   - Test coverage gaps
   - Code quality (ruff errors)
   - Documentation problems

3. Fix issues incrementally:
   - Start with simple fixes (docstrings, type hints)
   - Then more complex (test coverage, refactoring)
   - Run relevant validation after each category

4. For each fix:
   - Show me the diff
   - Explain what you're fixing
   - Wait for approval if significant change

5. After all fixes:
   - Run full validation: ./scripts/validate-package.sh $PACKAGE
   - Confirm all issues resolved

6. Follow TTA.dev patterns:
   - Use 'str | None' not 'Optional[str]'
   - 100% test coverage required
   - Google-style docstrings
   - pytest-asyncio for async tests

Please start by summarizing the issues you found, then fix them systematically."

echo ""
echo -e "${GREEN}✅ Cline has completed analysis${NC}"
echo ""
echo -e "${CYAN}📋 Next steps:${NC}"
echo "  1. Review the changes Cline made"
echo "  2. Run validation: ./scripts/validate-package.sh $PACKAGE"
echo "  3. Run tests: uv run pytest packages/$PACKAGE/tests/ -v"
echo "  4. If satisfied, commit: git add -p && git commit"
echo ""
echo -e "${CYAN}📄 Validation report: $TEMP_FILE${NC}"
