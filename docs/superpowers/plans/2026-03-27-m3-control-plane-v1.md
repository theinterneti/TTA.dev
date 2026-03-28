# TTA.dev M3 — Control Plane v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ESCALATE_TO_HUMAN` gate outcome added with workflow pause behavior; abandoned and orphaned workflow edge cases handled; MCP tool JSON Schema specs committed; L0 runbook updated.

**Architecture:** All changes are additive to existing `models.py`, `service.py`, and `server.py`. No existing gate or workflow APIs are broken. `WorkflowGateDecisionOutcome` gains one new value. `WorkflowTrackingStatus` gains one new value. The service gains escalation-handling logic. JSON Schema specs for all 23 MCP tools are committed as a single document.

**Tech Stack:** Python 3.11+, pytest, pytest-asyncio (`asyncio_mode = "auto"`), JSON Schema (draft-07), uv

---

## Baseline Check

- [ ] Run the existing control plane tests to confirm they all pass before touching anything:

  ```bash
  uv run pytest tests/unit/test_control_plane_gate_service.py \
    tests/unit/test_control_plane_lock_service.py \
    tests/unit/test_control_plane_workflow_service.py \
    tests/unit/test_control_plane_trace_attribution.py \
    tests/unit/test_mcp_control_plane_tools.py \
    tests/unit/test_l0_control_cli.py \
    -v 2>&1 | tail -10
  ```
  Expected: All PASS. If any fail, fix them before continuing — do not proceed with M3 work on top of pre-existing failures.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `ttadev/control_plane/models.py` | Modify | Add `ESCALATE_TO_HUMAN` to `WorkflowGateDecisionOutcome`; add `ESCALATED` to `WorkflowTrackingStatus` |
| `ttadev/control_plane/service.py` | Modify | Handle `ESCALATE_TO_HUMAN` outcome; handle abandoned/orphaned edge cases |
| `ttadev/primitives/mcp_server/server.py` | Read only | Verify tool signatures match JSON Schema specs |
| `tests/unit/test_control_plane_workflow_service.py` | Modify | Add tests for escalation, abandonment, orphaned steps |
| `tests/unit/test_mcp_control_plane_tools.py` | Modify | Add tests for escalation tool behavior |
| `docs/mcp-tool-specs.md` | Create | JSON Schema specs for all 23 MCP control-plane tools |
| `docs/agent-guides/l0-workflow-runbook.md` | Modify | Add escalation section; update known-gaps list |

---

## Task 1: Add `ESCALATE_TO_HUMAN` to Models

The `WorkflowGateDecisionOutcome` enum controls what happens after a policy gate evaluates. Currently: `CONTINUE`, `SKIP`, `EDIT`, `QUIT`. We add `ESCALATE_TO_HUMAN` to signal that the gate has determined a human must intervene before the workflow can proceed.

We also add `ESCALATED` to `WorkflowTrackingStatus` (the workflow-level status) so the overall workflow reflects the escalated state.

**Files:**
- Modify: `ttadev/control_plane/models.py`
- Modify: `tests/unit/test_control_plane_workflow_service.py`

- [ ] **Step 1: Write the failing test**

  Open `tests/unit/test_control_plane_workflow_service.py` and add:

  ```python
  def test_escalate_to_human_is_a_valid_gate_outcome():
      from ttadev.control_plane.models import WorkflowGateDecisionOutcome
      # Assert — the enum value exists
      assert WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN is not None
      assert WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN.value == "escalate_to_human"


  def test_escalated_is_a_valid_workflow_status():
      from ttadev.control_plane.models import WorkflowTrackingStatus
      assert WorkflowTrackingStatus.ESCALATED is not None
      assert WorkflowTrackingStatus.ESCALATED.value == "escalated"
  ```

- [ ] **Step 2: Run — verify FAIL**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_escalate_to_human_is_a_valid_gate_outcome -v
  ```
  Expected: `FAIL` with `AttributeError` — enum value doesn't exist yet.

- [ ] **Step 3: Add the enum values to models.py**

  In `ttadev/control_plane/models.py`, find `WorkflowGateDecisionOutcome` and add:

  ```python
  class WorkflowGateDecisionOutcome(str, Enum):
      CONTINUE = "continue"
      SKIP = "skip"
      EDIT = "edit"
      QUIT = "quit"
      ESCALATE_TO_HUMAN = "escalate_to_human"   # ← add this
  ```

  Find `WorkflowTrackingStatus` and add:

  ```python
  class WorkflowTrackingStatus(str, Enum):
      RUNNING = "running"
      COMPLETED = "completed"
      QUIT = "quit"
      FAILED = "failed"
      ESCALATED = "escalated"   # ← add this
  ```

- [ ] **Step 4: Run — verify PASS**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_escalate_to_human_is_a_valid_gate_outcome tests/unit/test_control_plane_workflow_service.py::test_escalated_is_a_valid_workflow_status -v
  ```
  Expected: Both PASS.

