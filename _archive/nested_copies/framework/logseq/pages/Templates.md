# Templates

**Purpose:** Reusable templates for consistent Logseq page creation
**Usage:** In Logseq, type `/template` and select the template name

---

## Template: New Primitive Documentation

template:: new-primitive

```markdown
# [Primitive Name]

type:: [[Primitive]]
category:: [[Core Workflow]] / [[Recovery]] / [[Performance]] / [[Testing]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Draft]] / [[Stable]] / [[Experimental]] / [[Deprecated]]
version:: 1.0.0
author:: [[TTA Team]]
python-class:: `ClassName`
import-path:: `from tta_dev_primitives import ClassName`
related-primitives:: [[Primitive1]], [[Primitive2]]

---

## Overview
- id:: [primitive-name]-overview
  Brief description of what this primitive does and why it's useful

## Use Cases
- id:: [primitive-name]-use-cases
  - **Use Case 1:** Description
  - **Use Case 2:** Description
  - **Use Case 3:** Description

## Key Benefits
- id:: [primitive-name]-benefits
  - **Benefit 1:** Why this matters
  - **Benefit 2:** Why this matters
  - **Benefit 3:** Why this matters

---

## API Reference
- id:: [primitive-name]-api

### Constructor
```python
ClassName(
    param1: Type1,
    param2: Type2 | None = None
)
```

### Input Types
- `InputType` - Description of what inputs are accepted

### Output Types
- `OutputType` - Description of what outputs are produced

### Configuration Options
- `param1` - Description
- `param2` - Description (optional, default: value)

---

## Examples

### Basic Example
- id:: [primitive-name]-basic-example

```python
from tta_dev_primitives import ClassName

# Basic usage
primitive = ClassName(param1="value")
result = await primitive.execute(context, input_data)
```

### Advanced Example
- id:: [primitive-name]-advanced-example

```python
# Advanced composition
workflow = (
    step1 >>
    ClassName(config) >>
    step3
)
```

### Real-World Example
- id:: [primitive-name]-real-world-example

{{embed [[TTA.dev/Examples/[Example Name]]]}}

---

## Composition Patterns
- id:: [primitive-name]-composition

### Sequential Composition
- Works well with: [[Primitive1]], [[Primitive2]]
- Pattern: `step1 >> ThisPrimitive >> step2`

### Parallel Composition
- Works well with: [[Primitive3]], [[Primitive4]]
- Pattern: `(branch1 | ThisPrimitive | branch3)`

---

## Related Content

### Related Primitives
- [[Primitive1]] - Why related
- [[Primitive2]] - Why related

### Used In Examples
{{query (and [[Example]] [[ThisPrimitiveName]])}}

### Related Guides
- [[TTA.dev/Guides/Guide Name]] - How to use this primitive

---

## Implementation Notes
- id:: [primitive-name]-implementation

### Performance Considerations
- Performance note 1
- Performance note 2

### Edge Cases
- Edge case 1
- Edge case 2

### Best Practices
- Best practice 1
- Best practice 2

---

## Metadata

**Last Updated:** [[YYYY-MM-DD]]
**Stability:** [[Stable]] / [[Experimental]]
**Test Coverage:** XX%
**Source:** [GitHub Link](https://github.com/theinterneti/TTA.dev/...)
```

---

## Template: New Example

template:: new-example

```markdown
# Example: [Example Name]

type:: [[Example]]
category:: [[Basic]] / [[Intermediate]] / [[Advanced]]
primitives:: [[Primitive1]], [[Primitive2]]
use-case:: [[Use Case]]
difficulty:: [[Beginner]] / [[Intermediate]] / [[Advanced]]
estimated-time:: X minutes
package:: [[TTA.dev/Packages/tta-dev-primitives]]

---

## Overview
- id:: [example-name]-overview
  Brief description of what this example demonstrates and why it's useful

## Learning Objectives
- id:: [example-name]-objectives
  - Learn concept 1
  - Learn concept 2
  - Learn concept 3

## Prerequisites
- id:: [example-name]-prerequisites
  - Understanding of [[Concept1]]
  - Familiarity with [[Primitive1]]
  - Basic Python async/await knowledge

---

## Complete Code
- id:: [example-name]-code

```python
"""
[Example Name]

Demonstrates: [key concepts]
Primitives: [primitives used]
"""

from tta_dev_primitives import WorkflowContext, Primitive1, Primitive2

# Step 1: Define components
# [explanation]

# Step 2: Compose workflow
workflow = (
    step1 >>
    step2 >>
    step3
)

