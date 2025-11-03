# TTA KB Automation - Agent Instructions

**Automated knowledge base maintenance for AI agents**

---

## 🎯 Quick Start for Agents

### What is KB Automation?

**The KB automation package helps you:**

1. **Build context with minimal input** - Get relevant KB pages, code, TODOs automatically
2. **Document as you build** - Auto-generate KB pages, flashcards, cross-references
3. **Maintain KB health** - Validate links, sync TODOs, find orphans
4. **Work efficiently** - Agents-first design, minimal context requirements

**Core principle:** Use these tools by default when working on TTA.dev.

---

## 🚀 Primary Workflows

### 1. Starting a Session (Build Synthetic Context)

**When:** Beginning work on a feature/bug/documentation

**What:** Build context from minimal input

**How:**

```python
from tta_kb_automation import build_session_context

# Agent provides minimal info (topic/task)
context = await build_session_context(
    topic="implement CachePrimitive timeout",
    include_related=True,
    max_depth=2
)

# Result: Everything you need
print(context.kb_pages)      # [[TTA Primitives/CachePrimitive]], related pages
print(context.code_files)    # cache.py, base primitives
print(context.todos)         # Related TODOs from journal
print(context.tests)         # Existing test files
print(context.summary)       # High-level overview
```

**Output:** You now have synthetic context without manually searching.

---

### 2. After Implementing a Feature

**When:** Completed code implementation

**What:** Auto-document the work

**How:**

```python
from tta_kb_automation import document_feature

result = await document_feature(
    feature_name="TimeoutPrimitive",
    code_files=["packages/tta-dev-primitives/src/.../timeout.py"],
    test_files=["tests/unit/recovery/test_timeout.py"],
    generate_flashcards=True,
    create_kb_page=True
)

# Result: Documentation created
print(result.kb_page_path)    # New KB page created
print(result.flashcards)      # Flashcards generated
print(result.cross_refs)      # Links added to related pages
```

**Output:** KB is updated, learning materials created, cross-references added.

---

### 3. Before Committing (Validate KB)

**When:** Ready to commit changes

**What:** Ensure KB is consistent

**How:**

```python
from tta_kb_automation import pre_commit_validation

validation = await pre_commit_validation()

if not validation.passed:
    print("⚠️ KB issues found:")
    for issue in validation.errors:
        print(f"  - {issue}")

    # Fix issues before committing
else:
    print("✅ KB is healthy!")
```

**Output:** Confidence that KB links work, TODOs are synced, orphans addressed.

---

## 🛠️ Core Tools

### Link Validator

**Purpose:** Validate [[Wiki Links]] in KB

**When to use:**
- Before committing
- After adding new pages
- Weekly maintenance

**Usage:**

```python
from tta_kb_automation import LinkValidator

validator = LinkValidator(kb_path="logseq/")
result = await validator.validate()

# Check results
print(f"Broken links: {len(result['broken_links'])}")
print(f"Orphaned pages: {len(result['orphaned_pages'])}")

# Generate report
await validator.validate_and_report("kb_report.md")
```

**What it checks:**
- ✅ [[Page]] links resolve to existing pages
- ✅ Code file paths exist
- ✅ Bi-directional linking complete
- ✅ No orphaned pages

---

### TODO Sync

**Purpose:** Bridge code comments and KB

**When to use:**
- After adding # TODO: comments in code
- Daily/weekly to keep journal updated
- Finding work items across codebase

**Usage:**

```python
from tta_kb_automation import TODOSync

sync = TODOSync()
todos = await sync.scan_and_create(
    paths=["packages/tta-dev-primitives"],
    create_journal_entries=True
)

print(f"Found {len(todos)} TODOs")
print(f"Created {todos.created_count} journal entries")
```

**What it does:**
- Scans Python files for `# TODO:` comments
- Creates journal entries with proper tags
- Links to relevant KB pages
- Tracks completion status

---

### Cross-Reference Builder

**Purpose:** Suggest missing links between code ↔ KB

**When to use:**
- After implementing features
- During KB tightening sessions
- Finding related work

**Usage:**

