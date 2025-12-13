# Cline Integration Guide for TTA.dev (Super-Cline)

This guide details the enhanced Cline integration for TTA.dev, designed to provide a seamless, automated, and highly opinionated development experience. By leveraging Cline's features, TTA.dev aims to guide developers and AI agents in adhering to best practices and efficiently utilizing TTA.dev's agentic primitives.

For information on development rules, setup, and recommended extensions, please refer to the [`README.md`](README.md) and `.clinerules` files.

## 1. Cline Hooks

Cline hooks are custom scripts that run automatically at specific points in Cline's workflow. For TTA.dev, project-specific hooks are configured in the `.cline/hooks/` directory.

### Implemented Hooks

*   **`PreToolUse`**: Enforces the use of `uv` for package management.
*   **`TaskStart`**: Automatically runs `uv sync --all-extras` to ensure all project dependencies are in place and injects TTA.dev-specific context into Cline's understanding.

## 2. TTA.dev Primitives as MCP Tools

TTA.dev's core agentic primitives are exposed as custom Cline tools through a Model Context Protocol (MCP) server named `tta-primitives-server`. This allows Cline to directly invoke and integrate TTA.dev's powerful workflow building blocks into its own operations.

### Implemented MCP Tools

*   **`execute_sequential_primitive`**: Executes a TTA.dev `SequentialPrimitive` workflow.
*   **`execute_retry_primitive`**: Executes a TTA.dev `RetryPrimitive` around a specified target primitive.

For more details on MCP servers, refer to [`MCP_SERVERS.md`](MCP_SERVERS.md).

## Conclusion

This enhanced Cline integration for TTA.dev aims to significantly enhance the developer experience by automating setup, enforcing coding standards, and providing Cline with direct programmatic access to TTA.dev's powerful agentic primitives.

---

**Last Updated:** 2025-11-10


---
**Logseq:** [[TTA.dev/Docs/Guides/Cline_integration_guide]]
