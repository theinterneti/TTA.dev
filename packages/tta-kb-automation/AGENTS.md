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

### 1. Starting a Session (Manual Context Building)

**When:** Beginning work on a feature/bug/documentation

**What:** Build context using available tools

**How:**

```python
from tta_kb_automation.tools import LinkValidator, TODOSync, CrossReferenceBuilder
from pathlib import Path

# Step 1: Validate KB health
validator = LinkValidator(kb_path=Path("logseq/"))
kb_health = await validator.validate()
print(f"KB Health Score: {kb_health['stats']['health_score']:.2f}")

# Step 2: Find related TODOs
todo_sync = TODOSync(
    code_paths=[Path("packages/tta-dev-primitives/src")],
    kb_path=Path("logseq/")
)
todos = await todo_sync.scan()
relevant_todos = [t for t in todos if "CachePrimitive" in t['text']]
print(f"Found {len(relevant_todos)} related TODOs")

# Step 3: Check cross-references
xref_builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)
xrefs = await xref_builder.build()
print(f"Bidirectional links: {xrefs['stats']['bidirectional_links']}")

# Now you have context:
# - KB health status
# - Related work items
# - Code ↔ KB connections
```

**Note:** SessionContextBuilder (automated context generation) is planned but not yet implemented. Use manual workflow above for now.

**Output:** You now have comprehensive context about KB state, related work, and cross-references.

---

### 2. After Implementing a Feature

**When:** Completed code implementation

**What:** Validate references and sync TODOs

**How:**

```python
from tta_kb_automation.tools import CrossReferenceBuilder, TODOSync
from pathlib import Path

# Step 1: Check if code references KB (or should)
xref_builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)
xrefs = await xref_builder.build()

# Find your new file
new_file = "packages/tta-dev-primitives/src/.../timeout.py"
if new_file in xrefs['code_files_missing_kb']:
    suggestions = xrefs['code_files_missing_kb'][new_file]
    print(f"Consider adding KB links: {suggestions['suggested_pages']}")

# Step 2: Sync any TODOs from implementation
todo_sync = TODOSync(
    code_paths=[Path("packages/tta-dev-primitives/src")],
    kb_path=Path("logseq/")
)
todos = await todo_sync.scan()
await todo_sync.create_journal_entries(todos)
print(f"Synced {len(todos)} TODOs to journal")

# Step 3: Manually create KB page if needed
# - Add to logseq/pages/TTA Primitives___TimeoutPrimitive.md
# - Link to implementation: `timeout.py`
# - Reference in related pages

print("✅ Code implemented, references checked, TODOs synced")
```

**Note:** Automatic KB page generation (planned feature) is not yet implemented. Create KB pages manually following TTA.dev patterns.

**Output:** Code ↔ KB references validated, TODOs synced to journal.

---

### 3. Before Committing (Validate KB)

**When:** Ready to commit changes

**What:** Ensure KB is consistent

**How:**

```python
from tta_kb_automation.tools import LinkValidator
from pathlib import Path

# Run full KB validation
validator = LinkValidator(kb_path=Path("logseq/"))
result = await validator.validate()

# Check health
health_score = result['stats']['health_score']
if health_score < 0.8:
    print(f"⚠️ KB health: {health_score:.2%}")
    print(f"Broken links: {len(result['broken_links'])}")
    print(f"Orphaned pages: {len(result['orphaned_pages'])}")

    # Review issues
    for broken in result['broken_links'][:5]:  # Show first 5
        print(f"  {broken['source']}: [[{broken['target']]}")

    # Generate full report
    report = await validator.generate_report(result)
    Path("kb_validation_report.md").write_text(report)
    print("Full report: kb_validation_report.md")
else:
    print(f"✅ KB is healthy! ({health_score:.2%})")

# Decision
if len(result['broken_links']) > 0:
    print("\n⚠️ Fix broken links before committing")
else:
    print("\n✅ Safe to commit")
```

**Output:** Confidence that KB links work, no new broken references introduced.

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

**Status:** ✅ Implemented and tested

**When to use:**
- Before committing (always!)
- After adding new pages
- Weekly KB health checks
- After refactoring/moving files

**Usage:**

```python
from tta_kb_automation.tools import LinkValidator
from pathlib import Path

# Initialize
validator = LinkValidator(kb_path=Path("logseq/"))

# Validate KB
result = await validator.validate()

# Check results
print(f"Total links: {result['stats']['total_links']}")
print(f"Valid links: {result['stats']['valid_links']}")
print(f"Broken links: {len(result['broken_links'])}")
print(f"Orphaned pages: {len(result['orphaned_pages'])}")

# View broken links
for broken in result['broken_links']:
    print(f"  {broken['source']}: [[{broken['target']]}")

# View orphans
for orphan in result['orphaned_pages']:
    print(f"  {orphan['path']} (no incoming links)")

# Generate detailed report
report = await validator.generate_report(result)
Path("kb_validation_report.md").write_text(report)
```