- [ ] **Step 5: Run the full test suite — verify no regressions**

  ```bash
  uv run pytest tests/unit/ -q
  ```
  Expected: All previously-passing tests still PASS.

- [ ] **Step 6: Commit**

  ```bash
  git add ttadev/control_plane/models.py tests/unit/test_control_plane_workflow_service.py
  git commit -m "feat(control-plane): add ESCALATE_TO_HUMAN gate outcome and ESCALATED workflow status"
  ```

---

## Task 2: Escalation Handling in Service

When a workflow gate records outcome `ESCALATE_TO_HUMAN`, the service must:
1. Set the workflow's `status` to `ESCALATED`
2. Leave the current step in `RUNNING` state (it can't proceed without human input)
3. **Not** advance to the next step

This mirrors how `QUIT` works, but `ESCALATED` is recoverable — a human approves the gate and the workflow can resume with `CONTINUE`.

**Files:**
- Modify: `ttadev/control_plane/service.py`
- Modify: `tests/unit/test_control_plane_workflow_service.py`

- [ ] **Step 1: Write the failing test**

  In `tests/unit/test_control_plane_workflow_service.py`, add:

  ```python
  async def test_escalate_to_human_pauses_workflow(tmp_path):
      # Arrange
      svc = ControlPlaneService(data_dir=tmp_path)
      claim = svc.start_tracked_workflow(
          workflow_name="test-wf",
          workflow_goal="test escalation",
          step_agents=["agent-a", "agent-b"],
      )
      task_id = claim.task.id

      svc.mark_workflow_step_running(task_id, step_index=0)
      svc.record_workflow_step_result(task_id, step_index=0, result_summary="done", confidence=0.5)

      # Act — record ESCALATE_TO_HUMAN outcome
      task = svc.record_workflow_gate_outcome(
          task_id,
          step_index=0,
          decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
          summary="Low confidence — needs human review",
      )

      # Assert — workflow is paused, not advanced
      from ttadev.control_plane.models import WorkflowTrackingStatus, WorkflowStepStatus
      assert task.workflow.status == WorkflowTrackingStatus.ESCALATED
      assert task.workflow.steps[0].status == WorkflowStepStatus.RUNNING
      # Step 1 has NOT started
      assert task.workflow.steps[1].status == WorkflowStepStatus.PENDING


  async def test_workflow_resumes_after_human_approves_escalated_gate(tmp_path):
      # Arrange
      svc = ControlPlaneService(data_dir=tmp_path)
      claim = svc.start_tracked_workflow(
          workflow_name="test-wf",
          workflow_goal="test escalation resume",
          step_agents=["agent-a", "agent-b"],
      )
      task_id = claim.task.id

      svc.mark_workflow_step_running(task_id, step_index=0)
      svc.record_workflow_step_result(task_id, step_index=0, result_summary="done", confidence=0.5)
      svc.record_workflow_gate_outcome(
          task_id, step_index=0,
          decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
          summary="needs human",
      )

      # Act — human approves via the standard gate mechanism
      # Find the gate for step 0
      task = svc.get_task(task_id)
      gate_id = task.workflow.steps[0].linked_gate_id
      task = svc.decide_gate(
          task_id, gate_id,
          status=GateStatus.APPROVED,
          decided_by="human-reviewer",
          summary="Looks good",
      )

      # Assert — workflow status restored to RUNNING after human approval
      from ttadev.control_plane.models import WorkflowTrackingStatus
      assert task.workflow.status == WorkflowTrackingStatus.RUNNING
  ```

  You will also need these imports at the top of the test file if not already present:
  ```python
  from ttadev.control_plane.models import WorkflowGateDecisionOutcome, GateStatus
  from ttadev.control_plane.service import ControlPlaneService
  ```

- [ ] **Step 2: Run — verify FAIL**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_escalate_to_human_pauses_workflow -v
  ```
  Expected: `FAIL` — `record_workflow_gate_outcome` doesn't handle `ESCALATE_TO_HUMAN` yet.

- [ ] **Step 3: Implement escalation handling in service.py**

  Open `ttadev/control_plane/service.py`. Find the `record_workflow_gate_outcome` method. Locate the section that handles each outcome type (`CONTINUE`, `SKIP`, `EDIT`, `QUIT`). Add handling for `ESCALATE_TO_HUMAN`:

  ```python
  elif decision == WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN:
      # Pause the workflow — do not advance to the next step.
      # The step remains RUNNING until a human approves the linked gate.
      task.workflow.status = WorkflowTrackingStatus.ESCALATED
  ```

  Also find the `decide_gate` method. After a gate is `APPROVED`, if `task.workflow.status == WorkflowTrackingStatus.ESCALATED`, restore it to `RUNNING`:

  ```python
  # After setting gate to APPROVED — check if workflow was escalated
  if (
      task.workflow is not None
      and task.workflow.status == WorkflowTrackingStatus.ESCALATED
      and new_status == GateStatus.APPROVED
  ):
      task.workflow.status = WorkflowTrackingStatus.RUNNING
  ```

  **Important:** Read the full `record_workflow_gate_outcome` and `decide_gate` methods carefully before editing. Match the existing code style exactly.

- [ ] **Step 4: Run — verify PASS**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_escalate_to_human_pauses_workflow tests/unit/test_control_plane_workflow_service.py::test_workflow_resumes_after_human_approves_escalated_gate -v
  ```

- [ ] **Step 5: Run full test suite — verify no regressions**

  ```bash
  uv run pytest tests/unit/ -q
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add ttadev/control_plane/service.py tests/unit/test_control_plane_workflow_service.py
  git commit -m "feat(control-plane): handle ESCALATE_TO_HUMAN — pause workflow, resume on gate approval"
  ```

---

## Task 3: Abandoned Workflow Edge Cases

Currently, when a run's lease expires, the workflow stays `RUNNING` indefinitely with no mechanism to detect or recover from the abandonment. This task:

1. Extends `start_tracked_workflow` to forward `lease_ttl_seconds` (needed for short-TTL tests)
2. Adds `expire_abandoned_workflows` to detect and recover abandoned runs
3. Tests the full abandonment path

**Files:**
- Modify: `ttadev/control_plane/service.py`
- Modify: `tests/unit/test_control_plane_workflow_service.py`

- [ ] **Step 0: Extend `start_tracked_workflow` to accept `lease_ttl_seconds`**

  `start_tracked_workflow` (line ~661) currently calls `claim_task` internally with a hardcoded TTL. The abandonment test needs a short TTL. Add the parameter:

  In `service.py`, update the signature:
  ```python
  def start_tracked_workflow(
      self,
      *,
      workflow_name: str,
      workflow_goal: str,
      step_agents: list[str],
      project_name: str | None = None,
      extra_gates: list[dict[str, Any]] | None = None,
      lease_ttl_seconds: float = 300.0,   # ← add this
  ) -> ClaimResult:
  ```

  Then find the internal `claim_task` call and add `lease_ttl_seconds=lease_ttl_seconds`.

  Verify existing tests still pass:
  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py -q
  ```

- [ ] **Step 1: Write the failing test**

  ```python
  async def test_expire_abandoned_workflow_marks_step_and_workflow_failed(tmp_path):
      # Arrange
      import asyncio
      svc = ControlPlaneService(data_dir=tmp_path)
      claim = svc.start_tracked_workflow(
          workflow_name="test-wf",
          workflow_goal="test abandonment",
          step_agents=["agent-a"],
          lease_ttl_seconds=0.01,
      )
      task_id = claim.task.id

      svc.mark_workflow_step_running(task_id, step_index=0)

      # Wait for lease to expire
      await asyncio.sleep(0.05)

      # Act — expire abandoned workflows
      affected = svc.expire_abandoned_workflows()

      # Assert
      from ttadev.control_plane.models import WorkflowTrackingStatus, WorkflowStepStatus
      assert task_id in affected
      task = svc.get_task(task_id)
      assert task.workflow.status == WorkflowTrackingStatus.FAILED
      assert task.workflow.steps[0].status == WorkflowStepStatus.FAILED
  ```

- [ ] **Step 2: Run — verify FAIL**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_expire_abandoned_workflow_marks_step_and_workflow_failed -v
  ```
  Expected: `FAIL` — `expire_abandoned_workflows` doesn't exist yet.

- [ ] **Step 3: Implement expire_abandoned_workflows in service.py**

  Add a new public method to `ControlPlaneService`:

  ```python
  def expire_abandoned_workflows(self) -> list[str]:
      """Find workflows whose active run lease has expired and mark them FAILED.

      Returns list of task IDs that were transitioned to FAILED.
      Call periodically (e.g., on session start or via a background process).
      """
      from datetime import datetime, timezone

      now = datetime.now(timezone.utc)
      affected: list[str] = []

      for task in self._store.list_tasks():
          if task.workflow is None:
              continue
          if task.workflow.status != WorkflowTrackingStatus.RUNNING:
              continue
          if task.active_run_id is None:
              continue

          lease = self._store.get_lease_for_run(task.active_run_id)
          if lease is None or lease.expires_at > now:
              continue

          # Lease expired — mark current running step as FAILED
          current_step_idx = task.workflow.current_step_index
          if current_step_idx is not None:
              step = task.workflow.steps[current_step_idx]
              if step.status == WorkflowStepStatus.RUNNING:
                  step.status = WorkflowStepStatus.FAILED

          task.workflow.status = WorkflowTrackingStatus.FAILED
          self._store.put_task(task)
          affected.append(task.id)

      return affected
  ```

  **Note:** Import `WorkflowTrackingStatus` and `WorkflowStepStatus` at the top of the method or confirm they are already imported in the file.

- [ ] **Step 4: Run — verify PASS**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_expire_abandoned_workflow_marks_step_and_workflow_failed -v
  ```

- [ ] **Step 5: Run full test suite**

  ```bash
  uv run pytest tests/unit/ -q
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add ttadev/control_plane/service.py tests/unit/test_control_plane_workflow_service.py
  git commit -m "feat(control-plane): add expire_abandoned_workflows for lease-expired workflow recovery"
  ```

---

## Task 4: Orphaned Step Edge Cases

An orphaned step occurs when a workflow is `QUIT` or `FAILED` but a step is still in `RUNNING` state (e.g., the workflow was force-quit). This task adds a cleanup method.

**Files:**
- Modify: `ttadev/control_plane/service.py`
- Modify: `tests/unit/test_control_plane_workflow_service.py`

- [ ] **Step 1: Write the failing test**

  ```python
  def test_cleanup_orphaned_steps_marks_running_steps_failed_when_workflow_terminated(tmp_path):
      # Arrange
      svc = ControlPlaneService(data_dir=tmp_path)
      claim = svc.start_tracked_workflow(
          workflow_name="test-wf",
          workflow_goal="test orphan cleanup",
          step_agents=["agent-a", "agent-b"],
      )
      task_id = claim.task.id

      # Manually force the workflow to QUIT while step 0 is still RUNNING
      svc.mark_workflow_step_running(task_id, step_index=0)

      # Simulate a crash that leaves the workflow in an inconsistent state:
      # workflow QUIT but step still RUNNING. This state is only reachable via
      # a process crash or external store mutation — intentional use of _store
      # here to create the precondition for recovery code testing.
      task = svc.get_task(task_id)
      task.workflow.status = WorkflowTrackingStatus.QUIT
      svc._store.put_task(task)  # noqa: SLF001 — intentional crash simulation

      # Act
      cleaned = svc.cleanup_orphaned_steps(task_id)

      # Assert
      from ttadev.control_plane.models import WorkflowStepStatus
      assert cleaned > 0
      task = svc.get_task(task_id)
      assert task.workflow.steps[0].status == WorkflowStepStatus.FAILED
  ```

- [ ] **Step 2: Run — verify FAIL**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_cleanup_orphaned_steps_marks_running_steps_failed_when_workflow_terminated -v
  ```

- [ ] **Step 3: Implement cleanup_orphaned_steps in service.py**

  ```python
  def cleanup_orphaned_steps(self, task_id: str) -> int:
      """Mark any RUNNING steps as FAILED for a terminated workflow.

      Use when a workflow is QUIT/FAILED but steps were not cleanly transitioned.
      Returns count of steps cleaned up.
      """
      # Use the existing pattern from throughout service.py (not _get_task_or_raise
      # which doesn't exist — the pattern is _store.get_task + explicit None check)
      task = self._store.get_task(task_id)
      if task is None:
          raise TaskNotFoundError(f"Task not found: {task_id}")
      if task.workflow is None:
          return 0

      terminal_statuses = {WorkflowTrackingStatus.QUIT, WorkflowTrackingStatus.FAILED}
      if task.workflow.status not in terminal_statuses:
          return 0

      cleaned = 0
      for step in task.workflow.steps:
          if step.status == WorkflowStepStatus.RUNNING:
              step.status = WorkflowStepStatus.FAILED
              cleaned += 1

      if cleaned > 0:
          self._store.put_task(task)

      return cleaned
  ```

- [ ] **Step 4: Run — verify PASS**

  ```bash
  uv run pytest tests/unit/test_control_plane_workflow_service.py::test_cleanup_orphaned_steps_marks_running_steps_failed_when_workflow_terminated -v
  ```

- [ ] **Step 5: Run full test suite**

  ```bash
  uv run pytest tests/unit/ -q
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add ttadev/control_plane/service.py tests/unit/test_control_plane_workflow_service.py
  git commit -m "feat(control-plane): add cleanup_orphaned_steps for terminated-workflow step recovery"
  ```

---

## Task 4b: GatePolicy Type

The M3 spec requires a `GatePolicy` named type (distinct from the existing `policy_name` string). `GatePolicy` formalises what the current `"auto:confidence>=0.8"` strings express, plus the new escalation condition.

**Files:**
- Modify: `ttadev/control_plane/models.py`
- Modify: `tests/unit/test_control_plane_gate_service.py`

- [ ] **Step 1: Write the failing test**

  ```python
  def test_gate_policy_is_a_typed_dataclass():
      from ttadev.control_plane.models import GatePolicy
      policy = GatePolicy(
          name="quality-gate",
          approve_above_confidence=0.8,
          escalate_below_confidence=0.5,
      )
      assert policy.name == "quality-gate"
      assert policy.approve_above_confidence == 0.8
      assert policy.escalate_below_confidence == 0.5


  def test_gate_policy_defaults_are_none():
      from ttadev.control_plane.models import GatePolicy
      policy = GatePolicy(name="minimal")
      assert policy.approve_above_confidence is None
      assert policy.escalate_below_confidence is None
  ```

- [ ] **Step 2: Run — verify FAIL**

  ```bash
  uv run pytest tests/unit/test_control_plane_gate_service.py::test_gate_policy_is_a_typed_dataclass -v
  ```
  Expected: `FAIL` — `GatePolicy` doesn't exist yet.

- [ ] **Step 3: Add GatePolicy to models.py**

  In `ttadev/control_plane/models.py`, add after the existing enums:

  ```python
  @dataclass
  class GatePolicy:
      """Named policy governing when a gate auto-approves or escalates.

      Replaces the opaque ``policy_name`` string for callers that want a
      typed representation. Convert to a ``policy_name`` string for storage:
      use ``GatePolicy.to_policy_name()`` when passing to service methods.
      """
      name: str
      approve_above_confidence: float | None = None
      escalate_below_confidence: float | None = None

      def to_policy_name(self) -> str:
          """Serialize to the policy_name string format used by the service."""
          if self.approve_above_confidence is not None:
              return f"auto:confidence>={self.approve_above_confidence}"
          if self.escalate_below_confidence is not None:
              return f"auto:escalate_below:{self.escalate_below_confidence}"
          return "auto:always"
  ```

- [ ] **Step 4: Run — verify PASS**

  ```bash
  uv run pytest tests/unit/test_control_plane_gate_service.py::test_gate_policy_is_a_typed_dataclass tests/unit/test_control_plane_gate_service.py::test_gate_policy_defaults_are_none -v
  ```

- [ ] **Step 5: Export GatePolicy from control_plane __init__.py**

  In `ttadev/control_plane/__init__.py`, add `GatePolicy` to the public exports.

  Verify:
  ```bash
  uv run python -c "from ttadev.control_plane import GatePolicy; print('OK')"
  ```

- [ ] **Step 6: Run full test suite**

  ```bash
  uv run pytest tests/unit/ -q
  ```

- [ ] **Step 7: Commit**

  ```bash
  git add ttadev/control_plane/models.py ttadev/control_plane/__init__.py tests/unit/test_control_plane_gate_service.py
  git commit -m "feat(control-plane): add GatePolicy typed dataclass for named gate policies"
  ```

---

## Task 5: MCP Tool JSON Schema Specs

Publish formal input/output schemas for all 23 MCP control-plane tools. This is the contract TTA consumers pin to.

**Files:**
- Read: `ttadev/primitives/mcp_server/server.py`
- Create: `docs/mcp-tool-specs.md`

- [ ] **Step 1: Read the MCP server to get exact tool signatures**

  ```bash
  uv run python -c "
  import ast, pathlib
  src = pathlib.Path('ttadev/primitives/mcp_server/server.py').read_text()
  tree = ast.parse(src)
  for node in ast.walk(tree):
      if isinstance(node, ast.FunctionDef) and node.name.startswith('control_'):
          args = [a.arg for a in node.args.args]
          print(f'{node.name}({', '.join(args)})')
  " 2>/dev/null | head -40
  ```

  Cross-reference the output with the server source to capture parameter types and return types.

- [ ] **Step 2: Create the spec document**

  Create `docs/mcp-tool-specs.md`. Use this structure for each tool (example shown for two tools — complete all 23):

  ````markdown
  # MCP Control-Plane Tool Specifications

  **Server:** `ttadev/primitives/mcp_server/server.py`
  **Version:** M3.0
  **Total tools:** 23

  All tools are exposed over the Model Context Protocol. Read-only tools are safe
  to call at any time. Mutating tools change persistent state in `.tta/control/`.

  ---

  ## control_create_task

  **Type:** Mutating
  **Description:** Create a new task in the control plane.

  **Input schema:**
  ```json
  {
    "type": "object",
    "required": ["title"],
    "properties": {
      "title": {"type": "string", "description": "Short imperative title"},
      "description": {"type": "string", "default": ""},
      "project_name": {"type": "string"},
      "requested_role": {"type": "string"},
      "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
      "gates": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["id", "gate_type", "label"],
          "properties": {
            "id": {"type": "string"},
            "gate_type": {"type": "string", "enum": ["approval", "policy", "review"]},
            "label": {"type": "string"},
            "required": {"type": "boolean", "default": true},
            "policy_name": {"type": "string"}
          }
        }
      }
    }
  }
  ```

  **Output:** `TaskRecord` serialized as JSON object.

  ---

  ## control_start_workflow

  **Type:** Mutating
  **Description:** Create a task and run representing a multi-step agent workflow.

  **Input schema:**
  ```json
  {
    "type": "object",
    "required": ["workflow_name", "workflow_goal", "step_agents"],
    "properties": {
      "workflow_name": {"type": "string"},
      "workflow_goal": {"type": "string"},
      "step_agents": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1
      },
      "project_name": {"type": "string"},
      "lease_ttl_seconds": {"type": "number", "default": 300}
    }
  }
  ```

  **Output:** `ClaimResult` (task + run + lease) serialized as JSON object.

  ---

  ## control_record_workflow_gate_outcome

  **Type:** Mutating
  **Description:** Record the outcome of a workflow step gate. Supports ESCALATE_TO_HUMAN to pause the workflow for human review.

  **Input schema:**
  ```json
  {
    "type": "object",
    "required": ["task_id", "step_index", "decision"],
    "properties": {
      "task_id": {"type": "string"},
      "step_index": {"type": "integer", "minimum": 0},
      "decision": {
        "type": "string",
        "enum": ["continue", "skip", "edit", "quit", "escalate_to_human"]
      },
      "summary": {"type": "string", "default": ""},
      "policy_name": {"type": "string"}
    }
  }
  ```

  **Output:** Updated `TaskRecord` as JSON object.

  ---

  ## control_list_tasks

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","properties":{"status":{"type":"string","enum":["pending","in_progress","completed"]},"project_name":{"type":"string"}}}
  ```
  **Output:** Array of `TaskRecord` objects.

  ---

  ## control_get_task

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","required":["task_id"],"properties":{"task_id":{"type":"string"}}}
  ```
  **Output:** `TaskRecord` as JSON object.

  ---

  ## control_claim_task

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id"],"properties":{"task_id":{"type":"string"},"agent_role":{"type":"string"},"lease_ttl_seconds":{"type":"number","default":300}}}
  ```
  **Output:** `ClaimResult` (task + run + lease).

  ---

  ## control_list_runs

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","properties":{"status":{"type":"string","enum":["active","completed","released","expired"]}}}
  ```
  **Output:** Array of `RunRecord` objects.

  ---

  ## control_get_run

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","required":["run_id"],"properties":{"run_id":{"type":"string"}}}
  ```
  **Output:** `RunRecord` as JSON object.

  ---

  ## control_heartbeat_run

  **Type:** Idempotent
  **Input schema:**
  ```json
  {"type":"object","required":["run_id"],"properties":{"run_id":{"type":"string"},"lease_ttl_seconds":{"type":"number","default":300}}}
  ```
  **Output:** Updated `LeaseRecord`.

  ---

  ## control_complete_run

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["run_id"],"properties":{"run_id":{"type":"string"},"summary":{"type":"string","default":""}}}
  ```
  **Output:** Updated `RunRecord`.

  ---

  ## control_release_run

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["run_id"],"properties":{"run_id":{"type":"string"},"reason":{"type":"string","default":""}}}
  ```
  **Output:** Updated `RunRecord`.

  ---

  ## control_decide_gate

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","gate_id","status"],"properties":{"task_id":{"type":"string"},"gate_id":{"type":"string"},"status":{"type":"string","enum":["approved","rejected","changes_requested"]},"decided_by":{"type":"string"},"decision_role":{"type":"string"},"summary":{"type":"string","default":""}}}
  ```
  **Output:** Updated `TaskRecord`.

  ---

  ## control_reopen_gate

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","gate_id"],"properties":{"task_id":{"type":"string"},"gate_id":{"type":"string"},"reopened_by":{"type":"string"},"summary":{"type":"string","default":""}}}
  ```
  **Output:** Updated `TaskRecord`.

  ---

  ## control_list_locks

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","properties":{"scope_type":{"type":"string","enum":["workspace","file"]}}}
  ```
  **Output:** Array of `LockRecord` objects.

  ---

  ## control_acquire_workspace_lock

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","run_id","workspace_name"],"properties":{"task_id":{"type":"string"},"run_id":{"type":"string"},"workspace_name":{"type":"string"}}}
  ```
  **Output:** `LockRecord`.

  ---

  ## control_acquire_file_lock

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","run_id","file_path"],"properties":{"task_id":{"type":"string"},"run_id":{"type":"string"},"file_path":{"type":"string"}}}
  ```
  **Output:** `LockRecord`.

  ---

  ## control_release_lock

  **Type:** Idempotent
  **Input schema:**
  ```json
  {"type":"object","required":["lock_id"],"properties":{"lock_id":{"type":"string"}}}
  ```
  **Output:** `null` (no body on success).

  ---

  ## control_mark_workflow_step_running

  **Type:** Idempotent
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","step_index"],"properties":{"task_id":{"type":"string"},"step_index":{"type":"integer","minimum":0},"trace_id":{"type":"string"},"span_id":{"type":"string"}}}
  ```
  **Output:** Updated `TaskRecord`.

  ---

  ## control_record_workflow_step_result

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","step_index","result_summary","confidence"],"properties":{"task_id":{"type":"string"},"step_index":{"type":"integer","minimum":0},"result_summary":{"type":"string"},"confidence":{"type":"number","minimum":0,"maximum":1}}}
  ```
  **Output:** Updated `TaskRecord`.

  ---

  ## control_mark_workflow_step_failed

  **Type:** Mutating
  **Input schema:**
  ```json
  {"type":"object","required":["task_id","step_index","error_summary"],"properties":{"task_id":{"type":"string"},"step_index":{"type":"integer","minimum":0},"error_summary":{"type":"string"}}}
  ```
  **Output:** Updated `TaskRecord`.

  ---

  ## control_list_ownership

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","properties":{}}
  ```
  **Output:** Array of ownership summary objects (task + run + lease + session + project).

  ---

  ## control_list_project_ownership

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","required":["project_id"],"properties":{"project_id":{"type":"string"}}}
  ```
  **Output:** Array of ownership summary objects for the project.

  ---

  ## control_list_session_ownership

  **Type:** Read-only
  **Input schema:**
  ```json
  {"type":"object","required":["session_id"],"properties":{"session_id":{"type":"string"}}}
  ```
  **Output:** Array of ownership summary objects for the session.
  ````

  **Complete all 23 tools** following this pattern. Read each tool's parameters from `server.py` to get exact field names and types.

