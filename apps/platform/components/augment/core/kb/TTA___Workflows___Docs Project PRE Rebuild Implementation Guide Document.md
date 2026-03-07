---
title: Pre-Rebuild Infrastructure Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/project/PRE_REBUILD_IMPLEMENTATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Pre-Rebuild Infrastructure Implementation Guide]]

**Purpose:** Step-by-step guide for implementing Tier 1 infrastructure improvements
**Timeline:** 5-7 hours over 2 days
**Goal:** Accelerate 16-week hybrid rebuild with automated tooling

---

## Overview

This guide provides detailed implementation steps for the 3 critical pre-rebuild improvements:

1. **Gemini-Powered Test Generation** (2-3 hours)
2. **Gemini-Powered Requirements Extraction** (2-3 hours)
3. **Enhanced Pre-commit Hooks** (1 hour)

---

## Day 1: Test Generation + Pre-commit Hooks (3-4 hours)

### Part 1: Gemini-Powered Test Generation (2-3 hours)

#### Step 1.1: Create Test Generation Script (30 min)

**File:** `scripts/rewrite/generate_tests.sh`

```bash
#!/bin/bash
# Gemini-Powered Test Generation for TTA Component Rewrites
# Usage: ./scripts/rewrite/generate_tests.sh <source_file> <component_name>

set -e

SOURCE_FILE="$1"
COMPONENT_NAME="$2"

if [ -z "$SOURCE_FILE" ] || [ -z "$COMPONENT_NAME" ]; then
    echo "Usage: $0 <source_file> <component_name>"
    echo "Example: $0 src/agent_orchestration/agents.py agent_orchestration"
    exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Source file not found: $SOURCE_FILE"
    exit 1
fi

# Create output directory
OUTPUT_DIR="tests/${COMPONENT_NAME}/generated"
mkdir -p "$OUTPUT_DIR"

echo "🤖 Generating tests for $SOURCE_FILE using Gemini Flash..."

# Load prompt template
PROMPT=$(cat <<EOF
CONTEXT: Generating comprehensive pytest test cases for TTA component rewrite using TDD.

GOAL: Generate pytest test cases for the following Python code that achieve 70%+ coverage.

SOURCE CODE:
$(cat "$SOURCE_FILE")

REQUIREMENTS:
- Use pytest and pytest-asyncio for async code
- Cover all public methods and classes
- Include edge cases and error scenarios
- Use fixtures for common setup (create conftest.py if needed)
- Follow TTA testing patterns (see existing tests for examples)
- Aim for 70%+ code coverage
- Use descriptive test names (test_<method>_<scenario>)
- Include docstrings explaining what each test validates

OUTPUT FORMAT:
1. test_<module_name>.py with all test cases
2. conftest.py with fixtures (if needed)
3. Brief explanation of test strategy and coverage approach

Please generate complete, runnable test code.
EOF
)

# Call Gemini CLI
gemini -m gemini-2.0-flash-exp "$PROMPT" > "${OUTPUT_DIR}/gemini_output.txt"

echo "✅ Test generation complete!"
echo "📁 Output saved to: ${OUTPUT_DIR}/gemini_output.txt"
echo ""
echo "Next steps:"
echo "1. Review generated tests in ${OUTPUT_DIR}/gemini_output.txt"
echo "2. Extract test code to ${OUTPUT_DIR}/test_*.py"
echo "3. Run tests: uvx pytest ${OUTPUT_DIR}/ -v"
echo "4. Refine and move to final location"
```

**Make executable:**
```bash
chmod +x scripts/rewrite/generate_tests.sh
```

#### Step 1.2: Create Prompt Templates (15 min)

**File:** `scripts/rewrite/test_generation_prompts.md`

