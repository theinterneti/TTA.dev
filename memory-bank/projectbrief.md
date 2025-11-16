# TTA.dev Project Brief

TTA.dev is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

## Core Requirements
- Composable workflow primitives (Sequential, Parallel, Router, etc.)
- Built-in observability (OpenTelemetry integration)
- Type-safe composition with operators (`>>`, `|`)
- 100% test coverage required
- Python 3.11+ with modern type hints

## Package Manager
**CRITICAL:** ALWAYS use `uv`, never `pip` or `poetry`

## Type Hints Style
**CRITICAL:** Use `str | None` NOT `Optional[str]`
