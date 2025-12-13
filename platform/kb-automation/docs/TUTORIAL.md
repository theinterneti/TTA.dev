# TTA KB Automation Tutorial

**Learn KB automation through hands-on examples**

---

## Tutorial 1: First KB Validation (15 minutes)

### Goal

Learn to validate KB links and catch broken references.

### Prerequisites

- TTA.dev repository cloned
- Python 3.11+ installed
- `tta-kb-automation` package installed

### Steps

#### 1. Install the Package

```bash
cd /path/to/TTA.dev
uv pip install -e packages/tta-kb-automation
```

#### 2. Create Validation Script

Create `examples/tutorial_01_validation.py`:

```python
"""Tutorial 1: Basic KB Link Validation"""

import asyncio
from pathlib import Path
from tta_kb_automation.tools import LinkValidator
from tta_kb_automation import WorkflowContext


async def main():
    """Run link validation and display results."""

    print("🔍 Starting KB link validation...\n")

    # Create validator with default settings
    validator = LinkValidator(
        kb_root=Path("logseq"),
        cache_results=True,
        retry_on_error=True
    )

    # Create execution context
    context = WorkflowContext(
        workflow_id="tutorial-01",
        metadata={"tutorial": "link-validation"}
    )

    # Run validation
    result = await validator.execute({}, context)

    # Display results
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    stats = result['stats']
    print(f"✅ Total pages scanned: {stats['total_pages']}")
    print(f"✅ Valid links: {stats['valid_links']}")
    print(f"❌ Broken links: {stats['broken_links']}")
    print(f"📄 Orphaned pages: {len(result['orphaned_pages'])}")
    print()

    # Show broken links (if any)
    if result['broken_links']:
        print("BROKEN LINKS:")
        print("-" * 60)
        for broken in result['broken_links'][:10]:
            print(f"  File: {broken['file']}")
            print(f"  Link: {broken['link']}")
            print(f"  Line: {broken['line']}")
            print()

    # Show orphaned pages (if any)
    if result['orphaned_pages']:
        print("ORPHANED PAGES:")
        print("-" * 60)
        for page in result['orphaned_pages'][:10]:
            print(f"  - {page}")
        print()

    # Save report
    report_path = Path("kb-validation-report.md")
    report_path.write_text(result['report'])
    print(f"📄 Full report saved to: {report_path}")

    return result


if __name__ == "__main__":
    result = asyncio.run(main())

    # Exit with error if issues found
    if result['stats']['broken_links'] > 0:
        exit(1)
```

#### 3. Run the Script

```bash
cd /path/to/TTA.dev
uv run python examples/tutorial_01_validation.py
```

#### 4. Review Output

You should see:

```
🔍 Starting KB link validation...

============================================================
VALIDATION RESULTS
============================================================
✅ Total pages scanned: 150
✅ Valid links: 523
❌ Broken links: 0
📄 Orphaned pages: 0

📄 Full report saved to: kb-validation-report.md
```

#### 5. Understanding the Results

- **Total pages**: All `.md` files in `logseq/`
- **Valid links**: `[[Page]]` links that resolve correctly
- **Broken links**: Links to non-existent pages
- **Orphaned pages**: Pages with no incoming links

### Challenge

Create a broken link and see the validator catch it:

```bash
echo "Test page with [[Broken Link]]" > logseq/pages/Test___Tutorial.md
uv run python examples/tutorial_01_validation.py
# Should report 1 broken link
```

### What You Learned

- ✅ How to use `LinkValidator`
- ✅ How to interpret validation results
- ✅ How to generate reports
- ✅ How to integrate validation into workflows

---

## Tutorial 2: TODO Synchronization (20 minutes)

### Goal

Extract TODOs from code and sync them to KB journal entries.

### Steps

#### 1. Create TODO Sync Script

Create `examples/tutorial_02_todo_sync.py`:

```python
"""Tutorial 2: TODO Synchronization"""

import asyncio
from pathlib import Path
from datetime import datetime
from tta_kb_automation.tools import TODOSync
from tta_kb_automation import WorkflowContext


async def main():
    """Sync TODOs from code to KB journal."""

    print("🔍 Scanning codebase for TODOs...\n")

    # Create TODO sync tool
    sync = TODOSync(
        codebase_root=Path("."),
        kb_root=Path("logseq"),
        auto_classify=True,      # Classify simple vs complex
        suggest_links=True,       # Suggest KB page links
        exclude_patterns=[
            "tests/",
            ".venv/",
            "htmlcov/",
            ".pytest_cache/",
            "__pycache__/",
            "node_modules/"
        ]
    )

    # Create context
    context = WorkflowContext(
        workflow_id="tutorial-02",
        metadata={"date": datetime.now().isoformat()}
    )

    # Run sync
    result = await sync.execute({}, context)

    # Display results
    print("=" * 60)
    print("TODO SYNC RESULTS")
    print("=" * 60)
    print(f"📊 Total TODOs found: {result['total_todos']}")
    print(f"✅ Simple TODOs: {result['simple_todos']}")
    print(f"⚙️  Complex TODOs: {result['complex_todos']}")
    print()

    print("TODOs by Package:")
    print("-" * 60)
    for package, count in result['todos_by_package'].items():
        print(f"  {package}: {count} TODOs")
    print()

    print(f"📝 Journal entry created: {result['journal_entry_path']}")
    print()
    print("💡 Next steps:")
    print("  1. Review the generated journal entry")
    print("  2. Promote important TODOs to KB pages")
    print("  3. Update priority/status as needed")

    return result


if __name__ == "__main__":
    asyncio.run(main())
```

#### 2. Add Sample TODOs to Code

Create a test file with TODOs:

```python
# examples/test_todos.py
"""Sample file with TODOs for tutorial."""


def example_function():
    # TODO: Add input validation
    pass


def another_function():
    # TODO: Implement caching layer with LRU and TTL support
    # This is a complex task that requires:
    # - LRU eviction policy
    # - Time-based expiration
    # - Thread-safe access
    pass


# TODO: Add comprehensive test coverage
```

#### 3. Run TODO Sync

```bash
uv run python examples/tutorial_02_todo_sync.py
```

#### 4. Review Generated Journal

Open `logseq/journals/2025_11_03.md` and look for the TODO section:

```markdown
## 🔍 Code TODOs Found (2025-11-03)

### Simple TODOs (2)

- TODO Add input validation #dev-todo
  type:: implementation
  priority:: low
  file:: examples/test_todos.py
  line:: 6

- TODO Add comprehensive test coverage #dev-todo
  type:: testing
  priority:: medium
  file:: examples/test_todos.py
  line:: 19

### Complex TODOs (1)

- TODO Implement caching layer with LRU and TTL support #dev-todo
  type:: implementation
  priority:: high
  file:: examples/test_todos.py
  line:: 11
  context:: This is a complex task that requires: LRU eviction policy, Time-based expiration, Thread-safe access
  suggested-kb:: [[TTA Primitives/CachePrimitive]], [[Performance Optimization]]
```

### Understanding Classification

**Simple TODOs:**
- Short (< 50 chars)
- No context
- Single-line
- Priority: low/medium

**Complex TODOs:**
- Long or multi-line
- Includes context
- Technical requirements
- Priority: medium/high
- KB links suggested

### Challenge

Add more TODOs to your code and re-run sync. Notice:
- How classification changes
- Which KB pages are suggested
- How package detection works

### What You Learned

- ✅ How to use `TODOSync`
- ✅ How TODOs are classified
- ✅ How KB links are suggested
- ✅ How to integrate with daily journals

---

## Tutorial 3: Building Custom Workflows (30 minutes)

### Goal

Compose primitives into custom KB automation workflows.

### Steps

#### 1. Understanding Primitives

KB automation is built from small primitives:

```python
from tta_kb_automation import (
    ParseLogseqPages,    # Parse KB structure
    ExtractLinks,        # Find links
    ValidateLinks,       # Check validity
    FindOrphanedPages,   # Find unreferenced pages
)
```

#### 2. Sequential Composition

Create `examples/tutorial_03_custom_workflow.py`:

```python
"""Tutorial 3: Custom Workflow Composition"""

import asyncio
from pathlib import Path
from tta_kb_automation import (
    ParseLogseqPages,
    ExtractLinks,
    ValidateLinks,
    FindOrphanedPages,
    WorkflowContext
)


async def sequential_workflow():
    """Example: Sequential execution (step by step)."""

    print("🔄 Running sequential workflow...\n")

    kb_root = Path("logseq")
    context = WorkflowContext(workflow_id="sequential-demo")

    # Step 1: Parse pages
    print("Step 1: Parsing KB pages...")
    parser = ParseLogseqPages(kb_root=kb_root)
    parse_result = await parser.execute({}, context)
    print(f"  Found {len(parse_result['pages'])} pages\n")

    # Step 2: Extract links
    print("Step 2: Extracting links...")
    extractor = ExtractLinks()

    all_links = []
    for page in parse_result['pages'][:5]:  # First 5 for demo
        result = await extractor.execute({'page_path': page}, context)
        all_links.extend(result['links'])

    print(f"  Found {len(all_links)} links\n")

    # Step 3: Validate links
    print("Step 3: Validating links...")
    validator = ValidateLinks(kb_root=kb_root)

    broken = 0
    for link in all_links[:10]:  # First 10 for demo
        result = await validator.execute({'link': link}, context)
        if not result['valid']:
            broken += 1

    print(f"  Broken links: {broken}\n")

    return {"total_links": len(all_links), "broken": broken}


async def composed_workflow():
    """Example: Composed workflow using >> operator."""

    print("🔀 Running composed workflow...\n")

    kb_root = Path("logseq")

    # Compose primitives
    workflow = (
        ParseLogseqPages(kb_root=kb_root) >>
        ExtractLinks() >>
        ValidateLinks(kb_root=kb_root)
    )

    # Execute composed workflow
    context = WorkflowContext(workflow_id="composed-demo")
    result = await workflow.execute({}, context)

    print(f"Result: {result}\n")

    return result


async def parallel_workflow():
    """Example: Parallel execution using | operator."""

    print("⚡ Running parallel workflow...\n")

    kb_root = Path("logseq")

    # Parse pages once
    parser = ParseLogseqPages(kb_root=kb_root)
    context = WorkflowContext(workflow_id="parallel-demo")
    parse_result = await parser.execute({}, context)

    # Run validation and orphan detection in parallel
    from tta_dev_primitives import ParallelPrimitive

    parallel = ParallelPrimitive([
        ValidateLinks(kb_root=kb_root),
        FindOrphanedPages(kb_root=kb_root)
    ])

    # Both run concurrently
    results = await parallel.execute(parse_result, context)

    print(f"Validation result: {results[0]}")
    print(f"Orphan result: {results[1]}\n")

    return results


async def main():
    """Run all workflow examples."""

    print("=" * 60)
    print("CUSTOM WORKFLOW TUTORIAL")
    print("=" * 60)
    print()

    # Run sequential
    await sequential_workflow()

    # Run composed
    await composed_workflow()

    # Run parallel
    await parallel_workflow()

    print("=" * 60)
    print("✅ All workflows completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. Run the Workflow Examples

```bash
uv run python examples/tutorial_03_custom_workflow.py
```

#### 4. Understanding Composition

**Sequential (`>>`):**
- Output of each step → input of next
- Use for: pipelines, transformations

**Parallel (`|`):**
- Same input to all branches
- All run concurrently
- Use for: independent operations

**Mixed:**
```python
workflow = (
    parse >>
    (validate | find_orphans) >>
    aggregate
)
```

### Challenge

Create a workflow that:
1. Parses pages
2. Validates links AND finds orphans (parallel)
3. Generates a combined report

### What You Learned

- ✅ How to compose primitives
- ✅ Sequential vs parallel execution
- ✅ How to build custom workflows
- ✅ When to use each pattern

---

## Tutorial 4: Integration Testing (25 minutes)

### Goal

Write integration tests for KB automation workflows.

### Steps

#### 1. Create Test KB Structure

```bash
mkdir -p test_kb/pages
mkdir -p test_kb/journals