```markdown
# Gemini Test Generation Prompt Templates

## Basic Test Generation

\`\`\`
CONTEXT: Generating pytest test cases for TTA component rewrite.

GOAL: Generate comprehensive test cases for the following code.

CODE:
@{source_file}

REQUIREMENTS:
- pytest and pytest-asyncio
- 70%+ coverage
- Edge cases and error scenarios
- Descriptive test names
- Fixtures for common setup

OUTPUT: Complete test_*.py file
\`\`\`

## Test Generation with Existing Tests as Examples

\`\`\`
CONTEXT: Generating pytest test cases following TTA patterns.

GOAL: Generate test cases matching the style of existing tests.

EXISTING TEST EXAMPLES:
@{tests/existing/test_example.py}

NEW CODE TO TEST:
@{src/new/component.py}

REQUIREMENTS:
- Match existing test patterns
- Use same fixtures and utilities
- Follow same naming conventions
- Achieve 70%+ coverage

OUTPUT: Complete test file matching TTA patterns
\`\`\`

## Fixture Generation

\`\`\`
CONTEXT: Generating pytest fixtures for TTA component tests.

GOAL: Create conftest.py with reusable fixtures.

CODE TO TEST:
@{src/component.py}

REQUIREMENTS:
- Common test data fixtures
- Mock fixtures for dependencies
- Async fixtures for async code
- Cleanup fixtures (yield pattern)

OUTPUT: Complete conftest.py
\`\`\`
```

#### Step 1.3: Test the Tool (30 min)

```bash
# Test with existing component
./scripts/rewrite/generate_tests.sh \
    src/components/carbon_component.py \
    carbon

# Review output
cat tests/carbon/generated/gemini_output.txt

# Extract and run tests
# (Manual step - copy test code to test_carbon_generated.py)
uvx pytest tests/carbon/generated/ -v
```

#### Step 1.4: Create Usage Guide (15 min)

**File:** `docs/rewrite/test-generation-guide.md`

```markdown
# Test Generation Guide

## Quick Start

\`\`\`bash
# Generate tests for a component
./scripts/rewrite/generate_tests.sh src/component/file.py component_name

# Review generated tests
cat tests/component_name/generated/gemini_output.txt

# Extract test code to proper files
# (Manual review and extraction)

# Run tests
uvx pytest tests/component_name/generated/ -v
\`\`\`

## Best Practices

1. **Review Before Using:** Always review generated tests
2. **Refine Prompts:** Adjust prompts for better results
3. **Use Examples:** Provide existing tests as examples
4. **Iterate:** Generate, review, refine, regenerate
5. **Human Touch:** Add edge cases Gemini might miss

## Workflow

1. Generate initial tests with Gemini
2. Review for completeness and accuracy
3. Add missing edge cases
4. Run tests and check coverage
5. Refine until 70%+ coverage achieved
```

---

### Part 2: Enhanced Pre-commit Hooks (1 hour)

#### Step 2.1: Update Pre-commit Config (20 min)

**File:** `.pre-commit-config.yaml`

Add to the `repos` section:

```yaml
  # Stricter rules for rewritten components
  - repo: local
    hooks:
      # Prevent anti-patterns in new code
      - id: ruff-strict-new-code
        name: Ruff (strict) for rewritten components
        entry: bash -c 'uvx ruff check --select T201,PLC0415,S110,BLE001,ANN001,ANN201 "$@"' --
        language: system
        types: [python]
        files: ^src/(docker|agent_orchestration|player_experience)/.*\.py$

      # Require type annotations
      - id: require-type-annotations
        name: Require type annotations (new code)
        entry: python scripts/pre-commit/check-type-annotations.py
        language: system
        types: [python]
        files: ^src/(docker|agent_orchestration|player_experience)/.*\.py$
```

#### Step 2.2: Create Type Annotation Checker (30 min)

**File:** `scripts/pre-commit/check-type-annotations.py`

```python
#!/usr/bin/env python3
"""
Check that new code has proper type annotations.

Usage: python scripts/pre-commit/check-type-annotations.py <file1> <file2> ...
"""

import ast
import sys
from pathlib import Path


def check_function_annotations(node: ast.FunctionDef, filename: str) -> list[str]:
    """Check if function has proper type annotations."""
    errors = []

    # Skip private functions and test functions
    if node.name.startswith('_') or node.name.startswith('test_'):
        return errors

    # Check return annotation
    if node.returns is None and node.name != '__init__':
        errors.append(
            f"{filename}:{node.lineno}: Function '{node.name}' missing return type annotation"
        )

    # Check argument annotations
    for arg in node.args.args:
        if arg.arg == 'self' or arg.arg == 'cls':
            continue
        if arg.annotation is None:
            errors.append(
                f"{filename}:{node.lineno}: Argument '{arg.arg}' in '{node.name}' missing type annotation"
            )

    return errors


def check_file(filepath: Path) -> list[str]:
    """Check a single file for type annotation issues."""
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read(), filename=str(filepath))
    except SyntaxError as e:
        return [f"{filepath}: Syntax error: {e}"]

    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            errors.extend(check_function_annotations(node, str(filepath)))

    return errors


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: check-type-annotations.py <file1> <file2> ...")
        sys.exit(1)

    all_errors = []
    for filepath in sys.argv[1:]:
        errors = check_file(Path(filepath))
        all_errors.extend(errors)

    if all_errors:
        print("❌ Type annotation errors found:")
        for error in all_errors:
            print(f"  {error}")
        print(f"\nTotal: {len(all_errors)} errors")
        sys.exit(1)
    else:
        print("✅ All functions have proper type annotations")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x scripts/pre-commit/check-type-annotations.py
```

