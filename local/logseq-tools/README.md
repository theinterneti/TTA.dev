# Logseq Documentation Assistant

**🔬 EXPERIMENTAL FEATURE - Local Development Only**

An intelligent assistant for analyzing and improving your Logseq documentation.

---

## 🎯 What It Does

This tool helps you maintain high-quality Logseq documentation by:

- **Analyzing** markdown files for common issues
- **Detecting** formatting problems (MD linting)
- **Finding** broken page links
- **Checking** task syntax (TODO/DOING/DONE)
- **Validating** code blocks and structure
- **Scoring** documentation quality (0-100)
- **Fixing** issues automatically (with your permission)

---

## 🚀 Quick Start

### Analyze Your Logseq Documentation

```bash
cd /home/thein/repos/TTA.dev
python local/logseq-tools/doc_assistant.py logseq/
```

This will scan all pages and journals, showing:
- Total files analyzed
- Issues found
- Quality scores
- Files needing attention

### Use in Python

```python
import asyncio
import sys
sys.path.insert(0, '/home/thein/repos/TTA.dev')

from local.logseq_tools.doc_assistant import analyze_logseq_docs

# Analyze all docs
results = asyncio.run(analyze_logseq_docs("logseq"))

print(f"Total issues: {results['total_issues']}")
print(f"Average quality: {results['average_quality_score']}/100")

# Show files with issues
for file_info in results['files_with_issues']:
    print(f"- {file_info['file']}: {file_info['issues']} issues")
```

### Analyze a Single File

```python
from pathlib import Path
from local.logseq_tools.doc_assistant import LogseqDocumentAnalyzer

analyzer = LogseqDocumentAnalyzer(Path("logseq"))
analysis = await analyzer.analyze_file(Path("logseq/pages/TTA.dev (Meta-Project).md"))

print(f"Quality Score: {analysis.quality_score}/100")
print(f"Issues Found: {len(analysis.issues)}")

for issue in analysis.issues:
    print(f"Line {issue.line_number}: {issue.message}")
```

### Fix Issues Automatically

```python
from local.logseq_tools.doc_assistant import LogseqDocumentAnalyzer, LogseqDocumentFixer

analyzer = LogseqDocumentAnalyzer(Path("logseq"))
fixer = LogseqDocumentFixer(analyzer)

# Dry run first (preview changes)
result = await fixer.fix_file(
    Path("logseq/pages/AI Research.md"),
    dry_run=True
)
print(f"Would fix {result['fixes_applied']} issues")

# Apply fixes
result = await fixer.fix_file(
    Path("logseq/pages/AI Research.md"),
    dry_run=False
)
print(f"Fixed {result['fixes_applied']} issues")
```

---

## 🔍 What Gets Checked

### Heading Structure

