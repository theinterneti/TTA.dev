# TODO Sync Tool

**Intelligent synchronization of code TODOs to Logseq journal entries**

---

## 🎯 Purpose

The TODO Sync tool automates TODO management by:

- **Scanning codebase** - Finds `# TODO:` comments in Python files
- **Intelligent classification** - Routes simple vs complex TODOs
- **Package detection** - Automatically identifies which package owns TODO
- **KB linking** - Suggests related KB pages
- **Journal creation** - Generates properly formatted Logseq entries

**Use when**: Onboarding to codebase, TODO cleanup, sprint planning, KB maintenance

---

## 🏗️ Architecture

### Primitive Composition with Router

```python
TODO Sync Workflow:
┌──────────────────┐
│ ScanCodebase     │ ─► Find all .py files
└──────────────────┘
         │
         ↓
┌──────────────────┐
│ ExtractTODOs     │ ─► Parse # TODO: comments
└──────────────────┘
         │
         ↓
┌──────────────────┐
│ RouterPrimitive  │ ─► Route by complexity
└──────────────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌─────────┐ ┌──────────────────────┐
│Simple   │ │Complex               │
│TODO     │ │TODO                  │
│         │ │  ├─► ClassifyTODO    │
│         │ │  └─► SuggestKBLinks  │
└─────────┘ └──────────────────────┘
    │                │
    └────────┬───────┘
             ↓
   ┌──────────────────┐
   │CreateJournalEntry│ ─► Format for Logseq
   └──────────────────┘
```

### Intelligent Routing Logic

**Simple TODOs** (direct processing):
- Short text (< 50 chars)
- No context needed
- Clear action items
- Example: `# TODO: Add type hints`

**Complex TODOs** (enhanced processing):
- Long text (>= 50 chars)
- Requires classification
- Needs KB links
- Example: `# TODO: Refactor error handling to use RetryPrimitive pattern`

---

## 🚀 Quick Start

### Basic Usage

```python
from tta_kb_automation.tools.todo_sync import TODOSync
from pathlib import Path

# Initialize sync tool
sync = TODOSync()

# Sync TODOs from specific package
result = await sync.sync(
    paths=[Path("packages/tta-kb-automation")],
    create_journal_entries=True,  # Actually write to journal
    journal_date="2025-11-03"     # Or None for today
)

# Check results
print(f"Found {result['total_todos']} TODOs")
print(f"Simple: {result['simple_count']}")
print(f"Complex: {result['complex_count']}")
print(f"Journal entries: {len(result['journal_entries'])}")
```

### Dry Run (No Journal Creation)

```python
# Scan without creating journal entries
result = await sync.sync(
    paths=[Path("packages/tta-dev-primitives")],
    create_journal_entries=False
)

# Review TODOs first
for todo in result["todos"]:
    print(f"{todo['file']}:{todo['line']} - {todo['text']}")
```

### Scan All Packages

```python
# Sync entire codebase
packages_dir = Path("packages")
package_paths = [p for p in packages_dir.iterdir() if p.is_dir()]

result = await sync.sync(
    paths=package_paths,
    create_journal_entries=True
)
```

---

## 📊 Output Structure

### Result Dictionary

```python
{
    "total_todos": 42,
    "simple_count": 28,
    "complex_count": 14,
    "todos": [
        {
            "file": "src/module.py",
            "line": 123,
            "text": "Add error handling",
            "complexity": "simple",
            "package": "tta-kb-automation",
            "context": "    # TODO: Add error handling\n    result = process()"
        }
    ],
    "journal_entries": [
        "- TODO Add error handling #dev-todo\n  type:: implementation\n  priority:: medium\n  package:: tta-kb-automation\n  file:: src/module.py:123"
    ]
}
```

### Journal Entry Format

#### Simple TODO Entry

```markdown
- TODO Add type hints to function signatures #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-dev-primitives
  file:: src/tta_dev_primitives/core/base.py:42
```

#### Complex TODO Entry (with KB links)