```python
from tta_kb_automation import CrossReferenceBuilder

builder = CrossReferenceBuilder()
graph = await builder.build()

# Review suggestions
print("Code files needing KB links:")
for suggestion in graph.code_updates:
    print(f"  {suggestion.file}:{suggestion.line}")
    print(f"    Suggest: {suggestion.link}")

print("\nKB pages needing code refs:")
for suggestion in graph.kb_updates:
    print(f"  {suggestion.page}")
    print(f"    Suggest: {suggestion.code_ref}")
```

**What it suggests:**
- Code docstrings → KB page links
- KB pages → source code references
- Test files → implementation links

---

### Session Context Builder

**Purpose:** Generate synthetic context for agents

**When to use:**
- Starting any work session
- Minimal context available
- Need comprehensive overview

**Usage:**

```python
from tta_kb_automation import SessionContextBuilder

builder = SessionContextBuilder()
context = await builder.build(
    topic="add metrics to RouterPrimitive",
    include_examples=True
)

# Context is now available
print(context.summary)         # High-level overview
print(context.kb_pages)        # Relevant KB pages
print(context.code_examples)   # Working code patterns
print(context.related_todos)   # Connected work items
print(context.test_patterns)   # How to test this
```

**Benefits:**
- ✅ No manual KB searching
- ✅ No manual code browsing
- ✅ No manual TODO hunting
- ✅ Start working immediately

---

## 🧪 Testing KB Automation

### Running Tests

```bash
# Unit tests (fast, default)
uv run pytest packages/tta-kb-automation/tests/

# With coverage
uv run pytest packages/tta-kb-automation/tests/ --cov

# Integration tests (explicit opt-in)
uv run pytest packages/tta-kb-automation/tests/ -m integration
```

### Writing Tests

**Follow agentic testing best practices:**

```python
import pytest
from tta_kb_automation.tools import LinkValidator

@pytest.mark.asyncio
async def test_link_validator_detects_broken_links(tmp_path):
    """Test broken link detection with mock filesystem."""
    # Arrange
    kb_path = tmp_path / "logseq"
    (kb_path / "pages").mkdir(parents=True)
    (kb_path / "pages" / "A.md").write_text("[[Broken]]")

    # Act
    validator = LinkValidator(kb_path=kb_path)
    result = await validator.validate()

    # Assert
    assert len(result["broken_links"]) == 1
    assert result["broken_links"][0]["target"] == "Broken"
```

**Key patterns:**
- Use `tmp_path` for filesystem isolation
- Mock KB structure for unit tests
- Use real KB for integration tests
- 100% coverage required

---

## 🎨 Implementation Patterns

### Building Workflows with Primitives

**KB Automation uses TTA.dev primitives:**

```python
from tta_dev_primitives import SequentialPrimitive
from tta_kb_automation.core import (
    ParseLogseqPages,
    ExtractLinks,
    ValidateLinks,
    FindOrphanedPages,
)

# Compose workflow
workflow = (
    ParseLogseqPages() >>
    ExtractLinks() >>
    (ValidateLinks() | FindOrphanedPages()) >>
    GenerateReport()
)

# Execute
result = await workflow.execute({}, context)
```

**Benefits:**
- ✅ Composable (use >> and |)
- ✅ Observable (automatic tracing)
- ✅ Cacheable (wrap in CachePrimitive)
- ✅ Resilient (wrap in RetryPrimitive)

---

### Adding New Primitives

**When:** Need new KB operation

**How:**

```python
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives import WorkflowContext
from typing import Any

class MyNewPrimitive(InstrumentedPrimitive[dict, dict]):
    """Brief description of what it does."""

    def __init__(self, param: str) -> None:
        super().__init__(name="my_new_primitive")
        self.param = param

    async def _execute_impl(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation."""
        # Do work
        result = {"output": "value"}

        # Pass through input for composition
        return {**input_data, **result}
```

**Requirements:**
- Extend `InstrumentedPrimitive`
- Type hints for input/output
- Comprehensive docstrings
- 100% test coverage

---

### Adding New Tools