- [ ] **Step 3: Commit**

  ```bash
  git add docs/mcp-tool-specs.md
  git commit -m "docs: add MCP control-plane tool JSON Schema specs (M3 contract)"
  ```

---

## Task 6: Update L0 Runbook

**Files:**
- Modify: `docs/agent-guides/l0-workflow-runbook.md`

- [ ] **Step 1: Read the current runbook**

  ```bash
  head -100 docs/agent-guides/l0-workflow-runbook.md
  ```

- [ ] **Step 2: Add escalation section**

  After the existing "Policy Gate Auto-Evaluation" section, add:

  ```markdown
  ## Escalation Path (ESCALATE_TO_HUMAN)

  When an agent determines that a workflow step needs human review before
  proceeding, it records `ESCALATE_TO_HUMAN` as the gate outcome:

  ```bash
  # MCP tool call
  control_record_workflow_gate_outcome(
      task_id="task_abc",
      step_index=0,
      decision="escalate_to_human",
      summary="Confidence 0.45 — below threshold for autonomous continuation",
  )
  ```

  This pauses the workflow (`status = ESCALATED`) without advancing to the next step.

  The developer reviews the situation:
  ```bash
  tta control workflow status <task_id>
  tta control gate list <task_id>
  ```

  To resume, approve the linked step gate:
  ```bash
  tta control gate approve <task_id> <gate_id> --note "Reviewed — looks good"
  ```

  The workflow returns to `RUNNING` and the agent can continue from where it paused.
  ```

