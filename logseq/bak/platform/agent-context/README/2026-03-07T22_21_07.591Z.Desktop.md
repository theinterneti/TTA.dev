# Universal Agent Context System

**Production-ready agentic primitives and context management for AI-native development**

[![Status](https://img.shields.io/badge/status-production-green.svg)](https://github.com/theinterneti/TTA.dev)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)

---

## Overview

The Universal Agent Context System provides two complementary approaches to AI-native development:

1. **Augment CLI-Specific Primitives** (`.augment/`) - Advanced agentic capabilities for Augment CLI
2. **Cross-Platform Primitives** (`.github/`) - Universal primitives that work across Claude, Gemini, Copilot, and Augment

Both structures are **actively maintained** and demonstrate different strategies for building sophisticated AI-powered development workflows.

---

## Quick Start

### Installation

```bash
# Clone or copy the package to your project
cp -r packages/universal-agent-context/ /path/to/your/project/

# Or install as a git submodule
git submodule add https://github.com/theinterneti/TTA.dev packages/universal-agent-context
```

### Choose Your Approach

#### Option 1: Augment CLI-Specific (Advanced Features)

Use the `.augment/` directory for:
- Augster identity system (16 traits, 13 maxims, 3 protocols)
- Python CLI for context management
- Memory system for architectural decisions
- Workflow templates for common tasks

```bash
# Copy .augment/ to your project root
cp -r packages/universal-agent-context/.augment/ .
```

#### Option 2: Cross-Platform (Universal Compatibility)

Use the `.github/` directory for:
- YAML frontmatter with selective loading
- Works across Claude, Gemini, Copilot, Augment
- MCP tool access controls
- Security levels and boundaries

```bash
# Copy .github/ to your project root
cp -r packages/universal-agent-context/.github/ .
```

#### Option 3: Both (Comprehensive)

Use both for maximum flexibility:

```bash
# Copy both structures
cp -r packages/universal-agent-context/.augment/ .
cp -r packages/universal-agent-context/.github/ .
cp packages/universal-agent-context/AGENTS.md .
cp packages/universal-agent-context/apm.yml .
```

---

## Features

### Augment CLI-Specific (`.augment/`)

- ✅ **Augster Identity System** - Sophisticated AI agent personality
- ✅ **Context Management** - Python CLI for session tracking
- ✅ **Memory System** - Architectural decisions and patterns
- ✅ **Workflow Templates** - Reusable prompts for common tasks
- ✅ **Modular Instructions** - Domain-specific guidelines
- ✅ **Chat Modes** - Role-based development modes

### Cross-Platform (`.github/`)

- ✅ **YAML Frontmatter** - Structured metadata for selective loading
- ✅ **Pattern-Based Loading** - Load instructions based on file patterns
- ✅ **Security Levels** - Explicit security boundaries (LOW, MEDIUM, HIGH)
- ✅ **MCP Tool Access** - Defined tool access controls
- ✅ **Universal Context** - Works across all AI agents
- ✅ **Chat Modes** - Role-based modes with tool boundaries

---

## Documentation

### Getting Started
- [Quick Start Guide](docs/guides/GETTING_STARTED.md) - 5-minute setup
- [Integration Guide](docs/guides/INTEGRATION_GUIDE.md) - Step-by-step adoption
- [Migration Guide](docs/guides/MIGRATION_GUIDE.md) - Migrate from legacy structures

### Architecture
- [System Overview](docs/architecture/OVERVIEW.md) - Architecture and design
- [YAML Schema](docs/architecture/YAML_SCHEMA.md) - Frontmatter specification
- [Selective Loading](docs/architecture/SELECTIVE_LOADING.md) - Loading mechanism

### Integration
- [Claude Integration](docs/integration/CLAUDE.md) - Claude-specific setup
- [Gemini Integration](docs/integration/GEMINI.md) - Gemini-specific setup
- [Copilot Integration](docs/integration/COPILOT.md) - GitHub Copilot setup
- [Augment Integration](docs/integration/AUGMENT.md) - Augment CLI setup

### Knowledge Base
- [Augment CLI Clarification](docs/knowledge/AUGMENT_CLI_CLARIFICATION.md) - Platform-specific vs. cross-platform

---

## Package Structure

```
packages/universal-agent-context/
├── .github/                    # Cross-platform primitives
│   ├── instructions/           # 14 modular instruction files
│   ├── chatmodes/              # 15 role-based chat modes
│   └── copilot-instructions.md
│
├── .augment/                   # Augment CLI-specific primitives
│   ├── instructions/           # 14 instruction files (Augster system)
│   ├── chatmodes/              # 7 chat mode files
│   ├── workflows/              # 8 workflow templates
│   ├── context/                # Context management system
│   ├── memory/                 # Memory system
│   └── rules/                  # Development rules
│
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   ├── architecture/           # Architecture docs
│   ├── development/            # Development guides
│   ├── integration/            # Agent-specific integration
│   ├── mcp/                    # MCP server docs
│   ├── examples/               # Usage examples
│   └── knowledge/              # Knowledge base
│
├── scripts/                    # Utility scripts
│   └── validate-export-package.py
│
├── tests/                      # Test suite
│   ├── test_yaml_frontmatter.py
│   ├── test_selective_loading.py
│   └── test_cross_agent_compat.py
│
├── .vscode/                    # VS Code integration
│   ├── tasks.json
│   └── settings.json
│
├── AGENTS.md                   # Universal context
├── CLAUDE.md                   # Claude-specific
├── GEMINI.md                   # Gemini-specific
├── apm.yml                     # Agent Package Manager
├── README.md                   # This file
├── GETTING_STARTED.md          # Quick start
├── CONTRIBUTING.md             # Contribution guide
└── LICENSE                     # MIT License
```

---

## Usage Examples

### Example 1: Basic Setup (Cross-Platform)

```bash
# Copy cross-platform primitives
cp -r packages/universal-agent-context/.github/ .
cp packages/universal-agent-context/AGENTS.md .

# Start using with any AI agent (Claude, Gemini, Copilot, Augment)
```

### Example 2: Advanced Setup (Augment CLI)

```bash
# Copy Augment CLI-specific primitives
cp -r packages/universal-agent-context/.augment/ .
cp packages/universal-agent-context/apm.yml .

# Use Augster identity system and context management
python .augment/context/cli.py new my-session
```

### Example 3: Comprehensive Setup (Both)

```bash
# Copy everything
cp -r packages/universal-agent-context/.github/ .
cp -r packages/universal-agent-context/.augment/ .
cp packages/universal-agent-context/AGENTS.md .
cp packages/universal-agent-context/CLAUDE.md .
cp packages/universal-agent-context/GEMINI.md .
cp packages/universal-agent-context/apm.yml .

# Use both approaches as needed
```

---

## Validation

Validate your setup:

```bash
# Run validation script
python packages/universal-agent-context/scripts/validate-export-package.py

# Or with strict mode
python packages/universal-agent-context/scripts/validate-export-package.py --strict
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**Quality Standards**:
- 100% test coverage for new code
- Comprehensive documentation
- Battle-tested in production
- Zero critical bugs

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions**: [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)
- **Documentation**: [docs/](docs/)

---

## Acknowledgments

Developed as part of the [TTA (Therapeutic Text Adventure)](https://github.com/theinterneti/TTA) project, demonstrating production-ready AI-native development practices.

**Key Contributors**:
- Augment CLI team for the sophisticated Augster identity system
- TTA development team for battle-testing these primitives
- AI development community for feedback and improvements

---

**Version**: 1.0.0  
**Status**: Production  
**Last Updated**: 2025-10-28

