"""Tests for MemoryWorkflowPrimitive."""

from pathlib import Path

import pytest

from tta_dev_primitives import (
    MemoryWorkflowPrimitive,
    WorkflowContext,
    WorkflowMode,
)


@pytest.fixture
def paf_core_path() -> Path:
    """Get path to PAFCORE.md (try repo root)."""
    # Try repo root (when running from package dir)
    repo_path = Path.cwd().parent.parent / ".universal-instructions" / "paf" / "PAFCORE.md"
    if repo_path.exists():
        return repo_path

    # Create minimal test PAFCORE.md in temp location
    test_path = Path.cwd() / ".test_pafs" / "paf" / "PAFCORE.md"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(
        """# PAFCORE.md - Permanent Architectural Facts

**QUAL-001**: Minimum test coverage is 80%
**QUAL-002**: Maximum file size is 500 lines
"""
    )
    return test_path


@pytest.fixture
def workflow_context() -> WorkflowContext:
    """Create a test workflow context."""
    return WorkflowContext(
        workflow_id="test-workflow",
        session_id="test-session",
        metadata={"test": True},
    )


class TestMemoryWorkflowPrimitiveInit:
    """Test MemoryWorkflowPrimitive initialization."""

    def test_init_without_redis(self, paf_core_path: Path) -> None:
        """Test initialization without Redis."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")
        assert memory.user_id == "test-user"
        assert memory.redis_client is None
        assert not memory.redis_available
        assert memory.paf_primitive is not None
        assert memory.session_groups is not None

    def test_init_with_redis_url_but_not_available(self, paf_core_path: Path) -> None:
        """Test initialization with Redis URL when agent_memory_client not installed."""
        memory = MemoryWorkflowPrimitive(
            redis_url="http://localhost:8000",
            user_id="test-user",
        )
        # Should work even if redis not installed
        assert memory.user_id == "test-user"


class TestLayer1SessionContext:
    """Test Layer 1: Session Context operations."""

    @pytest.mark.asyncio
    async def test_add_session_message_no_redis(self):
        """Test adding session message when Redis not available."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        # Should not raise error even without Redis
        await memory.add_session_message(
            session_id="test-session",
            role="user",
            content="Test message",
        )

    @pytest.mark.asyncio
    async def test_get_session_context_no_redis(self):
        """Test getting session context when Redis not available."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        result = await memory.get_session_context("test-session")
        assert result == []


class TestLayer2CacheMemory:
    """Test Layer 2: Cache Memory operations."""

    @pytest.mark.asyncio
    async def test_get_cache_memory_no_redis(self):
        """Test getting cache memory when Redis not available."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        result = await memory.get_cache_memory("test-session", hours=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cache_memory_custom_window(self):
        """Test cache memory with custom time window."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        # Should handle different time windows
        result_1h = await memory.get_cache_memory("test-session", hours=1)
        result_24h = await memory.get_cache_memory("test-session", hours=24)

        assert result_1h == []
        assert result_24h == []


class TestLayer3DeepMemory:
    """Test Layer 3: Deep Memory operations."""

    @pytest.mark.asyncio
    async def test_create_deep_memory_no_redis(self):
        """Test creating deep memory when Redis not available."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        result = await memory.create_deep_memory(
            text="Test pattern",
            memory_type="pattern",
            tags=["test"],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_search_deep_memory_no_redis(self):
        """Test searching deep memory when Redis not available."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        result = await memory.search_deep_memory(query="test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_deep_memory_with_filters(self):
        """Test searching with type and tag filters."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        result = await memory.search_deep_memory(
            query="authentication",
            memory_type="pattern",
            tags=["security"],
            k=10,
        )
        assert result == []


class TestLayer4PAFStore:
    """Test Layer 4: PAF Store operations."""

    def test_get_active_pafs(self):
        """Test getting active PAFs."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        pafs = memory.get_active_pafs()
        assert isinstance(pafs, list)
        # Should have PAFs from PAFCORE.md
        assert len(pafs) > 0

    def test_validate_paf(self):
        """Test validating against PAF."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        # Test generic validation (just checks PAF exists and is active)
        result = memory.validate_paf("QUAL-001", 75.0)
        assert result.is_valid is True

        # Test with non-existent PAF
        result_not_found = memory.validate_paf("FAKE-999", 50.0)
        assert result_not_found.is_valid is False
        assert "not found" in result_not_found.reason


