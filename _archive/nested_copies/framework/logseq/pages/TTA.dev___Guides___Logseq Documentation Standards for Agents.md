# Guide: Logseq Documentation Standards for Agents

type:: [[Agent Guide]]
category:: [[Documentation Standards]], [[Agent Instructions]]
priority:: [[Critical]]
difficulty:: [[Intermediate]]
target-audience:: [[AI Agents]], [[Copilot]], [[Development Team]]

---

## Overview

- id:: logseq-standards-overview
  **This guide teaches AI agents to ALWAYS use Logseq-formatted documentation** for anything intended to be preserved. This solves the problem of AI assistants creating many unorganized `.md` files that clutter the workspace.

---

## Core Principle

> **CRITICAL RULE:** `.md` files without Logseq properties MAY BE DELETED at any time as temporary notes. Only Logseq-formatted files are permanent documentation.

### Why This Matters

- **Problem:** AI assistants create dozens of temporary `.md` files during sessions
- **Impact:** Workspace becomes cluttered with unorganized, hard-to-find notes
- **Solution:** Use Logseq format for permanent docs, bare `.md` for temporary notes only

---

## Logseq Properties Format

### Required Structure

Every permanent documentation file MUST include:

1. **YAML-style properties** at the top of the file
2. **Property separator** (`---`) after properties
3. **Proper Logseq syntax** (`::`-based properties, `[[]]` links)

### Basic Template

```markdown
# Title of Document

type:: [[Document Type]]
category:: [[Category 1]], [[Category 2]]
difficulty:: [[Easy|Intermediate|Advanced]]

---

## Content starts here

- id:: section-id
  Content with block ID for referencing
```

---

## Property Reference

### Essential Properties (All Docs)

| Property | Required | Values | Purpose |
|----------|----------|--------|---------|
| `type::` | ✅ Yes | `[[Primitive]]`, `[[Guide]]`, `[[How-To]]`, `[[Example]]`, `[[Package]]`, `[[Architecture]]` | Document classification |
| `category::` | ✅ Yes | `[[Category Name]]`, ... | Topical categorization |
| `difficulty::` | ⚠️ Guides only | `[[Easy]]`, `[[Intermediate]]`, `[[Advanced]]` | User skill level |

### Document-Type Specific Properties

#### Primitives

```markdown
type:: [[Primitive]]
category:: [[Workflow]], [[Recovery]], [[Performance]], [[Testing]]
composition:: [[Sequential]], [[Parallel]]
imports:: tta_dev_primitives.core
```

#### Guides

```markdown
type:: [[Guide]]
category:: [[Core Concepts]], [[Architecture]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
prerequisites:: [[Other Guide]]
```

#### How-To Guides

```markdown
type:: [[How-To]]
category:: [[Practical Implementation]]
difficulty:: [[Intermediate]]
estimated-time:: 45 minutes
target-audience:: [[Backend Developers]], [[DevOps]]
primitives-used:: [[RetryPrimitive]], [[TimeoutPrimitive]]
```

#### Examples

```markdown
type:: [[Example]]
category:: [[Code Examples]]
difficulty:: [[Easy]]
primitives-used:: [[SequentialPrimitive]]
use-case:: [[API Integration]]
language:: [[Python]]
```

#### Packages

```markdown
type:: [[Package]]
category:: [[TTA.dev Package]]
package-name:: tta-dev-primitives
version:: 0.1.0
status:: [[Production]]
```

---

## File Naming Conventions

### Logseq Page Naming

Use `___` (triple underscore) as namespace separator:

```
TTA.dev___Namespace___Page Title.md
TTA.dev___Primitives___SequentialPrimitive.md
TTA.dev___Guides___Workflow Composition.md
TTA.dev___How-To___Building Reliable AI Workflows.md
TTA.dev___Examples___LLM Router.md
```

### Why This Format?

- **Hierarchical:** Logseq interprets `___` as namespace hierarchy
- **Discoverable:** Easy to search and browse by namespace
- **Organized:** Groups related documents together
- **Linkable:** Clean `[[TTA.dev/Namespace/Page Title]]` links

---

## Block IDs and References

### Creating Block IDs

Add `id::` property to important blocks for referencing:

```markdown
## Key Concept

- id:: key-concept-explanation
  This is the explanation text that can be referenced elsewhere.
```

### Referencing Blocks

```markdown
See ((key-concept-explanation)) for details.
```

### When to Add Block IDs

- **Key definitions** - Important concepts
- **Code examples** - Reusable snippets
- **Prerequisites** - Shared requirements
- **Best practices** - Reusable advice

---

## Linking Conventions

### Page Links

```markdown
[[TTA.dev/Primitives/RetryPrimitive]]
[[TTA.dev/Guides/Workflow Composition]]
```

### Tag/Category Links