#### Step 2.3: Test Pre-commit Hooks (10 min)

```bash
# Install pre-commit hooks
uvx pre-commit install

# Test on sample file
echo 'def bad_function(x):
    print("test")
    return x' > /tmp/test_bad.py

# Run pre-commit on test file
uvx pre-commit run --files /tmp/test_bad.py

# Should fail with:
# - T201: print found
# - ANN001: Missing type annotation for x
# - ANN201: Missing return type annotation
```

---

## Day 2: Requirements Extraction (2-3 hours)

### Part 3: Gemini-Powered Requirements Extraction

#### Step 3.1: Create Requirements Extraction Script (45 min)

**File:** `scripts/rewrite/extract_requirements.sh`

```bash
#!/bin/bash
# Gemini-Powered Requirements Extraction for TTA Component Rewrites
# Usage: ./scripts/rewrite/extract_requirements.sh <component_dir> <component_name>

set -e

COMPONENT_DIR="$1"
COMPONENT_NAME="$2"

if [ -z "$COMPONENT_DIR" ] || [ -z "$COMPONENT_NAME" ]; then
    echo "Usage: $0 <component_dir> <component_name>"
    echo "Example: $0 src/agent_orchestration agent_orchestration"
    exit 1
fi

if [ ! -d "$COMPONENT_DIR" ]; then
    echo "Error: Component directory not found: $COMPONENT_DIR"
    exit 1
fi

# Create output directory
OUTPUT_DIR="docs/rewrite/${COMPONENT_NAME}"
mkdir -p "$OUTPUT_DIR"

echo "🤖 Extracting requirements for $COMPONENT_NAME using Gemini Flash..."

# Step 1: Functional Inventory
echo "📋 Step 1/3: Functional Inventory..."
INVENTORY_PROMPT=$(cat <<EOF
CONTEXT: Extracting requirements from existing TTA component for rewrite.

GOAL: Create a comprehensive functional inventory of all public APIs, classes, and functions.

COMPONENT CODE:
$(find "$COMPONENT_DIR" -name "*.py" -exec cat {} \;)

REQUIREMENTS:
- List all public classes with their purpose
- List all public functions/methods with signatures
- List all public constants and configuration
- Identify external dependencies
- Note integration points with other components

OUTPUT FORMAT: Markdown document with:
## Modules
- module1.py - Description

## Public Classes
- Class1 - Purpose, key methods

## Public Functions
- function1(args) -> return - Purpose

## External Dependencies
- dependency1 - Usage

## Integration Points
- integration1 - Description
EOF
)

gemini -m gemini-2.0-flash-exp "$INVENTORY_PROMPT" > "${OUTPUT_DIR}/functional_inventory.md"

# Step 2: Business Logic Extraction
echo "📋 Step 2/3: Business Logic Extraction..."
LOGIC_PROMPT=$(cat <<EOF
CONTEXT: Extracting business logic from existing TTA component.

GOAL: Document core workflows, validation rules, and business logic.

COMPONENT CODE:
$(find "$COMPONENT_DIR" -name "*.py" -exec cat {} \;)

REQUIREMENTS:
- Document main workflows (step-by-step)
- Identify validation rules and constraints
- Note state machines or business rules
- Document domain models and their relationships

OUTPUT FORMAT: Markdown document with:
## Core Workflows
### Workflow 1: [Name]
**Steps:**
1. Step 1
2. Step 2

**Validation Rules:**
- Rule 1
- Rule 2

## Domain Models
### Model 1
**Fields:** ...
**Constraints:** ...
EOF
)

gemini -m gemini-2.0-flash-exp "$LOGIC_PROMPT" > "${OUTPUT_DIR}/business_logic.md"

# Step 3: Edge Case Discovery
echo "📋 Step 3/3: Edge Case Discovery..."
EDGE_CASE_PROMPT=$(cat <<EOF
CONTEXT: Identifying edge cases from existing TTA component.

GOAL: Document error scenarios, boundary conditions, and special cases.

COMPONENT CODE:
$(find "$COMPONENT_DIR" -name "*.py" -exec cat {} \;)

REQUIREMENTS:
- Identify all error handling patterns
- Document boundary conditions
- Note special cases and exceptions
- List validation edge cases

OUTPUT FORMAT: Markdown document with:
## Error Scenarios
1. **Scenario:** Description
   - **Handling:** How it's handled
   - **Test:** Reference to test

## Boundary Conditions
1. **Condition:** Description
   - **Behavior:** Expected behavior
EOF
)

gemini -m gemini-2.0-flash-exp "$EDGE_CASE_PROMPT" > "${OUTPUT_DIR}/edge_cases.md"

echo "✅ Requirements extraction complete!"
echo "📁 Output saved to: ${OUTPUT_DIR}/"
echo ""
echo "Generated files:"
echo "  - ${OUTPUT_DIR}/functional_inventory.md"
echo "  - ${OUTPUT_DIR}/business_logic.md"
echo "  - ${OUTPUT_DIR}/edge_cases.md"
echo ""
echo "Next steps:"
echo "1. Review extracted requirements"
echo "2. Create feature parity checklist"
echo "3. Use as reference during rewrite"
```

