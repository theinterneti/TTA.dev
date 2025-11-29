# GETTING STARTED

**Quick start guide for new TTA.dev users.**

## Overview

This page is a reference to the main getting started documentation.

**Primary documentation:** `GETTING_STARTED.md` (repository root)

## Quick Links

### Installation
```bash
# Install with pip
pip install tta-dev-primitives

# Or with uv (recommended)
uv pip install tta-dev-primitives
```

### Your First Workflow
```python
from tta_dev_primitives import (
    CachePrimitive,
    RouterPrimitive,
    RetryPrimitive,
    WorkflowContext
)

# Compose workflow
workflow = (
    CachePrimitive(ttl=3600) >>
    RouterPrimitive(tier="balanced") >>
    RetryPrimitive(max_attempts=3)
)

# Execute
context = WorkflowContext(trace_id="req-123")
result = await workflow.execute({"input": "Hello"}, context)
```

## Learning Path

### For New Users
1. [[New Users]] - New user onboarding
2. [[TTA.dev/Quick Start]] - 5-minute quick start
3. [[TTA.dev/Examples/Basic Workflow]] - Simple examples

### For Developers
1. [[Developers]] - Developer guide
2. [[TTA.dev/Guides/Workflow Composition]] - Composition patterns
3. [[TTA.dev/Primitives]] - Primitives reference

### For AI Engineers
1. [[AI Engineers]] - AI engineer guide
2. [[TTA.dev/Examples/RAG Workflow]] - Production RAG example
3. [[TTA.dev/Guides/Cost Optimization]] - Cost reduction strategies

## Core Concepts

- [[TTA.dev/Concepts/Primitives]] - What are primitives?
- [[TTA.dev/Concepts/Composition]] - Composing workflows
- [[WorkflowContext]] - Managing workflow state
- [[TTA.dev/Observability]] - Built-in observability

## Common Patterns

- [[TTA.dev/Patterns/Sequential Workflow]] - Step-by-step execution
- [[TTA.dev/Patterns/Parallel Execution]] - Concurrent processing
- [[TTA.dev/Patterns/Error Handling]] - Recovery patterns
- [[TTA.dev/Patterns/Caching]] - Cost optimization

## Reference

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - Primitives namespace
- [[TTA.dev/Examples]] - Working code examples
- [[TTA.dev (Meta-Project)]] - Project overview

## External Links

- Repository: [GETTING_STARTED.md](file://../../GETTING_STARTED.md)
- GitHub: <https://github.com/theinterneti/TTA.dev/blob/main/GETTING_STARTED.md>

## Tags

guide:: getting-started
audience:: all-users