```markdown
category:: [[Error Handling]], [[Recovery Patterns]]
```

### External Links

```markdown
- [GitHub Repository](https://github.com/theinterneti/TTA.dev)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
```

---

## Document Types and Templates

### 1. Primitive Documentation

**File:** `TTA.dev___Primitives___[Name].md`

**Template:**

```markdown
# Primitive: [Name]

type:: [[Primitive]]
category:: [[Category Name]]
composition:: [[Sequential]], [[Parallel]]
imports:: tta_dev_primitives.[module]

---

## Overview

- id:: [name]-overview
  Brief description of what this primitive does.

---

## Import

\`\`\`python
from tta_dev_primitives import [PrimitiveName]
\`\`\`

---

## Basic Usage

\`\`\`python
# Example code
\`\`\`

---

## Parameters

[Table of parameters]

---

## See Also

- [[Related Primitive 1]]
- [[Related Primitive 2]]
```

### 2. Guide Documentation

**File:** `TTA.dev___Guides___[Title].md`

**Template:**

```markdown
# Guide: [Title]

type:: [[Guide]]
category:: [[Category]]
difficulty:: [[Easy|Intermediate|Advanced]]
estimated-time:: [X] minutes
prerequisites:: [[Prerequisite Guide]]

---

## Overview

- id:: [slug]-overview
  What this guide covers.

---

## Prerequisites

- [[Required Guide 1]]
- [[Required Guide 2]]

---

## Content Sections

[Guide content]

---

## Next Steps

- [[Next Guide]]
- [[Related Guide]]

---

**Created:** [[YYYY-MM-DD]]
**Last Updated:** [[YYYY-MM-DD]]
```

### 3. How-To Documentation

**File:** `TTA.dev___How-To___[Task].md`

**Template:**

```markdown
# How-To: [Task]

type:: [[How-To]]
category:: [[Practical Implementation]]
difficulty:: [[Intermediate]]
estimated-time:: 45 minutes
target-audience:: [[Role 1]], [[Role 2]]
primitives-used:: [[Primitive 1]], [[Primitive 2]]

---

## Overview

- id:: [slug]-overview
  What you'll learn to do.

---

## Prerequisites

[Requirements]

---

## Step-by-Step Instructions

### Step 1: [Action]

[Instructions]

### Step 2: [Action]

[Instructions]

---

## Complete Example

\`\`\`python
# Full working example
\`\`\`

---

## Troubleshooting

[Common issues and solutions]

---

## Next Steps

- [[Related How-To]]
```

### 4. Example Documentation

**File:** `TTA.dev___Examples___[Name].md`

**Template:**

```markdown
# Example: [Name]

type:: [[Example]]
category:: [[Code Examples]]
difficulty:: [[Easy]]
primitives-used:: [[Primitive 1]]
use-case:: [[Use Case]]
language:: [[Python]]

---

## Overview

- id:: [slug]-overview
  What this example demonstrates.

---

## Complete Code

\`\`\`python
# Full example code with comments
\`\`\`

---

## Key Points

- Point 1
- Point 2

---

## See Also

- [[Related Example]]
- [[Related Guide]]
```

---

## When to Use Logseq Format

### ✅ ALWAYS Use Logseq Format For:

1. **Primitives documentation** - Permanent API reference
2. **Guides** - Tutorial and conceptual documentation
3. **How-To guides** - Step-by-step instructions
4. **Examples** - Code samples and demonstrations
5. **Architecture docs** - Design decisions and patterns
6. **Package pages** - Package-level documentation
7. **Agent instructions** - Rules and guidelines for agents

### ⚠️ Bare `.md` Acceptable For:

1. **Session notes** - Temporary working notes during development
2. **Scratch files** - Quick calculations or brainstorming
3. **Draft content** - Before finalizing into proper Logseq format
4. **External imports** - Third-party `.md` files not yet migrated

**RULE:** If you're unsure whether content will be needed later, use Logseq format.

---

## Migration Workflow

### Converting Bare `.md` to Logseq

**Step 1: Add Properties**

```markdown
# Original bare .md
# Some Title

Content here...
```

**↓ Convert to ↓**

```markdown
# Some Title

type:: [[Guide]]
category:: [[Topic]]
difficulty:: [[Intermediate]]

---

## Overview

- id:: some-title-overview
  Content here...
```

**Step 2: Rename File**

```bash
# Old
some-file.md

# New
TTA.dev___Namespace___Some Title.md
```

**Step 3: Update Links**

```markdown
# Old
See [some file](some-file.md)

# New
See [[TTA.dev/Namespace/Some Title]]
```

---

## Validation Tools

### Check for Logseq Properties

```bash
# Find .md files without properties
find logseq/pages -name "*.md" | while read file; do
  if ! grep -q "^type::" "$file"; then
    echo "❌ Missing properties: $file"
  fi
done
```

