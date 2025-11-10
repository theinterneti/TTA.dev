# Agent Adoption Implementation Plan

**Systematic Implementation of AGENT_INTEGRATION_TECHNICAL_REPORT.md Recommendations**

**Date:** November 10, 2025
**Scope:** Transform TTA.dev from documentation-driven to validation-enforced agent adoption
**Goal:** Achieve deterministic agent usage of TTA.dev primitives without explicit prompting

---

## 🎯 Implementation Strategy

I will work through the recommendations in **dependency order** (not priority order) to ensure each layer builds on previous work:

### Phase 1: Foundation (Immediate - Hours)
**Goal:** Create scaffolding and reference materials

### Phase 2: Validation (Short-term - Days)
**Goal:** Implement automated checks and enforcement

### Phase 3: Integration (Long-term - Weeks)
**Goal:** Build IDE tooling and training systems

---

## 📋 Phase 1: Foundation (IMMEDIATE)

### 1.1 Quick Start for Agents
**File:** `AGENTS.md` (modify)
**Approach:**
```markdown
I will add a new section at the top of AGENTS.md:

## 🚀 Quick Start for AI Agents

**Before working on TTA.dev, always use primitives for:**
- Sequential workflows → `SequentialPrimitive` or `>>` operator
- Parallel execution → `ParallelPrimitive` or `|` operator
- Error handling → `RetryPrimitive`, `FallbackPrimitive`
- Caching → `CachePrimitive`
- Routing → `RouterPrimitive`

**Import pattern:**
```python
from tta_dev_primitives import (
    WorkflowPrimitive,
    SequentialPrimitive,
    WorkflowContext
)
```

**Validation:** Before committing, run `./scripts/validate-primitive-usage.sh`
```

**Why first:** Agents read AGENTS.md on session start - this gives immediate guidance

---

### 1.2 Agent Checklist
**File:** `.github/AGENT_CHECKLIST.md` (create new)
**Approach:**
```markdown
I will create a checklist that agents can self-verify against:

# Agent Pre-Commit Checklist

Before creating a PR, verify:

## ✅ Code Quality
- [ ] All async operations use TTA.dev primitives (not manual asyncio)
- [ ] Sequential workflows use `>>` operator
- [ ] Parallel workflows use `|` operator
- [ ] Error handling uses `RetryPrimitive` or `FallbackPrimitive`
- [ ] Expensive operations wrapped in `CachePrimitive`

## ✅ Testing
- [ ] Unit tests use `MockPrimitive` from `tta_dev_primitives.testing`
- [ ] Integration tests verify primitive composition
- [ ] Test coverage ≥ 90%

## ✅ Documentation
- [ ] Docstrings explain which primitives are used and why
- [ ] CHANGELOG.md updated with primitive usage patterns
- [ ] Examples added to `examples/` directory if new pattern

## ✅ Observability
- [ ] All workflows use `WorkflowContext` for tracing
- [ ] Custom primitives extend `InstrumentedPrimitive`
- [ ] Metrics tagged with primitive type

## ✅ Validation
- [ ] `uv run python scripts/validate-primitive-usage.py` passes
- [ ] No `asyncio.gather()` or `asyncio.create_task()` in new code
- [ ] No manual retry logic (use `RetryPrimitive`)
```

**Why second:** Provides concrete checklist agents can reference during development

---

### 1.3 Prompt Templates
**File:** `.vscode/tta-prompts.md` (create new)
**Approach:**
```markdown
I will create reusable prompt templates for common tasks:

# TTA.dev Prompt Templates

## Template: Sequential Workflow
```
Create a sequential workflow using TTA.dev primitives:

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

workflow = step1 >> step2 >> step3

context = WorkflowContext(correlation_id="task-123")
result = await workflow.execute(input_data, context)
```

Requirements:
- Use `>>` operator for composition
- Pass `WorkflowContext` for observability
- Each step returns output for next step
```

## Template: Error Handling
```
Add error handling using TTA.dev recovery primitives:

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

reliable_workflow = RetryPrimitive(
    primitive=primary_operation,
    max_retries=3,
    backoff_strategy="exponential"
)

with_fallback = FallbackPrimitive(
    primary=reliable_workflow,
    fallbacks=[backup_operation]
)
```

