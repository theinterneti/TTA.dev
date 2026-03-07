# Augment Component

AI-assisted development workflow primitives for TTA platform development.

## Overview

The Augment component provides structured workflows, chatmodes, context management, and knowledge base integration for AI-assisted development. It serves as the cognitive framework for TTA platform development, offering reusable patterns for architecture, implementation, testing, and deployment.

## Component Structure

```
augment/
├── core/                    # Core augment functionality
│   ├── chatmodes/          # Behavior patterns for different dev roles
│   ├── workflows/          # Multi-step development procedures
│   ├── context/            # Context management and session handling
│   ├── memory/             # Persistent memory and learnings
│   ├── kb/                 # Knowledge base and documentation
│   ├── logseq/             # Logseq integration for knowledge management
│   ├── instructions/       # Development instructions and guidelines
│   ├── rules/              # Code quality and style rules
│   └── docs/               # Augment documentation
├── workflows/              # Extracted workflow primitives
│   ├── chatmodes/          # Role-based behavior modes
│   ├── prompts/            # Reusable prompt templates
│   └── scenarios/          # Common development scenarios
├── cli/                    # CLI tools for augment operations
├── mcp/                    # MCP server integration
├── personas/               # Agent persona definitions
├── integrations/           # Integration adapters
│   ├── tta_app/           # TTA application integration
│   ├── platform/          # Platform-specific integrations
│   └── external/          # External tool integrations
└── observability/          # Monitoring and metrics
    ├── traces/            # Execution traces
    ├── metrics/           # Performance metrics
    └── logs/              # Operation logs
```

## Chatmodes

Chatmodes define role-specific behavior patterns for AI assistants:

### Available Chatmodes

- **architect.chatmode.md**: System architecture and design decisions
- **backend-dev.chatmode.md**: Backend implementation patterns
- **frontend-dev.chatmode.md**: Frontend/UI development
- **devops.chatmode.md**: Deployment, infrastructure, Docker
- **qa-engineer.chatmode.md**: Testing strategies, coverage improvement

Each chatmode includes:
- Role description and responsibilities
- Technical focus areas
- Communication style guidelines
- Example interaction patterns
- Tool preferences

## Workflows

Structured multi-step procedures for common development tasks:

### Core Workflows

- **test-coverage-improvement**: Systematic coverage enhancement
- **component-promotion**: Maturity advancement workflow
- **bug-fix**: Structured debugging and remediation
- **refactoring**: Safe architectural changes with validation

Each workflow defines:
- Prerequisites and preconditions
- Step-by-step procedures
- Validation checkpoints
- Success criteria
- Rollback procedures

## Context Management

Conversation and session management:

- **conversation_manager.py**: Session state management
- **cli.py**: Command-line interface for context operations
- **Context loaders**: Automatic context injection for TTA development

## Memory System

Persistent learnings and project knowledge:

- **Project memories**: Component-specific knowledge
- **Pattern library**: Reusable solutions and approaches
- **Decision records**: Architecture decision documentation
- **Lessons learned**: Post-mortem insights

## Knowledge Base

Structured documentation and reference materials:

- **Quick references**: Common commands and patterns
- **Technical guides**: Deep-dive documentation
- **Integration guides**: Tool setup and configuration
- **Best practices**: Coding standards and conventions

## Logseq Integration

Knowledge graph management:

- **Graph database**: Interconnected documentation
- **Journals**: Development logs and progress tracking
- **Pages**: Topic-based documentation
- **Queries**: Dynamic content aggregation

## Usage

### Activate Chatmode

```bash
# In conversation, reference chatmode
@architect.chatmode.md  # Switch to architect role

# Or use in prompt
"As a backend developer (see backend-dev.chatmode.md), implement..."
```

### Run Workflow

```bash
# Execute structured workflow
python platform_tta_dev/components/augment/workflows/test-coverage-improvement.py --component gameplay_loop

# Or reference in conversation
"Follow the component-promotion workflow for circuit_breaker"
```

### Access Context

```bash
# Load conversation context
python platform_tta_dev/components/augment/context/cli.py load-session --id tta-dev-session

# View memory
cat platform_tta_dev/components/augment/memory/circuit-breaker-implementation.memory.md
```

### Query Knowledge Base

```bash
# Search KB
grep -r "circuit breaker pattern" platform_tta_dev/components/augment/kb/

# View quick reference
cat platform_tta_dev/components/augment/kb/dev-workflow-quick-reference.md
```

## Integration Points

### With Hypertool

- Augment chatmodes complement hypertool personas
- Workflows use hypertool MCP servers
- Shared context management

### With Serena

- Workflows leverage serena's code search capabilities
- Memory system uses serena for code analysis
- Integration for architectural insights

### With TTA Application

- Development workflows specific to TTA components
- Context includes TTA architecture patterns
- Memory captures TTA-specific decisions

## Key Features

### Structured Development

- **Role-based modes**: Switch between architect, developer, QA perspectives
- **Workflow templates**: Reusable procedures for common tasks
- **Context persistence**: Maintain state across sessions

### Knowledge Management

- **Memory system**: Learn from past decisions and implementations
- **KB integration**: Quick access to documentation and patterns
- **Logseq graphs**: Interconnected knowledge exploration

### Quality Assurance

- **Code rules**: Automated quality checks
- **Testing workflows**: Systematic test development
- **Review checklists**: Comprehensive code review

### Collaboration

- **Shared context**: Team-wide knowledge sharing
- **Decision records**: Transparent architecture decisions
- **Pattern library**: Reusable solutions

## Dependencies

- **Python 3.11+**: For CLI tools and workflows
- **Logseq**: For knowledge graph management (optional)
- **Hypertool**: For MCP server orchestration
- **Serena**: For code analysis integration

## Configuration

Augment is configured via:

- **chatmode frontmatter**: Role-specific settings
- **workflow YAML**: Workflow parameters and steps
- **context config**: Session management settings
- **memory structure**: Knowledge organization

## Files Migrated

- **398 total files**
- Chatmodes: 6 primary + templates
- Workflows: 10+ structured procedures
- Context management: CLI tools, loaders, session managers
- Memory: 20+ memory files
- KB: Documentation, guides, references
- Logseq: Graph database, journals, pages
- Instructions: Development guidelines
- Rules: Code quality rules

## Component Maturity

**Status**: Production
- Core chatmodes and workflows in active use
- Context management proven across multiple projects
- Memory system captures institutional knowledge
- KB provides comprehensive development reference

## Maintainers

- TTA Platform Team
- AI Development Workflow WG

## See Also

- `platform_tta_dev/components/hypertool/` - MCP server orchestration
- `platform_tta_dev/components/serena/` - Code analysis toolkit
- `platform_tta_dev/components/personas/` - Agent persona definitions


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Readme]]