# Step 3: Execute
context = WorkflowContext(correlation_id="example-123")
result = await workflow.execute(context, input_data)
```

---

## Step-by-Step Explanation
- id:: [example-name]-explanation

### Step 1: Setup
- Why: Explanation
- Code: `code snippet`
- Result: What happens

### Step 2: Composition
- Why: Explanation
- Code: `code snippet`
- Result: What happens

### Step 3: Execution
- Why: Explanation
- Code: `code snippet`
- Result: What happens

---

## Variations
- id:: [example-name]-variations

### Variation 1: [Name]
- What changes: Description
- Code:
```python
# Modified code
```

### Variation 2: [Name]
- What changes: Description
- Code:
```python
# Modified code
```

---

## Related Content

### Related Examples
- [[TTA.dev/Examples/Example1]] - Why related
- [[TTA.dev/Examples/Example2]] - Why related

### Uses Primitives
- {{embed [[TTA.dev/Primitives/Primitive1]]#overview}}
- {{embed [[TTA.dev/Primitives/Primitive2]]#overview}}

### Referenced By Guides
{{query (and [[Guide]] [[This Example Name]])}}

---

## Try It Yourself

### Exercise 1
- Task: Modify the example to...
- Expected outcome: ...
- Solution: [[TTA.dev/Examples/Solutions/Exercise1]]

### Exercise 2
- Task: Extend the workflow to...
- Expected outcome: ...
- Solution: [[TTA.dev/Examples/Solutions/Exercise2]]

---

## Metadata

**Source Code:** [GitHub](https://github.com/theinterneti/TTA.dev/...)
**Last Updated:** [[YYYY-MM-DD]]
**Difficulty:** [[Beginner]] / [[Intermediate]] / [[Advanced]]
**Estimated Time:** X minutes
```

---

## Template: New Guide

template:: new-guide

```markdown
# [Guide Title]

type:: [[Guide]]
category:: [[Getting Started]] / [[Concept]] / [[How-To]] / [[Decision]]
difficulty:: [[Beginner]] / [[Intermediate]] / [[Advanced]]
estimated-time:: X minutes
prerequisites:: [[Guide1]], [[Concept1]]
related-packages:: [[Package1]]

---

## Overview
- id:: [guide-name]-overview
  Brief summary of what this guide covers and who it's for

## What You'll Learn
- id:: [guide-name]-learning-objectives
  - Objective 1
  - Objective 2
  - Objective 3

## Prerequisites
- id:: [guide-name]-prerequisites

{{embed [[TTA.dev/Common/Prerequisites]]}}

---

## Main Content

### Section 1: [Title]
- id:: [guide-name]-section1

Content with explanations, code examples, and insights

### Section 2: [Title]
- id:: [guide-name]-section2

Content continues...

---

## Examples
- id:: [guide-name]-examples

{{embed [[TTA.dev/Examples/Example1]]}}

---

## Best Practices
- id:: [guide-name]-best-practices
  - Best practice 1
  - Best practice 2
  - Best practice 3

## Common Pitfalls
- id:: [guide-name]-pitfalls
  - ❌ **Anti-pattern:** Description
    - ✅ **Better approach:** Description
  - ❌ **Anti-pattern:** Description
    - ✅ **Better approach:** Description

---

## Next Steps
- id:: [guide-name]-next-steps
  - [[TTA.dev/Guides/Next Guide]] - What to learn next
  - [[TTA.dev/Examples/Example]] - Practice with examples

---

## Related Content

### Related Guides
- [[Guide1]] - Why related
- [[Guide2]] - Why related

### Referenced Primitives
{{query (and [[Primitive]] (mentions [[This Guide Name]]))}}

---

## Metadata

**Last Updated:** [[YYYY-MM-DD]]
**Difficulty:** [[Beginner]] / [[Intermediate]] / [[Advanced]]
**Estimated Time:** X minutes
```

---

## Template: Reusable Block (for Embedding)

template:: reusable-block

```markdown
# [Block Collection Name]

type:: [[Reusable Content]]
purpose:: Single source of truth for commonly embedded content

---

## Installation Prerequisites
- id:: installation-prerequisites
  ### Prerequisites
  - **Python 3.11+** - Required for modern type hints
  - **uv package manager** - NOT pip
  - **VS Code** - Recommended editor
  - **Git** - Version control

## UV Installation
- id:: uv-installation
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Basic Setup
- id:: basic-setup
  ```bash
  # Clone repository
  git clone https://github.com/theinterneti/TTA.dev.git
  cd TTA.dev

  # Sync dependencies
  uv sync --all-extras

  # Run tests
  uv run pytest -v
  ```

## Type Hints Best Practice
- id:: type-hints-best-practice
  ```python
  # ✅ Modern Python 3.11+ style
  def process(data: str | None) -> dict[str, Any]:
      ...

  # ❌ Old style
  def process(data: Optional[str]) -> Dict[str, Any]:
      ...
  ```

## WorkflowContext Pattern
- id:: workflow-context-pattern
  ```python
  from tta_dev_primitives import WorkflowContext

  # Create context with correlation ID
  context = WorkflowContext(
      correlation_id="req-12345",
      data={"user_id": "user-789"}
  )

  # Context is passed through entire workflow
  result = await workflow.execute(context, input_data)
  ```
```

---

## Template: Architecture Decision Record (ADR)

template:: adr