Requirements:
- Use `RetryPrimitive` for transient failures
- Use `FallbackPrimitive` for graceful degradation
- No manual try/except loops
```

These templates will be linked from copilot-instructions.md
```

**Why third:** Gives agents copy-paste starting points for common patterns

---

## 🔍 Phase 2: Validation (SHORT-TERM)

### 2.1 Pre-Commit Hook
**File:** `.git/hooks/pre-commit` (create)
**Approach:**
```bash
I will create a validation script that runs before commits:

#!/bin/bash
# TTA.dev Pre-Commit Validation

echo "🔍 Validating TTA.dev primitive usage..."

# Check for anti-patterns
python scripts/validate-primitive-usage.py

# Check for direct asyncio usage
if git diff --cached --name-only | grep -q "\.py$"; then
    if git diff --cached | grep -E "(asyncio\.gather|asyncio\.create_task|asyncio\.wait_for)" | grep -v "test_" | grep -v "# allowed"; then
        echo "❌ Direct asyncio usage detected. Use TTA.dev primitives instead."
        echo "   - asyncio.gather() → ParallelPrimitive or | operator"
        echo "   - asyncio.create_task() → ParallelPrimitive"
        echo "   - asyncio.wait_for() → TimeoutPrimitive"
        exit 1
    fi
fi

echo "✅ Pre-commit validation passed"
```

**Installation:** Add to `scripts/setup-git-hooks.sh` that runs during onboarding

**Why first in Phase 2:** Prevents anti-patterns from entering codebase

---

### 2.2 Primitive Usage Validator
**File:** `scripts/validate-primitive-usage.py` (create)
**Approach:**
```python
I will create an AST-based validator that detects primitive usage:

#!/usr/bin/env python3
"""Validate TTA.dev primitive usage in codebase."""

import ast
import sys
from pathlib import Path

class PrimitiveUsageChecker(ast.NodeVisitor):
    """Check for proper primitive usage."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def visit_AsyncWith(self, node):
        """Check for manual asyncio usage instead of TimeoutPrimitive."""
        if isinstance(node.items[0].context_expr, ast.Call):
            func = node.items[0].context_expr.func
            if isinstance(func, ast.Attribute):
                if func.attr == "wait_for":
                    self.warnings.append({
                        "line": node.lineno,
                        "message": "Consider using TimeoutPrimitive instead of asyncio.wait_for()",
                        "suggestion": "TimeoutPrimitive(primitive=..., timeout_seconds=...)"
                    })
        self.generic_visit(node)

    def visit_Call(self, node):
        """Check for direct asyncio.gather() instead of ParallelPrimitive."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "gather":
                self.warnings.append({
                    "line": node.lineno,
                    "message": "Consider using ParallelPrimitive instead of asyncio.gather()",
                    "suggestion": "ParallelPrimitive([...]) or primitive1 | primitive2"
                })
        self.generic_visit(node)

# Run validation on all Python files in packages/
# Return exit code 1 if errors found
```

**Why second:** Provides automated checking that pre-commit hook uses

---

### 2.3 Integration Tests
**File:** `tests/integration/test_agent_primitive_adoption.py` (create)
**Approach:**
```python
I will create tests that verify examples use primitives correctly:

"""Integration tests for agent primitive adoption."""

import ast
import pytest
from pathlib import Path

def test_examples_use_primitives():
    """Verify all examples use TTA.dev primitives."""
    examples_dir = Path("packages/tta-dev-primitives/examples")

    for example_file in examples_dir.glob("*.py"):
        if example_file.name.startswith("_"):
            continue

        content = example_file.read_text()
        tree = ast.parse(content)

        # Check for primitive imports
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        primitive_imports = [
            imp for imp in imports
            if imp.module and "tta_dev_primitives" in imp.module
        ]

        assert len(primitive_imports) > 0, (
            f"{example_file.name} should import from tta_dev_primitives"
        )

def test_no_direct_asyncio_in_examples():
    """Verify examples don't use asyncio directly."""
    examples_dir = Path("packages/tta-dev-primitives/examples")

    forbidden_patterns = ["asyncio.gather(", "asyncio.create_task("]

    for example_file in examples_dir.glob("*.py"):
        content = example_file.read_text()

        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"{example_file.name} uses {pattern} instead of primitives"
            )
```

**Why third:** Catches regressions in example code

---

## 🔧 Phase 3: Integration (LONG-TERM)

