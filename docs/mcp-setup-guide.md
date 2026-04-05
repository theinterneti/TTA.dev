# TTA.dev MCP Server Setup Guide

> Connect the TTA.dev MCP server to Claude Code, GitHub Copilot, OpenCode, or Cursor in minutes.

## Overview

TTA.dev exposes an **MCP (Model Context Protocol) server** with 43 tools that give your AI coding
agent direct access to:

- **Primitives catalog** — list, inspect, and search all `WorkflowPrimitive` implementations
- **Code analysis** — detect patterns and get primitive recommendations for any Python file
- **Control plane** — create and update workflow tasks, query session state
- **LLM advisor** — list available providers, get model recommendations by task profile
- **Orientation** — `tta_bootstrap` returns a full repo context package in a single call

The canonical server config lives in **`.mcp/config.json`** at the repo root.
Full tool reference: [`MCP_TOOL_REGISTRY.md`](../MCP_TOOL_REGISTRY.md)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | `python --version` |
| uv | latest | `pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | Required for `npx`-based MCP servers in `.mcp/config.json` |
| Docker | 24+ | Required for Docker-based servers (optional) |

Install all Python dependencies:

```bash
cd /path/to/TTA.dev
uv sync --all-extras
```

---

## Starting the TTA.dev MCP Server

The server speaks **stdio MCP** — your AI client starts it automatically using the config below.
To test it manually:

```bash
# Start the server directly
uv run python -m ttadev.primitives.mcp_server

# Or via the __main__ shortcut
uv run python -m ttadev.primitives.mcp_server.server
```

A healthy start prints:

```
INFO  TTA.dev MCP server starting  tools=43
```

---

## Client Configuration

### 1. Claude Code

Claude Code reads MCP server config from **`.mcp/config.json`** in the project root automatically
when you open the project. No extra steps needed if you're working inside this repo.

**Manual setup** (add to `~/.claude/settings.json` for global access):

```json
{
  "mcpServers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"],
      "cwd": "/path/to/TTA.dev"
    }
  }
}
```

**Verify:**

```bash
claude mcp list
# Expected output includes:
# tta-dev  uv run python -m ttadev.primitives.mcp_server  ✓ connected
```

> **Tip:** `CLAUDE.md` at the repo root documents which MCP tools each agent persona relies on.

---

### 2. GitHub Copilot (VS Code)

VS Code Copilot **auto-detects `.mcp/config.json`** in the workspace root — no manual
configuration required for repo contributors.

To verify or adjust:

1. Open **Settings** (`Ctrl+,` / `Cmd+,`)
2. Search for **Copilot MCP Servers**
3. Confirm `tta-dev` appears in the list with status **Connected**

For a workspace-specific override in `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

---

### 3. OpenCode (opencode.ai)

Edit **`~/.config/opencode/config.json`** (create it if it doesn't exist):

```json
{
  "mcp": {
    "servers": {
      "tta-dev": {
        "command": "uv",
        "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"],
        "cwd": "/path/to/TTA.dev"
      }
    }
  }
}
```

Restart OpenCode. The `tta-dev` server should appear under **Tools → MCP Servers**.

---

### 4. Cursor

Create **`.cursor/mcp.json`** in the project root:

```json
{
  "mcpServers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

Reload the Cursor window (`Ctrl+Shift+P` → **Reload Window**).
Verify via **Settings → Cursor → MCP Servers** — `tta-dev` should show a green dot.

---

## Top Tools to Know

| Tool | Domain | What it does |
|------|--------|--------------|
| `tta_bootstrap` | orientation | **Start here.** Returns primitives catalog, tool map, patterns, and provider status in one call. Pass `task_hint` to get the 3 most relevant primitives ranked for your task. |
| `list_primitives` | analysis | List all `WorkflowPrimitive` subclasses, optionally filtered by category (`recovery`, `performance`, `coordination`). |
| `get_primitive_info` | analysis | Full spec for a named primitive: description, parameters, import path, and usage examples. |
| `analyze_code` | analysis | Paste Python code; get primitive recommendations with confidence scores and code templates. |
| `search_templates` | analysis | Full-text search across code templates — find a retry+cache composition, circuit-breaker pattern, etc. |
| `get_composition_example` | analysis | Generate a working code snippet that composes a list of primitives. |
| `llm_list_providers` | llm | Live check of which LLM providers (Ollama, Groq, Gemini, …) are reachable and their latency. |
| `llm_recommend_model` | llm | Given a task profile (`coding/complex`, `general/simple`, …), get the best available model. |
| `control_create_task` | control | Create a tracked workflow task in the TTA.dev control plane. |
| `control_update_task_status` | control | Update task status (`in_progress`, `done`, `failed`) with a result payload. |

> Full reference with signatures and response schemas: [`MCP_TOOL_REGISTRY.md`](../MCP_TOOL_REGISTRY.md)

---

## Troubleshooting

### Server won't start — `ModuleNotFoundError`

```bash
# Ensure the package is installed in the uv environment
uv sync --all-extras
uv run python -c "import ttadev; print(ttadev.__version__)"
```

### `uv` not found by the client

Some clients inherit a minimal `PATH`. Use the absolute path:

```bash
which uv   # e.g. /home/user/.local/bin/uv
```

Replace `"command": "uv"` with the full path in your config.

### Port conflicts (HTTP-based servers)

The `tta-dev` server itself is stdio-only (no port). If you see port errors they come from
companion servers like `hindsight` (`:8888`) or `grafana` (`:3000`). Check:

```bash
ss -tlnp | grep 8888
```

### Missing environment variables

Several servers in `.mcp/config.json` require secrets (`GITHUB_PERSONAL_ACCESS_TOKEN`,
`E2B_API_KEY`, etc.). The `tta-dev` server itself requires **no secrets** for core tool access.
Set only the variables you need:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
export E2B_API_KEY=e2b_...
```

Or add them to a `.env` file and load with `uv run --env-file .env python -m ttadev.primitives.mcp_server`.

### Client shows server as disconnected after reload

1. Confirm the repo path in `cwd` is correct and absolute.
2. Run the start command manually in a terminal to see error output.
3. Check that `uv sync --all-extras` completed without errors.

---

## Related Docs

- [`AGENTS.md`](../AGENTS.md) — Agent personas and their MCP tool assignments
- [`MCP_TOOL_REGISTRY.md`](../MCP_TOOL_REGISTRY.md) — Complete 43-tool reference
- [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md) — All primitives with examples
- [modelcontextprotocol.io](https://modelcontextprotocol.io) — Official MCP specification
