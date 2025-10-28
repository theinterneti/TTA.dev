# Claude-Specific Instructions

> **Note**: This file provides Claude-specific guidance. For general agent behavior applicable to all AI assistants, see [`AGENTS.md`](./AGENTS.md).

## Purpose

`CLAUDE.md` contains instructions specific to Claude's capabilities, reasoning style, and features. This file is used by:

- **Cline** (uses Claude as backend)
- **Augment** (when configured with Claude models)
- **GitHub Copilot** (when using Claude models)
- **Any tool using Claude 3.5 Sonnet, Opus, or other Claude models**

## When to Use CLAUDE.md vs AGENTS.md

| File | Purpose | Example Content |
|------|---------|-----------------|
| **AGENTS.md** | Universal behavior for all agents | "Be concise", "Prioritize type safety", "Use primitives" |
| **CLAUDE.md** | Claude-specific capabilities/preferences | "Use artifacts for code generation", "Leverage extended context" |

**Rule of thumb**: If the instruction applies to any AI assistant (Copilot, Cline, Cursor), put it in `AGENTS.md`. If it's specific to Claude's capabilities, put it here.

---

# Claude-Specific Capabilities

## Artifacts

Claude can generate content in artifacts (separate, editable documents). When generating substantial code files or documentation:

- Use artifacts for complete, standalone files (>50 lines)
- Use inline code blocks for small snippets or examples
- Create separate artifacts for different file types (Python, config, docs)

## Extended Context

Claude has extended context windows (200K+ tokens). Leverage this:

- Reference multiple files when needed without concern for token limits
- Provide comprehensive context from the workspace
- Don't hesitate to include full file contents for analysis

## Reasoning Style

Claude excels at step-by-step reasoning:

- **Think through complex problems** using the `<thinking>` pattern
- **Break down multi-step tasks** into clear phases
- **Explain the "why"** behind architectural decisions

## Structured Output

Claude works well with XML and structured formats:

- Use XML tags for structured thinking: `<analysis>`, `<implementation>`, `<verification>`
- Prefer clear hierarchical structures over flat lists
- Use markdown tables for comparative information

## Extended Thinking Mode

Claude supports Extended Thinking mode for complex reasoning:

- Available for deep problem analysis and planning
- Useful for architecture decisions, debugging complex issues
- Access via chat mode selection in supported tools


# Claude-Specific Workflows

## When Working with tta-dev-primitives

1. **Composition over Implementation**
   - Before writing manual async code, check if primitives solve the problem
   - Suggest primitive-based refactoring for manual patterns
   - Use `MockPrimitive` for testing workflows

2. **Type Safety First**
   - Generate full type annotations using Python 3.11+ style (`T | None`)
   - Use `WorkflowPrimitive[InputType, OutputType]` for new primitives
   - Leverage Pydantic v2 models for data structures

3. **Documentation Standards**
   - Include docstrings with examples for all public APIs
   - Show before/after code when suggesting refactoring
   - Reference existing examples in `packages/tta-dev-primitives/examples/`

## When Generating Code

1. **Complete Solutions**
   - Generate runnable code with all imports
   - Include test files using `@pytest.mark.asyncio`
   - Add docstrings with usage examples

2. **Quality Checks**
   - Suggest running quality checks: `ruff format`, `ruff check`, `pyright`
   - Remind about test coverage: `uv run pytest --cov=packages`
   - Note any deviations from coding standards

3. **Package Management**
   - Always use `uv` commands, never `pip` directly
   - Show correct commands: `uv run pytest -v`, `uv sync --all-extras`
   - Reference the primitives package when available

## Multi-File Refactoring

When refactoring across multiple files:

1. Start with dependency analysis (which files depend on what)
2. Update in topological order (dependencies first, dependents second)
3. Run tests after each major change
4. Provide a summary of changes per file

## Architecture Analysis

When analyzing system architecture:

1. Use diagrams or structured markdown for component relationships
2. Identify coupling points and suggest improvements
3. Consider testability, maintainability, and performance
4. Reference existing patterns in the codebase

## Performance Optimization

When optimizing performance:

1. Profile before optimizing (suggest profiling commands)
2. Use `ParallelPrimitive` for independent operations
3. Add `CachePrimitive` to avoid redundant work
4. Measure impact with benchmarks


# Claude-Specific Preferences

## Response Format

- **Progress Updates**: After 3-5 tool calls or file edits, provide a brief progress summary
- **Code Changes**: Use edit tools, not full file dumps in chat
- **Error Handling**: Explain root cause first, then provide specific fix

