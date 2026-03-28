# Functional Specification: SessionAutomation

**Date:** 2026-03-21
**Phase:** 4 — Automation
**Status:** Approved — 2026-03-25
**Depends on:** `DevelopmentCycle` (Phase 3, complete), `AgentMemory` (Phase 2b, complete)
**Leads to:** Phase 5 — Quality Gates + Multi-model Fallback

---

## Overview

`SessionAutomation` eliminates the manual ceremony around the development loop by wiring three automation points into the environment:

1. **Auto-retain** — At the end of each Claude Code session, a `Stop` hook automatically snapshots the session's git activity to Hindsight.
2. **Pre-commit validation** — Before each `git commit`, a pre-commit hook runs pytest on any changed test files.
3. **Session-start directives** — A `UserPromptSubmit` hook fires on the first prompt of each session and injects Hindsight directives into the conversation context.

Together these remove the three most common manual steps: `/session-start`, retain-after-task, and run-tests-before-commit.

---

## Motivation

Today the developer must manually:
- Run `/session-start` to load Hindsight directives and check CGC state
- Call `mcp__hindsight__retain` after significant tasks to preserve decisions
- Run `uv run pytest` before committing to catch regressions

Phase 4 automates all three. The loop becomes: **start session → develop → commit** — no ceremony required. Each automation degrades silently when its dependency is unavailable.

---

## The Three Automation Points

```
Session start   →   Work   →   git commit   →   Session end
      |                              |                  |
[1. Auto-load            [2. Pre-commit          [3. Auto-retain
 directives from          pytest on changed        session summary
 Hindsight]               test files]              to Hindsight]
```

---

## User Journeys

### Journey 1 — Session starts, directives auto-loaded

A developer opens Claude Code. On the first user prompt, a `UserPromptSubmit` hook fires a shell script that calls the Hindsight recall endpoint and prints structured directives to stdout. Claude Code captures this output and injects it into the conversation context as additional context before responding.

```
User opens Claude Code and types first message.

Hook fires → scripts/session_start_recall.py runs → prints:
  ## Hindsight Directives (auto-loaded)
  - Always orient before editing: run CGC on target files first.
  - Use uv, never pip.
  - ...

Claude Code sees this and uses it as context for the first response.
```

If Hindsight is unavailable, the script prints nothing (or a brief warning) and exits 0 — the session proceeds normally.

### Journey 2 — Pre-commit runs pytest on changed test files

The developer runs `git commit`. The pre-commit framework fires a new local hook:
1. Collects all staged `.py` files.
2. For each staged file in `ttadev/`, looks for a corresponding test file in `tests/` (e.g. `ttadev/primitives/memory/agent_memory.py` → `tests/primitives/memory/test_agent_memory.py`).
3. If matching test files exist, runs `uv run pytest {test_files} -x --tb=short`.
4. Passes if tests pass or no test files are found. Blocks if tests fail.

```python
# Staged: ttadev/primitives/memory/agent_memory.py
# Found:  tests/primitives/memory/test_agent_memory.py
# Runs:   uv run pytest tests/primitives/memory/test_agent_memory.py -x --tb=short
# Result: PASS → commit proceeds
```

### Journey 3 — Session ends, decisions auto-retained

When Claude Code stops (the `Stop` event fires), `scripts/auto_retain.py` runs:
1. Reads recent git commits since the session started (best-effort: last 10 commits, or since `HINDSIGHT_SESSION_START` env var timestamp if set).
2. Formats a retention summary: `[type: session-end] YYYY-MM-DD — <commit subject lines>`.
3. POSTs to the Hindsight retain endpoint.
4. Exits 0 always — never blocks.

```
Session ends.
auto_retain.py runs → reads git log → builds summary:
  "[type: session-end] 2026-03-21 — feat(dev-cycle): add OTel spans; fix n_tests span attr"
→ POST /v1/default/banks/<derived-project-or-workspace-bank>/memories
→ exits 0
```

### Journey 4 — Hindsight down throughout session

- Session-start hook: prints `# Hindsight unavailable — no directives loaded`, exits 0.
- Auto-retain hook: prints warning `auto_retain: Hindsight unavailable, skipping`, exits 0.
- Pre-commit hook: unaffected (does not use Hindsight).

### Journey 5 — No matching test files for staged changes

```
# Staged: ttadev/workflows/llm_provider.py
# No corresponding tests/workflows/test_llm_provider.py found
# Pre-commit hook: passes through (exit 0)
```

### Journey 6 — Tests fail on commit

```
# Staged: ttadev/primitives/memory/agent_memory.py (breaking change)
# Found:  tests/primitives/memory/test_agent_memory.py
# Runs:   pytest ... → FAILED (2 errors)
# Pre-commit hook: exit 1 → commit blocked, test output shown
```

---

## Components

### 1. `scripts/auto_retain.py` — Session-end retain script

Standalone Python script invoked by the Claude Code `Stop` hook.

