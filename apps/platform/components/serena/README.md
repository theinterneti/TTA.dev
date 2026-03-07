# Serena Component

**Component Type:** Code Search & Architectural Analysis Agent Toolkit
**Status:** Migrated from `platform/dev/agentic/serena/runtime/`
**Migration Date:** 2025-11-16

## Overview

Serena is a powerful coding agent toolkit that provides IDE-like semantic code retrieval and editing tools for LLMs. It operates directly on codebases, offering symbol-level entity extraction and relational structure exploitation.

### Core Capabilities

- **Semantic Code Search**: Symbol-level search across entire codebase
- **Architectural Analysis**: Understand code relationships and dependencies
- **Code Editing Tools**: Precise, symbol-aware code modifications
- **MCP Server**: Model Context Protocol integration for Claude, Cursor, VSCode
- **CLI Tools**: Command-line interface for project indexing and operations
- **Memory System**: Project-specific memory store for context persistence

## Architecture

```text
serena/
├── README.md (this file)
├── core/                   # Serena runtime implementation
│   ├── src/                # Python source code (serena package)
│   ├── test/               # Test suite
│   ├── docs/               # Documentation
│   ├── pyproject.toml      # Project dependencies
│   ├── uv.lock             # Lockfile
│   ├── .serena/            # Serena project config & memories
│   ├── scripts/            # Utility scripts
│   └── resources/          # Static resources (logos, etc.)
├── mcp/                    # MCP server configuration
│   ├── server.py           # MCP server entry point
│   └── README.md           # MCP integration documentation
├── cli/                    # CLI tools and commands
│   ├── serena              # Main CLI entry point (symlink)
│   ├── index-project       # Project indexing command
│   └── README.md           # CLI usage documentation
├── workflows/              # Serena-specific workflows
│   ├── prompts/            # Code analysis prompt templates
│   ├── chatmodes/          # Serena conversation modes
│   └── scenarios/          # Test scenarios for code search
├── personas/               # Serena persona definitions
│   └── README.md           # Persona usage guide
├── integrations/           # Integration adapters
│   ├── tta_app/            # TTA application integration
│   ├── platform/           # Platform component integrations
│   ├── external/           # External tool adapters (Claude, VSCode, etc.)
│   └── README.md
└── observability/          # Serena-specific observability
    ├── traces/             # Tool invocation traces
    ├── metrics/            # Search performance metrics
    ├── logs/               # Operation logs
    └── README.md
```

## Key Components

### Core Runtime (`core/`)

**Python Package**: `serena-agent==0.1.4`

**Key Modules**:

- `serena.tools`: Code search and editing tools
- `serena.indexing`: Project indexing and symbol extraction
- `serena.memory`: Project-specific memory management
- `serena.cli`: Command-line interface
- `serena.mcp`: Model Context Protocol server

**Dependencies**:

- `pyright>=1.1.396` - Type analysis
- `mcp==1.12.3` - Model Context Protocol
- `anthropic>=0.54.0` - Claude integration
- `pydantic>=2.10.6` - Data validation
- `tiktoken>=0.9.0` - Token counting

### MCP Server (`mcp/`)

**Entry Point**: `serena-mcp-server`

**Integration Targets**:

- Claude Code & Claude Desktop
- VSCode (Cline, Roo Code extensions)
- Cursor IDE
- IntelliJ
- Terminal clients (Codex, Gemini-CLI, Qwen3-Coder)
- Local clients (OpenWebUI, Jan, Agno)

**Tools Exposed**:

- `find_symbol`: Global/local symbol search
- `find_referencing_symbols`: Reverse dependency lookup
- `find_referencing_code_snippets`: Code usage examples
- `get_symbols_overview`: File-level symbol overview
- `create_text_file`: File creation/overwriting
- `delete_lines`: Line-based editing
- `insert_after_symbol`: Symbol-aware insertion
- `execute_shell_command`: Shell command execution
- `read_memory`/`write_memory`: Project context persistence

### CLI Tools (`cli/`)

**Commands**:

- `serena`: Main CLI entry point
- `serena-mcp-server`: Start MCP server
- `index-project`: Index codebase for symbol search

**Configuration**: `.serena/project.yml` - Per-project settings

### Memory System (`.serena/memories/`)

**Persisted Knowledge**:

- `serena_core_concepts_and_architecture.md` - Architecture overview
- `serena_repository_structure.md` - Codebase organization
- `suggested_commands.md` - Common operations
- `adding_new_language_support_guide.md` - Extension guide

## Dependencies

### Platform Dependencies

- **Core**: None
- **Uses**: Hypertool personas (for agent orchestration)
- **Used By**: ace_framework (architecture analysis), anthropic_skills (Claude integration)

### External Dependencies

**Runtime**:

- Python 3.11 (strict requirement: `>=3.11, <3.12`)
- UV package manager
- Pyright (type checker)
- Fortls (Fortran language server - if analyzing Fortran code)

**MCP Servers**: Self-contained (provides MCP server, doesn't consume others)

## Observability Integration

### Trace Configuration

- **Tool Invocations**: Track all `find_symbol`, `find_referencing_symbols`, etc. calls
- **Search Performance**: Measure symbol search latency
- **Memory Operations**: Trace `read_memory`/`write_memory` usage

### Metrics

- Symbol search hit rate
- Code editing success rate
- MCP server response times
- Token consumption per tool invocation
- Index freshness (time since last reindex)

### Logs

- Symbol indexing progress
- Tool execution errors
- MCP server connection/disconnection
- Memory persistence events

## Usage

### MCP Server Integration

Start Serena MCP server for Claude/Cursor/VSCode:

```bash
cd platform_tta_dev/components/serena/core
uv run serena-mcp-server
```

Add to `.mcp.json` or similar MCP client configuration.

### CLI Usage

Index a project for symbol search:

```bash
cd platform_tta_dev/components/serena/core
uv run serena index-project /path/to/project
```

Search for symbols:

```bash
uv run serena find-symbol MyClass
```

### TTA Application Integration

Serena can analyze TTA's own codebase:

```python
# In TTA application code
from serena.tools import FindSymbolTool

# Find all agent classes in TTA
results = FindSymbolTool().execute(
    symbol_name="Agent",
    project_path="app_tta/src/agent_orchestration"
)
```

## Migration Notes

### Source Locations

- **Original Runtime**: `platform/dev/agentic/serena/runtime/`
- **Original State**: `platform/dev/agentic/serena/state/`

### File Mapping

| Source | Destination | Notes |
|--------|-------------|-------|
| `runtime/src/` | `core/src/` | Full Python package |
| `runtime/test/` | `core/test/` | Test suite |
| `runtime/docs/` | `core/docs/` | Documentation |
| `runtime/scripts/mcp_server.py` | `mcp/server.py` | MCP entry point |
| `runtime/scripts/` | `cli/` | CLI scripts |
| `runtime/.serena/` | `core/.serena/` | Project config |
| `runtime/pyproject.toml` | `core/pyproject.toml` | Dependencies |
| `state/` | `observability/` | Runtime state → metrics/logs |

### Symlink Updates

- None required (serena was not symlinked at root)

### Validation Checklist

- [ ] MCP server starts successfully
- [ ] CLI commands execute (`serena`, `index-project`)
- [ ] Symbol search works on TTA codebase
- [ ] Memory system persists correctly
- [ ] Integration with hypertool personas functional
- [ ] All tests pass in `core/test/`

## Integration Examples

### With Hypertool Personas

```yaml
# In hypertool/personas/personas/ArchitectureAnalyst.md
tools:
  - serena.find_symbol
  - serena.find_referencing_symbols
  - serena.get_symbols_overview

workflow:
  1. Use serena to map codebase architecture
  2. Identify key abstractions and patterns
  3. Generate architecture documentation
```

### With TTA Agent Orchestration

```python
# In TTA's agent orchestration layer
from serena.tools import FindReferencingSymbolsTool

# Find all places where CircuitBreaker is used
usage_sites = FindReferencingSymbolsTool().execute(
    symbol_location="src/agent_orchestration/circuit_breaker.py:CircuitBreaker"
)
```

## Next Steps

1. **Immediate**: Verify MCP server integration with Claude/Cursor
2. **Phase 5**: Migrate ace_framework component (depends on serena's architecture analysis)
3. **Phase 6**: Create serena-specific workflows for TTA codebase analysis
4. **Phase 7**: Instrument tool invocations with observability traces
5. **Phase 8**: Integrate with TTA's graph database for semantic code graph


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Serena/Readme]]
