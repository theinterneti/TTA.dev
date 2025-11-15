source-file:: /home/thein/repos/TTA.dev/packages/tta-documentation-primitives/README.md
type:: documentation

# TTA Documentation Primitives

**Automated documentation-to-Logseq integration with AI-powered metadata generation**

## Overview

This package provides seamless bidirectional synchronization between your markdown documentation and Logseq knowledge base, enhanced with free AI-powered metadata generation using Google Gemini Flash 2.0.

### Key Features

- 🔄 **Automated Sync** - Watch docs folder and sync changes to Logseq automatically
- 🤖 **AI Enhancement** - Free metadata extraction using Gemini Flash (1,500 req/day)
- 📚 **Dual Format** - Human-readable docs + AI-optimized KB sections
- 🔧 **TTA.dev Primitives** - Composable workflow primitives for documentation
- 🎯 **Agent-Native** - Built for AI agents to create documentation seamlessly

## Quick Start

### Installation

```bash
# From repository root
uv add --editable packages/tta-documentation-primitives

# Or with pip
pip install -e packages/tta-documentation-primitives
```

### Basic Usage

```python
from tta_documentation_primitives import DocumentWatcher

# Start watching docs folder
watcher = DocumentWatcher(
    docs_path="docs/",
    logseq_path="logseq/pages/"
)
watcher.start()
```

### CLI Commands

```bash
# Sync all documentation
tta-docs sync --all

# Sync specific file
tta-docs sync docs/guides/my-guide.md

# Start background watcher
tta-docs watch start

# Stop background watcher
tta-docs watch stop

# Validate sync status
tta-docs validate
```

## Architecture

```
docs/*.md → File Watcher → AI Processor → Logseq Converter → logseq/pages/*.md
                              ↓
                         Gemini Flash
                              ↓
                    Extract Metadata:
                    - type, category
                    - tags, links
                    - summary
                    - related pages
```

## AI Integration

### Google Gemini Flash 2.0

- **Free Tier:** 1,500 requests/day
- **Context Window:** 1.5M tokens
- **Use Cases:**
  - Extract document metadata
  - Suggest internal links
  - Categorize documentation
  - Generate summaries

### Ollama Fallback

If Gemini is unavailable, falls back to local AI:

- `llama3.2:3b` - Fast, efficient
- `mistral:7b` - Higher quality

## Dual-Format Documentation

### Human Section (Preserved)

Original markdown content remains unchanged:

```markdown
# How to Create a Primitive

This guide shows you how to...

## Steps

1. Create class extending WorkflowPrimitive
2. Implement _execute_impl method
...
```

### AI-Optimized Section (Generated)

Structured metadata added for AI consumption:

```markdown
---

## AI-Optimized Metadata

type:: how-to-guide
category:: primitives
difficulty:: intermediate
tags:: #primitives #workflow #development
related:: [[TTA Primitives]], [[InstrumentedPrimitive]]
summary:: Step-by-step guide for creating custom workflow primitives
key-concepts:: WorkflowPrimitive, InstrumentedPrimitive, type safety
prerequisites:: [[Understanding TTA Primitives]], [[Python 3.11+]]
estimated-time:: 30 minutes
```

## TTA.dev Primitives

Use as composable workflow primitives:

```python
from tta_dev_primitives import WorkflowContext
from tta_documentation_primitives import DocumentationPrimitive, LogseqSyncPrimitive

# Create documentation workflow
workflow = (
    DocumentationPrimitive(title="My Guide", category="guides") >>
    LogseqSyncPrimitive(enhance_with_ai=True) >>
    NotificationPrimitive(message="Documentation synced!")
)

# Execute
context = WorkflowContext(trace_id="doc-123")
result = await workflow.execute(content, context)
```

## Configuration

Create `.tta-docs.json` in repository root:

```json
{
  "docs_paths": [
    "docs/",
    "packages/*/README.md"
  ],
  "logseq_path": "logseq/pages/",
  "ai": {
    "provider": "gemini",
    "model": "gemini-2.0-flash-exp",
    "fallback": "ollama:llama3.2:3b"
  },
  "sync": {
    "auto": true,
    "debounce_ms": 500,
    "bidirectional": true
  },
  "format": {
    "dual_format": true,
    "preserve_code_blocks": true,
    "convert_links": true
  }
}
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/tta_documentation_primitives --cov-report=html

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uvx pyright packages/tta-documentation-primitives
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_watcher.py

# With verbose output
uv run pytest -v -s
```

## Package Structure

```
tta-documentation-primitives/
├── src/
│   └── tta_documentation_primitives/
│       ├── __init__.py
│       ├── watcher.py           # File watching service
│       ├── converter.py         # Markdown → Logseq
│       ├── ai_processor.py      # AI metadata extraction
│       ├── sync_service.py      # Sync orchestration
│       ├── primitives/          # TTA.dev primitives
│       │   ├── documentation.py
│       │   ├── logseq_sync.py
│       │   └── kb_index.py
│       ├── cli.py               # CLI commands
│       └── config.py            # Configuration management
├── tests/
│   ├── test_watcher.py
│   ├── test_converter.py
│   ├── test_ai_processor.py
│   └── test_primitives.py
├── examples/
│   ├── basic_sync.py
│   ├── with_primitives.py
│   └── custom_ai_processor.py
├── pyproject.toml
└── README.md
```

## Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] Package structure
- [ ] File watcher
- [ ] Markdown converter
- [ ] CLI commands

### Phase 2: AI Integration
- [ ] Gemini Flash API
- [ ] Property extraction
- [ ] Link suggestion
- [ ] Ollama fallback

### Phase 3: TTA.dev Primitives
- [ ] DocumentationPrimitive
- [ ] LogseqSyncPrimitive
- [ ] KnowledgeBaseIndexPrimitive
- [ ] Tests + examples

### Phase 4: Automation
- [ ] Auto-sync on save
- [ ] Background daemon
- [ ] Bidirectional sync
- [ ] Conflict resolution

### Phase 5: Agent Integration
- [ ] Copilot instructions
- [ ] Documentation templates
- [ ] Agent examples
- [ ] MCP server tools

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.

## License

See repository root for license information.

## Related Documentation

- [Architecture Design](../../local/planning/logseq-docs-db-integration-design.md)
- [Implementation TODOs](../../local/planning/logseq-docs-integration-todos.md)
- [TTA.dev Primitives](../tta-dev-primitives/README.md)
- [Logseq Knowledge Base](../../logseq/README.md)

---

**Status:** Phase 1 - Foundation (In Progress)
**Version:** 0.1.0
**Last Updated:** October 31, 2025
