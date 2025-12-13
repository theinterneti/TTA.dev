# Documentation Testing Scripts

This directory contains scripts for testing and validating markdown documentation.

## check_md.py

Lightweight markdown documentation checker for TTA.dev.

### Features

- **Link validation**: Checks internal links resolve to existing files
- **Code block syntax**: Ensures code blocks have language identifiers
- **Frontmatter validation**: Validates YAML frontmatter structure
- **Runnable code extraction**: Finds Python code blocks marked as runnable

### Usage

```bash
# Check all static properties (default)
python scripts/docs/check_md.py

# Check only internal links
python scripts/docs/check_md.py --links

# Check code blocks
python scripts/docs/check_md.py --code-blocks

# Check frontmatter
python scripts/docs/check_md.py --frontmatter

# Run all checks
python scripts/docs/check_md.py --all

# Extract runnable code blocks (doesn't run them)
python scripts/docs/check_md.py --extract-runnable
```

### Runnable Code Blocks

Code blocks can be marked as runnable by adding `# runnable` as the first line:

\`\`\`python
# runnable
from tta_dev_primitives import WorkflowPrimitive

print("This block can be executed in tests")
\`\`\`

**Note**: Actual execution of code blocks requires `RUN_DOCS_CODE=true` and is intended for CI environments only.

### Exclusions

By default, these directories are excluded:
- `node_modules`
- `.git`
- `htmlcov`
- `__pycache__`
- `.venv`
- `archive`

Use `--exclude` to customize:

```bash
python scripts/docs/check_md.py --all --exclude node_modules .git archive
```

## Integration with CI

The markdown checker is integrated into the GitHub Actions workflow:

```yaml
- name: Check markdown
  run: python scripts/docs/check_md.py --all
```

## Future Enhancements

- External link checking (with rate limiting)
- Spell checking integration
- Code block execution with mocking
- Automated link fixing suggestions
- Markdown style guide enforcement


---
**Logseq:** [[TTA.dev/Scripts/Docs/Readme]]
