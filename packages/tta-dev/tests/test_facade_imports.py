"""Tests for tta_dev façade package imports.

These tests verify that:
1. Core primitives are always importable from tta_dev
2. Optional extras work correctly when installed
3. Missing extras fail gracefully (return None, not ImportError)
"""

import pytest


class TestCoreImports:
    """Test that core primitives are always available."""

    def test_version_available(self) -> None:
        """Version string should always be importable."""
        from tta_dev import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_workflow_context_importable(self) -> None:
        """WorkflowContext should always be available."""
        from tta_dev import WorkflowContext

        ctx = WorkflowContext(workflow_id="test")
        assert ctx.workflow_id == "test"

    def test_workflow_primitive_importable(self) -> None:
        """WorkflowPrimitive base class should be available."""
        from tta_dev import WorkflowPrimitive

        assert WorkflowPrimitive is not None

    def test_sequential_primitive_importable(self) -> None:
        """SequentialPrimitive should be available."""
        from tta_dev import SequentialPrimitive

        assert SequentialPrimitive is not None

    def test_parallel_primitive_importable(self) -> None:
        """ParallelPrimitive should be available."""
        from tta_dev import ParallelPrimitive

        assert ParallelPrimitive is not None

    def test_conditional_primitive_importable(self) -> None:
        """ConditionalPrimitive should be available."""
        from tta_dev import ConditionalPrimitive

        assert ConditionalPrimitive is not None

    def test_retry_primitive_importable(self) -> None:
        """RetryPrimitive and RetryStrategy should be available."""
        from tta_dev import RetryPrimitive, RetryStrategy

        assert RetryPrimitive is not None
        assert RetryStrategy is not None

    def test_timeout_primitive_importable(self) -> None:
        """TimeoutPrimitive should be available."""
        from tta_dev import TimeoutPrimitive

        assert TimeoutPrimitive is not None

    def test_cache_primitive_importable(self) -> None:
        """CachePrimitive should be available."""
        from tta_dev import CachePrimitive

        assert CachePrimitive is not None

    def test_compensation_primitive_importable(self) -> None:
        """CompensationPrimitive and CompensationStrategy should be available."""
        from tta_dev import CompensationPrimitive, CompensationStrategy

        assert CompensationPrimitive is not None
        assert CompensationStrategy is not None

    def test_mock_primitive_importable(self) -> None:
        """MockPrimitive testing utility should be available."""
        from tta_dev import MockPrimitive

        assert MockPrimitive is not None


class TestAvailabilityChecks:
    """Test availability check functions."""

    def test_observability_available_function_exists(self) -> None:
        """observability_available() should be callable."""
        from tta_dev import observability_available

        result = observability_available()
        assert isinstance(result, bool)

    def test_context_available_function_exists(self) -> None:
        """context_available() should be callable."""
        from tta_dev import context_available

        result = context_available()
        assert isinstance(result, bool)


class TestObservabilityExtras:
    """Test observability optional extras (tta-dev[observability])."""

    def test_observability_imports_when_available(self) -> None:
        """If observability is installed, symbols should be importable."""
        from tta_dev import observability_available

        if observability_available():
            from tta_dev import (
                ObservableCachePrimitive,
                ObservableRouterPrimitive,
                ObservableTimeoutPrimitive,
                initialize_observability,
                is_observability_enabled,
            )

            assert initialize_observability is not None
            assert is_observability_enabled is not None
            assert ObservableRouterPrimitive is not None
            assert ObservableCachePrimitive is not None
            assert ObservableTimeoutPrimitive is not None

    def test_observability_graceful_fallback(self) -> None:
        """If observability is NOT installed, symbols should be None (not raise)."""
        from tta_dev import observability_available

        if not observability_available():
            # These should be None, not raise ImportError
            from tta_dev import (
                ObservableCachePrimitive,
                ObservableRouterPrimitive,
                ObservableTimeoutPrimitive,
                initialize_observability,
                is_observability_enabled,
            )

            assert initialize_observability is None
            assert is_observability_enabled is None
            assert ObservableRouterPrimitive is None
            assert ObservableCachePrimitive is None
            assert ObservableTimeoutPrimitive is None


class TestContextExtras:
    """Test agent context optional extras (tta-dev[context])."""

    def test_context_imports_when_available(self) -> None:
        """If context is installed, agent primitives should be importable."""
        from tta_dev import context_available

        if context_available():
            from tta_dev import (
                AgentCoordinationPrimitive,
                AgentHandoffPrimitive,
                AgentMemoryPrimitive,
            )

            assert AgentHandoffPrimitive is not None
            assert AgentMemoryPrimitive is not None
            assert AgentCoordinationPrimitive is not None

    def test_context_graceful_fallback(self) -> None:
        """If context is NOT installed, symbols should be None (not raise)."""
        from tta_dev import context_available

        if not context_available():
            from tta_dev import (
                AgentCoordinationPrimitive,
                AgentHandoffPrimitive,
                AgentMemoryPrimitive,
            )

            assert AgentHandoffPrimitive is None
            assert AgentMemoryPrimitive is None
            assert AgentCoordinationPrimitive is None

