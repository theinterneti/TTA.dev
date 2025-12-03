# CrossReferenceBuilder Tool

**Bidirectional analysis of code ↔ KB references for maintaining documentation consistency**

---

## 🎯 Purpose

The CrossReferenceBuilder tool creates a complete map of relationships between code and knowledge base by:

- **Finding code references in KB** - KB pages that mention code files
- **Finding KB references in code** - Code files that link to KB pages
- **Identifying missing links** - Gaps in bidirectional references
- **Generating reference reports** - Complete mapping for review

**Use when**: Architecture documentation, onboarding, KB maintenance, finding orphaned code/docs

---

## 🏗️ Architecture

### Primitive Composition

```python
CrossReferenceBuilder Workflow:
┌──────────────────────┐
│ ParseLogseqPages     │ ─► Parse all KB pages
└──────────────────────┘
         │
         ↓
┌──────────────────────┐
│ ExtractCodeReferences│ ─► Find code file mentions in KB
└──────────────────────┘
         │
         ↓ (KB → Code mapping)
         │
┌──────────────────────┐
│ ScanCodebase         │ ─► Find all code files
└──────────────────────┘
         │
         ↓
┌──────────────────────┐
│ ExtractKBReferences  │ ─► Find KB page mentions in code
└──────────────────────┘
         │
         ↓ (Code → KB mapping)
         │
┌──────────────────────┐
│ AnalyzeCrossRefs     │ ─► Build bidirectional map
└──────────────────────┘
         │
         ↓
┌──────────────────────┐
│ GenerateReport       │ ─► Markdown report
└──────────────────────┘
```

### Reference Detection Patterns

**Code references in KB** (KB → Code):
- `` `code.py` `` - Backtick-wrapped filenames
- `See: path/to/file.py` - Documentation style
- `[file.py](path/to/file.py)` - Markdown links

**KB references in code** (Code → KB):
- `[[Wiki Link]]` - Standard Logseq links
- `See: Architecture.md` - Doc references
- `KB: Page Name` - Explicit KB markers

---

## 🚀 Quick Start

### Basic Usage

```python
from tta_kb_automation.tools.cross_reference_builder import CrossReferenceBuilder
from pathlib import Path

# Initialize builder
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)

# Build cross-reference map
result = await builder.build()

# Access mappings
kb_to_code = result["kb_to_code"]
code_to_kb = result["code_to_kb"]

print(f"KB pages referencing code: {len(kb_to_code)}")
print(f"Code files referencing KB: {len(code_to_kb)}")
```

### Find Missing References

```python
# Build cross-references
result = await builder.build()

# Check for missing bidirectional refs
missing = result["missing_references"]

for ref in missing:
    if ref["direction"] == "kb_to_code":
        print(f"KB page '{ref['source']}' mentions code '{ref['target']}' but code doesn't link back")
    elif ref["direction"] == "code_to_kb":
        print(f"Code '{ref['source']}' mentions KB '{ref['target']}' but KB doesn't link back")
```

### Generate Report

```python
result = await builder.build()

# Get markdown report
report = result["report"]

# Save to file
Path("reports/cross-references.md").write_text(report)
```

---

## 📊 Output Structure

### Result Dictionary

```python
{
    "kb_to_code": {
        "TTA Primitives/RetryPrimitive.md": [
            "platform/primitives/src/retry.py",
            "platform/primitives/tests/test_retry.py"
        ],
        "Architecture Overview.md": [
            "platform/primitives/src/base.py"
        ]
    },
    "code_to_kb": {
        "platform/primitives/src/retry.py": [
            "TTA Primitives/RetryPrimitive",
            "Best Practices/Error Handling"
        ],
        "platform/primitives/README.md": [
            "Getting Started",
            "Architecture Overview"
        ]
    },
    "missing_references": [
        {
            "source": "TTA Primitives/CachePrimitive.md",
            "target": "cache.py",
            "direction": "kb_to_code",
            "suggestion": "Add [[TTA Primitives/CachePrimitive]] to cache.py docstring"
        }
    ],
    "stats": {
        "total_kb_pages": 95,
        "total_code_files": 234,
        "kb_pages_with_code_refs": 30,
        "code_files_with_kb_refs": 14,
        "total_missing_refs": 165
    },
    "report": "# Cross-Reference Analysis\n..."
}
```

