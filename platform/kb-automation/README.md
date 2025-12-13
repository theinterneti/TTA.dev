# TTA KB Automation

**Automated knowledge base maintenance and documentation generation for TTA.dev**

## 🎯 Purpose

This package provides **automated KB operations** that enable:

- **Agent-first documentation** - Agents use these tools by default
- **Minimal context requirements** - KB provides synthetic session context
- **Automatic maintenance** - Links, TODOs, cross-refs stay up-to-date
- **Discoverable patterns** - Agents learn from KB, build better docs

**Vision:** Agents that automatically document as they build, using minimal context, producing high-quality KB that serves future agents and users.

---

## 🏗️ Architecture

### Built with TTA.dev Primitives

All automation uses TTA.dev's primitives for:
- Composition (Sequential, Parallel)
- Recovery (Retry, Fallback, Timeout)
- Performance (Cache)
- Observability (Instrumented)

**Meta-pattern:** Using TTA.dev to build TTA.dev.

### Core Primitives

```python
from tta_kb_automation import (
    # KB Operations
    ParseLogseqPages,
    ExtractLinks,
    ValidateLinks,
    FindOrphanedPages,

    # Code Operations
    ScanCodebase,
    ParseDocstrings,
    ExtractTODOs,
    AnalyzeCodeStructure,

    # Intelligence
    ClassifyTODO,
    SuggestKBLinks,
    GenerateFlashcards,

    # Integration
    CreateJournalEntry,
    UpdateKBPage,
    GenerateReport
)
```

---

## 🚀 Quick Start for Agents

### 1. Validate KB Links

```python
from tta_kb_automation import validate_kb_links

# Validate all links in KB
result = await validate_kb_links()

# Output: Report with broken links, orphaned pages
print(result.broken_links)
print(result.suggestions)
```

### 2. Sync Code TODOs to Journal

```python
from tta_kb_automation import sync_code_todos

# Scan codebase for # TODO: comments
todos = await sync_code_todos(
    paths=["packages/tta-dev-primitives"],
    create_journal_entries=True
)

# Output: Journal entries created with KB links
print(f"Found {len(todos)} TODOs")
```

### 3. Build Cross-Reference Graph

```python
from tta_kb_automation import build_cross_references

# Analyze code ↔ KB relationships
graph = await build_cross_references()

# Output: Missing links, suggestions
print(graph.missing_code_refs)
print(graph.missing_kb_refs)
```

---

## 📦 Installation

```bash
# Install in monorepo
cd packages/tta-kb-automation
uv sync --all-extras

# Or use from other packages
uv add tta-kb-automation
```

---

## 🎯 Primary Use Cases

### For AI Agents

**1. Starting a Session (Build Synthetic Context)**

```python
from tta_kb_automation import build_session_context

# Agent gets relevant context automatically
context = await build_session_context(
    topic="CachePrimitive",
    include_related=True,
    max_depth=2
)

# Returns: KB pages, code files, tests, TODOs
print(context.kb_pages)      # Relevant KB pages
print(context.code_files)    # Implementation files
print(context.todos)         # Related TODOs
print(context.tests)         # Test files
```

**2. After Implementing a Feature**

```python
from tta_kb_automation import document_feature

# Agent auto-documents implementation
result = await document_feature(
    feature_name="TimeoutPrimitive",
    code_files=["packages/tta-dev-primitives/src/.../timeout.py"],
    test_files=["tests/unit/recovery/test_timeout.py"],
    generate_flashcards=True,
    create_kb_page=True
)

# Output: KB page created, flashcards generated, links added
```

**3. Validating Before Commit**

```python
from tta_kb_automation import pre_commit_validation

# Agent validates KB consistency
validation = await pre_commit_validation()

if not validation.passed:
    print(validation.errors)
    # Fix issues before committing
```

### For CI/CD

**GitHub Actions Integration:**