```markdown
# ADR-[Number]: [Title]

type:: [[Architecture Decision]]
category:: [[ADR]]
status:: [[Proposed]] / [[Accepted]] / [[Rejected]] / [[Deprecated]]
date:: [[YYYY-MM-DD]]
decision-makers:: [[Person1]], [[Person2]]
related-adrs:: [[ADR-X]], [[ADR-Y]]

---

## Context
- id:: adr-[number]-context
  What is the issue we're facing that motivates this decision?

## Decision
- id:: adr-[number]-decision
  What decision have we made?

## Rationale
- id:: adr-[number]-rationale
  Why did we choose this approach?
  - Reason 1
  - Reason 2
  - Reason 3

---

## Alternatives Considered
- id:: adr-[number]-alternatives

### Alternative 1: [Name]
- **Pros:**
  - Pro 1
  - Pro 2
- **Cons:**
  - Con 1
  - Con 2
- **Why rejected:** Reason

### Alternative 2: [Name]
- **Pros:**
  - Pro 1
- **Cons:**
  - Con 1
- **Why rejected:** Reason

---

## Consequences
- id:: adr-[number]-consequences

### Positive
- Positive consequence 1
- Positive consequence 2

### Negative
- Negative consequence 1
- Negative consequence 2

### Neutral
- Neutral consequence 1

---

## Implementation
- id:: adr-[number]-implementation

### Changes Required
- Change 1
- Change 2

### Affected Components
- [[Component1]]
- [[Component2]]

### Migration Path
- Step 1
- Step 2

---

## Related Content

### Related ADRs
- [[ADR-X]] - How this relates
- [[ADR-Y]] - How this relates

### Affected Packages
- [[TTA.dev/Packages/package1]]
- [[TTA.dev/Packages/package2]]

---

## Metadata

**Status:** [[Proposed]] / [[Accepted]] / [[Rejected]]
**Date:** [[YYYY-MM-DD]]
**Last Updated:** [[YYYY-MM-DD]]
```

---

## Template: Package Documentation

template:: package-doc

```markdown
# [Package Name]

type:: [[Package]]
package-type:: [[Core]] / [[Integration]] / [[Utility]]
status:: [[Active]] / [[Experimental]] / [[Deprecated]]
version:: X.Y.Z
python-package:: `package-name`
github:: [Repository Link]

---

## Overview
- id:: [package-name]-overview
  Brief description of what this package provides

## Purpose
- id:: [package-name]-purpose
  Why this package exists and what problems it solves

## Key Features
- id:: [package-name]-features
  - Feature 1
  - Feature 2
  - Feature 3

---

## Installation
- id:: [package-name]-installation

```bash
# Using uv (recommended)
uv add [package-name]

# Using pip
pip install [package-name]
```

---

## Quick Start
- id:: [package-name]-quickstart

```python
from [package-name] import MainClass

# Basic usage
instance = MainClass()
result = await instance.method()
```

---

## Components

### Primitives
- [[TTA.dev/Primitives/Primitive1]] - Description
- [[TTA.dev/Primitives/Primitive2]] - Description

### Utilities
- `utility1` - Description
- `utility2` - Description

---

## Examples

### Basic Example
{{embed [[TTA.dev/Examples/Package Basic]]}}

### Advanced Example
{{embed [[TTA.dev/Examples/Package Advanced]]}}

---

## API Reference

### Main Classes
logseq.table.version:: 2
| Class | Purpose | Status |
|-------|---------|--------|
| `Class1` | Description | [[Stable]] |
| `Class2` | Description | [[Experimental]] |

### Functions
logseq.table.version:: 2
| Function | Parameters | Returns |
|----------|------------|---------|
| `func1()` | `arg1: Type` | `ReturnType` |

---

## Development

### Setup
```bash
cd packages/[package-name]
uv sync
```

### Running Tests
```bash
uv run pytest -v
```

### Type Checking
```bash
uvx pyright
```

---

## Related Content

### Uses
- [[TTA.dev/Packages/dependency1]]
- [[TTA.dev/Packages/dependency2]]

### Used By
{{query (and [[Package]] (mentions [[This Package]]))}}

### Related Guides
- [[TTA.dev/Guides/Guide1]]

---

## Metadata

**Version:** X.Y.Z
**Status:** [[Active]] / [[Experimental]]
**Python:** 3.11+
**License:** [License Type]
**Maintainer:** [[TTA Team]]
```

---

## Usage Instructions

### How to Use Templates in Logseq

1. **Create a new page**
2. **Type `/template`** in a block
3. **Select the template name** from the dropdown
4. **Fill in the placeholders** (marked with `[...]`)
5. **Replace IDs** with unique block IDs for your content

### Best Practices

- **Always add block IDs** to important sections (use `id:: unique-name`)
- **Use consistent naming** for block IDs (e.g., `primitive-name-section-name`)
- **Link liberally** - use `[[Page Name]]` for any related concept
- **Embed shared content** - use `{{embed ((block-id))}}` to reuse content
- **Add properties** - use `key:: value` syntax for metadata
- **Keep it DRY** - define once in reusable blocks, embed everywhere

### Template Modification

To modify a template:

1. Edit this page
2. Update the template content
3. Template changes apply immediately to new instances

---

**Last Updated:** 2025-10-30
**Version:** 1.0
**Maintained by:** [[TTA Team]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Templates]]
