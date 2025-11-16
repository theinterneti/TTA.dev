"""
PersonaMetricsCollector - Prometheus metrics for Hypertool personas

Tracks:
- Persona switches (from → to transitions)
- Persona duration (time spent in each persona)
- Token usage per persona
- Token budget remaining
- Workflow stage duration
- Quality gate results

Singleton pattern ensures metrics are not duplicated in Prometheus registry.
"""

import threading
import time
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Gauge, Histogram, Info

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Graceful degradation - create no-op classes
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def observe(self, *args, **kwargs):
            pass

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def set(self, *args, **kwargs):
            pass

    class Info:
        def __init__(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass


class PersonaMetricsCollector:
    """
    Collects Prometheus metrics for Hypertool persona operations.

    Metrics:
    - hypertool_persona_switches_total: Total persona switches
    - hypertool_persona_duration_seconds: Time spent in persona
    - hypertool_persona_tokens_used_total: Tokens consumed by persona
    - hypertool_persona_token_budget_remaining: Remaining token budget
    - hypertool_workflow_stage_duration_seconds: Workflow stage execution time
    - hypertool_workflow_quality_gate_total: Quality gate pass/fail counts
    """

    def __init__(self, registry=None):
        """Initialize Prometheus metrics.

        Args:
            registry: Optional Prometheus registry. If None, uses default REGISTRY.
        """
        if PROMETHEUS_AVAILABLE:
            from prometheus_client import REGISTRY

            if registry is None:
                registry = REGISTRY

        # Persona switches
        self.persona_switches = Counter(
            "hypertool_persona_switches_total",
            "Total number of persona switches",
            ["from_persona", "to_persona", "chatmode"],
            registry=registry,
        )

        # Persona session duration
        self.persona_duration = Histogram(
            "hypertool_persona_duration_seconds",
            "Time spent in a persona session",
            ["persona", "chatmode"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=registry,
        )

        # Token usage
        self.persona_token_usage = Counter(
            "hypertool_persona_tokens_used_total",
            "Total tokens used by persona",
            ["persona", "chatmode", "model"],
            registry=registry,
        )

        # Token budget remaining
        self.persona_token_budget = Gauge(
            "hypertool_persona_token_budget_remaining",
            "Remaining token budget for persona",
            ["persona"],
            registry=registry,
        )

        # Workflow stage duration
        self.workflow_stage_duration = Histogram(
            "hypertool_workflow_stage_duration_seconds",
            "Duration of workflow stages",
            ["workflow", "stage", "persona"],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
            registry=registry,
        )

        # Quality gate results
        self.workflow_quality_gate_result = Counter(
            "hypertool_workflow_quality_gate_total",
            "Quality gate pass/fail results",
            ["workflow", "stage", "result"],
            registry=registry,
        )

        # Persona info (static metadata)
        self.persona_info = Info(
            "hypertool_persona_info", "Static persona metadata", registry=registry
        )

        # Track active sessions
        self._active_sessions: dict[str, float] = {}  # persona -> start_time

        # Default token budgets (from design)
        self._token_budgets = {
            "backend-engineer": 2000,
            "frontend-engineer": 1800,
            "devops-engineer": 1800,
            "testing-specialist": 1500,
            "observability-expert": 2000,
            "data-scientist": 1700,
        }

        # Initialize budgets
        for persona, budget in self._token_budgets.items():
            self.persona_token_budget.labels(persona=persona).set(budget)

    def switch_persona(
        self, from_persona: str | None, to_persona: str, chatmode: str
    ) -> None:
        """
        Record a persona switch.

        Args:
            from_persona: Previous persona (None if first switch)
            to_persona: New persona
            chatmode: Active chatmode
        """
        # End previous session if exists
        if from_persona and from_persona in self._active_sessions:
            start_time = self._active_sessions.pop(from_persona)
            duration = time.time() - start_time
            self.persona_duration.labels(
                persona=from_persona, chatmode=chatmode
            ).observe(duration)

        # Record switch
        self.persona_switches.labels(
            from_persona=from_persona or "none",
            to_persona=to_persona,
            chatmode=chatmode,
        ).inc()

        # Start new session
        self._active_sessions[to_persona] = time.time()

    def record_token_usage(
        self, persona: str, chatmode: str, model: str, tokens: int
    ) -> None:
        """
        Record token usage for a persona.

        Args:
            persona: Active persona
            chatmode: Active chatmode
            model: LLM model used
            tokens: Number of tokens consumed
        """
        # Increment usage counter
        self.persona_token_usage.labels(
            persona=persona, chatmode=chatmode, model=model
        ).inc(tokens)

        # Update remaining budget (if persona has a budget)
        if persona in self._token_budgets:
            current_budget = self.persona_token_budget.labels(
                persona=persona
            )._value._value
            new_budget = max(0, current_budget - tokens)
            self.persona_token_budget.labels(persona=persona).set(new_budget)

    def record_workflow_stage(
        self,
        workflow: str,
        stage: str,
        persona: str,
        duration_seconds: float,
        quality_gate_passed: bool,
    ) -> None:
        """
        Record workflow stage execution.

        Args:
            workflow: Workflow name
            stage: Stage name
            persona: Executing persona
            duration_seconds: Stage duration
            quality_gate_passed: Whether quality gate passed
        """
        # Record duration
        self.workflow_stage_duration.labels(
            workflow=workflow, stage=stage, persona=persona
        ).observe(duration_seconds)

        # Record quality gate result
        result = "passed" if quality_gate_passed else "failed"
        self.workflow_quality_gate_result.labels(
            workflow=workflow, stage=stage, result=result
        ).inc()

    @contextmanager
    def track_stage(
        self, workflow: str, stage: str, persona: str, auto_quality_gate: bool = True
    ):
        """
        Context manager to automatically track workflow stage.

        Args:
            workflow: Workflow name
            stage: Stage name
            persona: Executing persona
            auto_quality_gate: Assume passed if no exception

        Usage:
            with collector.track_stage("package_release", "version_bump", "backend-engineer"):
                # Execute stage
                result = bump_version()
        """
        start_time = time.time()
        quality_passed = auto_quality_gate

        try:
            yield
        except Exception:
            quality_passed = False
            raise
        finally:
            duration = time.time() - start_time
            self.record_workflow_stage(
                workflow=workflow,
                stage=stage,
                persona=persona,
                duration_seconds=duration,
                quality_gate_passed=quality_passed,
            )

    def get_remaining_budget(self, persona: str) -> int:
        """
        Get remaining token budget for a persona.

        Args:
            persona: Persona name

        Returns:
            Remaining token budget (0 if persona not found)
        """
        if not PROMETHEUS_AVAILABLE:
            return self._token_budgets.get(persona, 0)

        try:
            return int(self.persona_token_budget.labels(persona=persona)._value._value)
        except (AttributeError, ValueError):
            return self._token_budgets.get(persona, 0)

    def reset_budget(self, persona: str) -> None:
        """
        Reset token budget to default for a persona.

        Args:
            persona: Persona name
        """
        if persona in self._token_budgets:
            self.persona_token_budget.labels(persona=persona).set(
                self._token_budgets[persona]
            )


# Global singleton instance
_collector: PersonaMetricsCollector | None = None
_collector_lock = threading.Lock()


def get_persona_metrics() -> PersonaMetricsCollector:
    """
    Get global PersonaMetricsCollector instance with thread safety.

    Returns:
        PersonaMetricsCollector: Singleton instance
    """
    global _collector
    if _collector is None:
        with _collector_lock:
            if _collector is None:  # Double-check pattern
                _collector = PersonaMetricsCollector()
    return _collector


def reset_persona_metrics() -> None:
    """
    Reset the singleton instance (useful for testing).

    WARNING: This will lose all current metric data!
    Also clears Prometheus registry to avoid duplicated metrics.
    """
    global _collector

    with _collector_lock:
        # Clear Prometheus registry
        if PROMETHEUS_AVAILABLE:
            try:
                from prometheus_client import REGISTRY

                collectors = list(REGISTRY._collector_to_names.keys())
                for collector in collectors:
                    try:
                        if hasattr(collector, "_name") and "hypertool" in str(
                            collector._name
                        ):
                            REGISTRY.unregister(collector)
                    except Exception:
                        pass
            except Exception:
                pass

        _collector = None
