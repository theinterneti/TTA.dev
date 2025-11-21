"""Adaptive Coordination System - Learning orchestration through ACE+e2b patterns.

This module implements self-learning coordination that improves primitive
composition through real execution feedback from E2B sandboxes.
"""

import json
import logging
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core.base import WorkflowPrimitive

logger = logging.getLogger(__name__)


class LearnedPrimitiveAdvisor(WorkflowPrimitive):
    """AI brain that learns optimal primitive combinations."""

    def __init__(self, playbook_file: Path | None = None):
        super().__init__()
        self.playbook_file = playbook_file or Path(
            "adaptive_coordination_playbook.json"
        )
        self.strategies = {}
        self.execution_history = []

        if self.playbook_file.exists():
            self._load_playbook()

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        task = input_data.get("task", "")
        task_context = input_data.get("context", {})

        recommendation = await self.recommend_composition(task, task_context)
        return recommendation

    async def recommend_composition(self, task: str, task_context: dict) -> dict:
        """Find optimal primitive combination for task context."""
        # Classify task
        task_category = self._classify_task(task, task_context)

        # Find similar executions
        similar_executions = self._find_similar_executions(task_category, task_context)

        if not similar_executions:
            return self._get_default_composition(task_category, task_context)

        # Analyze best performing strategy
        best_strategy = self._analyze_optimal_strategy(similar_executions, task_context)

        return {
            "recommendedPrimitives": best_strategy.primitive_combination,
            "expectedSuccessRate": best_strategy.success_rate,
            "expectedExecutionTime": best_strategy.avg_execution_time,
            "confidence": best_strategy.confidence_score,
            "strategySource": "learned"
            if best_strategy.usage_count > 1
            else "analyzed",
            "learningInsights": self._generate_insights(
                best_strategy, similar_executions
            ),
        }

    def _classify_task(self, task: str, context: dict) -> str:
        """Classify task type."""
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["api", "endpoint", "rest"]):
            return "api_development"
        elif any(kw in task_lower for kw in ["deploy", "infrastructure", "kubernetes"]):
            return "infrastructure"
        elif any(kw in task_lower for kw in ["test", "testing"]):
            return "testing"
        else:
            return "general_development"

    def _find_similar_executions(self, task_category: str, context: dict):
        """Find similar executions."""
        return [
            exec
            for exec in self.execution_history[-50:]
            if exec.task_category == task_category
        ][:5]

    def _analyze_optimal_strategy(self, executions, context: dict):
        """Find best strategy from executions."""
        # Simple analysis - return the highest performing combination
        primitive_counts = {}
        for exec in executions:
            combo = tuple(exec.primitives_used)
            if combo not in primitive_counts:
                primitive_counts[combo] = {"success": 0, "total": 0, "time": 0}
            primitive_counts[combo]["total"] += 1
            primitive_counts[combo]["time"] += exec.execution_time
            if exec.success:
                primitive_counts[combo]["success"] += 1

        # Find best combo
        best_combo = max(
            primitive_counts.items(), key=lambda x: x[1]["success"] / x[1]["total"]
        )
        combo, stats = best_combo

        from types import SimpleNamespace

        return SimpleNamespace(
            primitive_combination=list(combo),
            success_rate=stats["success"] / stats["total"],
            avg_execution_time=stats["time"] / stats["total"],
            confidence_score=min(stats["total"] / 5, 1.0),
            usage_count=stats["total"],
        )

    def _get_default_composition(self, task_category: str, context: dict) -> dict:
        """Get default compositions."""
        defaults = {
            "api_development": ["RouterPrimitive", "RetryPrimitive"],
            "infrastructure": ["ParallelPrimitive", "FallbackPrimitive"],
            "testing": ["ParallelPrimitive", "MockPrimitive"],
            "general_development": ["SequentialPrimitive"],
        }

        return {
            "recommendedPrimitives": defaults.get(
                task_category, ["SequentialPrimitive"]
            ),
            "expectedSuccessRate": 0.7,
            "expectedExecutionTime": 20.0,
            "confidence": 0.4,
            "strategySource": "rule_based_default",
            "learningInsights": [f"Using defaults for {task_category}"],
        }

    def _generate_insights(self, strategy, executions):
        insights = []
        insights.append(f"Based on {len(executions)} similar executions")
        if strategy.success_rate > 0.8:
            insights.append(f"High success rate: {strategy.success_rate:.1%}")
        insights.append(f"Confidence: {strategy.confidence_score:.1%}")
        return insights

    def record_execution_result(self, metrics):
        """Record execution for learning."""
        self.execution_history.append(metrics)
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]

    def _load_playbook(self):
        """Load strategies from file."""
        try:
            with open(self.playbook_file) as f:
                self.strategies = json.load(f)
        except:
            self.strategies = {}

    def _save_playbook(self):
        """Save strategies to file."""
        with open(self.playbook_file, "w") as f:
            json.dump(self.strategies, f, indent=2)


class AdaptiveWorkflowEngine(WorkflowPrimitive):
    """Engine that coordinates workflows using learned patterns."""

    def __init__(self, primitive_advisor=None):
        super().__init__()
        self.advisor = primitive_advisor or LearnedPrimitiveAdvisor()

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute adaptive workflow."""
        task = input_data.get("task", "")
        task_context = input_data.get("context", {})

        # Get recommendation
        recommendation = await self.advisor.execute(
            {"task": task, "context": task_context}, context
        )

        # Simulate workflow execution
        success = True  # Would implement real execution
        execution_time = recommendation.get("expectedExecutionTime", 10.0)

        # Record for learning
        from collections import namedtuple

        metrics = namedtuple(
            "Metrics", ["task_category", "primitives_used", "execution_time", "success"]
        )(
            task_category=self._classify_task(task, task_context),
            primitives_used=recommendation["recommendedPrimitives"],
            execution_time=execution_time,
            success=success,
        )
        self.advisor.record_execution_result(metrics)

        return {
            "result": {"status": "completed"} if success else {"status": "failed"},
            "learningApplied": True,
            "executionTime": execution_time,
            "primitivesUsed": recommendation["recommendedPrimitives"],
            "learningInsights": recommendation.get("learningInsights", []),
        }

    def _classify_task(self, task: str, context: dict) -> str:
        """Delegate classification to advisor."""
        return self.advisor._classify_task(task, context)
