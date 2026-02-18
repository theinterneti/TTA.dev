# tta-dolt-primitives

Dolt primitives for versioned, branchable data — the engine for parallel universe mechanics in TTA and any branching-state application.

## What is this?

[Dolt](https://github.com/dolthub/dolt) is Git for data: a SQL database where every row is versioned, branchable, and mergeable. This package wraps Dolt's branch/commit/merge/diff operations as composable `WorkflowPrimitive` objects, making them first-class citizens in TTA.dev workflows.

## The Core Idea

```
Git concept   →  What it means in TTA
─────────────────────────────────────
branch        →  parallel universe
commit        →  game state snapshot (player choice, scene transition)
checkout      →  switch to a different universe
diff          →  compare two universe timelines
merge         →  editorial curation: universe → canonical timeline
```

## Primitives

| Primitive | What it does |
|-----------|-------------|
| `DoltUniversePrimitive` | Branch lifecycle: create, checkout, list, delete universes |
| `DoltCommitPrimitive` | Snapshot game state as a versioned commit |
| `DoltMergePrimitive` | Merge a universe into the canonical timeline (editorial PR) |
| `DoltDiffPrimitive` | Compare two universes to see how they diverged |
| `DoltQueryPrimitive` | SQL queries scoped to any universe branch |

## Quick Start

```python
from tta_dolt_primitives import (
    DoltConfig,
    DoltUniversePrimitive, UniverseInput, BranchOperation,
    DoltCommitPrimitive, CommitInput,
    DoltDiffPrimitive, DiffInput,
    DoltQueryPrimitive, QueryInput,
)
from tta_dev_primitives.core.base import WorkflowContext

config = DoltConfig(repo_path="/path/to/game-db")
context = WorkflowContext(workflow_id="session-123")

# Fork a new private universe for a player
universe = DoltUniversePrimitive(config)
await universe.execute(
    UniverseInput(
        operation=BranchOperation.CREATE_AND_CHECKOUT,
        name="player-42/forest-path",
    ),
    context,
)

# Snapshot state after a choice
commit = DoltCommitPrimitive(config)
await commit.execute(
    CommitInput(message="Player entered the forest", author="player-42"),
    context,
)

# See how this universe diverged from the canonical timeline
diff = DoltDiffPrimitive(config)
result = await diff.execute(
    DiffInput(from_branch="main", to_branch="player-42/forest-path"),
    context,
)

# Query this universe's character state in plain SQL
query = DoltQueryPrimitive(config)
result = await query.execute(
    QueryInput(
        sql="SELECT emotional_intelligence, resilience_level FROM character_state WHERE player_id = %s",
        branch="player-42/forest-path",
        params=("player-42",),
    ),
    context,
)
```

## Requirements

- Python 3.11+
- Dolt binary installed (`dolt version` should work)
- For `DoltQueryPrimitive`: a running Dolt SQL server (`dolt sql-server`)

## Installation

```bash
uv add tta-dolt-primitives
```

## Dolt SQL Server

`DoltQueryPrimitive` connects to Dolt's MySQL-compatible SQL server:

```bash
cd /path/to/game-db
dolt sql-server --host 127.0.0.1 --port 3306 &
```

All other primitives use the Dolt CLI directly and don't require the server.
