# LinkValidator Tool

**Automated validation of wiki links in Logseq knowledge base**

---

## 🎯 Purpose

The LinkValidator tool ensures KB integrity by:

- **Finding broken links** - Detects [[non-existent pages]]
- **Identifying orphaned pages** - Pages with no incoming links
- **Validating structure** - Ensures KB connectivity
- **Generating reports** - Markdown summaries for review

**Use when**: Maintaining KB quality, before commits, in CI/CD pipelines

---

## 🏗️ Architecture

### Primitive Composition

```python
LinkValidator Workflow:
┌─────────────────────┐
│ ParseLogseqPages    │ ─┐
└─────────────────────┘  │
                         ├──► Sequential
┌─────────────────────┐  │
│ ExtractLinks        │ ─┘
└─────────────────────┘
         │
         ↓
    ┌─────────────┐
    │  Parallel   │
    └─────────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌──────────┐ ┌──────────────┐
│Validate  │ │FindOrphaned  │
│Links     │ │Pages         │
└──────────┘ └──────────────┘
         │         │
         └────┬────┘
              ↓
    ┌──────────────────┐
    │ Aggregate Results│
    └──────────────────┘
              ↓
    ┌──────────────────┐
    │ Generate Report  │
    └──────────────────┘
```

### Wrapped in Recovery Patterns

- **RetryPrimitive** - Retries on file system errors (3 attempts, exponential backoff)
- **CachePrimitive** - Caches KB parsing results (TTL: 300s, keyed by KB path)

---

## 🚀 Quick Start

### Basic Usage

```python
from tta_kb_automation.tools.link_validator import LinkValidator
from pathlib import Path

# Initialize validator
validator = LinkValidator(
    kb_path=Path("logseq/"),
    use_cache=True
)

# Run validation
result = await validator.validate()

# Check results
print(f"Total pages: {result['total_pages']}")
print(f"Broken links: {len(result['broken_links'])}")
print(f"Orphaned pages: {len(result['orphaned_pages'])}")

# Get markdown report
report = result["report"]
```

### Integration with CI/CD

```python
# In GitHub Actions or pre-commit hook
validator = LinkValidator(kb_path=Path("logseq/"), use_cache=False)
result = await validator.validate()

# Fail if too many broken links
broken_count = len(result["broken_links"])
if broken_count > 10:
    raise ValueError(f"Too many broken links: {broken_count}")
```

---

## 📊 Output Structure

### Result Dictionary

```python
{
    "total_pages": 95,           # Total KB pages found
    "valid_links": 733,          # Links to existing pages
    "broken_links": [            # Links to non-existent pages
        {
            "source": "TODO Management System.md",
            "target": "Missing Page",
            "line": 42
        }
    ],
    "orphaned_pages": [          # Pages with no incoming links
        "Orphaned Page.md"
    ],
    "summary": "Validated 95 pages...",
    "report": "# KB Link Validation Report\n..."
}
```

### Markdown Report Format

```markdown
# KB Link Validation Report

## Summary
- Total pages: 95
- Valid links: 733
- Broken links: 18
- Orphaned pages: 5

## Broken Links (18)

### In "TODO Management System.md"
- Line 42: [[Non-existent Page]]
- Line 67: [[Another Missing Page]]

## Orphaned Pages (5)

- Old Notes.md (no incoming links)
- Draft Ideas.md (no incoming links)
```

---

## 🔧 Configuration Options

### Constructor Parameters

```python
LinkValidator(
    kb_path: Path,           # Path to logseq/ directory
    use_cache: bool = True,  # Enable caching (recommended for development)
    max_retries: int = 3,    # Retry attempts on errors
    cache_ttl: int = 300     # Cache lifetime in seconds (5 minutes)
)
```

### Performance Tuning

```python
# Fast validation (caching enabled)
validator = LinkValidator(kb_path=path, use_cache=True)

# Accurate validation (no caching)
validator = LinkValidator(kb_path=path, use_cache=False)

# Custom retry strategy
validator = LinkValidator(
    kb_path=path,
    max_retries=5,          # More retries for flaky filesystems
    cache_ttl=600           # Longer cache for larger KBs
)
```

---

## 🎓 Common Patterns

### Pattern 1: Pre-commit Hook

```python
async def pre_commit_validation():
    """Validate KB before committing changes."""
    validator = LinkValidator(kb_path=Path("logseq/"), use_cache=False)
    result = await validator.validate()

    broken = len(result["broken_links"])
    if broken > 0:
        print(f"❌ Found {broken} broken links")
        print(result["report"])
        return False

    print("✅ KB validation passed")
    return True
```

### Pattern 2: Daily Validation Job

```python
async def daily_kb_check():
    """Run comprehensive KB validation."""
    validator = LinkValidator(kb_path=Path("logseq/"), use_cache=False)
    result = await validator.validate()

    # Save report
    report_path = Path(f"reports/kb-validation-{date.today()}.md")
    report_path.write_text(result["report"])

    # Send notification if issues found
    broken_count = len(result["broken_links"])
    orphan_count = len(result["orphaned_pages"])

    if broken_count > 0 or orphan_count > 5:
        send_notification(f"KB needs attention: {broken_count} broken, {orphan_count} orphaned")
```

### Pattern 3: Integration Testing

```python
@pytest.mark.integration
async def test_kb_quality():
    """Test that KB meets quality standards."""
    validator = LinkValidator(kb_path=Path("logseq/"), use_cache=False)
    result = await validator.validate()

    # Quality assertions
    assert result["total_pages"] > 50, "KB too small"
    assert len(result["broken_links"]) < 10, "Too many broken links"
    assert len(result["orphaned_pages"]) < 5, "Too many orphaned pages"

    # Calculate health score
    total_links = result["valid_links"] + len(result["broken_links"])
    health = (result["valid_links"] / total_links * 100) if total_links > 0 else 100

    assert health > 90, f"KB health too low: {health:.1f}%"
```