### Report Format

```markdown
# Cross-Reference Analysis

## Summary
- Total KB pages: 95
- Total code files: 234
- KB pages referencing code: 30
- Code files referencing KB: 14
- Missing bidirectional references: 165

## KB → Code References (30 pages)

### TTA Primitives/RetryPrimitive.md
**Code files mentioned:**
- `platform/primitives/src/retry.py`
- `platform/primitives/tests/test_retry.py`

**Bidirectional:** ✅ Code links back to KB

### Architecture Overview.md
**Code files mentioned:**
- `platform/primitives/src/base.py`

**Bidirectional:** ❌ Code does NOT link back

## Code → KB References (14 files)

### platform/primitives/src/retry.py
**KB pages mentioned:**
- [[TTA Primitives/RetryPrimitive]]
- [[Best Practices/Error Handling]]

**Bidirectional:** ✅ KB links back to code

## Missing References (165)

### High-Priority Missing Links

**KB page mentions code but code doesn't reference KB:**
- `TTA Primitives/CachePrimitive.md` → `cache.py`
  - **Suggestion:** Add `See: [[TTA Primitives/CachePrimitive]]` to docstring

**Code mentions KB but KB doesn't reference code:**
- `retry.py` → [[Error Handling Patterns]]
  - **Suggestion:** Add `` `retry.py` `` to KB page

## Recommendations

1. **Add KB links to docstrings** (15 files need updates)
2. **Reference code in KB pages** (12 pages need code examples)
3. **Create missing KB pages** (8 referenced but don't exist)
```

---

## 🔧 Configuration Options

### Constructor Parameters

```python
CrossReferenceBuilder(
    kb_path: Path,              # Path to logseq/ directory
    code_path: Path,            # Path to code directory (e.g., packages/)
    use_cache: bool = True,     # Enable caching
    code_patterns: list[str] = ["**/*.py", "**/*.md"]  # File patterns to scan
)
```

### Performance Tuning

```python
# Fast analysis (with caching)
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/"),
    use_cache=True
)

# Accurate analysis (no caching)
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/"),
    use_cache=False
)

# Scan only Python files
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/"),
    code_patterns=["**/*.py"]
)
```

---

## 🎓 Common Patterns

### Pattern 1: Architecture Documentation Audit

```python
async def audit_architecture_docs():
    """Verify architecture KB pages reference actual code."""
    builder = CrossReferenceBuilder(
        kb_path=Path("logseq/"),
        code_path=Path("packages/")
    )

    result = await builder.build()

    # Find architecture pages without code references
    arch_pages = [
        page for page in result["kb_to_code"].keys()
        if "Architecture" in page or "Design" in page
    ]

    missing_code_refs = [
        page for page in arch_pages
        if len(result["kb_to_code"][page]) == 0
    ]

    if missing_code_refs:
        print(f"⚠️ Architecture pages without code references:")
        for page in missing_code_refs:
            print(f"  - {page}")
```

### Pattern 2: Onboarding Documentation

```python
async def generate_onboarding_map():
    """Create code-to-docs map for new developers."""
    builder = CrossReferenceBuilder(
        kb_path=Path("logseq/"),
        code_path=Path("packages/")
    )

    result = await builder.build()

    # Generate "Where to learn about this code" guide
    onboarding = {}
    for code_file, kb_pages in result["code_to_kb"].items():
        if kb_pages:
            onboarding[code_file] = {
                "documentation": kb_pages,
                "learning_path": generate_learning_path(kb_pages)
            }

    # Save for new team members
    save_onboarding_guide(onboarding)
```

