#!/bin/bash
# Package Validation Script for TTA.dev
# Validates that a package meets all quality standards before merging

set -e  # Exit on any error

PACKAGE=$1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage check
if [ -z "$PACKAGE" ]; then
  echo -e "${RED}❌ Usage: ./scripts/validate-package.sh <package-name>${NC}"
  echo ""
  echo "Example: ./scripts/validate-package.sh tta-workflow-primitives"
  exit 1
fi

# Check if package directory exists
if [ ! -d "packages/$PACKAGE" ]; then
  echo -e "${RED}❌ Package not found: packages/$PACKAGE${NC}"
  exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    TTA.dev Package Validation: $PACKAGE${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Track overall status
VALIDATION_PASSED=true

# ========================================
# 1. Structure Validation
# ========================================
echo -e "${BLUE}📦 Checking package structure...${NC}"

required_files=(
  "packages/$PACKAGE/pyproject.toml"
  "packages/$PACKAGE/README.md"
  "packages/$PACKAGE/src"
  "packages/$PACKAGE/tests"
)

for file in "${required_files[@]}"; do
  if [ -e "$file" ]; then
    echo -e "${GREEN}  ✓${NC} Found: $file"
  else
    echo -e "${RED}  ✗${NC} Missing: $file"
    VALIDATION_PASSED=false
  fi
done

echo ""

# ========================================
# 2. Code Formatting (Ruff)
# ========================================
echo -e "${BLUE}✨ Running code formatter (Ruff)...${NC}"

if uv run ruff format packages/$PACKAGE/ --check; then
  echo -e "${GREEN}  ✓${NC} Code formatting is correct"
else
  echo -e "${YELLOW}  ⚠${NC}  Code formatting issues found. Running auto-fix..."
  uv run ruff format packages/$PACKAGE/
  echo -e "${GREEN}  ✓${NC} Code formatted"
fi

echo ""

# ========================================
# 3. Linting (Ruff)
# ========================================
echo -e "${BLUE}🔍 Running linter (Ruff)...${NC}"

if uv run ruff check packages/$PACKAGE/ --fix; then
  echo -e "${GREEN}  ✓${NC} No linting issues"
else
  echo -e "${RED}  ✗${NC} Linting issues found"
  VALIDATION_PASSED=false
fi

echo ""

# ========================================
# 4. Type Checking (Pyright)
# ========================================
echo -e "${BLUE}🔬 Running type checker (Pyright)...${NC}"

if uvx pyright packages/$PACKAGE/; then
  echo -e "${GREEN}  ✓${NC} Type checking passed"
else
  echo -e "${RED}  ✗${NC} Type checking failed"
  VALIDATION_PASSED=false
fi

echo ""

# ========================================
# 5. Tests
# ========================================
echo -e "${BLUE}🧪 Running tests...${NC}"

if [ -d "packages/$PACKAGE/tests" ]; then
  if uv run pytest packages/$PACKAGE/tests/ -v --tb=short; then
    echo -e "${GREEN}  ✓${NC} All tests passed"
  else
    echo -e "${RED}  ✗${NC} Tests failed"
    VALIDATION_PASSED=false
  fi
else
  echo -e "${YELLOW}  ⚠${NC}  No tests directory found"
fi

echo ""

# ========================================
# 6. Documentation Check
# ========================================
echo -e "${BLUE}📚 Checking documentation...${NC}"

# Check for README sections
if grep -q "## Features" packages/$PACKAGE/README.md 2>/dev/null; then
  echo -e "${GREEN}  ✓${NC} README has Features section"
else
  echo -e "${YELLOW}  ⚠${NC}  README missing Features section"
fi

if grep -q "## Installation" packages/$PACKAGE/README.md 2>/dev/null; then
  echo -e "${GREEN}  ✓${NC} README has Installation section"
else
  echo -e "${YELLOW}  ⚠${NC}  README missing Installation section"
fi

if grep -q "## Usage" packages/$PACKAGE/README.md 2>/dev/null || \
   grep -q "## Quick Start" packages/$PACKAGE/README.md 2>/dev/null; then
  echo -e "${GREEN}  ✓${NC} README has Usage/Quick Start section"
else
  echo -e "${YELLOW}  ⚠${NC}  README missing Usage section"
fi

echo ""

# ========================================
# 7. Security Check
# ========================================
echo -e "${BLUE}🔒 Running security checks...${NC}"

# Check for common secrets patterns
if grep -r -i -E "(api[_-]?key|password|secret|token)" packages/$PACKAGE/src/ --exclude-dir=__pycache__ | \
   grep -v -E "(test|mock|example|TODO|FIXME)" | grep -q .; then
  echo -e "${YELLOW}  ⚠${NC}  Potential secrets found (review manually)"
else
  echo -e "${GREEN}  ✓${NC} No obvious secrets found"
fi

# Check for hardcoded paths
if grep -r "/home/" packages/$PACKAGE/src/ --exclude-dir=__pycache__ | grep -q .; then
  echo -e "${YELLOW}  ⚠${NC}  Hardcoded absolute paths found"
  VALIDATION_PASSED=false
else
  echo -e "${GREEN}  ✓${NC} No hardcoded paths found"
fi

echo ""

# ========================================
# 8. Dependencies Check
# ========================================
echo -e "${BLUE}📦 Checking dependencies...${NC}"

if [ -f "packages/$PACKAGE/pyproject.toml" ]; then
  # Check for version pinning
  if grep -A 20 "\[project.dependencies\]" packages/$PACKAGE/pyproject.toml | \
     grep -q "=="; then
    echo -e "${YELLOW}  ⚠${NC}  Exact version pinning found (consider using >=)"
  else
    echo -e "${GREEN}  ✓${NC} Dependencies use flexible versioning"
  fi

  echo -e "${GREEN}  ✓${NC} pyproject.toml exists"
else
  echo -e "${RED}  ✗${NC} pyproject.toml not found"
  VALIDATION_PASSED=false
fi

echo ""

# ========================================
# Final Report
# ========================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ "$VALIDATION_PASSED" = true ]; then
  echo -e "${GREEN}║  ✅ VALIDATION PASSED - Package is ready for merge!       ║${NC}"
else
  echo -e "${RED}║  ❌ VALIDATION FAILED - Please fix issues above           ║${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = true ]; then
  exit 0
else
  exit 1
fi