---

## 🔍 Troubleshooting

### Issue: "No pages found"

**Cause**: Incorrect KB path or empty pages directory

**Solution**:
```python
kb_path = Path("logseq/")  # Must contain pages/ and journals/ directories
assert (kb_path / "pages").exists(), f"Pages directory not found in {kb_path}"
```

### Issue: "Too many broken links"

**Cause**: Page references use different naming conventions

**Solution**:
- Logseq uses underscores for slashes: `TTA.dev/Testing` → `TTA.dev___Testing.md`
- Check naming conventions in your KB
- Use the report to identify patterns

### Issue: "Validation is slow"

**Cause**: Large KB without caching

**Solutions**:
1. Enable caching: `use_cache=True`
2. Increase cache TTL: `cache_ttl=600`
3. Run validation less frequently
4. Validate only changed pages (future enhancement)

### Issue: "Cache not invalidating"

**Cause**: Cache TTL too long or manual KB changes

**Solution**:
```python
# Force fresh validation
validator = LinkValidator(kb_path=path, use_cache=False)

# Or reduce TTL for active development
validator = LinkValidator(kb_path=path, use_cache=True, cache_ttl=60)  # 1 minute
```

---

## 📈 Metrics & Observability

### Automatic Metrics

LinkValidator emits OpenTelemetry metrics:

- `kb.pages.total` - Total pages in KB
- `kb.links.valid` - Valid link count
- `kb.links.broken` - Broken link count
- `kb.pages.orphaned` - Orphaned page count
- `kb.validation.duration_ms` - Validation time

### Structured Logging

All operations log structured events:

```json
{
  "event": "kb_validation_complete",
  "total_pages": 95,
  "valid_links": 733,
  "broken_links": 18,
  "orphaned_pages": 5,
  "duration_ms": 89.8,
  "workflow_id": "kb_link_validation",
  "correlation_id": "83c47538-96c3-4c19-be85-7fcd145d9200"
}
```

### Distributed Tracing

Each validation creates OpenTelemetry spans:

- `link_validator.validate` - Root span
- `parse_logseq_pages.execute` - KB parsing
- `extract_links.execute` - Link extraction
- `validate_links.execute` - Link validation
- `find_orphaned_pages.execute` - Orphan detection

---

## 🧪 Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_link_validator_basic(tmp_path):
    """Test LinkValidator with mock KB."""
    # Create test KB structure
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()

    (pages_dir / "Page A.md").write_text("Link to [[Page B]]")
    (pages_dir / "Page B.md").write_text("Link to [[Page A]]")
    (pages_dir / "Orphan.md").write_text("No incoming links")

    # Run validation
    validator = LinkValidator(kb_path=tmp_path, use_cache=False)
    result = await validator.validate()

    # Assertions
    assert result["total_pages"] == 3
    assert len(result["valid_links"]) == 2
    assert len(result["broken_links"]) == 0
    assert "Orphan.md" in result["orphaned_pages"]
```

### Integration Tests

See: `tests/integration/test_real_kb_integration.py`

- Tests against real TTA.dev KB
- Validates performance (<30s for typical KB)
- Checks report generation
- Handles special characters in page names

---

## 🔗 Related

### Tools

- [[TTA KB Automation/TODO Sync]] - Syncs code TODOs to KB
- [[TTA KB Automation/CrossReferenceBuilder]] - Code ↔ KB relationships

### Primitives

- [[TTA Primitives/ParseLogseqPages]] - KB parsing
- [[TTA Primitives/ExtractLinks]] - Link extraction
- [[TTA Primitives/ValidateLinks]] - Link validation
- [[TTA Primitives/FindOrphanedPages]] - Orphan detection

### Documentation

- [[TTA.dev/Guides/KB Integration Workflow]] - Integration patterns
- [[TTA.dev/Testing]] - Testing methodology

---

## 💡 Best Practices

### For Agents

1. **Always validate before commit** - Prevent broken links in KB
2. **Use caching in development** - Faster iteration cycles
3. **Disable caching in CI/CD** - Ensure accuracy
4. **Review orphaned pages** - Indicates missing connections
5. **Track metrics over time** - Monitor KB health trends

### For Users

1. **Run daily validations** - Catch issues early
2. **Fix broken links promptly** - Maintain KB quality
3. **Investigate orphaned pages** - May indicate structural issues
4. **Use reports for cleanup** - Prioritize fixes
5. **Integrate with workflows** - Pre-commit hooks, CI/CD

---

## 🎯 Flashcards

### Q: What does LinkValidator detect? #card

**A:** Three types of issues:
1. Broken links (references to non-existent pages)
2. Orphaned pages (pages with no incoming links)
3. KB structure problems

### Q: How does LinkValidator compose primitives? #card

**A:** Sequential workflow:
1. ParseLogseqPages - Parse KB
2. ExtractLinks - Find all wiki links
3. Parallel: ValidateLinks | FindOrphanedPages
4. AggregateParallelResults - Merge results
5. GenerateReport - Create markdown report

### Q: When should you disable caching? #card

**A:** Disable caching when:
- Running in CI/CD (accuracy over speed)
- KB has been manually edited
- Pre-commit validation (must be current)
- Testing (deterministic results)

Enable caching when:
- Active development (faster iteration)
- KB hasn't changed
- Performance matters more than accuracy

---

**Last Updated:** November 3, 2025
**Package:** tta-kb-automation
**Tool Status:** ✅ Production Ready
**Test Coverage:** 100% (70/70 tests passing)
