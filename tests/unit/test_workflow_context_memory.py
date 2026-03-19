"""Tests for WorkflowContext.memory field — Task T1."""

from ttadev.primitives.core.base import WorkflowContext


class TestWorkflowContextMemoryField:
    def test_default_memory_is_none(self):
        ctx = WorkflowContext()
        assert ctx.memory is None

    def test_child_context_inherits_none_memory(self):
        ctx = WorkflowContext()
        child = ctx.create_child_context()
        assert child.memory is None

    def test_memory_field_accepts_any_value(self):
        """WorkflowMemory not yet importable here — use a plain object as stand-in."""

        class _FakeMemory:
            pass

        m = _FakeMemory()
        ctx = WorkflowContext()
        ctx.memory = m
        assert ctx.memory is m