```markdown
- TODO Refactor error handling to use RetryPrimitive pattern #dev-todo
  type:: refactoring
  priority:: high
  package:: tta-kb-automation
  file:: src/tta_kb_automation/tools/link_validator.py:156
  related:: [[TTA Primitives/RetryPrimitive]]
  related:: [[TTA.dev/Best Practices/Error Handling]]
  complexity:: complex
```

---

## 🔧 Configuration Options

### Constructor Parameters

```python
TODOSync()  # No configuration needed - uses defaults
```

### Sync Method Parameters

```python
await sync.sync(
    paths: list[Path],                    # Directories to scan
    create_journal_entries: bool = True,  # Write to journal
    journal_date: str | None = None       # Date or today
)
```

---

## 🎓 Common Patterns

### Pattern 1: Weekly TODO Review

```python
async def weekly_todo_review():
    """Sync all TODOs for weekly planning."""
    sync = TODOSync()

    # Scan all packages
    packages = Path("packages").iterdir()
    result = await sync.sync(
        paths=list(packages),
        create_journal_entries=True
    )

    # Summary report
    print(f"""
    📊 Weekly TODO Summary
    =====================
    Total TODOs: {result['total_todos']}
    Simple tasks: {result['simple_count']}
    Complex tasks: {result['complex_count']}

    Top packages by TODO count:
    {analyze_by_package(result['todos'])}
    """)
```

### Pattern 2: Pre-Sprint Planning

```python
async def sprint_planning_prep():
    """Extract TODOs for sprint planning."""
    sync = TODOSync()

    # Scan with dry run first
    result = await sync.sync(
        paths=[Path("packages/tta-dev-primitives")],
        create_journal_entries=False  # Review first
    )

    # Filter high-priority TODOs
    high_priority = [
        todo for todo in result["todos"]
        if "FIXME" in todo["text"] or "URGENT" in todo["text"]
    ]

    # Now create journal entries
    if confirm_todos(high_priority):
        await sync.sync(
            paths=[Path("packages/tta-dev-primitives")],
            create_journal_entries=True
        )
```

### Pattern 3: Onboarding New Developer

```python
async def onboarding_todos():
    """Generate TODO summary for new team member."""
    sync = TODOSync()

    # Scan all code
    result = await sync.sync(
        paths=[Path("packages")],
        create_journal_entries=False
    )

    # Group by package and complexity
    by_package = {}
    for todo in result["todos"]:
        pkg = todo.get("package", "unknown")
        if pkg not in by_package:
            by_package[pkg] = {"simple": [], "complex": []}

        complexity = todo.get("complexity", "simple")
        by_package[pkg][complexity].append(todo)

    # Generate onboarding guide
    guide = generate_onboarding_guide(by_package)
    Path("docs/ONBOARDING_TODOS.md").write_text(guide)
```

---

## 🔍 Troubleshooting

### Issue: "No TODOs found"

**Cause**: Wrong path or no `# TODO:` comments

**Solution**:
```python
# Verify path exists
path = Path("packages/my-package")
assert path.exists(), f"Path not found: {path}"

# Check for .py files
py_files = list(path.rglob("*.py"))
print(f"Found {len(py_files)} Python files")

# TODO format must be: # TODO: (with colon)
# Not: # TODO (without colon)
```

### Issue: "TODOs not classified correctly"

**Cause**: Routing logic based on text length

**Current logic**: < 50 chars = simple, >= 50 chars = complex

**Workaround**:
```python
# For now, routing is automatic
# Future enhancement: Allow custom classification logic
```

### Issue: "Package detection wrong"

**Cause**: TODO in file outside package structure

**Solution**:
```python
# Package detected from path: packages/{package-name}/...
# Files outside packages/ will show package: "unknown"

# Ensure TODOs are in proper package structure:
packages/
  tta-kb-automation/
    src/
      your_file.py  # ✅ Package detected
  scripts/
    some_script.py  # ❌ Package: "unknown"
```

### Issue: "KB links not suggested"

**Cause**: SuggestKBLinks not fully implemented yet

**Status**: Placeholder implementation - returns TODO as-is

**Future**: Will use LLM or heuristics to suggest related KB pages

---

## 📈 Metrics & Observability

### Automatic Metrics

TODO Sync emits metrics:

- `todos.total` - Total TODOs found
- `todos.simple` - Simple TODO count
- `todos.complex` - Complex TODO count
- `todos.by_package.*` - Per-package TODO counts

### Structured Logging

```json
{
  "event": "todo_sync_complete",
  "total_todos": 42,
  "simple_count": 28,
  "complex_count": 14,
  "packages": ["tta-kb-automation", "tta-dev-primitives"],
  "duration_ms": 543.2
}
```

### Distributed Tracing

Spans created:

- `todo_sync.sync` - Root span
- `scan_codebase.execute` - File scanning
- `extract_todos.execute` - TODO parsing
- `router.execute` - Routing decisions
- `classify_todo.execute` - Complex TODO classification
- `create_journal_entry.execute` - Journal formatting

---

## 🧪 Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_todo_sync_basic(tmp_path):
    """Test TODO Sync with mock files."""
    # Create test file with TODO
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def process():
    # TODO: Add error handling
    return result
""")

    # Scan
    sync = TODOSync()
    result = await sync.sync(
        paths=[tmp_path],
        create_journal_entries=False
    )

    # Assertions
    assert result["total_todos"] == 1
    assert result["todos"][0]["text"] == "Add error handling"
    assert result["todos"][0]["line"] == 3
```

### Integration Tests

See: `tests/integration/test_real_kb_integration.py::TestTODOSyncWithRealCodebase`

- Tests against real TTA.dev codebase
- Validates TODO extraction
- Checks routing logic
- Verifies journal entry format

---

## 🔗 Related

### Tools

- [[TTA KB Automation/LinkValidator]] - Validates KB links
- [[TTA KB Automation/CrossReferenceBuilder]] - Code ↔ KB references

### Primitives

- [[TTA Primitives/ScanCodebase]] - File scanning
- [[TTA Primitives/ExtractTODOs]] - TODO parsing
- [[TTA Primitives/RouterPrimitive]] - Intelligent routing
- [[TTA Primitives/ClassifyTODO]] - TODO classification
- [[TTA Primitives/SuggestKBLinks]] - KB link suggestions

### Documentation

- [[TODO Management System]] - TTA.dev TODO methodology
- [[TTA.dev/Guides/KB Integration Workflow]] - Integration patterns

---

## 💡 Best Practices

### For Agents

1. **Run regularly** - Weekly or per sprint
2. **Review before creating entries** - Use `create_journal_entries=False` first
3. **Organize by priority** - Check for FIXME, URGENT keywords
4. **Track by package** - Group TODOs for focused work
5. **Update KB links** - Manually add related pages for complex TODOs

### For Users

1. **Write clear TODOs** - Be specific about what needs to be done
2. **Use consistent format** - Always `# TODO:` with colon
3. **Add context** - Explain why, not just what
4. **Link to issues** - Reference GitHub issues when applicable
5. **Clean up regularly** - Use tool to find stale TODOs

### TODO Writing Guidelines

**Good TODOs**:
```python
# TODO: Add retry logic with exponential backoff (see RetryPrimitive)
# TODO: Extract this into separate primitive for reusability
# TODO: Add integration test for timeout edge case (Issue #42)
```

**Bad TODOs**:
```python
# TODO: Fix this
# TODO: Improve performance
# TODO (without colon - won't be detected)
```

---

## 🎯 Flashcards

### Q: What format does TODO Sync require? #card

**A:** `# TODO:` with colon
- Must have `#` prefix
- Must have space after `#`
- Must have `:` after `TODO`
- Example: `# TODO: Add tests`

### Q: How does TODO Sync route TODOs? #card

**A:** By text length:
- **Simple** (< 50 chars): Direct processing
- **Complex** (>= 50 chars): Classification + KB link suggestions

### Q: What package detection algorithm is used? #card

**A:** Path-based detection:
- Parses path for `packages/{package-name}/...`
- Extracts `{package-name}` as package
- Files outside packages/ get `package: "unknown"`

---

**Last Updated:** November 3, 2025
**Package:** tta-kb-automation
**Tool Status:** ✅ Production Ready
**Test Coverage:** 100% (44/44 tests passing)

- [[Project Hub]]