```yaml
# .github/workflows/kb-validation.yml
- name: Validate KB
  run: |
    uv run python -m tta_kb_automation validate --all

- name: Generate KB Report
  run: |
    uv run python -m tta_kb_automation report --output docs/kb-report.html
```

---

## 🎓 Tools & Workflows

### 1. Link Validator

**Validates KB integrity:**
- `[[Page]]` links resolve
- Code file paths exist
- Bi-directional linking complete
- No orphaned pages

**Usage:**

```bash
# Command line
uv run python -m tta_kb_automation validate-links

# Python API
from tta_kb_automation import LinkValidator

validator = LinkValidator()
result = await validator.validate()
```

**Output:**

```json
{
  "broken_links": [
    {
      "source": "pages/TTA Primitives.md",
      "target": "[[NonExistentPage]]",
      "line": 42
    }
  ],
  "orphaned_pages": ["pages/Old Feature.md"],
  "missing_bidirectional": [
    {
      "from": "Page A",
      "to": "Page B",
      "missing_direction": "B -> A"
    }
  ]
}
```

---

### 2. TODO Sync

**Bridges code comments and KB:**
- Finds `# TODO:` in code
- Creates journal entries
- Links to relevant KB pages
- Tracks completion

**Usage:**

```bash
# Command line
uv run python -m tta_kb_automation sync-todos --path packages/

# Python API
from tta_kb_automation import TODOSync

sync = TODOSync()
todos = await sync.scan_and_create(paths=["packages/"])
```

**Output:**

```markdown
## [[2025-11-03]] Auto-Generated TODOs

- TODO Add timeout support to CachePrimitive #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]
  source:: packages/tta-dev-primitives/src/.../cache.py:127
  context:: "Consider adding timeout parameter for cache operations"
```

---

### 3. Cross-Reference Builder

**Suggests missing links:**
- Analyzes code ↔ KB relationships
- Detects missing references
- Generates suggestions
- Creates visual graph

**Usage:**

```bash
# Command line
uv run python -m tta_kb_automation build-cross-refs --graph

# Python API
from tta_kb_automation import CrossReferenceBuilder

builder = CrossReferenceBuilder()
graph = await builder.build()
```

**Output:**

```json
{
  "suggestions": {
    "code_updates": [
      {
        "file": "cache.py",
        "line": 10,
        "suggestion": "Add KB link: [[TTA Primitives/CachePrimitive]]"
      }
    ],
    "kb_updates": [
      {
        "page": "TTA Primitives/CachePrimitive.md",
        "suggestion": "Add code reference: packages/.../cache.py"
      }
    ]
  },
  "graph": "docs/kb-graph.svg"
}
```

---

### 4. Session Context Builder

**Provides synthetic context for agents:**
- Relevant KB pages
- Related code files
- Connected TODOs
- Test files

**Usage:**

```python
from tta_kb_automation import SessionContextBuilder

builder = SessionContextBuilder()
context = await builder.build(
    topic="implement retry logic",
    include_examples=True
)

# Agent gets everything needed to start
print(context.summary)           # High-level overview
print(context.kb_pages)          # Relevant pages
print(context.code_examples)     # Working code
print(context.related_todos)     # Connected work
print(context.test_patterns)     # Testing approaches
```

---

## 🏗️ Implementation Architecture

### Primitive-Based Design

```python
# Example: Link Validator implementation
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

class LinkValidator:
    def __init__(self):
        # Build workflow with primitives
        self.workflow = (
            ParseLogseqPages() >>           # Step 1: Parse
            ExtractLinks() >>               # Step 2: Extract
            (                               # Step 3: Parallel validation
                ValidatePageLinks() |
                ValidateCodePaths() |
                CheckBidirectional()
            ) >>
            GenerateReport()                # Step 4: Report
        )

        # Add caching for performance
        self.cached_workflow = CachePrimitive(
            self.workflow,
            ttl=3600
        )

    async def validate(self):
        from tta_dev_primitives import WorkflowContext
        context = WorkflowContext(workflow_id="kb_link_validation")
        return await self.cached_workflow.execute({}, context)
```