**When:** Need new high-level workflow

**How:**

```python
from tta_kb_automation.core import ParseLogseqPages, ExtractLinks
from tta_dev_primitives import WorkflowContext

class MyNewTool:
    """High-level tool composing primitives."""

    def __init__(self) -> None:
        # Build workflow
        self.workflow = ParseLogseqPages() >> ExtractLinks()

    async def execute(self) -> dict:
        """Run the tool."""
        context = WorkflowContext(workflow_id="my_tool")
        return await self.workflow.execute({}, context)
```

---

## 📚 Documentation Guidelines

### When to Create KB Pages

**Always create KB pages for:**
- New primitives
- New tools
- New workflows
- Integration guides

**KB page template:**

```markdown
# Tool/Primitive Name

**Brief one-line description**

## Purpose

Why this exists.

## Usage

\```python
# Code example
\```

## When to Use

- Use case 1
- Use case 2

## Related

- [[Related Page 1]]
- [[Related Page 2]]

## Examples

See: `examples/tool_usage.py`
```

---

### When to Add Flashcards

**Create flashcards for:**
- Key concepts (primitives, patterns)
- Common workflows
- Error solutions

**Flashcard template:**

```markdown
### What does LinkValidator do? #card

- Validates [[Wiki Links]] in KB
- Detects broken links
- Finds orphaned pages
- Generates reports

Related: [[TTA KB Automation/LinkValidator]]
```

---

## 🔄 Integration with TTA.dev

### Using in Other Packages

```python
# In your package
from tta_kb_automation import validate_kb_links

# Before committing
result = await validate_kb_links()
if result["total_broken"] > 0:
    print("⚠️ Fix broken KB links before commit")
```

### CI/CD Integration

```yaml
# .github/workflows/kb-validation.yml
- name: Validate KB
  run: |
    uv run python -m tta_kb_automation validate --all
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

uv run python -m tta_kb_automation pre-commit-check
if [ $? -ne 0 ]; then
    echo "❌ KB validation failed"
    exit 1
fi
```

---

## 🎯 Agent Decision Trees

### "Should I use KB Automation?"

**YES if:**
- ✅ Starting a new session (build context)
- ✅ Implementing a feature (document it)
- ✅ Before committing (validate KB)
- ✅ Finding related work (cross-refs)
- ✅ Syncing TODOs (code → journal)

**NO if:**
- ❌ Quick syntax fix (no KB impact)
- ❌ Trivial change (no docs needed)

### "Which tool should I use?"

**Flow:**

```
New session?
  └─> SessionContextBuilder

Implemented feature?
  └─> document_feature()

Adding KB pages?
  └─> LinkValidator

Adding TODOs in code?
  └─> TODOSync

Before commit?
  └─> pre_commit_validation()

Finding related work?
  └─> CrossReferenceBuilder
```

---

## ⚠️ Common Pitfalls

### ❌ Don't: Manual KB Maintenance

```python
# Bad: Manual link checking
for page in pages:
    for link in extract_links(page):
        if not page_exists(link):
            print(f"Broken: {link}")
```

### ✅ Do: Use LinkValidator

```python
# Good: Use automation
result = await LinkValidator().validate()
print(result["summary"])
```

---

### ❌ Don't: Forget KB After Implementation

```python
# Bad: Implement and move on
def new_feature():
    # Code here
    pass

# KB never updated, no links, no docs
```

### ✅ Do: Document Automatically

```python
# Good: Auto-document
await document_feature(
    feature_name="new_feature",
    code_files=["src/new_feature.py"],
    create_kb_page=True
)
```

---

## 🔗 Quick Links

- **Package README:** `packages/tta-kb-automation/README.md`
- **API Reference:** [[TTA.dev/API/tta-kb-automation]]
- **Examples:** `packages/tta-kb-automation/examples/`
- **Tests:** `packages/tta-kb-automation/tests/`
- **KB Page:** [[TTA.dev/Packages/tta-kb-automation]]

---

**Last Updated:** November 3, 2025
**Status:** 🚧 Phase 1 Implementation
**For:** AI Agents working on TTA.dev
