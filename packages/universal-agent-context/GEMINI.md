# Project: TTA.dev - AI Development Toolkit

## Overview
TTA.dev is a production-ready AI development toolkit for building reliable, observable, and composable AI-native applications. It provides a robust set of agentic primitives and workflow patterns that empower developers to create complex AI systems and intelligent agents with confidence. This repository contains the core framework, while specific applications (like the Therapeutic Text Adventure game) are built using this framework.

## Tech Stack
- **Core Language:** Python 3.11+
- **Package Management:** uv
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Quality Tools:** ruff (linting, formatting), pyright (type checking)
- **Observability:** OpenTelemetry, Prometheus

## Project Structure
The project is a monorepo containing several key packages:
```
/home/thein/repos/TTA.dev/
├── packages/
│   ├── tta-dev-primitives/          # Core workflow primitives (Sequential, Parallel, Router, etc.)
│   ├── tta-observability-integration/  # OpenTelemetry and Prometheus integration
│   ├── universal-agent-context/      # This package, for agent context management
│   ├── keploy-framework/             # API testing framework
│   └── python-pathway/               # Python code analysis utilities
├── docs/                             # Comprehensive documentation
├── scripts/                          # Automation and validation scripts
└── tests/                            # Integration tests for the framework
```

## Code Style & Patterns
- **Composition over Inheritance:** Workflows are built by composing primitives using operators like `>>` (sequential) and `|` (parallel).
- **Strong Typing:** Python 3.11+ style type hints are required and enforced with Pyright.
- **Observability by Default:** Primitives are instrumented with OpenTelemetry for tracing and metrics.
- **Async First:** The framework is built around `async/await` patterns.

## AI Agent Support
TTA.dev provides comprehensive support for building sophisticated AI agents through:
- **Agentic Primitives:** A rich set of reusable building blocks (e.g., Sequential, Parallel, Router) for constructing complex agent workflows.
- **Workflow Patterns:** Established patterns for orchestrating agent behaviors, enabling robust and scalable AI applications.
- **Observability:** Built-in OpenTelemetry integration for tracing and monitoring agent execution, crucial for debugging and understanding agent decisions.
- **Modularity:** Designed for modularity, allowing easy integration of various AI models, tools, and external services into agent architectures.

## Current Mission: Framework/Application Separation

### Context
The repository currently contains code and context for both the `TTA.dev` framework and the `TTA` application. The mission is to refactor the repository to create a clean separation between the two.

### Goals
1.  **Isolate Framework:** Ensure the root of the repository and its core packages contain only generic, reusable framework code.
2.  **Isolate Application:** Move all code, documentation, and artifacts specific to the Therapeutic Text Adventure (TTA) game into a distinct directory (e.g., `example-applications/tta/`).
3.  **Update Imports:** Correct all import paths that break as a result of the file relocation.
4.  **Verify Integrity:** Ensure all framework tests pass after the refactoring is complete.

## Common Commands

### Development
```bash
# Sync all dependencies
uv sync --all-extras

# Run all tests
uv run pytest -v

# Run quality checks (format, lint, type-check)
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
```

---

**Last Updated:** 2025-10-30
**Current Session:** framework-application-separation
**Current Goal:** Refactor the repository to separate the TTA.dev framework from the TTA application.