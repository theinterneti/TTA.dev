"""TTA.dev CLI - Batteries-included workflow primitives for AI agents."""

import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    print("🚀 TTA.dev - Workflow Primitives for AI Agents")
    print()
    print("Quick Start:")
    print("  1. Clone this repo: git clone https://github.com/theinterneti/TTA.dev")
    print("  2. Install: uv sync --all-extras")
    print("  3. Point your CLI agent (Copilot/Claude/Cline) at this directory")
    print("  4. Your agent will auto-detect AGENTS.md and use TTA.dev primitives")
    print()
    print("Observability UI:")
    print("  Run: tta-dev-ui")
    print("  Opens at: http://localhost:8501")
    print()
    print("Documentation:")
    print("  AGENTS.md - Agent coordination guide")
    print("  PRIMITIVES_CATALOG.md - Complete primitive reference")
    print("  GETTING_STARTED.md - Setup walkthrough")
    print()
    
    repo_root = Path(__file__).parent.parent.parent
    agents_md = repo_root / "AGENTS.md"
    
    if agents_md.exists():
        print("✅ AGENTS.md detected - your CLI agent can use TTA.dev primitives")
    else:
        print("⚠️  AGENTS.md not found - creating it now...")
        create_agents_md(repo_root)
        print("✅ Created AGENTS.md")
    
    print()
    print("For more info: https://github.com/theinterneti/TTA.dev")


def create_agents_md(repo_root: Path):
    """Create AGENTS.md if it doesn't exist."""
    content = """# TTA.dev Agents

TTA.dev provides workflow primitives that make AI coding agents reliable and production-ready.

## Quick Reference

### Core Primitives
- `SequentialPrimitive` - Execute steps in order
- `ParallelPrimitive` - Execute steps concurrently
- `ConditionalPrimitive` - Branch based on conditions
- `RouterPrimitive` - Route to different handlers

### Recovery Primitives
- `RetryPrimitive` - Retry with exponential backoff
- `TimeoutPrimitive` - Enforce time limits
- `FallbackPrimitive` - Try alternatives on failure
- `CircuitBreakerPrimitive` - Fail fast when service is down

### Performance Primitives
- `CachePrimitive` - Cache expensive operations
- `MemoryPrimitive` - Optimize memory usage

## Usage

All primitives follow the same pattern:

```python
from tta_dev.primitives import RetryPrimitive, WorkflowContext

# Create primitive
workflow = RetryPrimitive(
    primitive=my_operation,
    max_attempts=3,
    backoff_factor=2.0
)

# Execute
context = WorkflowContext(workflow_id="my-workflow")
result = await workflow.execute(input_data, context)
```

## Auto-Discovery

CLI agents (GitHub Copilot, Claude, Cline) automatically detect this file and know to use TTA.dev primitives in their code generation.

## Documentation

- `PRIMITIVES_CATALOG.md` - Complete API reference
- `GETTING_STARTED.md` - Setup guide
- `USER_JOURNEY.md` - End-to-end walkthrough
"""
    
    (repo_root / "AGENTS.md").write_text(content)


if __name__ == "__main__":
    main()
