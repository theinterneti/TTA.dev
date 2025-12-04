# Beginner

**Entry-level difficulty for users new to TTA.dev**

type:: difficulty-level
status:: active
level:: 1

---

## Overview

**Beginner** content is designed for users who are:

🆕 New to TTA.dev
📚 Learning workflow primitives
🐍 Familiar with Python basics
⚡ Understanding async/await

**No prior TTA.dev knowledge required!**

---

## Prerequisites

### Required Knowledge

Python 3.11+ basics
Understanding of `async`/`await`
Basic command line usage
pip/uv package management

### Helpful But Optional

OpenTelemetry concepts
API development experience
Testing frameworks (pytest)

---

## What You'll Learn

### Core Concepts

**Primitives** - Building blocks of workflows
**Context** - Data flow between primitives
**Composition** - Combining primitives
**Execution** - Running workflows

### Key Primitives

[[SequentialPrimitive]] - Run steps in order
[[ParallelPrimitive]] - Run steps concurrently
[[LambdaPrimitive]] - Custom logic wrapper

---

## Beginner Content

### Start Here

1. [[GETTING_STARTED]] - Installation and setup
2. [[TTA.dev/Guides/Getting Started]] - First workflow
3. [[PRIMITIVES_CATALOG]] - Primitive reference

### Guides

{{query (and (property difficulty [[Beginner]]) (property type Guide))}}

### Examples

[[TTA.dev/Examples/Hello World]]
[[TTA.dev/Examples/Simple Pipeline]]
[[TTA.dev/Examples/Basic Composition]]

---

## Learning Path

```
┌──────────────────────────────────────────────┐
│  🟢 BEGINNER PATH                            │
├──────────────────────────────────────────────┤
│  1. Install TTA.dev                          │
│  2. Create first primitive                   │
│  3. Compose two primitives                   │
│  4. Add workflow context                     │
│  5. Run and observe                          │
└──────────────────────────────────────────────┘
         ↓
    [[Intermediate]]
```

### Milestone: First Workflow

After completing beginner content, you should be able to:
[x] Install tta-dev-primitives package
[x] Create a simple primitive
[x] Compose primitives with `>>`
[x] Pass context between steps
[x] Execute and view results

---

## Quick Start

```python
from tta_dev_primitives import SequentialPrimitive, LambdaPrimitive

# Create simple primitives
hello = LambdaPrimitive(lambda ctx: {**ctx, "greeting": "Hello"})
world = LambdaPrimitive(lambda ctx: {**ctx, "message": ctx["greeting"] + " World!"})

# Compose them
workflow = hello >> world

# Execute
result = await workflow.execute({"user": "Developer"})
print(result["message"])  # "Hello World!"
```

---

## Difficulty Levels

| Level | Icon | Description |
|-------|------|-------------|
| **Beginner** | 🟢 | No prior knowledge needed |
| [[Intermediate]] | 🟡 | Foundational knowledge required |
| [[Advanced]] | 🔴 | Deep expertise needed |

---

## Next Steps

After mastering beginner content:
Move to [[Intermediate]] level
Explore [[Recovery Patterns]]
Learn about [[TTA.dev/Observability]]

---

## Related

[[Intermediate]] - Next difficulty level
[[Advanced]] - Expert level content
[[TTA.dev/Learning Paths]] - Structured learning
[[Guide]] - All guides
[[Developers]] - Target audience

---

**Tags:** #difficulty-level #beginner #learning #getting-started

**Last Updated:** 2025-12-04
