"""Unit tests for WorkflowContext auto-identity — Task 3."""

import sys
from unittest.mock import patch


def _reload_base():
    for mod in list(sys.modules):
        if "agent_identity" in mod or "primitives.core.base" in mod:
            del sys.modules[mod]
    from ttadev.primitives.core import base

    return base


class TestWorkflowContextAutoIdentity:
    def test_agent_id_auto_populated(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test")
        assert ctx.agent_id is not None
        assert len(ctx.agent_id) > 0

    def test_agent_id_is_consistent_within_process(self):
        base = _reload_base()
        # Two contexts created in the same process share the same agent_id
        ctx1 = base.WorkflowContext(workflow_id="a")
        ctx2 = base.WorkflowContext(workflow_id="b")
        assert ctx1.agent_id == ctx2.agent_id

    def test_agent_id_explicit_override(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test", agent_id="my-override")
        assert ctx.agent_id == "my-override"

    def test_agent_tool_auto_populated(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test")
        assert ctx.agent_tool is not None

    def test_agent_tool_explicit_override(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test", agent_tool="copilot")
        assert ctx.agent_tool == "copilot"

    def test_project_id_defaults_none(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test")
        assert ctx.project_id is None

    def test_project_id_explicit(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="test", project_id="pr-223")
        assert ctx.project_id == "pr-223"

    def test_backward_compat_no_required_args_broken(self):
        """Existing code using only workflow_id still works."""
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="legacy-workflow")
        assert ctx.workflow_id == "legacy-workflow"
        assert ctx.correlation_id  # still auto-generated

    def test_child_context_inherits_agent_id(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="parent", agent_id="agent-abc")
        child = ctx.create_child_context()
        assert child.agent_id == "agent-abc"

    def test_child_context_inherits_project_id(self):
        base = _reload_base()
        ctx = base.WorkflowContext(workflow_id="parent", project_id="proj-x")
        child = ctx.create_child_context()
        assert child.project_id == "proj-x"


class TestWorkflowContextIsolatedFromObservability:
    def test_works_when_agent_identity_unavailable(self):
        """WorkflowContext must construct even without ttadev.observability."""
        # Temporarily hide the agent_identity module
        with patch.dict(sys.modules, {"ttadev.observability.agent_identity": None}):
            for mod in list(sys.modules):
                if "primitives.core.base" in mod:
                    del sys.modules[mod]
            from ttadev.primitives.core import base

            # Should not raise — agent_id may be None but construction succeeds
            ctx = base.WorkflowContext(workflow_id="isolated")
            assert ctx.workflow_id == "isolated"
