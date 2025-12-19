# Hindsight Memory Banks

This directory contains organized memory storage for TTA.dev agents.

## Bank Structure

```
banks/
├── tta-dev/           # TTA.dev core knowledge (shared)
│   ├── implementation-failures/
│   ├── successful-patterns/
│   └── architectural-decisions/
├── user-repo/          # Target repository knowledge (per-project)
│   ├── codebase-insights/
│   ├── module-structure/
│   └── api-patterns/
├── session/            # Current session (ephemeral)
└── ace-strategies/     # ACE agent learned strategies
```

## Memory File Format

All memories use `.memory.md` extension with YAML frontmatter:

```markdown
---
category: successful-patterns
date: 2025-12-19
component: primitives
severity: medium
tags: [tag1, tag2]
---
# Memory Title

## Context
...

## Solution/Pattern
...

## Lesson Learned
...
```

## Usage

See [HINDSIGHT_MEMORY_ARCHITECTURE.md](../../docs/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md) for full documentation.
