"""Unit tests for WorkflowContext.from_project() — Task 8."""


def _make_project(tmp_path, name="test-proj"):
    from ttadev.observability.project_session import ProjectSessionManager

    m = ProjectSessionManager(data_dir=tmp_path)
    return m.create(name)


class TestFromProject:
    def test_returns_workflow_context(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="step-1")
        assert isinstance(ctx, WorkflowContext)

    def test_workflow_id_set(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="my-step")
        assert ctx.workflow_id == "my-step"

    def test_project_id_populated(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="step")
        assert ctx.project_id == proj.id

    def test_agent_id_auto_populated(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="step")
        assert ctx.agent_id is not None

    def test_agent_tool_auto_populated(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="step")
        assert ctx.agent_tool is not None

    def test_child_inherits_project_id(self, tmp_path):
        from ttadev.primitives.core.base import WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="parent")
        child = ctx.create_child_context()
        assert child.project_id == proj.id

    def test_usable_with_primitive(self, tmp_path):
        """from_project ctx can be passed to a primitive without error."""
        import asyncio

        from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext

        proj = _make_project(tmp_path)
        ctx = WorkflowContext.from_project(proj, workflow_id="prim-test")
        prim = LambdaPrimitive(lambda x, _c: x * 2)
        result = asyncio.run(prim.execute(21, ctx))
        assert result == 42
