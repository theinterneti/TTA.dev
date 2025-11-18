# TTA.dev Scripts Directory

Automation scripts and utilities for TTA.dev development and operations.

## 📁 Organization

### Git Workflow Tools

- **`git_workflow_primitive.py`** - Local git state analysis using TTA.dev primitive patterns
  - Demonstrates ConditionalPrimitive, RouterPrimitive, and FallbackPrimitive
  - Analyzes local git state (staging, commits, branches)
  - Recommends appropriate git actions
  - Educational: Shows how TTA.dev patterns apply to non-AI workflows

### Development Tools

- **`validate-package.sh`** - Package validation script
- **`check-environment.sh`** - Environment verification
- **`test_fast.sh`** - Fast unit test runner
- **`test_integration.sh`** - Integration test runner

### Observability

- **`verify-and-setup-persistence.sh`** - Observability infrastructure verification

## 🎯 Using git_workflow_primitive.py

**Purpose:** Understand local git state and get actionable recommendations.

**When to use:**
- VS Code commit button is disabled
- Unsure what git operation to perform next
- Learning TTA.dev primitive decision patterns

**Example:**

```bash
python3 scripts/git_workflow_primitive.py
```

**Output:**

```
🎯 TTA.dev Git Workflow Primitive Demo

Analyzing with different primitive patterns:

1️⃣  Conditional Pattern (if/else):
   → push_current

2️⃣  Router Pattern (multi-way):
   → push_current

3️⃣  Fallback Pattern (try with alternatives):
   → push_current
   → Reason: Clean state, commits ready to push

============================================================
🌳 Git Workflow Decision Tree (TTA.dev Primitive Pattern)
============================================================

📊 Context:
   Branch: feature/my-feature
   Has changes: False
   Has staged: False
   Ahead of remote: True
   Behind remote: False

🎯 Decision: push_current
   Reason: Clean state, commits ready to push

🔀 Decision Path (Router Pattern):
   ├─ [IS_AHEAD] → Push or Create PR
============================================================

🚀 Pushing feature/my-feature to remote...
```

## 🔗 Related

- **GitHub API Operations:** See `packages/tta-dev-primitives/examples/orchestration_pr_review.py`
- **TTA.dev Primitives:** See `PRIMITIVES_CATALOG.md`
- **Workflow Patterns:** See `docs/architecture/PRIMITIVE_PATTERNS.md`

## 📝 Contributing

When adding new scripts:
1. Add proper documentation header
2. Update this README
3. Add to appropriate category
4. Include usage examples
