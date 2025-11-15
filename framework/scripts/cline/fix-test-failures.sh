#!/bin/bash
# Smart Test Failure Analysis and Fixing with Cline CLI
#
# This script runs pytest and pipes failures to Cline for analysis and fixing.
#
# Usage:
#   ./scripts/cline/fix-test-failures.sh [MODE] [PACKAGE]
#
#   MODE: interactive (default) | autonomous
#   PACKAGE: specific package to test (optional)
#
# Examples:
#   ./scripts/cline/fix-test-failures.sh interactive tta-dev-primitives
#   ./scripts/cline/fix-test-failures.sh autonomous
#   ./scripts/cline/fix-test-failures.sh
#
# Modes:
#   interactive  - Cline shows diffs and asks for approval
#   autonomous   - Auto-fixes simple errors (imports, syntax)

set -e

MODE=${1:-interactive}
PACKAGE=${2:-}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Validate mode
if [[ "$MODE" != "interactive" && "$MODE" != "autonomous" ]]; then
  echo -e "${RED}❌ Invalid mode: $MODE${NC}"
  echo "Valid modes: interactive, autonomous"
  exit 1
fi

# Check cline CLI
if ! command -v cline &> /dev/null; then
  echo -e "${RED}❌ Cline CLI not found${NC}"
  echo "Install: npm install -g @cline/cli"
  exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Cline CLI: Smart Test Failure Analysis                   ║${NC}"
echo -e "${BLUE}║  Mode: ${MODE}${NC}"
if [ -n "$PACKAGE" ]; then
  echo -e "${BLUE}║  Package: ${PACKAGE}${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Build test command
if [ -n "$PACKAGE" ]; then
  TEST_PATH="packages/$PACKAGE/tests/"
  if [ ! -d "$TEST_PATH" ]; then
    echo -e "${RED}❌ Test directory not found: $TEST_PATH${NC}"
    exit 1
  fi
  TEST_CMD="uv run pytest $TEST_PATH --tb=short -v"
else
  TEST_CMD="uv run pytest --tb=short -v"
fi

# Run tests
echo -e "${CYAN}🧪 Running tests...${NC}"
echo "$ $TEST_CMD"
echo ""

TEST_OUTPUT=$($TEST_CMD 2>&1 || true)

# Check results
if echo "$TEST_OUTPUT" | grep -q "passed" && ! echo "$TEST_OUTPUT" | grep -q "failed"; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  echo ""
  echo "$TEST_OUTPUT" | tail -n 5
  exit 0
fi

if ! echo "$TEST_OUTPUT" | grep -q "failed"; then
  echo -e "${YELLOW}⚠️  No test failures, but tests didn't pass either${NC}"
  echo ""
  echo "$TEST_OUTPUT" | tail -n 20
  exit 1
fi

# Save output
TEMP_FILE="/tmp/test-failures-$(date +%s).txt"
echo "$TEST_OUTPUT" > "$TEMP_FILE"

echo -e "${YELLOW}❌ Test failures detected${NC}"
echo ""
echo "Failure summary:"
echo "$TEST_OUTPUT" | grep -E "(FAILED|ERROR|failed|error)" | head -n 10
echo ""
echo -e "${CYAN}📄 Full test output: $TEMP_FILE${NC}"
echo ""

# Different handling based on mode
if [ "$MODE" = "autonomous" ]; then
  echo -e "${CYAN}🤖 Autonomous Mode: Auto-fixing simple errors${NC}"
  echo ""
  echo "Will auto-fix:"
  echo "  - ImportError (missing imports)"
  echo "  - SyntaxError (syntax mistakes)"
  echo "  - NameError (undefined names)"
  echo "  - IndentationError (indentation issues)"
  echo ""

  # Extract simple errors
  SIMPLE_ERRORS=$(echo "$TEST_OUTPUT" | grep -E "(ImportError|SyntaxError|NameError|IndentationError)" || true)

  if [ -z "$SIMPLE_ERRORS" ]; then
    echo -e "${YELLOW}No simple errors found. Switching to interactive mode.${NC}"
    MODE="interactive"
  else
    echo "Simple errors found:"
    echo "$SIMPLE_ERRORS"
    echo ""

    echo "$SIMPLE_ERRORS" | cline -y "Fix these simple test errors automatically.

ERRORS:
$(cat)

INSTRUCTIONS:
1. Fix each error type:
   - ImportError: Add missing imports or fix import paths
   - SyntaxError: Fix syntax mistakes
   - NameError: Fix undefined variable names or add missing definitions
   - IndentationError: Fix indentation

2. After fixing:
   - Run tests again: $TEST_CMD
   - Verify fixes worked

3. Follow TTA.dev standards:
   - Use 'from package import X' not relative imports
   - Use 'str | None' not 'Optional[str]'

Please fix these errors and confirm tests pass."

    echo ""
    echo -e "${GREEN}✅ Auto-fix complete${NC}"
    exit 0
  fi
fi

# Interactive mode
echo -e "${CYAN}🤖 Interactive Mode: Detailed analysis and fixing${NC}"
echo ""
read -p "Send test failures to Cline for analysis? (y/n) " -n 1 -r
echo
if [[ ! $RRESPONSE =~ ^[Yy]$ ]]; then
  echo "Cancelled. Test output in: $TEMP_FILE"
  exit 0
fi

echo ""
echo -e "${CYAN}🔍 Cline is analyzing test failures...${NC}"
echo ""

cat "$TEMP_FILE" | cline "Analyze these test failures and help me fix them.

TEST OUTPUT:
$(cat)

CONTEXT:
- Repository: TTA.dev monorepo
- Package manager: uv (not pip)
- Python: 3.11+
- Testing: pytest with pytest-asyncio
- Follow .clinerules for standards

ANALYSIS NEEDED:
1. Categorize failures:
   - Logic errors (wrong implementation)
   - Missing test cases
   - Incorrect assertions
   - Type issues
   - Async handling problems
   - Import errors
   - Fixture issues

2. For each failure:
   - Identify root cause
   - Explain what's wrong
   - Show relevant code context
   - Propose specific fix
   - Estimate impact (isolated vs widespread)

3. Prioritize fixes:
   - Critical (breaks functionality)
   - Important (test quality issues)
   - Minor (formatting, etc.)

4. For each fix you propose:
   - Show me the diff
   - Explain the change
   - Wait for my approval
   - Apply the fix
   - Re-run relevant tests

5. After all fixes:
   - Run full test suite: $TEST_CMD
   - Confirm all failures resolved

WORKFLOW:
Please start by summarizing the failures and your analysis.
Then we'll fix them one by one or in logical groups.
Ask me questions if you need more context about the codebase."

echo ""
echo -e "${GREEN}✅ Analysis complete${NC}"
echo ""
echo -e "${CYAN}📋 Next steps:${NC}"
echo "  1. Review Cline's analysis and proposed fixes"
echo "  2. Apply fixes you approve"
echo "  3. Run tests: $TEST_CMD"
echo "  4. Iterate if needed"
echo ""
echo -e "${CYAN}📄 Test output: $TEMP_FILE${NC}"
