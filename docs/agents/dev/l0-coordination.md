# L0 Coordination Reference

## What TTA.dev owns

TTA.dev owns the **L0 developer control plane** — task coordination, agent leases, approval gates,
and workflow state for coding agents operating on this repository.

This is **separate** from TTA's player-session orchestration (IPA/WBA/NGA). Those are
different control planes serving different audiences.

## L0 surface

| Component | Location | Purpose |
|---|---|---|
| `control_plane/` | `ttadev/control_plane/` | JSON-backed task/run/lease state |
| CLI | `ttadev/cli/control.py` | `tta control task|run|workflow …` |
| MCP tools | `ttadev/primitives/mcp_server/server.py` | Coding-agent facing tool interface |

## Task lifecycle

```
create_task → claim_task (agent takes lease)
  → mark_step_running → record_step_result
  → record_gate_outcome (policy evaluation)
  → release_run → complete_task
```

State machine:

```
PENDING → RUNNING (claim) → COMPLETED
                          → FAILED (release with failure)
                          → WAITING_APPROVAL (gate requires human)
```

Leases expire automatically. An agent that crashes forfeits its lease; another agent
can claim the task after the lease TTL.

## Starting a workflow (CLI)

```bash
tta control workflow start \
  --name "feature-x" \
  --goal "implement and review feature X" \
  --agents "developer,reviewer" \
  --policy-gate "id=quality,label=Quality gate,policy=auto:confidence>=0.8"
```

## MCP tool interface (coding agents)

The following MCP tools are available to coding agents via the `tta-mcp` server:

| Tool | Purpose |
|---|---|
| `control_start_workflow` | Start a new workflow |
| `control_claim_task` | Claim next available task (takes a lease) |
| `control_mark_workflow_step_running` | Signal step has started |
| `control_record_workflow_step_result` | Record outcome of a step |
| `control_record_workflow_gate_outcome` | Record policy gate decision |
| `control_mark_workflow_step_failed` | Signal step failure |

Full tool signatures: `docs/mcp-tool-specs.md` or inspect `ttadev/primitives/mcp_server/server.py`.

## Continuation rule

**If a task involves coding-agent coordination, task ownership, approvals, or leases —
extend the existing L0 surface. Do not build a second orchestration system.**

Current priority order:

1. Prove one documented, repeatable multi-agent workflow end-to-end
2. Deepen approval/policy workflows where needed by that workflow
3. Strengthen ownership and telemetry attribution
4. Connect more agent surfaces to L0 state (not parallel systems)

## Cross-repo sync

This file has a counterpart in TTA: `docs/agents/dev/l0-boundary.md`.

Any structural or protocol change (not typo/formatting) requires opening a tracking
issue in TTA. See `docs/agents/MAINTENANCE.md` for the sync protocol.

Current sync status: TTA.dev L0 phase-1 complete as of 2026-03-30.
TTA boundary doc documents what TTA does NOT own (developer-agent coordination stays in TTA.dev).

## What belongs in TTA.dev vs TTA

| Concern | Owner |
|---|---|
| Developer-agent task queues, leases, approval gates | TTA.dev (this repo) |
| L0 control plane (routing, state, MCP interface) | TTA.dev (this repo) |
| Player-session orchestration (IPA/WBA/NGA) | TTA |
| Redis keys for player state | TTA |
| Therapeutic safety signals | TTA |

**Do not add L0 state into TTA's Redis keys or player-session tables.**