## Tone & Communication

- **Concise but Complete**: Respect user's time while providing full context
- **Specific Examples**: Use actual file names, line numbers, function names
- **Proactive Suggestions**: Anticipate follow-up questions and address them

## Context Management

- **File References**: Use backticks for filenames: `packages/tta-dev-primitives/src/core/base.py`
- **Code References**: Reference specific functions/classes: `WorkflowPrimitive.execute()`
- **Documentation Links**: Point to relevant files: See `docs/architecture/Overview.md`

## Chat Modes

Claude offers different chat modes for different tasks:

- **Normal Mode**: General conversation and code assistance
- **Extended Thinking**: Deep reasoning for complex problems, architecture decisions
- **Code Mode**: Optimized for code generation and editing

Choose the appropriate mode based on task complexity and user needs.


# MCP Integration with Claude

## Model Context Protocol (MCP)

Claude integrates with MCP servers to extend capabilities with external tools and data sources.

## Available MCP Servers

When working in this repository, the following MCP servers may be available:

### Context7 MCP Server

Provides access to library documentation:

- **Use for**: Fetching up-to-date library docs (React, Python packages, frameworks)
- **Tool**: `resolve-library-id` → `get-library-docs`
- **Example**: Validating API usage, checking latest features

### Grafana MCP Server

Provides monitoring and observability integration:

- **Use for**: Querying metrics, dashboards, alerts
- **Tools**: Dashboard queries, alert rules, data source queries
- **Example**: Analyzing system performance, debugging production issues

### Sift MCP Server

Provides investigation and analysis capabilities:

- **Use for**: Root cause analysis, incident investigation
- **Tools**: Investigation management, analysis retrieval
- **Example**: Tracking debugging sessions, documenting findings

### Pylance MCP Server

Provides Python language analysis:

- **Use for**: Type checking, import analysis, syntax validation
- **Tools**: Syntax error checking, import resolution, refactoring
- **Example**: Validating Python code before execution

## MCP Workflow Patterns

### Documentation Lookup Workflow

```text
User asks about library API
↓
resolve-library-id (get Context7 ID)
↓
get-library-docs (fetch documentation)
↓
Apply knowledge to current task
```

### Debugging Workflow

```text
User reports issue
↓
Check Grafana metrics (identify anomalies)
↓
Query Loki logs (find error patterns)
↓
Create Sift investigation (track analysis)
↓
Apply fix and verify
```

### Code Quality Workflow

```text
Generate Python code
↓
pylance syntax check (validate before running)
↓
pylance import analysis (verify dependencies)
↓
Run tests with pytest
```

## MCP Server Discovery

Use the appropriate MCP tool based on task:

- **Library docs?** → Context7
- **System metrics?** → Grafana
- **Investigation tracking?** → Sift
- **Python validation?** → Pylance

## Integration with tta-dev-primitives

MCP servers can be integrated into workflow primitives:

```python
# Example: Documentation lookup primitive
class DocLookupPrimitive(WorkflowPrimitive[str, str]):
    async def execute(self, library_name: str, context: WorkflowContext) -> str:
        # Use Context7 MCP to fetch docs
        library_id = await resolve_library_id(library_name)
        docs = await get_library_docs(library_id)
        return docs
```

Consider creating primitives that wrap MCP tools for reusable workflows.


---

## Integration with Universal Config System

This file is **generated** by the universal config system from `.universal-instructions/claude-specific/`.

To regenerate `CLAUDE.md`:

```bash
./scripts/config/generate-configs.sh
```

Or directly:

```bash
cd /home/thein/repos/TTA.dev
uv run python scripts/config/generate_assistant_configs.py
```

## Source Files

The content in this file is generated from:

- `.universal-instructions/claude-specific/capabilities.md` - Claude-specific features
- `.universal-instructions/claude-specific/workflows.md` - Project-specific workflows
- `.universal-instructions/claude-specific/preferences.md` - Response formatting and tone
- `.universal-instructions/claude-specific/mcp-integration.md` - MCP server integration

## References

- **Workspace Behavior**: [`AGENTS.md`](./AGENTS.md) - Universal agent behavior
- **Technical Config**: `.cline/instructions.md` - Cline tool-specific config
- **Universal Source**: `.universal-instructions/` - Source of truth for generated configs

---

**Last Updated**: October 28, 2025

**Note**: Do not edit this file directly. Make changes in `.universal-instructions/claude-specific/` and regenerate.
