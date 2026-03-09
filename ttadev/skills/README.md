# tta-skill-primitives

**SKILL.md-compatible agent skill framework built on TTA workflow primitives.**

## Overview

`tta-skill-primitives` provides composable, self-describing skill primitives for AI agents. Skills follow the open SKILL.md specification — the standard format adopted by OpenAI, Anthropic, and LangChain for portable agent capabilities.

A **Skill** extends `WorkflowPrimitive`, which means it:

- Composes with `>>` (sequential) and `|` (parallel) operators
- Wraps in `RetryPrimitive`, `TimeoutPrimitive`, etc.
- Carries rich metadata for agent discovery and tool selection

## Installation

```bash
uv pip install -e platform/skills
```

## Quick Start

```python
from tta_skill_primitives import Skill, SkillDescriptor, SkillRegistry
from tta_dev_primitives import WorkflowContext

class CodeReviewSkill(Skill[str, dict]):
    descriptor = SkillDescriptor(
        name="code-review",
        description="Analyse code for quality and security issues.",
    )

    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {"issues": [], "score": 100}

# Register and discover
registry = SkillRegistry()
registry.register(CodeReviewSkill())

skill = registry.get("code-review")
result = await skill.execute("def foo(): pass", WorkflowContext())
```

## SKILL.md Files

Parse standard SKILL.md files into descriptors:

```python
from tta_skill_primitives import parse_skill_md, dump_skill_md

descriptor = parse_skill_md("""
---
name: code-review
description: Analyse code for quality and security issues.
metadata:
  author: TTA Team
  version: "1.0.0"
  tags: [code-quality, security]
---

# Code Review Skill

## When to use
Use this skill when the user requests a code review.

## Instructions
1. Receive the code and language.
2. Analyse for anti-patterns.
3. Return issues and score.
""")

print(descriptor.name)  # "code-review"
print(descriptor.metadata.tags)  # ["code-quality", "security"]
```

## Composition with Primitives

```python
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy

# Skills compose like any WorkflowPrimitive
pipeline = code_review_skill >> security_scan_skill >> format_report

# Wrap with recovery primitives
resilient = RetryPrimitive(
    code_review_skill,
    strategy=RetryStrategy(max_retries=3, backoff_factor=2.0),
)
```

## API Reference

| Class | Purpose |
|-------|---------|
| `Skill[T, U]` | Base class for agent skills (extends `WorkflowPrimitive`) |
| `SkillDescriptor` | Pydantic model for SKILL.md YAML frontmatter |
| `SkillMetadata` | Author, version, and tags |
| `SkillParameter` | Input parameter declaration |
| `SkillStatus` | Lifecycle enum: draft / stable / deprecated |
| `SkillRegistry` | In-memory registry for discovery and search |
| `parse_skill_md()` | Parse SKILL.md text to `SkillDescriptor` |
| `load_skill_md()` | Load SKILL.md file from disk |
| `dump_skill_md()` | Serialise `SkillDescriptor` to SKILL.md format |

## Development

```bash
uv sync --all-extras
uv run pytest platform/skills/tests -v
uv run ruff format platform/skills/
uv run ruff check platform/skills/
```