- [ ] **Step 3: Update the known-gaps section**

  Remove or mark as resolved any gaps that M3 addresses. Add any new known limitations discovered during this work.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/agent-guides/l0-workflow-runbook.md
  git commit -m "docs: update L0 runbook with escalation path and M3 edge case handling"
  ```

---

## Task 7: M3 Final Verification

- [ ] **Step 1: Run the full test suite**

  ```bash
  uv run pytest tests/ -q
  ```
  Expected: All PASS.

- [ ] **Step 2: Run lint + type check**

  ```bash
  uv run ruff check ttadev/control_plane/ --fix
  uv run ruff format ttadev/control_plane/
  uvx pyright ttadev/control_plane/
  ```
  Expected: No errors.

- [ ] **Step 3: Verify M3 acceptance criteria**

  - [ ] `WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN` exists and is handled
  - [ ] `WorkflowTrackingStatus.ESCALATED` exists
  - [ ] Recording `ESCALATE_TO_HUMAN` pauses workflow (test passes)
  - [ ] Human gate approval resumes ESCALATED workflow (test passes)
  - [ ] `expire_abandoned_workflows()` exists and handles expired leases
  - [ ] `cleanup_orphaned_steps()` exists and handles terminated workflows
  - [ ] `docs/mcp-tool-specs.md` covers all 23 tools
  - [ ] L0 runbook updated with escalation section

- [ ] **Step 4: Smoke-test escalation end-to-end via CLI**

  ```bash
  # Start a workflow
  tta control workflow start \
    --name "m3-smoke-test" \
    --goal "verify escalation path" \
    --agents "agent-a,agent-b"

  # Get the task ID from the output, then:
  tta control workflow status <task_id>

  # Mark step 0 running and record low-confidence result
  # (Use MCP tools or service directly in a Python snippet)
  uv run python -c "
  from ttadev.control_plane.service import ControlPlaneService
  from ttadev.control_plane.models import WorkflowGateDecisionOutcome
  svc = ControlPlaneService()
  tasks = svc.list_tasks()
  task = next(t for t in tasks if t.workflow and t.workflow.workflow_name == 'm3-smoke-test')
  svc.mark_workflow_step_running(task.id, 0)
  svc.record_workflow_step_result(task.id, 0, 'done', 0.4)
  task = svc.record_workflow_gate_outcome(task.id, 0, WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN, 'low confidence')
  print('Workflow status:', task.workflow.status)
  "

  # Verify status shows ESCALATED
  tta control workflow status <task_id>
  ```

  Expected output includes `status: escalated`.

- [ ] **Step 5: Retain M3 completion in Hindsight**

  ```bash
  # In a Python snippet or via the MCP server:
  # mcp__hindsight__retain with bank_id="project-tta-dev-1fb5e15d"
  # content: "[type: decision] M3 Control Plane v1 complete. ESCALATE_TO_HUMAN added.
  #           Abandon/orphan edge cases handled. MCP specs committed."
  ```
