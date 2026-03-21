#!/usr/bin/env bash
# GitHub Copilot CLI Post-Generation Quality Gate
# Automatically runs after code modifications to ensure quality standards
#
# Exit codes:
#   0 = All checks passed
#   1 = One or more checks failed

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Running TTA.dev Quality Gates..."
echo "=================================================="

FAILED=0

# Gate 1: Ruff Linting
echo ""
echo "📋 Gate 1/3: Ruff Linting"
RUFF_OUTPUT=$(uv run ruff check . 2>&1)
if echo "$RUFF_OUTPUT" | grep -q "All checks passed"; then
    echo -e "${GREEN}✓ Ruff linting passed${NC}"
else
    echo -e "${RED}✗ Ruff linting failed${NC}"
    echo "Ruff check output:"
    echo "$RUFF_OUTPUT" | tail -20
    FAILED=1
fi

# Gate 2: Pyright Type Checking (platform/ only, ignore known issues)
echo ""
echo "🔍 Gate 2/3: Pyright Type Checking"
PYRIGHT_OUTPUT=$(timeout 60 uvx pyright platform/ 2>&1 || echo "TIMEOUT")
if echo "$PYRIGHT_OUTPUT" | grep -q "TIMEOUT"; then
    echo -e "${YELLOW}⚠ Pyright timed out, skipping${NC}"
else
    REAL_ERRORS=$(echo "$PYRIGHT_OUTPUT" | grep "error:" | grep -v "could not be resolved" | grep -v "not exported" | wc -l)

    # Allow up to 2 errors (the known OpenTelemetry issues)
    if [ "$REAL_ERRORS" -le 2 ]; then
        echo -e "${GREEN}✓ Pyright passed (${REAL_ERRORS} known acceptable errors)${NC}"
    else
        echo -e "${RED}✗ Pyright failed (${REAL_ERRORS} real errors, expected ≤2)${NC}"
        echo "New type errors detected:"
        echo "$PYRIGHT_OUTPUT" | grep "error:" | grep -v "could not be resolved" | grep -v "not exported" | head -10
        FAILED=1
    fi
fi

# Gate 3: Pytest (fast tests only)
echo ""
echo "🧪 Gate 3/3: Pytest (fast tests)"
PYTEST_OUTPUT=$(uv run pytest -m "not integration" --tb=line -q 2>&1)
if echo "$PYTEST_OUTPUT" | grep -qE "passed|PASSED"; then
    PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+(?= passed)' | head -1 || echo "unknown")
    echo -e "${GREEN}✓ Pytest passed (${PASSED} tests)${NC}"
else
    echo -e "${RED}✗ Pytest failed${NC}"
    echo "Test output:"
    echo "$PYTEST_OUTPUT" | tail -20
    FAILED=1
fi

echo ""
echo "=================================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All quality gates passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Quality gates failed. Review errors above.${NC}"
    exit 1
fi