### Verify Property Format

```python
import re
from pathlib import Path

def validate_logseq_properties(file_path: Path) -> bool:
    """Check if file has valid Logseq properties."""
    content = file_path.read_text()

    # Check for type:: property
    if not re.search(r'^type::', content, re.MULTILINE):
        return False

    # Check for category:: property
    if not re.search(r'^category::', content, re.MULTILINE):
        return False

    # Check for separator
    if '---' not in content:
        return False

    return True

# Usage
for md_file in Path("logseq/pages").glob("*.md"):
    if not validate_logseq_properties(md_file):
        print(f"❌ Invalid: {md_file}")
```

---

## Agent Workflow Integration

### For Copilot/AI Assistants

When creating documentation:

1. **Check purpose:** Is this permanent or temporary?
2. **Choose format:**
   - Permanent → Use Logseq format
   - Temporary → Bare `.md` (with warning in filename)
3. **Follow template:** Use appropriate template from this guide
4. **Add properties:** All required properties for document type
5. **Use namespaces:** Proper `TTA.dev___Namespace___Title.md` naming
6. **Link properly:** Use `[[TTA.dev/Namespace/Title]]` links
7. **Add block IDs:** For key concepts and examples

### Example Session Flow

**User:** "Create documentation for the new CachePrimitive"

**Agent Response:**

```markdown
I'll create permanent documentation using Logseq format:

File: `logseq/pages/TTA.dev___Primitives___CachePrimitive.md`

Properties:
- type:: [[Primitive]]
- category:: [[Performance]], [[Caching]]
- composition:: [[Wraps any primitive]]
- imports:: tta_dev_primitives.performance

[Creates full Logseq-formatted document]
```

---

## Best Practices for Agents

### DO ✅

1. **Default to Logseq format** - When in doubt, use Logseq
2. **Ask if uncertain** - "Should this be permanent documentation?"
3. **Use templates** - Follow document-type templates
4. **Add all required properties** - Don't skip properties
5. **Use proper namespacing** - Follow `___` separator convention
6. **Create block IDs** - For reusable content
7. **Link extensively** - Connect related documents

### DON'T ❌

1. **Don't create bare `.md` for permanent docs**
2. **Don't skip properties** - Even if in a hurry
3. **Don't use custom property names** - Stick to standards
4. **Don't forget separators** - Always add `---` after properties
5. **Don't use spaces in namespaces** - Use `___` not ` / `
6. **Don't nest namespaces too deeply** - Max 2-3 levels
7. **Don't create orphan pages** - Always link from somewhere

---

## Cleanup Strategy

### Identifying Temporary Files

```bash
# Find bare .md files in root
find . -maxdepth 1 -name "*.md" | grep -v "README\|AGENTS\|GETTING_STARTED"

# Find .md files without properties
grep -L "^type::" *.md 2>/dev/null
```

### Safe Cleanup Process

1. **Review file content** - Is it still needed?
2. **Check for references** - Any links to this file?
3. **Migrate if valuable** - Convert to Logseq format
4. **Delete if temporary** - Remove if truly temporary

```bash
# Archive before deleting
mkdir -p archive/$(date +%Y-%m-%d)
mv temporary-note.md archive/$(date +%Y-%m-%d)/

# Delete after verification
rm temporary-note.md
```

---

## Examples

### ✅ Correct Logseq Documentation

**File:** `logseq/pages/TTA.dev___Guides___Error Handling.md`

```markdown
# Guide: Error Handling Patterns

type:: [[Guide]]
category:: [[Error Handling]], [[Best Practices]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
prerequisites:: [[TTA.dev/Guides/Agentic Primitives]]

---

## Overview

- id:: error-handling-overview
  This guide covers error handling patterns in TTA.dev workflows.

---

## Content here...
```

**Why it's correct:**
- ✅ Has required properties (`type::`, `category::`, `difficulty::`)
- ✅ Uses proper namespace (`TTA.dev___Guides___`)
- ✅ Has separator (`---`)
- ✅ Has block ID for overview
- ✅ Uses `[[]]` links for properties

### ❌ Incorrect (Will be deleted)

**File:** `error-handling-notes.md`

```markdown
# Error Handling Notes

Just some thoughts on error handling...

- Use try/except
- Add logging
- etc.
```

**Why it's wrong:**
- ❌ No properties
- ❌ No namespace
- ❌ No separator
- ❌ No block IDs
- ❌ Bare `.md` format

**This file will be deleted as temporary!**

---

## Integration with TTA.dev Workflows

### Agentic Primitives Context

The Logseq documentation standard integrates with TTA.dev's agentic primitives:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext # Keep import for now, will address later if needed

class DocumentationPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive that creates Logseq-formatted documentation."""

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext # This is a code example, will address later if needed
    ) -> dict:
        # Extract doc type from context
        doc_type = input_data.get("type", "Guide")

        # Validate required properties
        required_props = ["type", "category"]
        if doc_type == "Guide":
            required_props.append("difficulty")

        # Generate Logseq properties
        properties = self._generate_properties(input_data, required_props)

        # Generate content with proper structure
        content = self._generate_content(
            properties=properties,
            sections=input_data["sections"],
            block_ids=True  # Always add block IDs
        )

        # Validate format
        if not self._validate_logseq_format(content):
            raise ValueError("Generated content missing required Logseq properties")

        return {"content": content, "format": "logseq"}
```

---

## Monitoring and Metrics

### Track Documentation Quality

```python
def audit_documentation(docs_path: Path) -> dict:
    """Audit documentation for Logseq compliance."""
    stats = {
        "total_files": 0,
        "logseq_formatted": 0,
        "missing_properties": [],
        "bare_md_files": []
    }

    for md_file in docs_path.glob("**/*.md"):
        stats["total_files"] += 1

        content = md_file.read_text()

        # Check for properties
        if re.search(r'^type::', content, re.MULTILINE):
            stats["logseq_formatted"] += 1
        else:
            stats["bare_md_files"].append(str(md_file))

        # Check individual properties
        if not re.search(r'^type::', content, re.MULTILINE):
            stats["missing_properties"].append((str(md_file), "type"))
        if not re.search(r'^category::', content, re.MULTILINE):
            stats["missing_properties"].append((str(md_file), "category"))

    # Calculate compliance
    stats["compliance_rate"] = (
        stats["logseq_formatted"] / stats["total_files"] * 100
        if stats["total_files"] > 0
        else 0
    )

    return stats

# Usage
stats = audit_documentation(Path("logseq/pages"))
print(f"Compliance rate: {stats['compliance_rate']:.1f}%")
print(f"Bare .md files: {len(stats['bare_md_files'])}")
```

---

## FAQ

### Q: What if I'm not sure if content will be permanent?

**A:** Default to Logseq format. It's easier to delete a Logseq file than to migrate a bare `.md` later.

### Q: Can I use Logseq format outside the `logseq/` directory?

**A:** No. Logseq format is specifically for the `logseq/pages/` directory. Other `.md` files (like `README.md`, `AGENTS.md`) use standard markdown.

### Q: What about CHANGELOG.md and similar standard files?

**A:** Standard project files (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE.md`) remain as bare `.md` in the repository root. They're exceptions to the rule.

### Q: How do I handle code snippets in Logseq?

**A:** Use standard markdown code fences with language specifiers:

````markdown
```python
from tta_dev_primitives import RetryPrimitive
```
````

### Q: Can I nest namespaces more than 3 levels?

**A:** Avoid deep nesting. Keep it to 2-3 levels maximum:
- ✅ `TTA.dev___Guides___Workflow Composition`
- ✅ `TTA.dev___Primitives___Core___SequentialPrimitive`
- ❌ `TTA.dev___Team___Backend___Services___API___Handlers` (too deep!)

### Q: What happens to existing bare `.md` files?

**A:** They will be gradually:
1. **Reviewed** - Determine if permanent or temporary
2. **Migrated** - Convert permanent docs to Logseq format
3. **Deleted** - Remove temporary notes and scratch files

---

## Enforcement

### Automated Checks (CI/CD)

```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation

on: [pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Logseq format
        run: |
          python scripts/validate-logseq-docs.py

      - name: Report violations
        if: failure()
        run: |
          echo "❌ Documentation validation failed!"
          echo "See job logs for files missing Logseq properties."
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for new .md files without Logseq properties
NEW_MD_FILES=$(git diff --cached --name-only --diff-filter=A | grep '\.md$')

for file in $NEW_MD_FILES; do
  if [[ ! "$file" =~ ^(README|AGENTS|CHANGELOG|CONTRIBUTING|LICENSE)\.md$ ]]; then
    if ! grep -q "^type::" "$file" 2>/dev/null; then
      echo "❌ Error: $file is missing Logseq properties"
      echo "   Add 'type::' and 'category::' properties at the top"
      exit 1
    fi
  fi
done
```

---

## Key Takeaways

1. **All permanent docs use Logseq format** - No exceptions
2. **Bare `.md` = temporary** - Will be deleted without warning
3. **Properties are required** - `type::`, `category::`, plus type-specific
4. **Use namespaces** - `TTA.dev___Namespace___Title.md` format
5. **Add block IDs** - For reusable content
6. **Link extensively** - Connect related documents
7. **Validate regularly** - Use automated tools to check compliance

**Remember:** When in doubt, use Logseq format. It's the standard for TTA.dev documentation.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Priority:** [[Critical]]
**Applies To:** [[All AI Agents]], [[GitHub Copilot]], [[Development Team]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___guides___logseq documentation standards for agents]]
