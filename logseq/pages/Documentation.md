# Documentation

**Tag page for documentation, guides, and knowledge resources**

---

## Overview

**Documentation** in TTA.dev includes:
- 📚 API documentation
- 📖 User guides and tutorials
- 🎓 Learning materials
- 📋 Architecture documents
- 💡 Best practices guides

**Goal:** Make TTA.dev accessible, understandable, and usable for all skill levels.

**See:** [[TTA.dev/Best Practices]], [[Learning TTA Primitives]]

---

## Pages Tagged with #Documentation

{{query (page-tags [[Documentation]])}}

---

## Documentation Categories

### 1. API Documentation

**Reference documentation:**
- Class/method signatures
- Parameter descriptions
- Return value types
- Usage examples
- Error handling

**Examples:**
- [[PRIMITIVES_CATALOG]] - Complete primitive reference
- [[WorkflowPrimitive]] - Base class API
- [[TTA Primitives/RouterPrimitive]] - Router API

**See:** [[TTA.dev/API Reference]]

---

### 2. User Guides

**Step-by-step tutorials:**
- Getting started guides
- Feature walkthroughs
- Integration guides
- Migration guides
- Troubleshooting guides

**Examples:**
- [[GETTING_STARTED]] - Quick start guide
- [[TTA.dev/Integration Guide]] - Integration patterns
- [[TTA.dev/Migration Guide]] - Version upgrades

**See:** [[TTA.dev/Guides]]

---

### 3. Architecture Documentation

**Design and decision records:**
- System architecture
- Design decisions
- Component interactions
- Data flows
- Performance considerations

**Examples:**
- [[TTA.dev/Architecture Overview]] - System design
- [[TTA.dev/Architecture/Agent Discoverability]] - Agent patterns
- [[TTA.dev/Architecture/Primitive Composition]] - Composition design

**See:** [[TTA.dev/Architecture]]

---

### 4. Learning Materials

**Educational resources:**
- Flashcards
- Exercises
- Examples
- Tutorials
- Workshops

**Examples:**
- [[Learning TTA Primitives]] - Flashcard system
- [[TTA.dev/Learning Paths]] - Structured learning
- [[TTA.dev/Examples]] - Code examples

**See:** [[TTA.dev/Learning Paths]]

---

### 5. Best Practices

**Guidance and patterns:**
- Coding standards
- Testing practices
- Performance optimization
- Security guidelines
- Production patterns

**Examples:**
- [[TTA.dev/Best Practices]] - General guidelines
- [[TTA.dev/Testing Best Practices]] - Test patterns
- [[TTA.dev/Performance Best Practices]] - Optimization

**See:** [[TTA.dev/Best Practices]]

---

## Documentation Structure

### Repository Documentation

**Root-Level Docs:**
```
TTA.dev/
├── README.md                    # Project overview
├── GETTING_STARTED.md           # Quick start
├── PRIMITIVES_CATALOG.md        # Primitive reference
├── AGENTS.md                    # Agent instructions
├── MCP_SERVERS.md               # MCP integration
├── CONTRIBUTING.md              # Contribution guide
├── CHANGELOG.md                 # Version history
└── docs/
    ├── architecture/            # Architecture docs
    ├── guides/                  # User guides
    ├── knowledge/               # Knowledge base
    └── observability/           # Observability docs
```

---

### Package Documentation

**Each package includes:**
```
packages/tta-dev-primitives/
├── README.md                    # Package overview
├── AGENTS.md                    # Agent guidance
├── docs/
│   ├── api/                     # API reference
│   ├── guides/                  # Usage guides
│   └── examples/                # Code examples
├── examples/                    # Working examples
└── tests/                       # Test documentation
```

---

### Logseq Knowledge Base

**Organized knowledge:**
```
logseq/
├── pages/                       # Wiki pages
│   ├── TTA.dev/                # Project pages
│   ├── TTA Primitives/         # Primitive pages
│   └── [Tag pages]             # Index pages
├── journals/                    # Daily entries
└── ADVANCED_FEATURES.md        # KB guide
```

**See:** [[Logseq Knowledge Base]], [[TODO Management System]]

---

## Documentation TODOs

### High-Priority Documentation

