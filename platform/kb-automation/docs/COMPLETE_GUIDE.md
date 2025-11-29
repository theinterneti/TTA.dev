# TTA KB Automation - Complete Guide

**Automated knowledge base maintenance for TTA.dev**

---

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Concepts](#core-concepts)
4. [Tools Guide](#tools-guide)
5. [Integration Guide](#integration-guide)
6. [Advanced Usage](#advanced-usage)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is TTA KB Automation?

TTA KB Automation is a suite of tools and primitives that automate knowledge base maintenance for TTA.dev. It enables:

- **Automatic link validation** - Catch broken links before they're committed
- **TODO synchronization** - Extract TODOs from code into journal entries
- **Cross-reference building** - Map relationships between code and KB pages
- **Session context generation** - Create synthetic context for agents

### Why KB Automation?

**Problem:** Manual KB maintenance is error-prone and time-consuming.

**Solution:** Automate repetitive tasks using composable primitives.

**Benefits:**
- ✅ Always up-to-date KB
- ✅ Reduced manual effort
- ✅ Better documentation quality
- ✅ Agent-friendly workflows

### Architecture Philosophy

Built using TTA.dev's own primitives:
- **Composable** - Combine primitives for complex workflows
- **Observable** - OpenTelemetry tracing throughout
- **Testable** - 100% test coverage
- **Type-safe** - Full type annotations

**Meta-pattern:** Using TTA.dev to build TTA.dev.

---

## Getting Started

### Installation

```bash
# Install from local package
cd /path/to/TTA.dev
uv pip install -e packages/tta-kb-automation

# Verify installation
python -c "import tta_kb_automation; print(tta_kb_automation.__version__)"
```

### Quick Start: Validate KB Links

```python
import asyncio
from pathlib import Path
from tta_kb_automation.tools import LinkValidator
from tta_kb_automation import WorkflowContext

async def main():
    # Create validator
    validator = LinkValidator(
        kb_root=Path("logseq"),
        cache_results=True,
        retry_on_error=True
    )

    # Run validation
    context = WorkflowContext(workflow_id="quick-validation")
    result = await validator.execute({}, context)

    # Check results
    print(f"✅ Valid links: {result['stats']['valid_links']}")
    print(f"❌ Broken links: {result['stats']['broken_links']}")
    print(f"📄 Orphaned pages: {len(result['orphaned_pages'])}")

asyncio.run(main())
```

### Quick Start: Sync TODOs

```python
import asyncio
from pathlib import Path
from tta_kb_automation.tools import TODOSync
from tta_kb_automation import WorkflowContext

async def main():
    # Create TODO sync tool
    sync = TODOSync(
        codebase_root=Path("."),
        kb_root=Path("logseq"),
        auto_classify=True
    )

    # Run sync
    context = WorkflowContext(workflow_id="todo-sync")
    result = await sync.execute({}, context)

    # View results
    print(f"Found {result['total_todos']} TODOs")
    print(f"Journal entry: {result['journal_entry_path']}")

asyncio.run(main())
```

---

## Core Concepts

### Primitives

All automation is built from **primitives** - small, composable units:

```python
from tta_kb_automation import (
    ParseLogseqPages,    # Parse KB structure
    ExtractLinks,        # Find links in markdown
    ValidateLinks,       # Check link validity
    FindOrphanedPages,   # Find unreferenced pages
    ScanCodebase,        # Scan Python files
    ExtractTODOs,        # Find TODO comments
    ClassifyTODO,        # Categorize TODOs
    SuggestKBLinks,      # Suggest relevant KB pages
)
```

### Composition

Primitives compose using operators:

```python
# Sequential: output of each step → input of next
workflow = parse_pages >> extract_links >> validate_links

# Parallel: same input to all branches
workflow = validate_links | find_orphans

# Mixed: complex workflows
workflow = (
    parse_pages >>
    (extract_links | find_orphans) >>
    aggregate_results
)
```

### WorkflowContext

Every execution needs context:

```python
from tta_kb_automation import WorkflowContext

context = WorkflowContext(
    workflow_id="my-workflow",
    correlation_id="task-123",
    metadata={"package": "tta-kb-automation"}
)

result = await primitive.execute(input_data, context)
```

**Context provides:**
- Correlation IDs for tracing
- Metadata propagation
- Observability integration

### Tools

Tools are **composed primitives** for complete workflows:

| Tool | Purpose | Primitives Used |
|------|---------|-----------------|
| `LinkValidator` | Validate all KB links | Parse → Extract → (Validate \| FindOrphans) |
| `TODOSync` | Sync code TODOs to KB | Scan → Extract → Route → (Classify \| Suggest) → Create |
| `CrossRefBuilder` | Map code ↔ KB | Scan → Parse → Analyze → Link → Generate |
| `SessionContextBuilder` | Generate context | Parse → Analyze → Prioritize → Compose |

---

## Tools Guide

### LinkValidator

**Purpose:** Validate all links in KB, find orphaned pages.

**Usage:**

```python
from tta_kb_automation.tools import LinkValidator

validator = LinkValidator(
    kb_root=Path("logseq"),
    cache_results=True,          # Cache for performance
    retry_on_error=True,          # Retry failed validations
    timeout_seconds=60.0          # Timeout per file
)

result = await validator.execute({}, context)
```

**Output:**

```python
{
    'stats': {
        'total_pages': 150,
        'valid_links': 523,
        'broken_links': 3,
        'orphaned_pages': 2
    },
    'broken_links': [
        {'file': 'pages/Example.md', 'link': '[[Missing Page]]', 'line': 42}
    ],
    'orphaned_pages': [
        'pages/Old___Draft.md'
    ],
    'report': "# KB Validation Report\n..."
}
```

**CLI:**

```bash
# Run from command line
python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output report.md \
    --fail-on-broken
```

**In CI/CD:** See `.github/workflows/kb-validation.yml`

---

### TODOSync

**Purpose:** Extract TODOs from code, create journal entries.

**Usage:**

```python
from tta_kb_automation.tools import TODOSync

sync = TODOSync(
    codebase_root=Path("."),
    kb_root=Path("logseq"),
    auto_classify=True,           # Classify simple vs complex
    suggest_links=True,           # Suggest KB page links
    exclude_patterns=[            # Skip these directories
        "tests/",
        ".venv/",
        "__pycache__/"
    ]
)

result = await sync.execute({}, context)
```

**Output:**

```python
{
    'total_todos': 12,
    'simple_todos': 7,
    'complex_todos': 5,
    'journal_entry_path': 'logseq/journals/2025_11_03.md',
    'todos_by_package': {
        'tta-dev-primitives': 5,
        'tta-observability-integration': 3,
        'tta-kb-automation': 4
    }
}
```

**Generated Journal Entry:**

```markdown
## 🔍 Code TODOs Found (2025-11-03)

### Simple TODOs (7)

- TODO Fix typo in docstring #dev-todo
  type:: documentation
  priority:: low
  file:: packages/tta-dev-primitives/src/core/base.py
  line:: 42

### Complex TODOs (5)

- TODO Implement caching layer with TTL support #dev-todo
  type:: implementation
  priority:: high
  file:: packages/tta-kb-automation/src/primitives/kb_primitives.py
  line:: 156
  context:: Need to add LRU cache with time-based expiration
  suggested-kb:: [[TTA Primitives/CachePrimitive]], [[Performance Optimization]]
```

**CLI:**

```bash
# Run sync
python -m tta_kb_automation.tools.todo_sync \
    --codebase-root . \
    --kb-root logseq \
    --output journal
```

---

### CrossRefBuilder (Coming Soon)

**Purpose:** Build bidirectional links between code and KB.

**Planned Features:**
- Map docstrings to KB pages
- Find code examples in KB
- Generate "Referenced by" sections
- Create dependency graphs

**Preview:**

```python
from tta_kb_automation.tools import CrossRefBuilder

builder = CrossRefBuilder(
    codebase_root=Path("."),
    kb_root=Path("logseq")
)

result = await builder.execute({}, context)

# Output includes:
# - Code → KB mappings
# - KB → Code reverse links
# - Dependency graphs
# - Missing documentation alerts
```

---

### SessionContextBuilder (Coming Soon)

**Purpose:** Generate synthetic context for agents.

**Planned Features:**
- Analyze task requirements
- Find relevant KB pages
- Extract code examples
- Build focused context (< 100KB)

**Preview:**

```python
from tta_kb_automation.tools import SessionContextBuilder

builder = SessionContextBuilder(kb_root=Path("logseq"))

context_bundle = await builder.execute({
    'task': 'Implement retry primitive',
    'packages': ['tta-dev-primitives'],
    'max_context_size': 100_000  # bytes
}, context)

# Output includes:
# - Relevant KB pages
# - Similar implementations
# - Related TODOs
# - Testing patterns
```

---

## Integration Guide

### Pre-commit Hook

Automatically validate KB on commit:

```bash
# Install hook
ln -s ../../scripts/kb-validation-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Test it
echo "[[Broken Link]]" >> logseq/pages/Test.md
git add logseq/pages/Test.md
git commit -m "test"
# ❌ Hook catches broken link
```

### GitHub Actions

KB validation runs automatically on PRs and pushes.

**Jobs:**
- `kb-link-validation` - Validate all links
- `kb-orphan-detection` - Find orphaned pages
- `kb-structure-validation` - Check required pages
- `kb-todo-sync` - Check for new TODOs (PRs only)
- `kb-metrics` - Generate metrics (main branch)

**See:** `.github/workflows/kb-validation.yml`

### VS Code Tasks

Add to `.vscode/tasks.json`:

```json
{
    "label": "🔍 Validate KB Links",
    "type": "shell",
    "command": "uv run python -m tta_kb_automation.tools.link_validator --kb-root logseq --output kb-report.md",
    "group": "test"
},
{
    "label": "📝 Sync TODOs to KB",
    "type": "shell",
    "command": "uv run python -m tta_kb_automation.tools.todo_sync --codebase-root . --kb-root logseq",
    "group": "build"
}
```

### Daily Automation

Schedule daily KB maintenance:

```bash
# Add to crontab
0 3 * * * cd /path/to/TTA.dev && ./scripts/daily-kb-maintenance.sh
```

**Script template:**

```bash
#!/bin/bash
# scripts/daily-kb-maintenance.sh

set -e

echo "🔍 Running daily KB maintenance..."

# Validate links
uv run python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output logs/kb-validation-$(date +%Y%m%d).md

# Sync TODOs
uv run python -m tta_kb_automation.tools.todo_sync \
    --codebase-root . \
    --kb-root logseq

# Generate metrics
uv run python -m tta_kb_automation.tools.metrics \
    --kb-root logseq \
    --output logs/kb-metrics-$(date +%Y%m%d).json

echo "✅ KB maintenance complete"
```

---

## Advanced Usage

### Custom Primitives

Create your own KB automation primitives:

```python
from tta_kb_automation.primitives.base import InstrumentedPrimitive
from tta_kb_automation import WorkflowContext
from pathlib import Path

class CustomKBPrimitive(InstrumentedPrimitive[dict, dict]):
    """Your custom KB operation."""

    def __init__(self, kb_root: Path):
        super().__init__(name="custom_kb_primitive")
        self.kb_root = kb_root

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Your logic here
        pages = list(self.kb_root.glob("pages/*.md"))

        return {
            "processed_pages": len(pages),
            "custom_metric": 42
        }
```

### Composing Custom Workflows

Build complex workflows from primitives:

```python
from tta_kb_automation import (
    ParseLogseqPages,
    ExtractLinks,
    ValidateLinks,
    FindOrphanedPages,
    WorkflowContext
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

# Add caching and retry to validation
cached_validator = CachePrimitive(
    primitive=ValidateLinks(kb_root=Path("logseq")),
    ttl_seconds=3600,
    cache_key_fn=lambda data, ctx: str(data.get('page', ''))
)

reliable_validator = RetryPrimitive(
    primitive=cached_validator,
    max_retries=3,
    backoff_strategy="exponential"
)

# Build workflow
workflow = (
    ParseLogseqPages(kb_root=Path("logseq")) >>
    ExtractLinks() >>
    reliable_validator >>
    FindOrphanedPages(kb_root=Path("logseq"))
)

# Execute
context = WorkflowContext(workflow_id="custom-validation")
result = await workflow.execute({}, context)
```

### Observability Integration

KB automation integrates with OpenTelemetry:

```python
from opentelemetry import trace
from tta_kb_automation.tools import LinkValidator

# Get tracer
tracer = trace.get_tracer(__name__)

# Operations are automatically traced
with tracer.start_as_current_span("kb-validation-job") as span:
    validator = LinkValidator(kb_root=Path("logseq"))
    result = await validator.execute({}, context)

    # Add custom attributes
    span.set_attribute("kb.broken_links", result['stats']['broken_links'])
    span.set_attribute("kb.orphaned_pages", len(result['orphaned_pages']))
```

**View traces in Jaeger:** http://localhost:16686

---

## Best Practices

### 1. Run Validation Before Commits

```bash
# Add to your workflow
git add logseq/
./scripts/kb-validation-hook.sh  # Manual check
git commit -m "Update KB"
```

### 2. Sync TODOs Weekly

```bash
# Monday morning routine
uv run python -m tta_kb_automation.tools.todo_sync \
    --codebase-root . \
    --kb-root logseq
```

Review generated journal entry, promote important TODOs to KB pages.

### 3. Monitor KB Metrics

Track KB health over time:

```python
from tta_kb_automation import ParseLogseqPages, WorkflowContext

async def track_metrics():
    parser = ParseLogseqPages(kb_root=Path("logseq"))
    result = await parser.execute({}, WorkflowContext())

    pages = result['pages']

    metrics = {
        'total_pages': len(pages),
        'journals': len([p for p in pages if 'journals' in str(p)]),
        'knowledge_pages': len([p for p in pages if 'journals' not in str(p)])
    }

    # Send to your metrics system
    # prometheus_client.gauge('kb_total_pages').set(metrics['total_pages'])
```

### 4. Keep KB Structure Clean

**Do:**
- ✅ Use consistent naming: `Category___Page Name.md`
- ✅ Link liberally: `[[Related Page]]`
- ✅ Add tags: `#dev-todo`, `#learning-todo`
- ✅ Update journals daily

**Don't:**
- ❌ Create orphaned pages
- ❌ Use broken links
- ❌ Duplicate content
- ❌ Skip TODO sync

### 5. Document with KB Links

In code, reference KB pages:

```python
class RetryPrimitive(WorkflowPrimitive):
    """
    Retry failed operations with exponential backoff.

    See KB: [[TTA Primitives/RetryPrimitive]]
    Examples: [[Learning TTA Primitives]]
    """
```

Tools like `CrossRefBuilder` can extract these references.

---

## Troubleshooting

### Issue: "Module not found: tta_kb_automation"

**Solution:**

```bash
# Install package
cd /path/to/TTA.dev
uv pip install -e packages/tta-kb-automation

# Verify
python -c "import tta_kb_automation"
```

### Issue: "Broken links detected"

**Solution:**

```bash
# Get full report
uv run python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output report.md

# Review report.md
cat report.md

# Fix broken links in KB files
```

### Issue: "Pre-commit hook failing"

**Debug:**

```bash
# Run hook manually
./scripts/kb-validation-hook.sh

# Check what files are staged
git diff --cached --name-only

# Skip hook (not recommended)
git commit --no-verify
```

### Issue: "TODO sync not finding TODOs"

**Debug:**

```python
from tta_kb_automation import ScanCodebase, ExtractTODOs, WorkflowContext
from pathlib import Path

async def debug_todos():
    # Scan codebase
    scanner = ScanCodebase(
        root=Path("."),
        patterns=["**/*.py"],
        exclude=["tests/", ".venv/"]
    )

    result = await scanner.execute({}, WorkflowContext())
    print(f"Found {len(result['files'])} Python files")

    # Extract TODOs
    extractor = ExtractTODOs()
    for file in result['files'][:5]:
        todos_result = await extractor.execute(
            {'file_path': file},
            WorkflowContext()
        )
        print(f"{file}: {len(todos_result['todos'])} TODOs")
```

### Issue: "Performance is slow"

**Solutions:**

1. **Enable caching:**

```python
from tta_dev_primitives.performance import CachePrimitive

cached_primitive = CachePrimitive(
    primitive=your_primitive,
    ttl_seconds=3600
)
```

2. **Process in parallel:**

```python
from tta_dev_primitives import ParallelPrimitive

parallel_workflow = (
    scanner >>
    ParallelPrimitive([processor1, processor2, processor3]) >>
    aggregator
)
```

3. **Exclude unnecessary directories:**

```python
scanner = ScanCodebase(
    root=Path("."),
    exclude=[
        "tests/",
        ".venv/",
        "htmlcov/",
        ".pytest_cache/",
        "node_modules/"
    ]
)
```

---

## Next Steps

### Learn More

- 📖 [Package README](../README.md) - API reference
- 🤖 [Agent Guide](../AGENTS.md) - For AI agents
- 🎯 [Examples](../examples/) - Working code examples
- 📊 [Architecture](../../docs/architecture/KB_AUTOMATION.md) - Design decisions

### Contribute

- 🐛 [Report Issues](https://github.com/theinterneti/TTA.dev/issues)
- 💡 [Suggest Features](https://github.com/theinterneti/TTA.dev/discussions)
- 🔧 [Submit PRs](https://github.com/theinterneti/TTA.dev/pulls)

### Get Help

- 💬 [Discussions](https://github.com/theinterneti/TTA.dev/discussions)
- 📧 Email: support@tta.dev

---

**Last Updated:** November 3, 2025
**Version:** 0.1.0
**License:** MIT
