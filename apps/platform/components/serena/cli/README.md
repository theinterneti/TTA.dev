# Serena CLI Tools

**CLI Entry Point**: `serena`
**Package**: `serena-agent==0.1.4`

## Overview

This directory contains command-line interface (CLI) tools for Serena, providing direct access to code search, indexing, and project management functionality.

## Available Commands

### Main CLI: `serena`

Entry point for all Serena CLI operations.

```bash
# General usage
cd ../core
uv run serena <command> [options]
```

### MCP Server: `serena-mcp-server`

Start the Model Context Protocol server for IDE integration.

```bash
cd ../core
uv run serena-mcp-server
```

See `../mcp/README.md` for MCP server documentation.

### Project Indexing: `index-project` (deprecated)

Index a project for symbol search. **Note**: This command is deprecated; use `serena index-project` instead.

```bash
cd ../core
uv run serena index-project /path/to/project
```

## CLI Scripts

This directory contains utility scripts from the original Serena runtime:

### `scripts/mcp_server.py`

MCP server implementation (symlinked to `../mcp/server.py`).

### `scripts/agno_agent.py`

Agent integration for Agno playground.

```bash
cd ../core
uv run python ../cli/scripts/agno_agent.py
```

### `scripts/demo_run_tools.py`

Demonstration of tool execution.

```bash
cd ../core
uv run python ../cli/scripts/demo_run_tools.py
```

### `scripts/gen_prompt_factory.py`

Generate prompt templates for code analysis workflows.

```bash
cd ../core
uv run python ../cli/scripts/gen_prompt_factory.py
```

### `scripts/print_tool_overview.py`

Print overview of all available Serena tools.

```bash
cd ../core
uv run python ../cli/scripts/print_tool_overview.py
```

### `scripts/print_mode_context_options.py`

Print available context modes and options.

```bash
cd ../core
uv run python ../cli/scripts/print_mode_context_options.py
```

## Usage Examples

### Index TTA Application Codebase

```bash
cd platform_tta_dev/components/serena/core
uv run serena index-project ../../../../app_tta/src
```

### Search for Agent Classes

```bash
cd platform_tta_dev/components/serena/core
uv run serena find-symbol Agent --project-path ../../../../app_tta/src
```

### Find Circuit Breaker Usage

```bash
cd platform_tta_dev/components/serena/core
uv run serena find-referencing-symbols \
  --symbol-location app_tta/src/agent_orchestration/circuit_breaker.py:CircuitBreaker
```

### Get Symbol Overview

```bash
cd platform_tta_dev/components/serena/core
uv run serena get-symbols-overview \
  --file-path app_tta/src/agent_orchestration/agents.py
```

## Configuration

CLI tools respect `.serena/project.yml` configuration:

```yaml
# In ../core/.serena/project.yml

# Ignore paths during indexing
ignored_paths:
  - "node_modules/**"
  - ".venv/**"
  - "**/__pycache__/**"

# Exclude dangerous tools
excluded_tools:
  - execute_shell_command

# Enable read-only mode
read_only: false
```

## Integration with TTA Platform

### Analyze Platform Components

```bash
# Index all platform components
for component in hypertool serena ace_framework; do
  uv run serena index-project \
    "platform_tta_dev/components/$component"
done
```

### Generate Architecture Documentation

```bash
# Use gen_prompt_factory to create analysis prompts
cd ../core
uv run python ../cli/scripts/gen_prompt_factory.py \
  --template architecture-analysis \
  --project-path ../../../../app_tta
```

### Cross-Component Symbol Search

```bash
# Find all MCP server implementations across platform
uv run serena find-symbol "mcp_server" \
  --project-path platform_tta_dev/components
```

## Development

### Adding New CLI Commands

1. Implement command in `../core/src/serena/cli.py`
2. Register in `[project.scripts]` section of `../core/pyproject.toml`
3. Update this README with usage examples

### Testing CLI Tools

```bash
cd ../core
uv run pytest test/serena/test_cli.py
```

## Troubleshooting

### Command Not Found

```bash
# Ensure UV environment is active
cd ../core
uv sync

# Verify serena package installation
uv run python -c "import serena; print(serena.__version__)"
```

### Symbol Search Returns No Results

```bash
# Re-index the project
uv run serena index-project /path/to/project

# Check indexing status
ls -lh .serena/index/
```

### Permission Errors

```bash
# Ensure .serena directory is writable
chmod -R u+w ../core/.serena/
```

## References

- [Serena CLI Documentation](../core/docs/02-usage/cli.md)
- [Tool Reference](../core/docs/01-about/035_tools.html)
- [Project Configuration Guide](../core/.serena/README.md)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Serena/Cli/Readme]]