### Pattern 3: Documentation Completeness Check

```python
async def check_doc_completeness():
    """Ensure all important code is documented in KB."""
    builder = CrossReferenceBuilder(
        kb_path=Path("logseq/"),
        code_path=Path("packages/")
    )

    result = await builder.build()

    # Find code files without KB references
    all_code_files = set(scan_all_code_files())
    documented_files = set(result["code_to_kb"].keys())
    undocumented = all_code_files - documented_files

    # Filter for important files (exclude tests, __init__, etc.)
    important_undocumented = [
        f for f in undocumented
        if "test" not in str(f)
        and "__init__" not in str(f)
        and str(f).endswith(".py")
    ]

    print(f"⚠️ {len(important_undocumented)} important files lack KB documentation")
    for file in important_undocumented[:10]:  # Show first 10
        print(f"  - {file}")
```

---

## 🔍 Troubleshooting

### Issue: "No cross-references found"

**Cause**: Incorrect reference patterns or paths

**Solution**:
```python
# Verify KB path has pages/
assert (Path("logseq/") / "pages").exists()

# Verify code path has .py files
code_files = list(Path("packages/").rglob("*.py"))
assert len(code_files) > 0

# Check reference formats in code:
# ✅ [[Page Name]] - Will be detected
# ❌ [Page Name] - Won't be detected (missing brackets)

# Check reference formats in KB:
# ✅ `file.py` - Will be detected
# ❌ file.py - Won't be detected (missing backticks)
```

### Issue: "Missing references too high"

**Cause**: Not all code/KB uses bidirectional linking

**This is normal!** Missing references indicate opportunities:
- Add KB links to docstrings
- Add code examples to KB pages
- Create new KB pages for undocumented code

**Goal**: Not 0 missing refs, but strategic documentation

### Issue: "Analysis is slow"

**Cause**: Large codebase + no caching

**Solutions**:
```python
# Enable caching (default)
builder = CrossReferenceBuilder(..., use_cache=True)

# Scan fewer files
builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("platform/kb-automation"),  # Just one package
    code_patterns=["**/*.py"]  # Skip .md files
)

# Run less frequently (e.g., weekly instead of daily)
```

### Issue: "False positives in references"

**Cause**: Pattern matching finds similar filenames

**Example**: KB mentions `base.py` but there are 3 files named `base.py`

**Mitigation**:
- Use full paths in KB: `` `platform/primitives/src/base.py` ``
- Review report manually
- Future enhancement: Smarter disambiguation

---

## 📈 Metrics & Observability

### Automatic Metrics

CrossReferenceBuilder emits:

- `xref.kb_pages.total` - Total KB pages scanned
- `xref.code_files.total` - Total code files scanned
- `xref.kb_to_code.count` - KB pages with code refs
- `xref.code_to_kb.count` - Code files with KB refs
- `xref.missing.count` - Missing bidirectional refs
- `xref.analysis.duration_ms` - Analysis time

### Structured Logging

```json
{
  "event": "cross_reference_analysis_complete",
  "total_kb_pages": 95,
  "total_code_files": 234,
  "kb_pages_with_code_refs": 30,
  "code_files_with_kb_refs": 14,
  "missing_references": 165,
  "duration_ms": 876.3,
  "workflow_id": "cross_reference_builder"
}
```

### Distributed Tracing

Spans created:

- `cross_reference_builder.build` - Root span
- `parse_logseq_pages.execute` - KB parsing
- `extract_code_references.execute` - Find code refs in KB
- `scan_codebase.execute` - Code scanning
- `extract_kb_references.execute` - Find KB refs in code
- `analyze_cross_references.execute` - Build bidirectional map

---