- Reads `HINDSIGHT_URL` (default: `http://localhost:8888`).
- Targets the current derived `project-*` or `workspace-*` bank by default, unless `HINDSIGHT_BANK` is explicitly set.
- Runs `git log --oneline -10` to collect recent commit subjects.
- POSTs `{"items": [{"content": "[type: session-end] YYYY-MM-DD — <subjects>"}], "async": true}` to `{HINDSIGHT_URL}/v1/default/banks/{bank}/memories`.
- If POST fails (network error, timeout, 4xx/5xx): prints warning to stderr, exits 0.
- If git log is empty: posts `[type: session-end] YYYY-MM-DD — no commits this session`.
- Uses only the Python standard library so the hook works under plain `python`.

### 2. `scripts/session_start_recall.py` — Session-start directives script

Standalone Python script invoked by the Claude Code `UserPromptSubmit` hook.

- Reads `HINDSIGHT_URL` (default: `http://localhost:8888`).
- Loads directives from `adam-global` first, then from the current derived `project-*` or `workspace-*` bank unless `HINDSIGHT_BANK` is explicitly set.
- GETs `{HINDSIGHT_URL}/v1/default/banks/{bank}/directives`.
- Prints directives formatted as Markdown (prefixed `## Hindsight Directives (auto-loaded)`).
- If unavailable: prints nothing, exits 0 (silent).
- Timeout: 2 seconds (must not slow down session start perceptibly).

### 3. Pre-commit hook entry in `.pre-commit-config.yaml`

A new `local` entry in the existing `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pytest-changed
      name: "🧪 Pytest Changed Tests"
      entry: python scripts/run_changed_tests.py
      language: system
      types: [python]
      pass_filenames: true
```

Backed by `scripts/run_changed_tests.py`:
- Receives staged `.py` file paths as `sys.argv[1:]`.
- For each path matching `ttadev/**/*.py` (not already a test file), looks for `tests/**/<filename>` or `tests/**/test_<stem>.py`.
- Collects all found test files.
- If none: exits 0 (pass-through).
- If found: runs `subprocess.run(["uv", "run", "pytest"] + test_files + ["-x", "--tb=short"])` and mirrors the exit code.

### 4. Claude Code hook configuration in `settings.local.json`

Adds entries to `.claude/settings.local.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python scripts/auto_retain.py"}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python scripts/session_start_recall.py"}
        ]
      }
    ]
  }
}
```

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Hindsight down (session-start) | Script prints nothing, exits 0 — session proceeds |
| Hindsight down (auto-retain) | Script prints warning to stderr, exits 0 |
| Git log empty | `auto_retain.py` retains `"no commits this session"` |
| No test files found for staged files | Pre-commit hook exits 0 |
| Test run fails | Pre-commit hook exits 1, output shown to developer |
| `uv` not on PATH | Pre-commit hook prints error and exits 1 |
| Script timeout (Hindsight slow) | 2s timeout for session-start; 5s for auto-retain — exits 0 on timeout |
| `settings.local.json` missing hooks key | Hooks not configured; automations simply don't fire |
| Pre-commit not installed | `git commit` skips pre-commit entirely — developer runs `uv run pre-commit install` |

---

## File Layout

| Action | Path | Purpose |
|---|---|---|
| Create | `scripts/auto_retain.py` | Session-end retain (Stop hook target) |
| Create | `scripts/session_start_recall.py` | Session-start directives loader (UserPromptSubmit hook target) |
| Create | `scripts/run_changed_tests.py` | Pre-commit pytest runner |
| Modify | `.pre-commit-config.yaml` | Add `pytest-changed` local hook entry |
| Modify | `.claude/settings.local.json` | Register `Stop` and `UserPromptSubmit` hooks |
| Create | `tests/scripts/test_auto_retain.py` | Unit tests for auto_retain.py |
| Create | `tests/scripts/test_session_start_recall.py` | Unit tests for session_start_recall.py |
| Create | `tests/scripts/test_run_changed_tests.py` | Unit tests for run_changed_tests.py |

---

## Success Criteria

1. `python scripts/auto_retain.py` exits 0 when Hindsight is available and retains a session summary.
2. `python scripts/auto_retain.py` exits 0 when Hindsight is unavailable (graceful degradation).
3. `python scripts/session_start_recall.py` prints Markdown directives when Hindsight is available.
4. `python scripts/session_start_recall.py` exits 0 silently when Hindsight is unavailable.
5. `python scripts/run_changed_tests.py ttadev/primitives/memory/agent_memory.py` finds and runs `tests/primitives/memory/test_agent_memory.py`.
6. `python scripts/run_changed_tests.py ttadev/workflows/llm_provider.py` exits 0 when no test file is found.
7. `uv run pre-commit run --all-files` passes on a clean repo.
8. Claude Code `Stop` hook fires `auto_retain.py` after each session.
9. Claude Code `UserPromptSubmit` hook fires `session_start_recall.py` on first prompt.
10. 100% test coverage for all three scripts using mocked `httpx` and `subprocess`.

---

## Out of Scope

- Quality gates / confidence scoring on LLM output (separate Phase 4 sub-feature)
- Multi-model fallback chains via `FallbackPrimitive` (separate Phase 4 sub-feature)
- `feature_dev_workflow` and `quick_fix_workflow` updates (separate Phase 4 sub-feature)
- `DevelopmentCycle` invocation in pre-commit (too heavy for commit-time validation)
- Streaming LLM responses
- `AgentRegistry` integration
- Scheduled / cron-based auto-retain (hook-based only)
- Auto-staging or auto-committing from hooks
- Running hooks in CI (these are developer-local automations)
