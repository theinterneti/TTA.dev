"""
Workflow Tracer

OpenTelemetry tracing for multi-persona workflows.

Features:
- Automatic span creation for workflows
- Per-stage tracing with persona context
- Error capture and status tracking
- Correlation with Prometheus metrics
- Integration with existing TTA observability

Usage:
    from .hypertool.instrumentation import WorkflowTracer

    async def my_workflow():
        async with WorkflowTracer("package_release") as tracer:
            # Stage 1
            result1 = await tracer.trace_stage(
                "version_bump",
                "backend-engineer",
                bump_version_func
            )

            # Stage 2
            result2 = await tracer.trace_stage(
                "quality_validation",
                "testing-specialist",
                run_tests_func
            )
"""

import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, ParamSpec, TypeVar

try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, Status, StatusCode

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

    # Graceful degradation
    class StatusCode:
        OK = "OK"
        ERROR = "ERROR"

    class Status:
        def __init__(self, status_code, description=None):
            pass

    class Span:
        def set_attribute(self, *args, **kwargs):
            pass

        def set_status(self, *args, **kwargs):
            pass

        def record_exception(self, *args, **kwargs):
            pass


from .persona_metrics import get_persona_metrics

P = ParamSpec("P")
T = TypeVar("T")


class WorkflowTracer:
    """
    OpenTelemetry tracer for multi-persona workflows.

    Creates hierarchical spans:
    - Workflow span (top-level)
      - Stage span 1 (with persona context)
      - Stage span 2 (with persona context)
      - ...
    """

    def __init__(self, workflow_name: str, metadata: dict[str, Any] | None = None):
        """
        Initialize workflow tracer.

        Args:
            workflow_name: Name of the workflow
            metadata: Additional metadata to attach to workflow span
        """
        self.workflow_name = workflow_name
        self.metadata = metadata or {}
        self._workflow_span: Span | None = None
        self._start_time: float | None = None

        # Get tracer
        if OPENTELEMETRY_AVAILABLE:
            self._tracer = trace.get_tracer(__name__)
        else:
            self._tracer = None

        # Get metrics collector
        self._metrics = get_persona_metrics()

    async def __aenter__(self):
        """Start workflow span."""
        self._start_time = time.time()

        if self._tracer:
            self._workflow_span = self._tracer.start_span(f"workflow.{self.workflow_name}")

            # Add metadata
            for key, value in self.metadata.items():
                self._workflow_span.set_attribute(f"workflow.{key}", str(value))

            self._workflow_span.set_attribute("workflow.name", self.workflow_name)
            self._workflow_span.set_attribute("workflow.start_time", self._start_time)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End workflow span with status."""
        if self._workflow_span:
            duration = time.time() - (self._start_time or time.time())
            self._workflow_span.set_attribute("workflow.duration_seconds", duration)

            if exc_type:
                # Workflow failed
                self._workflow_span.set_status(
                    Status(StatusCode.ERROR, f"Workflow failed: {exc_type.__name__}")
                )
                self._workflow_span.record_exception(exc_val)
            else:
                # Workflow succeeded
                self._workflow_span.set_status(Status(StatusCode.OK))

            self._workflow_span.end()

    async def trace_stage(
        self,
        stage_name: str,
        persona: str,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """
        Trace a workflow stage with automatic span creation.

        Args:
            stage_name: Name of the stage
            persona: Executing persona
            func: Function to execute (sync or async)
            *args: Positional arguments to func
            **kwargs: Keyword arguments to func

        Returns:
            Result of func execution

        Raises:
            Any exception raised by func
        """
        stage_span = None
        start_time = time.time()
        quality_passed = True
        result = None

        try:
            # Create stage span
            if self._tracer:
                stage_span = self._tracer.start_span(
                    f"stage.{stage_name}",
                    context=trace.set_span_in_context(self._workflow_span)
                    if self._workflow_span
                    else None,
                )
                stage_span.set_attribute("stage.name", stage_name)
                stage_span.set_attribute("stage.persona", persona)
                stage_span.set_attribute("workflow.name", self.workflow_name)

            # Execute function (handle both sync and async)
            import asyncio

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Mark success
            if stage_span:
                stage_span.set_status(Status(StatusCode.OK))

            return result

        except Exception as e:
            # Mark failure
            quality_passed = False

            if stage_span:
                stage_span.set_status(Status(StatusCode.ERROR, f"Stage failed: {type(e).__name__}"))
                stage_span.record_exception(e)

            raise

        finally:
            # Record metrics
            duration = time.time() - start_time
            self._metrics.record_workflow_stage(
                workflow=self.workflow_name,
                stage=stage_name,
                persona=persona,
                duration_seconds=duration,
                quality_gate_passed=quality_passed,
            )

            # End stage span
            if stage_span:
                stage_span.set_attribute("stage.duration_seconds", duration)
                stage_span.set_attribute("stage.quality_gate_passed", quality_passed)
                stage_span.end()

    @asynccontextmanager
    async def stage_context(
        self, stage_name: str, persona: str, metadata: dict[str, Any] | None = None
    ):
        """
        Context manager for manual stage tracing.

        Args:
            stage_name: Name of the stage
            persona: Executing persona
            metadata: Additional metadata for the stage

        Usage:
            async with tracer.stage_context("version_bump", "backend-engineer") as stage:
                # Your code here
                result = await do_work()
        """
        stage_span = None
        start_time = time.time()
        quality_passed = True

        try:
            # Create stage span
            if self._tracer:
                stage_span = self._tracer.start_span(
                    f"stage.{stage_name}",
                    context=trace.set_span_in_context(self._workflow_span)
                    if self._workflow_span
                    else None,
                )
                stage_span.set_attribute("stage.name", stage_name)
                stage_span.set_attribute("stage.persona", persona)
                stage_span.set_attribute("workflow.name", self.workflow_name)

                # Add metadata
                if metadata:
                    for key, value in metadata.items():
                        stage_span.set_attribute(f"stage.{key}", str(value))

            # Yield control to user code
            yield stage_span

            # Mark success if no exception
            if stage_span:
                stage_span.set_status(Status(StatusCode.OK))

        except Exception as e:
            # Mark failure
            quality_passed = False

            if stage_span:
                stage_span.set_status(Status(StatusCode.ERROR, f"Stage failed: {type(e).__name__}"))
                stage_span.record_exception(e)

            raise

        finally:
            # Record metrics
            duration = time.time() - start_time
            self._metrics.record_workflow_stage(
                workflow=self.workflow_name,
                stage=stage_name,
                persona=persona,
                duration_seconds=duration,
                quality_gate_passed=quality_passed,
            )

            # End stage span
            if stage_span:
                stage_span.set_attribute("stage.duration_seconds", duration)
                stage_span.set_attribute("stage.quality_gate_passed", quality_passed)
                stage_span.end()


@asynccontextmanager
async def trace_workflow(workflow_name: str, metadata: dict[str, Any] | None = None):
    """
    Quick helper to trace a workflow.

    Args:
        workflow_name: Name of the workflow
        metadata: Additional metadata

    Usage:
        async with trace_workflow("package_release") as tracer:
            await tracer.trace_stage("version_bump", "backend-engineer", func)
    """
    tracer = WorkflowTracer(workflow_name, metadata)
    async with tracer:
        yield tracer