- ✅ No skipped heading levels (# → ### is bad)
- ✅ Proper spacing after `#`
- ✅ Logical heading hierarchy

### List Formatting

- ✅ Blank lines before/after lists
- ✅ Consistent list markers (`-`, `*`, `+`)
- ✅ Proper indentation

### Task Syntax

- ✅ Uppercase status: `TODO` not `todo`
- ✅ Valid statuses: TODO, DOING, DONE, LATER, NOW, WAITING
- ✅ Proper formatting

### Code Blocks

- ✅ Language specifiers: ` ```python` not just ` ``` `
- ✅ Proper opening/closing
- ✅ No unclosed blocks

### Links

- ✅ Page links: `[[Page Name]]`
- ✅ No bare URLs (should be `<url>` or `[text](url)`)
- ✅ Valid relative paths to code files

### Structure

- ✅ Has meaningful headings
- ✅ Not just a wall of text
- ✅ Logical organization

---

## 🎨 Issue Types & Severity

### Errors (Fix Required)

- **task_case** - Task status not uppercase
- **heading_format** - Missing space after #
- **code_unclosed** - Unclosed code block

### Warnings (Should Fix)

- **heading_skip** - Skipped heading level
- **list_spacing** - Missing blank lines around lists
- **code_language** - Missing language specifier

### Info (Nice to Fix)

- **bare_url** - Bare URL should be wrapped

---

## 📊 Quality Scoring

Quality score (0-100) is calculated based on:

- **Errors:** -10 points each
- **Warnings:** -5 points each
- **Info:** -1 point each

Normalized by document length for fairness.

**Score Interpretation:**
- **90-100:** Excellent documentation
- **75-89:** Good, minor issues
- **60-74:** Acceptable, needs improvement
- **Below 60:** Poor quality, significant issues

---

## 🛠️ Advanced Usage

### Analyze Specific Issue Types

```python
# Only check task syntax
issues = analyzer._check_task_syntax(lines)

# Only check code blocks
issues = analyzer._check_code_blocks(lines)

# Only check links
issues = analyzer._check_link_formatting(lines)
```

### Fix Specific Issue Types

```python
# Only fix task case issues
result = await fixer.fix_file(
    file_path,
    fix_types=["task_case"],
    dry_run=False
)

# Fix multiple types
result = await fixer.fix_file(
    file_path,
    fix_types=["task_case", "heading_format", "list_spacing"],
    dry_run=False
)
```

### Batch Processing

```python
from pathlib import Path

logseq_root = Path("logseq")
pages = list(logseq_root.glob("pages/*.md"))

for page in pages:
    analysis = await analyzer.analyze_file(page)
    if analysis.quality_score < 75:
        print(f"Needs attention: {page.name} (score: {analysis.quality_score})")
```

---

## 🎯 Use Cases

### Morning Documentation Review

```bash
# Check all documentation quality
python local/logseq-tools/doc_assistant.py logseq/

# See which pages need attention
# Fix issues manually or automatically
```

### Pre-Commit Hook

```python
# Check if documentation quality meets threshold
results = await analyze_logseq_docs("logseq")

if results['average_quality_score'] < 80:
    print("❌ Documentation quality below threshold")
    sys.exit(1)
```

### CI/CD Integration

```yaml
# .github/workflows/doc-quality.yml
- name: Check Logseq Documentation Quality
  run: |
    python local/logseq-tools/doc_assistant.py logseq/ || true
```

### IDE Integration

Create a VS Code task:

```json
{
  "label": "📝 Check Logseq Docs",
  "type": "shell",
  "command": "python local/logseq-tools/doc_assistant.py logseq/"
}
```

---

## 🚧 Current Limitations

This is experimental code. Known limitations:

- **No backup** - Make git commits before auto-fixing
- **Simple fixes only** - Complex issues need manual attention
- **English only** - Assumes English documentation
- **Basic linting** - Not as comprehensive as dedicated linters
- **No plugins** - Doesn't understand Logseq plugins/extensions

---

## 🔄 Future Enhancements

Ideas for improvement (add to backlog):

- [ ] Integrate with markdownlint for comprehensive checking
- [ ] Generate missing page stubs automatically
- [ ] Detect orphaned pages (no incoming links)
- [ ] Suggest better page organization
- [ ] Generate table of contents
- [ ] Check for broken external links
- [ ] Validate query syntax
- [ ] Suggest tags based on content
- [ ] Generate weekly review summaries
- [ ] Integration with LLM for content quality

---

## 💡 Tips

### Use with Git

```bash
# Always commit before auto-fixing
git add logseq/
git commit -m "Backup before doc fixes"

# Run fixer
python local/logseq-tools/doc_assistant.py logseq/ --fix

# Review changes
git diff

# Commit or revert
git commit -m "Fix doc issues" OR git checkout -- logseq/
```

### Incremental Improvement

Don't try to fix everything at once:

1. Start with errors only
2. Then tackle warnings
3. Finally address info issues

### Document Your Decisions

If you intentionally ignore an issue, add a comment:

```markdown
<!-- Intentionally using bare URL for readability -->
See: https://example.com/long-url-that-would-be-ugly-as-link
```

---

## 🎓 Learning Resources

To become a "Logseq documentation expert":

1. **Logseq Best Practices:** <https://docs.logseq.com>
2. **Markdown Guide:** <https://www.markdownguide.org>
3. **Documentation Style Guide:** <https://developers.google.com/style>

---

## 🐛 Known Issues

- Line number calculation may be off by one in some edge cases
- Doesn't handle multi-line task descriptions well
- May suggest redundant blank lines in nested lists
- Doesn't understand Logseq's block references yet

---

## 🤝 Contributing

This is experimental code in `local/`. If you improve it:

1. Test thoroughly on your Logseq graph
2. Document your changes
3. Consider graduating to `packages/` if it's ready for public release

---

**Status:** Experimental / Prototype
**Created:** 2025-10-30
**Last Updated:** 2025-10-30
**Maintainer:** TTA.dev
**Location:** `local/logseq-tools/`


---
**Logseq:** [[TTA.dev/Local/Logseq-tools/Readme]]