### 3.1 Custom Ruff Rules
**File:** `scripts/ruff_tta_dev_plugin.py` (create)
**Approach:**
```python
I will create custom Ruff linting rules for TTA.dev patterns:

"""Custom Ruff plugin for TTA.dev primitive usage."""

from ruff.rules import Rule

class PreferPrimitiveOverAsyncio(Rule):
    """Prefer TTA.dev primitives over direct asyncio usage."""

    code = "TTA001"
    message = "Use ParallelPrimitive instead of asyncio.gather()"

    def check(self, node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "gather":
                    return [self.error(node)]
        return []

class RequireWorkflowContext(Rule):
    """Require WorkflowContext in primitive execute() calls."""

    code = "TTA002"
    message = "Pass WorkflowContext to primitive.execute() for observability"

    def check(self, node):
        # Check for .execute() calls without context parameter
        pass

# Register with Ruff in pyproject.toml:
# [tool.ruff.lint.extend-per-file-ignores]
# Add TTA rules to selection
```

**Configuration:** Update `pyproject.toml` to enable TTA rules:
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "TTA"]

[tool.ruff.lint.extend-per-file-ignores]
"tests/*" = ["TTA001"]  # Allow asyncio in tests
```

**Why first in Phase 3:** Provides IDE-integrated linting

---

### 3.2 VS Code Extension
**File:** `vscode-extension/` (create new directory)
**Approach:**
```typescript
I will create a VS Code extension for primitive scaffolding:

// src/extension.ts
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // Command: Scaffold Sequential Workflow
    let scaffoldSequential = vscode.commands.registerCommand(
        'tta-dev.scaffoldSequential',
        () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                editor.insertSnippet(new vscode.SnippetString(`
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

workflow = \${1:step1} >> \${2:step2} >> \${3:step3}

context = WorkflowContext(correlation_id="\${4:task-id}")
result = await workflow.execute(\${5:input_data}, context)
                `));
            }
        }
    );

    // Command: Scaffold Parallel Workflow
    // Command: Add Retry Logic
    // Command: Add Caching

    context.subscriptions.push(scaffoldSequential);
}
```

**Features:**
- Code snippets for common patterns
- Quick fixes for detected anti-patterns
- IntelliSense for primitive composition
- Diagnostic warnings for missing WorkflowContext

**Why second:** Provides in-editor scaffolding and guidance

---

### 3.3 Agent Training Dataset
**File:** `datasets/agent-training/` (create new directory)
**Approach:**
```markdown
I will create a structured dataset for fine-tuning agent models:

datasets/agent-training/
├── examples/
│   ├── sequential_workflows.jsonl
│   ├── parallel_workflows.jsonl
│   ├── error_handling.jsonl
│   └── caching_patterns.jsonl
├── anti_patterns/
│   ├── manual_asyncio.jsonl
│   ├── missing_context.jsonl
│   └── direct_retry_loops.jsonl
└── corrections/
    ├── asyncio_to_primitive.jsonl
    └── add_context.jsonl

Each .jsonl file contains:
{
  "input": "User request or code snippet",
  "output": "Correct implementation using TTA.dev primitives",
  "explanation": "Why this pattern is preferred"
}

