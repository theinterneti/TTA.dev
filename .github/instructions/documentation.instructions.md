---
applyTo: "**/*.md,**/README.md,**/CHANGELOG.md"
description: "Documentation files - clear, actionable, with code examples"
---

# Documentation Guidelines

## Core Principles

- Show, don't tell - include working code examples
- Be specific - reference actual files and functions
- Stay current - update when code changes
- Keep it scannable - use bullet points and tables

## README Template

```markdown
# Package Name

Brief one-line description.

## Installation

\`\`\`bash
uv pip install -e packages/package-name
\`\`\`

## Quick Start

\`\`\`python
from package_name import Component
result = Component().do_thing()
\`\`\`

## API Reference

### ComponentName

Description and example.

## Development

\`\`\`bash
uv sync --all-extras
uv run pytest -v
\`\`\`
```

## Code Examples

- Every public API needs a working example
- Examples should be copy-paste runnable
- Include imports in examples

```markdown
### Good Example

\`\`\`python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(my_operation, max_attempts=3)
result = await workflow.execute(data, WorkflowContext())
\`\`\`
```

## Formatting

- Use GitHub Flavored Markdown
- Tables for comparisons and reference data
- Code blocks with language hints
- Limit line length to 100 characters

## Links

- Use relative links for internal docs
- Verify links work before committing
- Link to source code where relevant

## What NOT to Document

- Status reports (use git commits/PRs)
- Meeting notes (use issues)
- Implementation details that change frequently


---
**Logseq:** [[TTA.dev/.github/Instructions/Documentation.instructions]]