**Critical documentation needs:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "documentation") (property priority high))}}

---

### Medium-Priority Documentation

**Standard documentation work:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "documentation") (property priority medium))}}

---

### All Documentation TODOs

**Complete documentation backlog:**

{{query (and (task TODO DOING DONE) [[#dev-todo]] (property type "documentation"))}}

---

## Documentation Standards

### Writing Guidelines

**Clear and Concise:**
- Use simple language
- Short sentences
- Active voice
- Concrete examples
- Scannable format

**Structure:**
- Clear headings
- Logical flow
- Code examples
- Visual aids (diagrams)
- Links to related content

**Accessibility:**
- Plain language
- Explain jargon
- Progressive disclosure
- Multiple formats
- International audience

---

### Code Example Standards

**Good Code Examples:**

```python
# ✅ Good: Complete, runnable example
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

async def example_workflow():
    """Retry a flaky API call."""
    # Create retry primitive
    retry = RetryPrimitive(
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Execute with retry
    context = WorkflowContext(correlation_id="demo-123")
    result = await retry.execute(context, {"url": "https://api.example.com"})

    return result

# Run it
import asyncio
asyncio.run(example_workflow())
```

**Key Elements:**
- ✅ Complete imports
- ✅ Working code
- ✅ Clear comments
- ✅ Expected output
- ✅ Error handling

---

### Documentation Types

**1. Reference Documentation**
- **Purpose:** Complete API coverage
- **Format:** Auto-generated + curated
- **Audience:** Developers needing details
- **Example:** [[PRIMITIVES_CATALOG]]

**2. Tutorial Documentation**
- **Purpose:** Learn by doing
- **Format:** Step-by-step guide
- **Audience:** New users
- **Example:** [[GETTING_STARTED]]

**3. Conceptual Documentation**
- **Purpose:** Understand concepts
- **Format:** Explanatory prose
- **Audience:** All users
- **Example:** [[TTA.dev/Architecture Overview]]

**4. How-To Documentation**
- **Purpose:** Solve specific problems
- **Format:** Problem → Solution
- **Audience:** Users with specific needs
- **Example:** [[TTA.dev/Integration Guide]]

---

## Best Practices

### ✅ DO

**Start with Examples:**
```markdown
## CachePrimitive

**Example:**
\`\`\`python
from tta_dev_primitives.performance import CachePrimitive

cache = CachePrimitive(ttl_seconds=3600, max_size=1000)
workflow = cache >> expensive_operation
\`\`\`

**Parameters:**
- `ttl_seconds`: Cache TTL (default: 300)
- `max_size`: Max cache entries (default: 100)
```

**Keep Documentation Current:**
- Update with code changes
- Review regularly
- Fix broken links
- Update examples

**Use Consistent Structure:**
- Same format across docs
- Predictable organization
- Standard terminology
- Clear navigation

**Test Code Examples:**
- All examples should run
- Include expected output
- Handle errors properly
- Use realistic data

---

### ❌ DON'T

**Don't Use Broken Examples:**
```python
# ❌ Bad: Won't run
workflow = thing >> other_thing

# ✅ Good: Complete imports and setup
from tta_dev_primitives import SequentialPrimitive
workflow = step1 >> step2
```

**Don't Assume Knowledge:**
```markdown
# ❌ Bad: Assumes user knows what "primitive" means
Use the primitive to process data.

# ✅ Good: Explains concept
A primitive is a reusable workflow component that processes
input data and returns output. Use primitives to build workflows.
```

**Don't Neglect Maintenance:**
- Documentation rots quickly
- Review quarterly
- Update with releases
- Fix user-reported issues

---

## Documentation Tools

### Generation Tools

**API Documentation:**
```bash
# Generate API docs from docstrings
uv run pdoc packages/tta-dev-primitives/src

# Sphinx documentation
uv run sphinx-build docs/ docs/_build
```

**Markdown Tools:**
```bash
# Check markdown quality
uv run python scripts/docs/check_md.py --all

# Fix markdown formatting
uv run ruff format docs/
```

---

### Validation Tools

**Link Checking:**
```bash
# Validate internal links
uv run python scripts/validate_kb_links.py

# Check external links
uv run python scripts/check_external_links.py
```

**Example Testing:**
```bash
# Test code examples
uv run pytest docs/ --doctest-modules

# Test example files
uv run pytest examples/
```

**See:** [[TTA.dev/CI-CD Pipeline]]

---

## Documentation Metrics

### Quality Metrics

```promql
# Documentation coverage (pages per package)
documentation_pages_total / code_packages_total

# Example coverage (examples per primitive)
code_examples_total / primitives_total

# Freshness (days since last update)
time() - documentation_updated_timestamp
```

**Targets:**
- Coverage: 1+ page per primitive
- Examples: 2+ examples per primitive
- Freshness: Updated within 30 days

---

### Usage Metrics

```promql
# Page views (if instrumented)
documentation_page_views_total{page="/primitives"}

# Search queries
documentation_search_queries_total

# User feedback
documentation_helpful_votes_total / documentation_page_views_total
```

**See:** [[TTA.dev/Observability]]

---

## Contributing Documentation

### How to Contribute

**1. Identify Need:**
- Missing documentation
- Unclear explanation
- Outdated content
- User request

**2. Plan Documentation:**
- Define scope
- Choose format
- Outline structure
- Gather examples

**3. Write Documentation:**
- Follow standards
- Include examples
- Add cross-references
- Test code samples

**4. Review Process:**
- Self-review
- Peer review
- User testing
- Final polish

**See:** [[CONTRIBUTING]]

---

### Documentation PRs

**Good PR Description:**
```markdown
## Documentation Update: CachePrimitive Guide

### Changes
- Add comprehensive CachePrimitive guide
- Include 5 working examples
- Add performance benchmarks
- Update cross-references

### Review Checklist
- [x] Code examples tested
- [x] Links validated
- [x] Spelling checked
- [x] Structure reviewed

### Related
- Closes #123 (CachePrimitive documentation request)
- Related to [[TTA Primitives/CachePrimitive]]
```

---

## Documentation Patterns

### API Documentation Pattern

```markdown
## PrimitiveName

**Purpose:** Brief description

**Example:**
\`\`\`python
# Working code example
\`\`\`

**Parameters:**
- `param1` (type): Description
- `param2` (type, optional): Description, default: value

**Returns:**
- (return_type): Description

**Raises:**
- `ExceptionType`: When this happens

**See Also:**
- [[Related Primitive 1]]
- [[Related Primitive 2]]
```

---

### Tutorial Pattern

```markdown
## Tutorial: Building Your First Workflow

### What You'll Learn
- How to create primitives
- How to compose workflows
- How to add error handling

### Prerequisites
- Python 3.11+
- TTA.dev installed
- Basic async knowledge

### Step 1: Create Input Processor
\`\`\`python
# Code...
\`\`\`

### Step 2: Add Error Handling
\`\`\`python
# Code...
\`\`\`

### Complete Example
\`\`\`python
# Full working code
\`\`\`

### Next Steps
- Try [[Advanced Patterns]]
- Read [[Best Practices]]
```

---

## Related Concepts

- [[TTA.dev/Best Practices]] - Best practices
- [[TTA.dev/Learning Paths]] - Learning paths
- [[Examples]] - Code examples
- [[Architecture]] - Architecture docs
- [[CONTRIBUTING]] - Contributing guide

---

## Documentation Index

### Core Documentation

- [[README]] - Project overview
- [[GETTING_STARTED]] - Quick start
- [[PRIMITIVES_CATALOG]] - Primitive reference
- [[AGENTS]] - Agent instructions
- [[MCP_SERVERS]] - MCP integration
- [[CONTRIBUTING]] - Contributing guide
- [[CHANGELOG]] - Version history
- [[ROADMAP]] - Future plans
- [[VISION]] - Project vision

### Package Documentation

- [[tta-dev-primitives]] - Core primitives
- [[tta-observability-integration]] - Observability
- [[universal-agent-context]] - Agent context

### Guides

- [[TTA.dev/Integration Guide]] - Integration patterns
- [[TTA.dev/Migration Guide]] - Version upgrades
- [[TTA.dev/Testing Best Practices]] - Testing guide
- [[TTA.dev/Performance Best Practices]] - Performance guide

---

**Tags:** #documentation #guides #learning #reference #knowledge #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]