class TestStageAwareLoading:
    """Test workflow stage-aware context loading."""

    @pytest.mark.asyncio
    async def test_load_understand_stage_rapid(self, workflow_context):
        """Test loading Understand stage in Rapid mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="understand",
            workflow_mode=WorkflowMode.RAPID,
        )

        assert context["stage"] == "understand"
        assert context["workflow_mode"] == "rapid"
        assert "session_context" in context
        # Rapid mode: minimal context
        assert "deep_memory" not in context
        assert "active_pafs" not in context

    @pytest.mark.asyncio
    async def test_load_understand_stage_standard(self, workflow_context):
        """Test loading Understand stage in Standard mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="understand",
            workflow_mode=WorkflowMode.STANDARD,
        )

        assert context["stage"] == "understand"
        assert context["workflow_mode"] == "standard"
        assert "session_context" in context
        assert "cache_memory" in context
        assert "deep_memory" in context
        assert "active_pafs" in context

    @pytest.mark.asyncio
    async def test_load_understand_stage_augster(self, workflow_context):
        """Test loading Understand stage in Augster-Rigorous mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="understand",
            workflow_mode=WorkflowMode.AUGSTER_RIGOROUS,
        )

        assert context["stage"] == "understand"
        assert context["workflow_mode"] == "augster-rigorous"
        assert "session_context" in context
        assert "cache_memory" in context
        assert "deep_memory" in context
        assert "active_pafs" in context
        assert "session_groups" in context  # Only in Augster

    @pytest.mark.asyncio
    async def test_load_decompose_stage_rapid(self, workflow_context):
        """Test Decompose stage skipped in Rapid mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="decompose",
            workflow_mode=WorkflowMode.RAPID,
        )

        # Decompose skipped in rapid mode
        assert context["stage"] == "decompose"
        assert "session_context" not in context

    @pytest.mark.asyncio
    async def test_load_decompose_stage_standard(self, workflow_context):
        """Test Decompose stage in Standard mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="decompose",
            workflow_mode=WorkflowMode.STANDARD,
        )

        assert context["stage"] == "decompose"
        assert "session_context" in context
        assert "active_pafs" in context
        assert "deep_memory" not in context  # Not in standard decompose

    @pytest.mark.asyncio
    async def test_load_plan_stage_augster(self, workflow_context):
        """Test Plan stage in Augster mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="plan",
            workflow_mode=WorkflowMode.AUGSTER_RIGOROUS,
        )

        assert context["stage"] == "plan"
        assert "session_context" in context
        assert "cache_memory" in context
        assert "active_pafs" in context
        assert "deep_memory" in context  # Augster includes deep memory

    @pytest.mark.asyncio
    async def test_load_implement_stage(self, workflow_context):
        """Test Implement stage (all modes similar)."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="implement",
            workflow_mode=WorkflowMode.STANDARD,
        )

        assert context["stage"] == "implement"
        assert "session_context" in context
        assert "cache_memory" in context
        assert "deep_memory" not in context  # Not needed during implementation

    @pytest.mark.asyncio
    async def test_load_validate_stage_rapid_skipped(self, workflow_context):
        """Test Validate stage skipped in Rapid mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="validate",
            workflow_mode=WorkflowMode.RAPID,
        )

        # Validation skipped in rapid mode
        assert context["stage"] == "validate"
        assert "session_context" not in context

    @pytest.mark.asyncio
    async def test_load_reflect_stage_augster_only(self, workflow_context):
        """Test Reflect stage only in Augster mode."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        # Standard mode - reflect skipped
        context_std = await memory.load_workflow_context(
            context=workflow_context,
            stage="reflect",
            workflow_mode=WorkflowMode.STANDARD,
        )
        assert "session_context" not in context_std

        # Augster mode - reflect included
        context_aug = await memory.load_workflow_context(
            context=workflow_context,
            stage="reflect",
            workflow_mode=WorkflowMode.AUGSTER_RIGOROUS,
        )
        assert "session_context" in context_aug
        assert "deep_memory_available" in context_aug

    @pytest.mark.asyncio
    async def test_load_context_with_string_mode(self, workflow_context):
        """Test loading with mode as string."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        context = await memory.load_workflow_context(
            context=workflow_context,
            stage="understand",
            workflow_mode="standard",  # String instead of enum
        )

        assert context["workflow_mode"] == "standard"

    @pytest.mark.asyncio
    async def test_load_context_without_session_id(self):
        """Test loading context when session_id is None."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")
        context = WorkflowContext(workflow_id="test", session_id=None)

        result = await memory.load_workflow_context(
            context=context,
            stage="understand",
            workflow_mode=WorkflowMode.STANDARD,
        )

        # Should return minimal context without errors
        assert result["stage"] == "understand"
        assert "session_context" not in result


class TestSummary:
    """Test summary method."""

    def test_summary(self):
        """Test getting system summary."""
        memory = MemoryWorkflowPrimitive(user_id="test-user")

        summary = memory.summary()

        assert "redis_available" in summary
        assert summary["redis_available"] is False
        assert summary["user_id"] == "test-user"
        assert "paf_store" in summary
        assert "session_groups" in summary
