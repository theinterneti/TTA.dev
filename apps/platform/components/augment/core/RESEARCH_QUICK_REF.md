# 📓 Research Notebook Quick Reference

**Notebook ID:** `d998992e-acd6-4151-a5f2-615ac1f242f3`
**Query Script:** `scripts/query_notebook_helper.py`

## Quick Start

```bash
# Ask a question
uv run python scripts/query_notebook_helper.py "Your question here"
```

## Common Queries by Role

### 🏗️ Architect
```bash
# Framework patterns
uv run python scripts/query_notebook_helper.py \
  "What are the three layers of the AI-Native framework?"

# Agent design
uv run python scripts/query_notebook_helper.py \
  "How should I design agent primitive interfaces?"

# MCP security
uv run python scripts/query_notebook_helper.py \
  "What are MCP security best practices?"
```

### 🔧 DevOps
```bash
# CI/CD integration
uv run python scripts/query_notebook_helper.py \
  "How should Agent CLI runtimes integrate with CI/CD?"

# Package management
uv run python scripts/query_notebook_helper.py \
  "How does the Agent Package Manager work?"

# Deployment
uv run python scripts/query_notebook_helper.py \
  "What are best practices for deploying agent primitives?"
```

### 💻 Backend Developer
```bash
# Implementation
uv run python scripts/query_notebook_helper.py \
  "How should I implement a new chatmode?"

# Context engineering
uv run python scripts/query_notebook_helper.py \
  "What context should instruction files include?"

# Prompt engineering
uv run python scripts/query_notebook_helper.py \
  "What Markdown patterns work best for prompt engineering?"
```

### 🧪 QA Engineer
```bash
# Testing agents
uv run python scripts/query_notebook_helper.py \
  "How should I test agent primitive workflows?"

# Validation gates
uv run python scripts/query_notebook_helper.py \
  "What validation gates should agentic workflows include?"

# Security testing
uv run python scripts/query_notebook_helper.py \
  "How do I test MCP tool security boundaries?"
```

## Research Topics

The notebook contains research on:

- ✅ **AI-Native Development Framework** (3 layers)
- ✅ **Markdown Prompt Engineering** (structural patterns)
- ✅ **Agent Primitives** (chatmodes, workflows, instructions, specs)
- ✅ **Context Engineering** (session splitting, modular rules)
- ✅ **MCP Integration** (tools, security, boundaries)
- ✅ **Agent Package Manager** (distribution, versioning)
- ✅ **Agent CLI Runtimes** (outer loop execution)
- ✅ **AGENTS.md Standard** (context portability)

## Integration Points

Chatmodes with research access:
- `architect.chatmode.md` - Framework & patterns
- `devops.chatmode.md` - Agent CLI & APM
- `backend-dev.chatmode.md` - Implementation patterns
- `qa-engineer.chatmode.md` - Testing & validation

## Python API

```python
from scripts.query_notebook_helper import query_notebook

# In async context
response = await query_notebook("Your question")
```

## Configuration

- **Config:** `notebooklm-config.json`
- **Auth Profile:** `./chrome_profile_notebooklm/`
- **Setup Script:** `./setup-notebooklm-auth.sh`

## Full Documentation

See `.augment/RESEARCH_NOTEBOOK_INTEGRATION.md` for complete details.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Research_quick_ref]]
