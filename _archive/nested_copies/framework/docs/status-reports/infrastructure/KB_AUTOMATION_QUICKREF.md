# KB Automation Quick Reference

**Fast lookup for common KB automation tasks**

---

## 🚀 Quick Start

### Run Integration Tests

```bash
# All integration tests
uv run pytest tests/integration/test_kb_automation_integration.py -v -m integration

# Specific test class
uv run pytest tests/integration/test_kb_automation_integration.py::TestRealCodebaseScanning -v

# With output
uv run pytest tests/integration/test_kb_automation_integration.py -v -s
```

### Run Demo Script

```bash
# Dry run (no files written)
uv run python examples/demo_todo_sync.py --dry-run

# Scan specific package
uv run python examples/demo_todo_sync.py --dry-run --package tta-dev-primitives

# Write to journals
uv run python examples/demo_todo_sync.py --write

# Custom output directory
uv run python examples/demo_todo_sync.py --write --output-dir /tmp/journals
```

---

## 📝 Code Examples

### Basic TODO Sync

```python
from tta_kb_automation.tools.todo_sync import TODOSync

# Initialize
sync = TODOSync()

# Scan and create journal
result = await sync.scan_and_create(
    paths=["packages/tta-dev-primitives/src"],
    journal_date="2025_11_03",
)

print(f"Found {result['todos_found']} TODOs")
```

### Dry Run Mode

```python
# Don't write files (testing/analysis)
result = await sync.scan_and_create(
    paths=["packages"],
    dry_run=True,  # No files written
)

# Access TODO data
todos = result["todos"]
for todo in todos:
    print(f"{todo['type']}: {todo['message']}")
```

### Custom Output Directory

```python
# Write to custom location (useful for testing)
result = await sync.scan_and_create(
    paths=["packages"],
    journal_date="2025_11_03",
    output_dir="/tmp/test-journals",
)
```

---

## 🧪 Testing Patterns

### Integration Test Structure

```python
import pytest
from pathlib import Path

@pytest.mark.integration
class TestMyFeature:
    @pytest.mark.asyncio
    async def test_with_real_codebase(self, workspace_root):
        """Test against real TTA.dev codebase."""
        # workspace_root fixture provides repo root
        paths = [str(workspace_root / "packages")]

        # Your test here
        result = await my_tool.execute(paths)

        # Validate results
        assert result["success"]
```

### Fixtures

```python
@pytest.fixture
def workspace_root():
    """Get the TTA.dev workspace root."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def logseq_dir(workspace_root):
    """Get the logseq directory."""
    return workspace_root / "logseq"

@pytest.fixture
def temp_journal_dir(tmp_path):
    """Create temporary journal directory."""
    journal_dir = tmp_path / "journals"
    journal_dir.mkdir()
    return journal_dir
```

---

## 📊 Common Queries

### Find Orphaned KB Pages

```python
# In integration tests
pages_dir = logseq_dir / "pages"

all_pages = set()
for page_file in pages_dir.glob("**/*.md"):
    all_pages.add(page_file.stem)

all_links = set()
for page_file in pages_dir.glob("**/*.md"):
    content = page_file.read_text()
    links = re.findall(r"\[\[(.*?)\]\]", content)
    all_links.update(links)

orphaned = all_pages - all_links
print(f"Orphaned pages: {len(orphaned)}")
```

### Analyze TODO Distribution

```python
# Group TODOs by type
by_type = {}
for todo in todos:
    todo_type = todo["type"]
    by_type[todo_type] = by_type.get(todo_type, 0) + 1

# Sort and display
for todo_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    print(f"{todo_type:15s}: {count:3d}")
```

### Format Logseq Entry

```python
# Use TODOSync helper method
sync = TODOSync()
formatted = sync.format_todo_entry(todo)

print(formatted)
# Output:
# - TODO message #dev-todo
#   type:: implementation
#   priority:: high
#   package:: tta-dev-primitives
#   source:: file.py:123
```

---

## 🔧 Configuration

### Scan Settings

```python
result = await sync.scan_and_create(
    paths=["packages"],
    include_tests=False,     # Exclude test files
    context_lines=3,         # Lines of context around TODO
    journal_date="2025_11_03",
)
```

### Router Customization

```python
class CustomTODOSync(TODOSync):
    def _route_todo(self, todo, context):
        """Custom routing logic."""
        message = todo.get("message", "").lower()

        # Your custom logic
        if "architecture" in message:
            return "complex"
        else:
            return "simple"
```

---

## 📈 Performance Tips

### 1. Use Dry Run for Analysis

```python
# Fast analysis without file I/O
result = await sync.scan_and_create(
    paths=["packages"],
    dry_run=True,
)
```

### 2. Scan Specific Packages

```python
# Instead of scanning all
paths = ["packages"]

# Scan specific packages
paths = [
    "packages/tta-dev-primitives/src",
    "packages/tta-observability-integration/src",
]
```

### 3. Exclude Test Files

```python
# Faster scanning
result = await sync.scan_and_create(
    paths=["packages"],
    include_tests=False,  # Skip test files
)
```

---

## 🐛 Troubleshooting

### Issue: TODO structure mismatch

**Problem:** KeyError on "message" or "todo_text"

**Solution:** Normalization already implemented in `_route_todo`:

```python
# Handles both keys
message = todo.get("message", todo.get("todo_text", "")).lower()
```

### Issue: Integration tests fail

**Problem:** Can't find workspace_root

**Solution:** Ensure fixture is correct:

```python
@pytest.fixture
def workspace_root():
    # Navigate from tests/integration to repo root
    return Path(__file__).parent.parent.parent
```

### Issue: Journal not created

**Problem:** Directory doesn't exist

**Solution:** CreateJournalEntry creates directories automatically:

```python
journal_dir.mkdir(parents=True, exist_ok=True)
```

---

## 📦 File Locations

### Source Code

```
packages/tta-kb-automation/
├── src/tta_kb_automation/
│   ├── core/
│   │   ├── code_primitives.py         # Scan, Extract
│   │   ├── integration_primitives.py  # CreateJournalEntry
│   │   └── intelligence_primitives.py # ClassifyTODO
│   └── tools/
│       └── todo_sync.py                # TODOSync main tool
```

### Tests

```
tests/
└── integration/
    └── test_kb_automation_integration.py  # Integration tests
```

### Examples

```
examples/
└── demo_todo_sync.py  # Demo script
```

### Documentation

```
docs/
└── KB_AUTOMATION_SUMMARY.md  # Full implementation summary
```

---

## 🔗 Related Resources

- **Full Summary:** `docs/KB_AUTOMATION_SUMMARY.md`
- **Package README:** `packages/tta-kb-automation/README.md`
- **Integration Tests:** `tests/integration/test_kb_automation_integration.py`
- **Demo Script:** `examples/demo_todo_sync.py`
- **TODO Tracking:** Use `manage_todo_list` tool (read operation)

---

## 🎯 Next Steps

See `docs/KB_AUTOMATION_SUMMARY.md` for:
- Cross-Reference Builder implementation plan
- Session Context Builder design
- LLM integration approach

---

**Last Updated:** November 3, 2025
**Version:** 1.0
**Status:** Phase 1 Complete


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Status-reports/Infrastructure/Kb_automation_quickref]]
