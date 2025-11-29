# Agentic Runtimes Strategy

**Status**: Draft
**Created**: 2025-11-21
**Context**: Phase 3 of Agentic Reliability Rollout

## Overview

To achieve "Outer Loop" automation, TTA.dev requires an **Agentic Runtime**—a CLI tool capable of executing agentic workflows (prompts) outside the IDE. We treat these runtimes as interchangeable execution engines, similar to how we treat LLM models.

## The "Agentic Runtime" Abstraction

An Agentic Runtime must support:
1.  **Prompt Injection**: Accepting a markdown prompt file (`.prompt.md`).
2.  **Context Awareness**: Reading the repository context.
3.  **Tool Execution**: Running shell commands, file edits, etc.
4.  **Headless/YOLO Mode**: Running without user interaction (for CI/CD).

## Supported Runtimes

### 1. Gemini CLI (`gemini`)
*Primary runtime for local automation.*
- **Pros**: Fast, supports `--yolo` mode, good tool integration.
- **Cons**: Requires separate installation/auth.
- **Config**: `.gemini/settings.json`

### 2. GitHub Copilot CLI (`gh copilot`)
*Standard runtime for GitHub ecosystem.*
- **Pros**: Ubiquitous, integrated auth.
- **Cons**: "Suggest" vs "Explain" modes are limited; full agentic mode is evolving.
- **Config**: Standard `gh` config.

### 3. Cline (`cline`)
*Advanced runtime for complex tasks.*
- **Pros**: Powerful, supports MCP, "Super-Cline" integration.
- **Cons**: Primarily VS Code extension, CLI support varies.
- **Config**: `.clinerules`, `.cline/`

## Configuration Strategy

We standardize configuration via the **Agent Package Manager (APM)**.

### `apm.yml` Abstraction
Workflows in `apm.yml` should use a generic runner script that dispatches to the configured runtime.

```yaml
scripts:
  feature-implementation: "python scripts/run_agent.py --prompt .github/prompts/feature-implementation.prompt.md"
```

### `scripts/run_agent.py` (Proposed)
A wrapper script that:
1.  Reads `TTA_AGENT_RUNTIME` env var (default: `gemini`).
2.  Translates the request to the specific CLI syntax.
    -   Gemini: `gemini --yolo -p ...`
    -   Cline: `cline run ...` (hypothetical)
3.  Handles logging and observability (Langfuse).

## Next Steps
1.  Document specific setup for each runtime.
2.  Implement `scripts/run_agent.py`.
3.  Update `apm.yml` to use the wrapper.
