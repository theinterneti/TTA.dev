# Feature Dev Workflow with L0 Tracking

Run the built-in `feature_dev` workflow and inspect it through the local L0
control plane.

## Why this example matters

This is the first repo-supported Phase 2 proof path that ties together:

- `ttadev/workflows/`
- `ttadev/control_plane/`
- `tta workflow ...`
- `tta control ...`

It is intentionally narrow. This slice proves **tracking and inspection** for a
real workflow. It does **not** add resume or restart controls yet.

## Run the workflow

Use `--track-l0` to create one top-level L0 task and one L0 run for the
workflow execution.

```bash
tta workflow run feature_dev --goal "Add password reset flow" --track-l0
```

The CLI prints the created L0 identifiers early:

```text
L0 task: task_...
L0 run:  run_...
Inspect with: tta control task show task_...
```

If you want to bypass interactive gate prompts during experimentation, add
`--no-confirm`:

```bash
tta workflow run feature_dev \
  --goal "Add password reset flow" \
  --track-l0 \
  --no-confirm
```

## Inspect workflow progress

Show the tracked task:

```bash
tta control task show <task_id>
```

The control-plane view includes:

- workflow name and goal
- overall workflow status
- current step and current agent
- per-step status and attempt count
- step result summaries and confidence
- gate outcomes such as `continue`, `skip`, `edit`, and `quit`
- linked gate IDs for the existing approval checkpoints

You can also inspect the underlying run directly:

```bash
tta control run show <run_id>
```

## What gets tracked

For a tracked `feature_dev` execution, TTA.dev creates:

- one top-level L0 task for the whole workflow
- one active L0 run for the orchestrator execution
- workflow metadata on the task for each step:
  - `developer`
  - `qa`
  - `security`
  - `git`
  - `github`

The current slice keeps workflow-specific outcomes in workflow metadata and uses
the embedded task gates mainly as approval-friendly checkpoints for successful
forward progress.

## Current limits

- tracking is opt-in with `--track-l0`
- this proof path is implemented for the built-in `feature_dev` workflow first
- `quit` and failure states stay inspectable, but they are not resumable yet
- this example is about honest local coordination, not full production workflow
  orchestration