Example entry:
{
  "input": "Create a workflow that processes data through 3 steps sequentially",
  "output": "workflow = step1 >> step2 >> step3\nresult = await workflow.execute(data, context)",
  "explanation": "Using >> operator creates SequentialPrimitive automatically with built-in observability"
}
```

**Usage:** Fine-tune local models or create RAG index for agent context

**Why third:** Enables model-level learning of patterns

---

## 📊 Success Metrics

I will track these metrics to measure adoption success:

### Immediate (Phase 1)
- ✅ AGENTS.md includes Quick Start section
- ✅ `.github/AGENT_CHECKLIST.md` created
- ✅ `.vscode/tta-prompts.md` with 5+ templates
- 📈 **Goal:** Agents reference checklist in 80%+ of PRs

### Short-term (Phase 2)
- ✅ Pre-commit hook installed
- ✅ `validate-primitive-usage.py` catches 90%+ of anti-patterns
- ✅ Integration tests cover example code
- 📈 **Goal:** 0 anti-patterns in new PRs

### Long-term (Phase 3)
- ✅ Ruff plugin with 5+ TTA rules
- ✅ VS Code extension published
- ✅ Training dataset with 100+ examples
- 📈 **Goal:** Deterministic primitive usage without explicit prompting

---

## 🔄 Implementation Order

I will implement in this specific order to minimize rework:

1. **Day 1 (Foundation - 4 hours)**
   - [ ] Update AGENTS.md with Quick Start
   - [ ] Create AGENT_CHECKLIST.md
   - [ ] Create tta-prompts.md with templates
   - [ ] Link checklist from copilot-instructions.md

2. **Day 2-3 (Validation - 8 hours)**
   - [ ] Create validate-primitive-usage.py script
   - [ ] Create pre-commit hook
   - [ ] Add setup-git-hooks.sh installer
   - [ ] Create integration tests
   - [ ] Run validation on existing codebase

3. **Week 2 (Ruff Plugin - 16 hours)**
   - [ ] Research Ruff plugin architecture
   - [ ] Implement TTA001-TTA005 rules
   - [ ] Test on codebase
   - [ ] Update pyproject.toml
   - [ ] Document rules in docs/

4. **Week 3-4 (VS Code Extension - 32 hours)**
   - [ ] Scaffold extension project
   - [ ] Implement snippet commands
   - [ ] Add diagnostics provider
   - [ ] Add quick fixes
   - [ ] Test in VS Code
   - [ ] Publish to marketplace

5. **Week 5+ (Training Dataset - Ongoing)**
   - [ ] Extract patterns from examples/
   - [ ] Create anti-pattern examples
   - [ ] Generate corrections
   - [ ] Build RAG index
   - [ ] Fine-tune local model (optional)

---

## 🎯 How I Will Work

### Step-by-Step Process

For each recommendation, I will:

1. **Read Context:** Read relevant files (AGENTS.md, copilot-instructions.md, etc.)
2. **Create/Modify:** Implement the recommendation with proper formatting
3. **Validate:** Test the change (run scripts, check imports, verify syntax)
4. **Document:** Update this plan with completion status
5. **Report:** Provide summary of what was done and any issues

### Example: Implementing Quick Start Section

```
Step 1: Read AGENTS.md to understand current structure
Step 2: Add new "🚀 Quick Start for AI Agents" section at line 20
Step 3: Run `uv run ruff format AGENTS.md` to validate formatting
Step 4: Update this plan: "✅ Quick Start section added to AGENTS.md"
Step 5: Report: "Added 40-line Quick Start section with import patterns and validation reminder"
```

### Communication

I will:
- ✅ Report completion of each task
- ⚠️ Flag any blockers or decisions needed
- 💡 Suggest improvements discovered during implementation
- 📊 Provide metrics as milestones are reached

---

## 🚦 Decision Points

I will pause for your input at these decision points:

1. **After Phase 1 Complete:** Review foundation before moving to validation
2. **After validate-primitive-usage.py:** Review detected issues in existing code
3. **Before Ruff Plugin:** Confirm plugin architecture approach
4. **Before VS Code Extension:** Confirm feature set and UX
5. **Before Training Dataset:** Confirm model fine-tuning strategy

---

## 📝 Execution Prompt

**When you're ready for me to begin, say:**

> "Start with Phase 1: Foundation - implement Quick Start, Checklist, and Prompts"

**I will then:**
1. Read AGENTS.md and understand structure
2. Add Quick Start section with copy-paste examples
3. Create AGENT_CHECKLIST.md with verification steps
4. Create .vscode/tta-prompts.md with templates
5. Link checklist from copilot-instructions.md
6. Report completion with summary

**Estimated time:** 2-4 hours
**Output:** 3 new/modified files, all validated and formatted

---

## 🎓 Learning Outcomes

By completing this implementation plan, we will achieve:

1. **Immediate Guidance:** Agents know what to do on session start
2. **Automated Validation:** Pre-commit hooks prevent anti-patterns
3. **IDE Integration:** Real-time guidance during development
4. **Model Learning:** Fine-tuned models understand TTA.dev patterns
5. **Deterministic Adoption:** Agents use primitives by default, not by instruction

**Result:** Transform TTA.dev from "well-documented" to "automatically adopted"

---

**Ready to proceed?** Let me know which phase to start with!

**Questions?** Ask about any recommendation or approach before I begin.

**Modifications?** Suggest changes to the implementation order or strategy.
