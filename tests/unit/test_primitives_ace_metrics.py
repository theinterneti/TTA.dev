"""Unit tests for ACE metrics module (MetricsTracker, LearningMetrics, AggregatedMetrics).

Tests cover:
- LearningMetrics dataclass construction
- AggregatedMetrics dataclass construction and defaults
- MetricsTracker: record_session, get_aggregated_metrics, export_for_visualization
- Learning curve computation
- Task type breakdown
- Improvement rate calculation
- File persistence (mocked)
- Empty session edge cases
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from ttadev.primitives.ace.metrics import (
    AggregatedMetrics,
    LearningMetrics,
    MetricsTracker,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session(
    task_type: str = "test_generation",
    success: bool = True,
    strategies_used: int = 2,
    strategies_learned: int = 1,
    iterations: int = 2,
    exec_time: float = 1.0,
    playbook_size: int = 5,
    success_rate: float = 0.8,
    improvement_score: float = 0.1,
    error_type: str | None = None,
    ts: float | None = None,
) -> LearningMetrics:
    return LearningMetrics(
        timestamp=ts if ts is not None else time.time(),
        task_type=task_type,
        execution_success=success,
        strategies_used=strategies_used,
        strategies_learned=strategies_learned,
        iteration_count=iterations,
        execution_time=exec_time,
        playbook_size=playbook_size,
        success_rate=success_rate,
        improvement_score=improvement_score,
        error_type=error_type,
    )


def _make_tracker(with_file: bool = False) -> MetricsTracker:
    """Create a MetricsTracker that will not attempt real file I/O on init."""
    if with_file:
        # file doesn't exist → won't try to load
        return MetricsTracker(metrics_file=Path("/tmp/fake_metrics_test.json"))
    # default path; ensure it doesn't exist so load is not triggered
    with patch.object(Path, "exists", return_value=False):
        return MetricsTracker()


# ---------------------------------------------------------------------------
# LearningMetrics dataclass
# ---------------------------------------------------------------------------


class TestLearningMetrics:
    def test_required_fields(self) -> None:
        m = _session()
        assert isinstance(m.timestamp, float)
        assert m.task_type == "test_generation"
        assert m.execution_success is True
        assert m.strategies_used == 2
        assert m.strategies_learned == 1
        assert m.iteration_count == 2
        assert m.execution_time == 1.0
        assert m.playbook_size == 5
        assert m.success_rate == 0.8
        assert m.improvement_score == 0.1

    def test_optional_error_type_defaults_to_none(self) -> None:
        m = _session()
        assert m.error_type is None

    def test_optional_error_type_set(self) -> None:
        m = _session(error_type="TimeoutError")
        assert m.error_type == "TimeoutError"

    def test_metadata_defaults_to_empty_dict(self) -> None:
        m = _session()
        assert m.metadata == {}

    def test_metadata_custom(self) -> None:
        m = LearningMetrics(
            timestamp=1.0,
            task_type="t",
            execution_success=True,
            strategies_used=0,
            strategies_learned=0,
            iteration_count=1,
            execution_time=0.1,
            playbook_size=0,
            success_rate=1.0,
            improvement_score=0.0,
            metadata={"source": "unit-test"},
        )
        assert m.metadata == {"source": "unit-test"}

    def test_failed_session(self) -> None:
        m = _session(success=False, error_type="ValueError")
        assert m.execution_success is False
        assert m.error_type == "ValueError"


# ---------------------------------------------------------------------------
# AggregatedMetrics dataclass defaults
# ---------------------------------------------------------------------------


class TestAggregatedMetrics:
    def test_defaults(self) -> None:
        agg = AggregatedMetrics()
        assert agg.total_executions == 0
        assert agg.successful_executions == 0
        assert agg.total_strategies_learned == 0
        assert agg.total_execution_time == 0.0
        assert agg.average_iterations == 0.0
        assert agg.success_rate == 0.0
        assert agg.improvement_rate == 0.0
        assert agg.task_type_breakdown == {}
        assert agg.learning_curve == []

    def test_can_be_constructed_with_values(self) -> None:
        agg = AggregatedMetrics(
            total_executions=5,
            successful_executions=4,
            success_rate=0.8,
        )
        assert agg.total_executions == 5
        assert agg.success_rate == 0.8


# ---------------------------------------------------------------------------
# MetricsTracker — construction
# ---------------------------------------------------------------------------


class TestMetricsTrackerInit:
    def test_default_path_assigned(self) -> None:
        with patch.object(Path, "exists", return_value=False):
            tracker = MetricsTracker()
        assert tracker.metrics_file.name == "ace_learning_metrics.json"

    def test_custom_path_assigned(self) -> None:
        custom = Path("/tmp/custom_metrics.json")
        with patch.object(Path, "exists", return_value=False):
            tracker = MetricsTracker(metrics_file=custom)
        assert tracker.metrics_file == custom

    def test_sessions_empty_on_init(self) -> None:
        with patch.object(Path, "exists", return_value=False):
            tracker = MetricsTracker()
        assert tracker.sessions == []

    def test_loads_from_file_if_exists(self) -> None:
        session_data = [
            {
                "timestamp": 1000.0,
                "task_type": "loaded",
                "execution_success": True,
                "strategies_used": 1,
                "strategies_learned": 0,
                "iteration_count": 1,
                "execution_time": 0.5,
                "playbook_size": 3,
                "success_rate": 1.0,
                "improvement_score": 0.0,
                "error_type": None,
                "metadata": {},
            }
        ]
        mo = mock_open(read_data=json.dumps(session_data))
        with patch.object(Path, "exists", return_value=True), patch("builtins.open", mo):
            tracker = MetricsTracker()
        assert len(tracker.sessions) == 1
        assert tracker.sessions[0].task_type == "loaded"


# ---------------------------------------------------------------------------
# MetricsTracker — record_session
# ---------------------------------------------------------------------------


class TestMetricsTrackerRecordSession:
    def test_session_appended(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session())
        assert len(tracker.sessions) == 1

    def test_multiple_sessions_appended(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            for _ in range(5):
                tracker.record_session(_session())
        assert len(tracker.sessions) == 5

    def test_saves_after_record(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m) as mock_file:
            tracker.record_session(_session())
        mock_file.assert_called_once()  # _save_metrics was called


# ---------------------------------------------------------------------------
# MetricsTracker — get_aggregated_metrics: empty
# ---------------------------------------------------------------------------


class TestAggregatedMetricsEmpty:
    def test_returns_defaults_when_no_sessions(self) -> None:
        tracker = _make_tracker()
        agg = tracker.get_aggregated_metrics()
        assert agg.total_executions == 0
        assert agg.success_rate == 0.0
        assert agg.learning_curve == []


# ---------------------------------------------------------------------------
# MetricsTracker — get_aggregated_metrics: single session
# ---------------------------------------------------------------------------


class TestAggregatedMetricsSingleSession:
    def setup_method(self) -> None:
        self.tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            self.tracker.record_session(
                _session(success=True, strategies_learned=3, iterations=4, exec_time=2.0)
            )

    def test_total_executions(self) -> None:
        assert self.tracker.get_aggregated_metrics().total_executions == 1

    def test_success_rate_all_success(self) -> None:
        assert self.tracker.get_aggregated_metrics().success_rate == 1.0

    def test_total_strategies_learned(self) -> None:
        assert self.tracker.get_aggregated_metrics().total_strategies_learned == 3

    def test_average_iterations(self) -> None:
        assert self.tracker.get_aggregated_metrics().average_iterations == 4.0

    def test_total_execution_time(self) -> None:
        assert self.tracker.get_aggregated_metrics().total_execution_time == 2.0

    def test_improvement_rate_zero_for_single(self) -> None:
        # Only 1 session → not enough for improvement calc → 0.0
        assert self.tracker.get_aggregated_metrics().improvement_rate == 0.0

    def test_learning_curve_has_one_entry(self) -> None:
        agg = self.tracker.get_aggregated_metrics()
        assert len(agg.learning_curve) == 1
        ts, sr = agg.learning_curve[0]
        assert isinstance(ts, float)
        assert sr == 0.8  # success_rate from session


# ---------------------------------------------------------------------------
# MetricsTracker — get_aggregated_metrics: multiple sessions
# ---------------------------------------------------------------------------


class TestAggregatedMetricsMultipleSessions:
    def _add_sessions(self, tracker: MetricsTracker, sessions: list[LearningMetrics]) -> None:
        m = mock_open()
        with patch("builtins.open", m):
            for s in sessions:
                tracker.record_session(s)

    def test_partial_success_rate(self) -> None:
        tracker = _make_tracker()
        sessions = [
            _session(success=True),
            _session(success=True),
            _session(success=False),
            _session(success=False),
        ]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.success_rate == 0.5

    def test_all_fail_success_rate_zero(self) -> None:
        tracker = _make_tracker()
        sessions = [_session(success=False), _session(success=False)]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.success_rate == 0.0

    def test_total_strategies_summed(self) -> None:
        tracker = _make_tracker()
        sessions = [_session(strategies_learned=2), _session(strategies_learned=5)]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.total_strategies_learned == 7

    def test_average_iterations_computed(self) -> None:
        tracker = _make_tracker()
        sessions = [_session(iterations=2), _session(iterations=4)]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.average_iterations == 3.0

    def test_improvement_rate_positive(self) -> None:
        """Second half has higher success rate → positive improvement."""
        tracker = _make_tracker()
        # 4 sessions: first 2 fail, last 2 succeed
        sessions = [
            _session(success=False),
            _session(success=False),
            _session(success=True),
            _session(success=True),
        ]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.improvement_rate > 0

    def test_improvement_rate_negative(self) -> None:
        """Second half has lower success rate → negative improvement."""
        tracker = _make_tracker()
        sessions = [
            _session(success=True),
            _session(success=True),
            _session(success=False),
            _session(success=False),
        ]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert agg.improvement_rate < 0

    def test_learning_curve_length_matches_sessions(self) -> None:
        tracker = _make_tracker()
        sessions = [_session() for _ in range(6)]
        self._add_sessions(tracker, sessions)
        agg = tracker.get_aggregated_metrics()
        assert len(agg.learning_curve) == 6


# ---------------------------------------------------------------------------
# MetricsTracker — task type breakdown
# ---------------------------------------------------------------------------


class TestTaskTypeBreakdown:
    def _add_sessions(self, tracker: MetricsTracker, sessions: list[LearningMetrics]) -> None:
        m = mock_open()
        with patch("builtins.open", m):
            for s in sessions:
                tracker.record_session(s)

    def test_single_task_type(self) -> None:
        tracker = _make_tracker()
        self._add_sessions(tracker, [_session("codegen"), _session("codegen", success=False)])
        agg = tracker.get_aggregated_metrics()
        assert "codegen" in agg.task_type_breakdown
        bd = agg.task_type_breakdown["codegen"]
        assert bd["count"] == 2
        assert bd["successes"] == 1
        assert bd["success_rate"] == 0.5

    def test_multiple_task_types(self) -> None:
        tracker = _make_tracker()
        self._add_sessions(
            tracker,
            [
                _session("codegen"),
                _session("test_gen"),
                _session("codegen"),
            ],
        )
        agg = tracker.get_aggregated_metrics()
        assert "codegen" in agg.task_type_breakdown
        assert "test_gen" in agg.task_type_breakdown
        assert agg.task_type_breakdown["codegen"]["count"] == 2
        assert agg.task_type_breakdown["test_gen"]["count"] == 1

    def test_strategies_learned_per_task_type(self) -> None:
        tracker = _make_tracker()
        self._add_sessions(
            tracker,
            [
                _session("codegen", strategies_learned=3),
                _session("codegen", strategies_learned=2),
            ],
        )
        agg = tracker.get_aggregated_metrics()
        assert agg.task_type_breakdown["codegen"]["strategies_learned"] == 5


# ---------------------------------------------------------------------------
# MetricsTracker — export_for_visualization
# ---------------------------------------------------------------------------


class TestExportForVisualization:
    def test_export_creates_valid_json(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session())

        output_path = Path("/tmp/test_viz_export.json")
        written_data: list[str] = []
        capture = mock_open()
        capture.return_value.__enter__.return_value.write = lambda d: written_data.append(d)

        with patch("builtins.open", capture):
            tracker.export_for_visualization(output_path)

        # Verify json.dump was called (open was called for writing)
        capture.assert_called_with(output_path, "w")

    def test_export_structure_keys(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session())

        # Capture the JSON data written
        export_data: list[object] = []

        def fake_dump(data: object, _f: object, **kwargs: object) -> None:
            export_data.append(data)

        output_path = Path("/tmp/test_viz_keys.json")
        with patch("builtins.open", mock_open()), patch("json.dump", side_effect=fake_dump):
            tracker.export_for_visualization(output_path)

        assert len(export_data) == 1
        data = export_data[0]
        assert isinstance(data, dict)
        assert "summary" in data
        assert "learning_curve" in data
        assert "task_type_breakdown" in data
        assert "sessions" in data

    def test_summary_keys(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session())

        export_data: list[object] = []

        def fake_dump(data: object, _f: object, **kwargs: object) -> None:
            export_data.append(data)

        with patch("builtins.open", mock_open()), patch("json.dump", side_effect=fake_dump):
            tracker.export_for_visualization(Path("/tmp/x.json"))

        summary = export_data[0]["summary"]  # type: ignore[index]
        assert "total_executions" in summary
        assert "success_rate" in summary
        assert "improvement_rate" in summary
        assert "total_strategies_learned" in summary

    def test_sessions_serialized(self) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session(task_type="serialization_test"))

        export_data: list[object] = []

        def fake_dump(data: object, _f: object, **kwargs: object) -> None:
            export_data.append(data)

        with patch("builtins.open", mock_open()), patch("json.dump", side_effect=fake_dump):
            tracker.export_for_visualization(Path("/tmp/x.json"))

        sessions = export_data[0]["sessions"]  # type: ignore[index]
        assert len(sessions) == 1
        assert sessions[0]["task_type"] == "serialization_test"


# ---------------------------------------------------------------------------
# MetricsTracker — print_summary (smoke test, no crash)
# ---------------------------------------------------------------------------


class TestPrintSummary:
    def test_empty_tracker_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        tracker = _make_tracker()
        tracker.print_summary()
        out = capsys.readouterr().out
        assert "Metrics Summary" in out

    def test_with_sessions_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        tracker = _make_tracker()
        m = mock_open()
        with patch("builtins.open", m):
            tracker.record_session(_session("codegen"))
            tracker.record_session(_session("test_gen", success=False))
        tracker.print_summary()
        out = capsys.readouterr().out
        assert "codegen" in out or "test_gen" in out