---

## 🧪 Testing

All tools follow **agentic testing best practices:**

```python
# Unit tests (fast, default)
def test_link_validator_detects_broken_links():
    """Test link validator with mocked filesystem."""
    mock_fs = {
        "pages/A.md": "[[B]]",  # B doesn't exist
        "pages/C.md": "[[A]]"
    }

    validator = LinkValidator(filesystem=mock_fs)
    result = validator.validate()

    assert "B" in result.broken_links
    assert len(result.orphaned_pages) == 0

# Integration tests (explicit opt-in)
@pytest.mark.integration
async def test_todo_sync_with_real_codebase():
    """Test TODO sync with actual Git repo."""
    sync = TODOSync()
    todos = await sync.scan_and_create(paths=["packages/tta-dev-primitives"])

    assert len(todos) > 0
    # Verify journal entries created
```

**Coverage Target:** 100% for all primitives

---

## 🎯 Design Principles

1. **Agent-First** - Designed for AI agents to use by default
2. **Minimal Context** - Agents don't need to remember patterns
3. **Self-Documenting** - Output includes usage examples
4. **Primitive-Based** - Built with TTA.dev primitives
5. **Observable** - OpenTelemetry tracing throughout
6. **Testable** - 100% coverage, unit + integration
7. **Fail Gracefully** - Retry, fallback, timeout patterns

---

## 🔗 Integration Points

### VS Code Tasks

```json
{
  "label": "🔗 Validate KB Links",
  "type": "shell",
  "command": "uv run python -m tta_kb_automation validate-links"
}
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
uv run python -m tta_kb_automation pre-commit-check
```

### CI/CD

```yaml
# .github/workflows/kb-validation.yml
jobs:
  validate-kb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate KB
        run: uv run python -m tta_kb_automation validate --all
```

---

## 📚 Documentation

- **KB Page:** [[TTA.dev/Packages/tta-kb-automation]]
- **API Reference:** `docs/api/tta-kb-automation.md`
- **Examples:** `examples/kb_automation_usage.py`
- **Agent Guide:** [[TTA.dev/Guides/KB Automation for Agents]]

---

## 🎓 Learning Materials

### For Agents

**When to use KB Automation:**

- ✅ Starting a new session (build context)
- ✅ After implementing a feature (document it)
- ✅ Before committing (validate KB)
- ✅ Finding related work (cross-references)
- ✅ Creating TODOs (sync with code)

### For Users

**Benefits:**

- 📚 Always up-to-date documentation
- 🔗 No broken links
- ✅ TODOs tracked automatically
- 🎓 Learning materials generated
- 🤖 Agents maintain consistency

---

## 🚀 Roadmap

**Phase 1 (Week 1):** ✅ Foundation
- [x] Package structure
- [x] Link Validator
- [x] TODO Sync
- [x] Basic testing

**Phase 2 (Week 2):** Cross-References
- [ ] Cross-Reference Builder
- [ ] Session Context Builder
- [ ] CI/CD integration

**Phase 3 (Week 3):** Intelligence
- [ ] LLM-based classification
- [ ] Flashcard generation
- [ ] Documentation drift detection

**Phase 4 (Ongoing):** Enhancement
- [ ] Quality metrics dashboard
- [ ] Visual graph generation
- [ ] Auto-fix suggestions

---

## 🔧 Development

```bash
# Run tests
uv run pytest packages/tta-kb-automation/tests/

# Run specific tool
uv run python -m tta_kb_automation validate-links

# Development mode
cd packages/tta-kb-automation
uv sync --all-extras
uv run pytest -v
```

---

## 🤝 Contributing

See [[TTA.dev/Guides/KB Automation Development]] for:
- Adding new primitives
- Creating new tools
- Testing patterns
- Integration guidelines

---

**Last Updated:** November 3, 2025
**Status:** 🚧 In Development - Phase 1
**Maintainer:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Platform/Kb-automation/Readme]]
