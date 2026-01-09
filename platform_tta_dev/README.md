# TTA.dev Platform

Agentic primitives, MCP servers, CLI tools, and workflows for AI-assisted development.

## Structure

- `components/`: Individual agentic components (hypertool, serena, ACE, etc.)
- `shared/`: Cross-component utilities (observability, MCP core, CLI core, workflow engine)
- `docs/`: Platform-level documentation

## Components

Components will be migrated sequentially. Each component follows this structure:

```text
component_name/
├── README.md              # Component overview, usage, integration points
├── core/                  # Implementation (language-agnostic)
├── mcp/                   # MCP server definitions
│   ├── servers/           # Server entrypoints
│   └── config/            # Capabilities, transport, auth
├── cli/                   # Command-line interfaces (if applicable)
├── workflows/             # Markdown-as-code
│   ├── prompts/           # Prompt templates with tracing metadata
│   ├── chatmodes/         # Chatmode/persona definitions
│   └── scenarios/         # Scripted flows
├── personas/              # Persona definitions (md/json/yaml)
├── integrations/          # Adapters
│   ├── tta_app/           # Integration with TTA game
│   ├── platform/          # Integration with other components
│   └── external/          # Third-party services
└── observability/
    ├── tracing/           # Span naming, attributes, prompt tracing
    ├── metrics/           # Counters, histograms, dashboards
    └── logging/           # Structured log schemas
```

## Migration Status

- [ ] hypertool - Personas, MCPs, workflows
- [ ] serena - Code search, memory management
- [ ] ace_framework - Agent architecture
- [ ] anthropic_skills - Claude capabilities
- [ ] cline_cli - CLI interface
- [ ] e2b - Execution runtime
- [ ] logseq - Knowledge base integration

## Shared Modules

### observability_core/

Cross-component observability framework:

- Common instrumentation helpers
- Circuit breaker integration
- Standardized metric/log naming
- Trace aggregation and export

### mcp_core/

MCP server base scaffolding:

- Server lifecycle management
- Transport abstractions
- Capability registration
- Common middleware

### cli_core/

CLI utilities:

- Argument parsing patterns
- Output formatting
- Progress reporting
- Error handling conventions

### workflows_core/

Workflow engine for markdown-as-code:

- Prompt template loader and validator
- Chatmode orchestration
- Scenario execution
- Frontmatter metadata parsing (for tracing)

## Usage

See individual component READMEs for specific usage instructions.

For platform-wide documentation, see `docs/`.

## Development

See [REFACTOR_STRATEGY.md](../REFACTOR_STRATEGY.md) for migration protocol and architectural decisions.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Readme]]
