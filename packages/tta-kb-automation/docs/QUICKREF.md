# TTA KB Automation - Quick Reference

**Fast lookup for common KB automation tasks**

---

## Installation

```bash
# Install package
uv pip install -e packages/tta-kb-automation

# Verify
python -c "import tta_kb_automation"
```

---

## Common Tasks

### Validate KB Links

```bash
# CLI
python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output report.md \
    --fail-on-broken

# Python
from tta_kb_automation.tools import LinkValidator
validator = LinkValidator(kb_root=Path("logseq"))
result = await validator.execute({}, context)
```

### Sync TODOs to Journal

```bash
# CLI
python -m tta_kb_automation.tools.todo_sync \
    --codebase-root . \
    --kb-root logseq

# Python
from tta_kb_automation.tools import TODOSync
sync = TODOSync(codebase_root=Path("."), kb_root=Path("logseq"))
result = await sync.execute({}, context)
```

### Run Pre-commit Hook

```bash
# Install
ln -s ../../scripts/kb-validation-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Test
echo "[[Broken]]" >> logseq/pages/Test.md
git add logseq/pages/Test.md
git commit -m "test"  # Hook catches broken link
```

---

## Primitives Reference

### KB Operations

```python
from tta_kb_automation import (
    ParseLogseqPages,    # Parse KB structure
    ExtractLinks,        # Find [[links]] in markdown
    ValidateLinks,       # Check if links resolve
    FindOrphanedPages,   # Find pages with no incoming links
)
```

### Code Operations

```python
from tta_kb_automation import (
    ScanCodebase,        # Find Python files
    ExtractTODOs,        # Find TODO comments
    ParseDocstrings,     # Extract docstrings
    AnalyzeCodeStructure,# Analyze imports/deps
)
```

### Intelligence

```python
from tta_kb_automation import (
    ClassifyTODO,        # Simple vs complex
    SuggestKBLinks,      # Relevant KB pages
    GenerateFlashcards,  # Learning materials
)
```

---

## Composition Patterns

### Sequential (>>)

```python
# Output of each → input of next
workflow = step1 >> step2 >> step3
```

### Parallel (|)

```python
# Same input to all, run concurrently
workflow = branch1 | branch2 | branch3
```

### Mixed

```python
# Complex workflows
workflow = (
    parse_pages >>
    (validate_links | find_orphans) >>
    aggregate_results
)
```

---

## Error Handling

### Retry on Failure

```python
from tta_dev_primitives.recovery import RetryPrimitive

reliable_workflow = RetryPrimitive(
    primitive=your_primitive,
    max_retries=3,
    backoff_strategy="exponential"
)
```

### Cache Results

```python
from tta_dev_primitives.performance import CachePrimitive

cached_workflow = CachePrimitive(
    primitive=your_primitive,
    ttl_seconds=3600,
    cache_key_fn=lambda data, ctx: str(data)
)
```

### Timeout Protection

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

protected_workflow = TimeoutPrimitive(
    primitive=your_primitive,
    timeout_seconds=60.0
)
```

---

## CI/CD Integration

### GitHub Actions Workflow

See `.github/workflows/kb-validation.yml` for:
- Link validation on PRs
- Orphan detection
- TODO sync checks
- KB metrics

### VS Code Tasks

Add to `.vscode/tasks.json`:

```json
{
    "label": "🔍 Validate KB",
    "type": "shell",
    "command": "uv run python -m tta_kb_automation.tools.link_validator --kb-root logseq"
}
```

---

## Troubleshooting

### Module Not Found

```bash
# Reinstall
cd /path/to/TTA.dev
uv pip install -e packages/tta-kb-automation
```

### Broken Links Detected

```bash
# Get report
python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output report.md

# Review
cat report.md
```

### Slow Performance

```python
# Enable caching
from tta_dev_primitives.performance import CachePrimitive

cached = CachePrimitive(
    primitive=your_primitive,
    ttl_seconds=3600
)
```

---

## Common Workflows

### Daily KB Maintenance

```bash
#!/bin/bash
# Run daily at 3 AM

# Validate links
python -m tta_kb_automation.tools.link_validator \
    --kb-root logseq \
    --output logs/kb-$(date +%Y%m%d).md

# Sync TODOs
python -m tta_kb_automation.tools.todo_sync \
    --codebase-root . \
    --kb-root logseq
```

### Pre-Release Checklist

```bash
# 1. Validate KB
./scripts/kb-validation-hook.sh

# 2. Sync outstanding TODOs
python -m tta_kb_automation.tools.todo_sync

# 3. Check for orphaned pages
python -c "
from tta_kb_automation import FindOrphanedPages
finder = FindOrphanedPages(kb_root=Path('logseq'))
result = await finder.execute({}, context)
print(f'Orphans: {len(result[\"orphaned_pages\"])}')
"
```

---

## Documentation Links

- 📖 [Complete Guide](COMPLETE_GUIDE.md) - Full documentation
- 🎓 [Tutorial](TUTORIAL.md) - Hands-on learning
- 📦 [Package README](../README.md) - API reference
- 🤖 [Agent Guide](../AGENTS.md) - For AI agents

---

## Support

- 🐛 [Report Issues](https://github.com/theinterneti/TTA.dev/issues)
- 💡 [Discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

**Last Updated:** November 3, 2025
