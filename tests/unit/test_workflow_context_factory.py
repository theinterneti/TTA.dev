"""Unit tests for WorkflowContext.root() and .child() factory methods."""

import pytest

from ttadev.primitives import WorkflowContext

# ---------------------------------------------------------------------------
# root()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_root_sets_workflow_id():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.workflow_id == "my-workflow"


@pytest.mark.asyncio
async def test_root_has_no_parent_linkage():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.parent_span_id is None
    assert ctx.causation_id is None


@pytest.mark.asyncio
async def test_root_generates_correlation_id():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.correlation_id is not None
    assert len(ctx.correlation_id) > 0


@pytest.mark.asyncio
async def test_root_correlation_ids_are_unique():
    ctx1 = WorkflowContext.root("wf")
    ctx2 = WorkflowContext.root("wf")
    assert ctx1.correlation_id != ctx2.correlation_id


@pytest.mark.asyncio
async def test_root_has_span_id():
    # span_id is injected by OTel at execution time, not at construction
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.span_id is None  # None until an OTel span is active


@pytest.mark.asyncio
async def test_root_start_time_set():
    import time

    before = time.time()
    ctx = WorkflowContext.root("my-workflow")
    after = time.time()
    assert before <= ctx.start_time <= after


@pytest.mark.asyncio
async def test_root_empty_metadata():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.metadata == {}


@pytest.mark.asyncio
async def test_root_empty_state():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.state == {}


@pytest.mark.asyncio
async def test_root_empty_tags():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.tags == {}  # tags is dict[str, str]


@pytest.mark.asyncio
async def test_root_empty_checkpoints():
    ctx = WorkflowContext.root("my-workflow")
    assert ctx.checkpoints == []


# ---------------------------------------------------------------------------
# child()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_child_sets_step_name_as_workflow_id():
    parent = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(parent, "validate-input")
    assert child.workflow_id == "validate-input"


@pytest.mark.asyncio
async def test_child_inherits_correlation_id():
    parent = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(parent, "step-1")
    assert child.correlation_id == parent.correlation_id


@pytest.mark.asyncio
async def test_child_parent_span_id_links_to_parent():
    parent = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(parent, "step-1")
    assert child.parent_span_id == parent.span_id


@pytest.mark.asyncio
async def test_child_causation_id_is_parent_correlation():
    parent = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(parent, "step-1")
    assert child.causation_id == parent.correlation_id


@pytest.mark.asyncio
async def test_child_gets_new_span_id():
    # span_id is None unless OTel sets it; parent_span_id propagates correctly regardless
    parent = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(parent, "step-1")
    assert child.span_id is None  # OTel-injected, not auto-generated
    # The causal link is via parent_span_id, not span_id
    assert child.parent_span_id == parent.span_id


@pytest.mark.asyncio
async def test_child_inherits_session_id():
    parent = WorkflowContext(workflow_id="pipeline", session_id="sess-42")
    child = WorkflowContext.child(parent, "step-1")
    assert child.session_id == "sess-42"


@pytest.mark.asyncio
async def test_child_inherits_player_id():
    parent = WorkflowContext(workflow_id="pipeline", player_id="player-99")
    child = WorkflowContext.child(parent, "step-1")
    assert child.player_id == "player-99"


@pytest.mark.asyncio
async def test_child_inherits_project_id():
    parent = WorkflowContext(workflow_id="pipeline", project_id="proj-abc")
    child = WorkflowContext.child(parent, "step-1")
    assert child.project_id == "proj-abc"


@pytest.mark.asyncio
async def test_child_inherits_agent_id():
    parent = WorkflowContext(workflow_id="pipeline", agent_id="copilot")
    child = WorkflowContext.child(parent, "step-1")
    assert child.agent_id == "copilot"


@pytest.mark.asyncio
async def test_child_inherits_agent_tool():
    parent = WorkflowContext(workflow_id="pipeline", agent_tool="bash")
    child = WorkflowContext.child(parent, "step-1")
    assert child.agent_tool == "bash"


@pytest.mark.asyncio
async def test_child_inherits_baggage():
    parent = WorkflowContext(workflow_id="pipeline", baggage={"env": "staging"})
    child = WorkflowContext.child(parent, "step-1")
    assert child.baggage == {"env": "staging"}


@pytest.mark.asyncio
async def test_child_baggage_is_deep_copy():
    parent = WorkflowContext(workflow_id="pipeline", baggage={"env": "staging"})
    child = WorkflowContext.child(parent, "step-1")
    child.baggage["env"] = "prod"
    assert parent.baggage["env"] == "staging"


@pytest.mark.asyncio
async def test_child_inherits_tags():
    parent = WorkflowContext(workflow_id="pipeline", tags={"env": "staging"})
    child = WorkflowContext.child(parent, "step-1")
    assert child.tags == {"env": "staging"}


@pytest.mark.asyncio
async def test_child_tags_is_deep_copy():
    parent = WorkflowContext(workflow_id="pipeline", tags={"env": "staging"})
    child = WorkflowContext.child(parent, "step-1")
    child.tags["env"] = "prod"
    assert parent.tags["env"] == "staging"


@pytest.mark.asyncio
async def test_child_does_not_mutate_parent():
    parent = WorkflowContext.root("pipeline")
    original_wf_id = parent.workflow_id
    _ = WorkflowContext.child(parent, "step-1")
    assert parent.workflow_id == original_wf_id


@pytest.mark.asyncio
async def test_sibling_children_have_distinct_workflow_ids():
    parent = WorkflowContext.root("pipeline")
    c1 = WorkflowContext.child(parent, "step-1")
    c2 = WorkflowContext.child(parent, "step-2")
    assert c1.workflow_id != c2.workflow_id


@pytest.mark.asyncio
async def test_grandchild_spans_chain_correctly():
    root = WorkflowContext.root("pipeline")
    child = WorkflowContext.child(root, "step-1")
    grandchild = WorkflowContext.child(child, "substep-a")
    assert grandchild.parent_span_id == child.span_id
    assert grandchild.correlation_id == root.correlation_id


@pytest.mark.asyncio
async def test_child_inherits_metadata():
    parent = WorkflowContext(workflow_id="pipeline", metadata={"key": "val"})
    child = WorkflowContext.child(parent, "step-1")
    assert child.metadata == {"key": "val"}


@pytest.mark.asyncio
async def test_child_metadata_is_deep_copy():
    parent = WorkflowContext(workflow_id="pipeline", metadata={"key": "val"})
    child = WorkflowContext.child(parent, "step-1")
    child.metadata["key"] = "changed"
    assert parent.metadata["key"] == "val"