**What it checks:**
- ✅ `[[Page]]` links resolve to existing pages
- ✅ `[[Namespace/Page]]` hierarchical links
- ✅ `[[Page___Subpage]]` underscore notation
- ✅ Code file path references (`` `file.py` ``)
- ✅ Orphaned pages (no incoming links)
- ✅ Missing pages (linked but don't exist)

**Output structure:**

```python
{
    "broken_links": [
        {
            "source": "pages/A.md",
            "target": "NonExistent",
            "line": 5,
            "context": "See [[NonExistent]] for details"
        }
    ],
    "valid_links": [
        {
            "source": "pages/A.md",
            "target": "B",
            "resolved_path": "pages/B.md"
        }
    ],
    "orphaned_pages": [
        {
            "path": "pages/Unused.md",
            "title": "Unused Page"
        }
    ],
    "stats": {
        "total_links": 1500,
        "valid_links": 1200,
        "broken_links": 300,
        "orphaned_pages": 5,
        "health_score": 0.80  # (valid - broken) / total
    }
}
```

**See:** [[TTA KB Automation/LinkValidator]] for complete documentation

---

### TODO Sync

**Purpose:** Bridge code comments and KB journal system

**Status:** ✅ Implemented and tested

**When to use:**
- After adding `# TODO:` comments in code
- Daily/weekly to keep journal updated
- Finding all work items across codebase
- Syncing code TODOs to Logseq

**Usage:**

```python
from tta_kb_automation.tools import TODOSync
from pathlib import Path

# Initialize
sync = TODOSync(
    code_paths=[Path("packages/tta-dev-primitives/src")],
    kb_path=Path("logseq/"),
    auto_classify=True  # Automatically classify as dev/learning/ops
)

# Scan for TODOs
todos = await sync.scan()

print(f"Found {len(todos)} TODOs across {len(set(t['file'] for t in todos))} files")

# Create journal entries
created = await sync.create_journal_entries(
    todos=todos,
    date="2025-11-03"  # Optional, defaults to today
)

print(f"Created {len(created)} new journal entries")

# Get classification breakdown
from collections import Counter
by_type = Counter(t['type'] for t in todos)
print(f"Development: {by_type['dev-todo']}")
print(f"Learning: {by_type['learning-todo']}")
print(f"Operations: {by_type['ops-todo']}")
```

**What it does:**
- ✅ Scans Python files for `# TODO:` comments
- ✅ Extracts context (function/class name, line number)
- ✅ Auto-classifies as #dev-todo, #learning-todo, or #ops-todo
- ✅ Creates Logseq journal entries with proper formatting
- ✅ Links to relevant KB pages if mentioned
- ✅ Preserves file path and line number for traceability

**TODO Format Detection:**

```python
# Simple TODO
# TODO: Add caching support

# With classifier hints (priority)
# TODO[HIGH]: Fix memory leak in CachePrimitive

# With KB page reference
# TODO: Update [[TTA Primitives/CachePrimitive]] documentation

# With context
# TODO: Implement timeout (related to [[RetryPrimitive]])
```

**Output format:**

```python
{
    "file": "packages/tta-dev-primitives/src/.../cache.py",
    "line": 156,
    "text": "Add metrics for cache hit rate",
    "context": "class CachePrimitive",
    "type": "dev-todo",  # or learning-todo, ops-todo
    "priority": "medium",  # extracted from [HIGH], [MED], [LOW]
    "related_pages": ["TTA Primitives/CachePrimitive"]
}
```

**Journal entry format:**

```markdown
## TODOs from Code

- TODO Add metrics for cache hit rate #dev-todo
  file:: cache.py:156
  context:: CachePrimitive class
  related:: [[TTA Primitives/CachePrimitive]]
  priority:: medium
```

**See:** [[TTA KB Automation/TODO Sync]] for complete documentation

---

### Cross-Reference Builder

**Purpose:** Analyze and suggest missing links between code ↔ KB

**Status:** ✅ Implemented and tested

**When to use:**
- After implementing features
- During KB maintenance sessions
- Finding bidirectional reference gaps
- Improving code ↔ documentation links

**Usage:**

```python
from tta_kb_automation.tools import CrossReferenceBuilder
from pathlib import Path

# Initialize
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)

# Build cross-reference graph
graph = await builder.build()

# Review statistics
print("=== Cross-Reference Statistics ===")
print(f"KB pages analyzed: {graph['stats']['kb_pages']}")
print(f"Code files analyzed: {graph['stats']['code_files']}")
print(f"KB → Code references: {graph['stats']['kb_to_code_refs']}")
print(f"Code → KB references: {graph['stats']['code_to_kb_refs']}")
print(f"Bidirectional links: {graph['stats']['bidirectional_links']}")

# View KB pages missing code references
print("\n=== KB Pages Needing Code References ===")
for page, info in graph['kb_pages_missing_code'].items():
    print(f"\n{page}:")
    print(f"  Mentioned in code: {info['mentioned_in_code']}")
    print(f"  Has code refs: {info['has_code_refs']}")
    print(f"  Suggested refs: {info['suggested_refs']}")

# View code files missing KB links
print("\n=== Code Files Needing KB Links ===")
for file, info in graph['code_files_missing_kb'].items():
    print(f"\n{file}:")
    print(f"  Has KB mentions: {info['has_kb_mentions']}")
    print(f"  Suggested pages: {info['suggested_pages']}")

# Generate detailed report
report = await builder.generate_report(graph)
Path("cross_reference_report.md").write_text(report)
```

**What it detects:**

**KB → Code:**
- ✅ KB pages mentioning code files (`` `cache.py` ``)
- ✅ KB pages referencing classes/functions
- ✅ Missing implementation links in documentation

**Code → KB:**
- ✅ Docstrings with `See: [[Page]]` style links
- ✅ Comments mentioning KB pages
- ✅ Missing documentation links in code

**Bidirectional Analysis:**
- ✅ One-way references (code → KB but not KB → code)
- ✅ Complete bidirectional links (both directions)
- ✅ Orphaned references (link to non-existent targets)

**Output structure:**

```python
{
    "kb_pages_missing_code": {
        "pages/TTA Primitives/CachePrimitive.md": {
            "mentioned_in_code": ["cache.py", "test_cache.py"],
            "has_code_refs": False,
            "suggested_refs": [
                "packages/tta-dev-primitives/src/.../cache.py"
            ]
        }
    },
    "code_files_missing_kb": {
        "packages/tta-dev-primitives/src/.../cache.py": {
            "has_kb_mentions": ["CachePrimitive"],
            "suggested_pages": [
                "[[TTA Primitives/CachePrimitive]]"
            ]
        }
    },
    "stats": {
        "kb_pages": 150,
        "code_files": 45,
        "kb_to_code_refs": 87,
        "code_to_kb_refs": 62,
        "bidirectional_links": 34,
        "kb_orphans": 5,
        "code_orphans": 3
    }
}
```

**See:** [[TTA KB Automation/CrossReferenceBuilder]] for complete documentation

---

### Session Context Builder

**Purpose:** Generate synthetic context for agents (PLANNED)

**Status:** ⚠️ Stub implementation - Not yet functional

**When to use (planned):**
- Starting any work session
- Minimal context available
- Need comprehensive overview
- Onboarding new agents

**Planned Usage:**

```python
from tta_kb_automation.tools import SessionContextBuilder
from pathlib import Path

# Initialize
builder = SessionContextBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/"),
    max_files=20  # Limit context size
)

# Build context from minimal input
context = await builder.build_context(
    topic="CachePrimitive"
)

# Use generated context
print(f"Found {len(context['kb_pages'])} relevant KB pages")
print(f"Found {len(context['code_files'])} relevant code files")
print(f"Found {len(context['todos'])} related TODOs")

# Context structure
for page in context['kb_pages']:
    print(f"  {page['path']} (relevance: {page['relevance']})")

for code_file in context['code_files']:
    print(f"  {code_file['path']} ({code_file['type']})")
```

**Planned Features:**
- ✅ Automatic KB page discovery by topic
- ✅ Related code file detection
- ✅ TODO extraction from relevant files
- ✅ Cross-reference mapping
- ✅ Relevance scoring and ranking
- ✅ Size-bounded context (configurable max)

**Current Status:**
- ⚠️ Stub implementation exists (68 lines)
- ⚠️ Returns placeholder data
- ⚠️ Not integrated into workflows
- ⚠️ No tests written yet

**Implementation Plan:**
- Phase 1 (Week 1): Basic context aggregation
- Phase 2 (Week 2): Intelligent relevance scoring
- Phase 3 (Week 3): Advanced features (semantic search, LLM ranking)
- Phase 4 (Week 4): Agent workflow integration

**See:** [[TTA KB Automation/SessionContextBuilder]] for complete specification

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

## 📊 Current Implementation Status

### ✅ Implemented Tools
- **LinkValidator** - Full implementation with tests
- **TODO Sync** - Full implementation with tests
- **CrossReferenceBuilder** - Full implementation with tests

### ⚠️ Planned Tools
- **SessionContextBuilder** - Stub only, not yet functional

### 🧪 Test Coverage
- Unit tests: ✅ Complete
- Integration tests: ✅ Complete (4 end-to-end workflows)
- Coverage: ✅ High (all implemented tools)

### 📚 Documentation
- Tool-specific KB pages: ✅ Complete
- Agent guide (this file): ✅ Updated with real usage
- API documentation: ✅ Available in KB

---

**Last Updated:** November 3, 2025
**Status:** ✅ Phase 4 Complete (Integration tests, KB documentation, agent guides)
**For:** AI Agents working on TTA.dev
**Package Version:** 0.1.0