# Create test pages
cat > test_kb/pages/Home.md << 'EOF'
# Home

Welcome to test KB.

See [[Test Page]] and [[Another Page]].
EOF

cat > test_kb/pages/Test___Page.md << 'EOF'
# Test Page

This page links to [[Home]].
EOF

cat > test_kb/pages/Another___Page.md << 'EOF'
# Another Page

No links here.
EOF
```

#### 2. Create Integration Test

Create `examples/tutorial_04_integration_test.py`:

```python
"""Tutorial 4: Integration Testing"""

import asyncio
from pathlib import Path
import pytest
from tta_kb_automation.tools import LinkValidator
from tta_kb_automation import WorkflowContext


@pytest.mark.asyncio
async def test_link_validation_integration():
    """Test link validation with real KB structure."""

    # Use test KB
    validator = LinkValidator(
        kb_root=Path("test_kb"),
        cache_results=False  # Disable for testing
    )

    context = WorkflowContext(workflow_id="integration-test")
    result = await validator.execute({}, context)

    # Assertions
    assert result['stats']['total_pages'] == 3
    assert result['stats']['valid_links'] > 0
    assert result['stats']['broken_links'] == 0

    print("✅ Integration test passed!")


@pytest.mark.asyncio
async def test_broken_link_detection():
    """Test that broken links are detected."""

    # Add page with broken link
    test_page = Path("test_kb/pages/Broken___Links.md")
    test_page.write_text("# Broken\n\nLink to [[Nonexistent Page]]")

    try:
        validator = LinkValidator(kb_root=Path("test_kb"))
        context = WorkflowContext(workflow_id="broken-link-test")
        result = await validator.execute({}, context)

        # Should detect broken link
        assert result['stats']['broken_links'] == 1
        assert any('Nonexistent Page' in link['link']
                   for link in result['broken_links'])

        print("✅ Broken link detection test passed!")

    finally:
        # Cleanup
        test_page.unlink()


async def run_tests():
    """Run all integration tests."""

    print("=" * 60)
    print("INTEGRATION TESTS")
    print("=" * 60)
    print()

    await test_link_validation_integration()
    await test_broken_link_detection()

    print()
    print("=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())
```

#### 3. Run Tests

```bash
# Run with pytest
uv run pytest examples/tutorial_04_integration_test.py -v

# Or run directly
uv run python examples/tutorial_04_integration_test.py
```

### What You Learned

- ✅ How to write integration tests
- ✅ How to use test KB structures
- ✅ How to verify tool behavior
- ✅ How to test error conditions

---

## Next Steps

### Advanced Topics

1. **Custom Primitives** - Build your own KB operations
2. **Observability** - Add tracing and metrics
3. **Performance** - Optimize with caching and parallelism
4. **CI/CD Integration** - Automate in GitHub Actions

### Resources

- 📖 [Complete Guide](COMPLETE_GUIDE.md)
- 📖 [Package README](../README.md)
- 🤖 [Agent Guide](../AGENTS.md)
- 🔧 [API Reference](../src/tta_kb_automation/)

### Practice Projects

1. **KB Health Dashboard** - Build metrics visualization
2. **Auto-Documentation** - Generate KB pages from code
3. **Link Recommendation** - Suggest links for new pages
4. **TODO Prioritization** - ML-based priority inference

---

**Happy automating! 🚀**


---
**Logseq:** [[TTA.dev/Platform/Kb-automation/Docs/Tutorial]]