## 🧪 Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_cross_reference_builder_basic(tmp_path):
    """Test CrossReferenceBuilder with mock structure."""
    # Create mock KB
    kb_dir = tmp_path / "logseq" / "pages"
    kb_dir.mkdir(parents=True)

    (kb_dir / "Architecture.md").write_text("""
    # Architecture

    See implementation in `src/base.py`.
    """)

    # Create mock code
    code_dir = tmp_path / "packages" / "my-pkg" / "src"
    code_dir.mkdir(parents=True)

    (code_dir / "base.py").write_text('''
    """Base module.

    See: [[Architecture]]
    """
    ''')

    # Build cross-references
    builder = CrossReferenceBuilder(
        kb_path=tmp_path / "logseq",
        code_path=tmp_path / "packages"
    )
    result = await builder.build()

    # Assertions
    assert "Architecture.md" in result["kb_to_code"]
    assert "base.py" in str(result["code_to_kb"])
    assert result["stats"]["total_kb_pages"] == 1
    assert result["stats"]["total_code_files"] > 0
```

### Integration Tests

See: `tests/integration/test_real_kb_integration.py::TestCrossReferenceBuilderWithRealData`

- Tests against real TTA.dev codebase
- Validates bidirectional reference detection
- Checks report generation
- Verifies performance (<30s for full repo)

---

## 🔗 Related

### Tools

- [[TTA KB Automation/LinkValidator]] - Validates wiki links
- [[TTA KB Automation/TODO Sync]] - Syncs code TODOs

### Primitives

- [[TTA Primitives/ParseLogseqPages]] - KB parsing
- [[TTA Primitives/ExtractCodeReferences]] - Code ref extraction
- [[TTA Primitives/ExtractKBReferences]] - KB ref extraction
- [[TTA Primitives/ScanCodebase]] - Code scanning

### Documentation

- [[TTA.dev/Guides/KB Integration Workflow]] - Integration patterns
- [[TTA.dev/Architecture]] - TTA.dev architecture docs

---

## 💡 Best Practices

### For Agents

1. **Run during architecture changes** - Ensure docs stay in sync
2. **Review missing references** - Identify documentation gaps
3. **Use in onboarding** - Generate learning paths
4. **Track over time** - Monitor doc coverage trends
5. **Combine with LinkValidator** - Full KB health check

### For Users

1. **Use bidirectional linking** - Reference code in KB, KB in code
2. **Be specific with filenames** - Use full paths in KB pages
3. **Update docstrings** - Add KB page references
4. **Create missing pages** - Address gaps proactively
5. **Review reports regularly** - Weekly or monthly

### Reference Writing Guidelines

**Good KB references in code**:
```python
"""RetryPrimitive implementation.

Implements exponential backoff pattern.

Documentation: [[TTA Primitives/RetryPrimitive]]
Architecture: [[TTA.dev/Architecture/Recovery Patterns]]
"""
```

**Good code references in KB**:
```markdown
## RetryPrimitive

Implementation: `platform/primitives/src/tta_dev_primitives/recovery/retry.py`

Tests: `platform/primitives/tests/test_retry.py`
```

---

## 🎯 Flashcards

### Q: What does CrossReferenceBuilder analyze? #card

**A:** Bidirectional relationships:
1. **KB → Code**: KB pages mentioning code files
2. **Code → KB**: Code files referencing KB pages
3. **Missing**: Gaps in bidirectional links

### Q: What patterns detect code references in KB? #card

**A:**
- `` `filename.py` `` - Backtick-wrapped
- `See: path/to/file.py` - Doc style
- `[file.py](path/to/file.py)` - Markdown links

### Q: What patterns detect KB references in code? #card

**A:**
- `[[Wiki Link]]` - Logseq style
- `See: Page Name.md` - Doc references
- `KB: Page Name` - Explicit markers

---

**Last Updated:** November 3, 2025
**Package:** tta-kb-automation
**Tool Status:** ✅ Production Ready
**Test Coverage:** 100% (10/10 tests passing)