**Make executable:**
```bash
chmod +x scripts/rewrite/extract_requirements.sh
```

#### Step 3.2: Test Requirements Extraction (30 min)

```bash
# Test with existing component
./scripts/rewrite/extract_requirements.sh \
    src/components \
    carbon

# Review outputs
cat docs/rewrite/carbon/functional_inventory.md
cat docs/rewrite/carbon/business_logic.md
cat docs/rewrite/carbon/edge_cases.md
```

#### Step 3.3: Create Usage Guide (15 min)

**File:** `docs/rewrite/requirements-extraction-guide.md`

```markdown
# Requirements Extraction Guide

## Quick Start

\`\`\`bash
# Extract requirements for a component
./scripts/rewrite/extract_requirements.sh src/component/ component_name

# Review extracted requirements
cat docs/rewrite/component_name/functional_inventory.md
cat docs/rewrite/component_name/business_logic.md
cat docs/rewrite/component_name/edge_cases.md
\`\`\`

## Workflow

1. **Extract:** Run extraction script
2. **Review:** Read generated documents
3. **Refine:** Add missing details manually
4. **Checklist:** Create feature parity checklist
5. **Reference:** Use during rewrite

## Best Practices

1. **Review Thoroughly:** Gemini may miss subtle details
2. **Cross-Reference:** Compare with existing tests
3. **Document Assumptions:** Note any assumptions made
4. **Update Checklist:** Keep feature parity checklist current
```

---

## Validation & Testing

### Test All Tools Together

```bash
# 1. Extract requirements
./scripts/rewrite/extract_requirements.sh src/components carbon

# 2. Generate tests
./scripts/rewrite/generate_tests.sh src/components/carbon_component.py carbon

# 3. Test pre-commit hooks
echo 'def test(): print("x")' > /tmp/test.py
uvx pre-commit run --files /tmp/test.py
```

### Success Criteria

✅ **Test Generation:**
- Generates 70%+ coverage tests
- Tests are runnable with minimal edits
- Follows TTA testing patterns

✅ **Requirements Extraction:**
- Captures 90%+ of functionality
- Documents all public APIs
- Identifies edge cases

✅ **Pre-commit Hooks:**
- Catches print statements
- Requires type annotations
- Prevents anti-patterns

---

## Next Steps

After completing these improvements:

1. ✅ **Validate tools work correctly**
2. ✅ **Document usage in team wiki**
3. ✅ **Start Week 1 of hybrid rebuild**
4. ✅ **Use tools throughout rewrite process**

**Estimated Time Saved:** 45-69 hours over 16-week rebuild
**ROI:** 6-10x on 5-7 hour investment


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs project pre rebuild implementation guide document]]
