# TTA.dev/Examples

**Working code examples demonstrating TTA.dev primitives and patterns.**

## Overview

This namespace contains practical, runnable examples showing how to use TTA.dev primitives in real-world scenarios.

## Production Examples

### Core Workflow Examples
- [[TTA.dev/Examples/Basic Workflow]] - Sequential composition basics
- [[TTA.dev/Examples/Parallel Execution]] - Concurrent processing patterns
- [[TTA.dev/Examples/Router Pattern]] - Dynamic model selection

### RAG Examples
- [[TTA.dev/Examples/RAG Workflow]] - Production RAG with caching and retry
- [[TTA.dev/Examples/Agentic RAG Workflow]] - Self-correcting RAG with grading
- [[TTA.dev/Examples/Memory Workflow]] - Conversational memory patterns

### Cost Optimization
- [[TTA.dev/Examples/Cost Tracking Workflow]] - Budget enforcement and metrics
- [[TTA.dev/Examples/Caching Strategy]] - 40-60% cost reduction patterns

### Multi-Agent
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Agent coordination and delegation
- [[TTA.dev/Examples/Streaming Workflow]] - Real-time response streaming

## Example Location

**Source:** `packages/tta-dev-primitives/examples/`

### Available Examples
- `basic_workflow.py` - Foundation patterns
- `rag_workflow.py` - Production RAG
- `agentic_rag_workflow.py` - Self-correcting RAG
- `cost_tracking_workflow.py` - Budget controls
- `streaming_workflow.py` - Streaming responses
- `multi_agent_workflow.py` - Agent coordination
- `memory_workflow.py` - Conversational memory

## Running Examples

```bash
# Run any example
cd packages/tta-dev-primitives
uv run python examples/rag_workflow.py

# Run all examples
for f in examples/*.py; do
  echo "Running $f..."
  uv run python "$f"
done
```

## Example Categories

### Beginner Examples
- Basic composition (`>>` operator)
- Simple error handling
- Caching patterns

### Intermediate Examples
- Multi-model routing
- Parallel execution
- Memory management

### Advanced Examples
- Multi-agent coordination
- Cost optimization
- Production patterns

## Related Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - Primitives namespace
- [[GETTING STARTED]] - Quick start guide
- [[TTA.dev/Guides]] - Usage guides

## Implementation Guide

**Reference:** `PHASE3_EXAMPLES_COMPLETE.md` - Complete implementation details

## Tags

namespace:: examples
type:: code-examples
audience:: all-users
