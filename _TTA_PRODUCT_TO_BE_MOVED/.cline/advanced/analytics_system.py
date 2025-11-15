# pragma: allow-asyncio - Legacy file being moved
"""
Phase 3: Advanced Analytics & Learning System

Comprehensive feedback and improvement system for continuous learning and self-improvement.
This module provides usage analytics, A/B testing, machine learning models, and adaptive algorithms.

Key Features:
- Usage Analytics: tracking, success rates, productivity impact, satisfaction measurement
- Continuous Improvement: A/B testing, feedback processing, automated pattern improvement
- Learning Algorithms: ML models, reinforcement learning, knowledge base updates
"""

import asyncio
import hashlib
import json
import logging
import math
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

# Import from our existing systems
from .dynamic_context_loader import ProjectContext


class MetricType(Enum):
    """Types of metrics that can be tracked."""

    USAGE_FREQUENCY = "usage_frequency"
    SUCCESS_RATE = "success_rate"
    SATISFACTION_SCORE = "satisfaction_score"
    PRODUCTIVITY_IMPACT = "productivity_impact"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    ADOPTION_RATE = "adoption_rate"
    RETENTION_RATE = "retention_rate"


class LearningMethod(Enum):
    """Types of learning methods."""

    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    FEDERATED = "federated"
    TRANSFER = "transfer"


class ABTestStatus(Enum):
    """Status of A/B tests."""

    DESIGN = "design"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class UserInteraction:
    """Represents a user interaction with the system."""

    interaction_id: str
    user_id: str
    timestamp: datetime
    action: str
    context: dict[str, Any]
    outcome: str
    satisfaction_score: float
    duration: float
    primitive_used: str | None = None
    suggestion_confidence: float = 0.0
    actual_benefit: float = 0.0

    def __post_init__(self):
        if not self.interaction_id:
            self.interaction_id = str(uuid.uuid4())


@dataclass
class UsageMetric:
    """Represents a usage metric."""

    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: dict[str, Any]
    user_id: str | None = None
    session_id: str | None = None

    def __post_init__(self):
        if not self.metric_id:
            self.metric_id = str(uuid.uuid4())


@dataclass
class ABTest:
    """Represents an A/B test configuration."""

    test_id: str
    name: str
    description: str
    status: ABTestStatus
    variant_a: dict[str, Any]
    variant_b: dict[str, Any]
    metrics: list[MetricType]
    start_date: datetime
    end_date: datetime | None = None
    traffic_split: float = 0.5
    sample_size_target: int = 1000
    confidence_level: float = 0.95
    results: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.test_id:
            self.test_id = str(uuid.uuid4())


@dataclass
class LearningModel:
    """Represents a machine learning model."""

    model_id: str
    name: str
    model_type: LearningMethod
    version: str
    training_data: dict[str, Any]
    performance_metrics: dict[str, float]
    features: list[str]
    predictions: list[dict[str, Any]]
    created_at: datetime
    last_updated: datetime
    status: str = "training"

    def __post_init__(self):
        if not self.model_id:
            self.model_id = str(uuid.uuid4())


class UsageAnalytics:
    """System for tracking and analyzing usage patterns."""

    def __init__(self, data_retention_days: int = 90):
        self.data_retention_days = data_retention_days
        self.interactions: list[UserInteraction] = []
        self.metrics: list[UsageMetric] = []
        self.sessions: dict[str, dict[str, Any]] = {}
        self.user_profiles: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def record_interaction(self, interaction: UserInteraction):
        """Record a user interaction."""
        async with self._lock:
            self.interactions.append(interaction)

            # Update user profile
            if interaction.user_id not in self.user_profiles:
                self.user_profiles[interaction.user_id] = {
                    "first_seen": interaction.timestamp,
                    "total_interactions": 0,
                    "total_time_spent": 0.0,
                    "satisfaction_history": [],
                    "primitive_usage": defaultdict(int),
                    "success_rate": 0.0,
                }

            profile = self.user_profiles[interaction.user_id]
            profile["total_interactions"] += 1
            profile["total_time_spent"] += interaction.duration
            profile["satisfaction_history"].append(interaction.satisfaction_score)

            if interaction.primitive_used:
                profile["primitive_usage"][interaction.primitive_used] += 1

            # Update success rate
            recent_interactions = [
                i
                for i in self.interactions
                if i.user_id == interaction.user_id
                and (interaction.timestamp - i.timestamp).days <= 7
            ]
            successful_interactions = [
                i
                for i in recent_interactions
                if i.outcome in ["success", "partial_success"]
            ]
            profile["success_rate"] = len(successful_interactions) / max(
                len(recent_interactions), 1
            )

            # Clean old data
            await self._clean_old_data()

    async def record_metric(self, metric: UsageMetric):
        """Record a usage metric."""
        async with self._lock:
            self.metrics.append(metric)
            await self._clean_old_data()

    async def calculate_success_rates(
        self, time_window_days: int = 30
    ) -> dict[str, float]:
        """Calculate success rates for different primitives and contexts."""
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_interactions = [
            i for i in self.interactions if i.timestamp >= cutoff_date
        ]

        success_rates = {}

        # Calculate by primitive
        primitive_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for interaction in recent_interactions:
            if interaction.primitive_used:
                primitive_stats[interaction.primitive_used]["total"] += 1
                if interaction.outcome in ["success", "partial_success"]:
                    primitive_stats[interaction.primitive_used]["successful"] += 1

        for primitive, stats in primitive_stats.items():
            success_rates[f"primitive_{primitive}"] = stats["successful"] / max(
                stats["total"], 1
            )

        # Calculate by suggestion type
        suggestion_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for interaction in recent_interactions:
            suggestion_type = interaction.context.get("suggestion_type")
            if suggestion_type:
                suggestion_stats[suggestion_type]["total"] += 1
                if interaction.outcome in ["success", "partial_success"]:
                    suggestion_stats[suggestion_type]["successful"] += 1

        for suggestion_type, stats in suggestion_stats.items():
            success_rates[f"suggestion_{suggestion_type}"] = stats["successful"] / max(
                stats["total"], 1
            )

        return success_rates

    async def analyze_productivity_impact(self) -> dict[str, Any]:
        """Analyze the productivity impact of using TTA.dev primitives."""
        # Calculate time saved vs time spent
        time_saved = 0.0
        time_spent = 0.0

        for interaction in self.interactions:
            time_spent += interaction.duration
            time_saved += interaction.actual_benefit

        total_interactions = len(self.interactions)
        avg_satisfaction = (
            statistics.mean([i.satisfaction_score for i in self.interactions])
            if self.interactions
            else 0.0
        )

        return {
            "total_interactions": total_interactions,
            "total_time_spent_hours": time_spent / 3600,
            "total_time_saved_hours": time_saved / 3600,
            "efficiency_ratio": time_saved / max(time_spent, 0.1),
            "average_satisfaction": avg_satisfaction,
            "time_roi": (time_saved - time_spent) / max(time_spent, 0.1),
            "most_used_primitives": self._get_most_used_primitives(),
            "high_satisfaction_contexts": self._get_high_satisfaction_contexts(),
        }

    async def track_satisfaction_trends(
        self, time_window_days: int = 30
    ) -> dict[str, Any]:
        """Track satisfaction trends over time."""
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_interactions = [
            i for i in self.interactions if i.timestamp >= cutoff_date
        ]

        # Group by week
        weekly_satisfaction = defaultdict(list)
        daily_satisfaction = defaultdict(list)

        for interaction in recent_interactions:
            week_key = interaction.timestamp.strftime("%Y-W%U")
            day_key = interaction.timestamp.strftime("%Y-%m-%d")

            weekly_satisfaction[week_key].append(interaction.satisfaction_score)
            daily_satisfaction[day_key].append(interaction.satisfaction_score)

        # Calculate trends
        weekly_trends = {
            week: statistics.mean(scores)
            for week, scores in weekly_satisfaction.items()
        }

        daily_trends = {
            day: statistics.mean(scores) for day, scores in daily_satisfaction.items()
        }

        return {
            "weekly_trends": weekly_trends,
            "daily_trends": daily_trends,
            "overall_trend": self._calculate_trend(list(daily_trends.values())),
            "satisfaction_distribution": self._get_satisfaction_distribution(
                recent_interactions
            ),
        }

    def _get_most_used_primitives(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get the most used primitives."""
        usage_count = defaultdict(int)
        for interaction in self.interactions:
            if interaction.primitive_used:
                usage_count[interaction.primitive_used] += 1

        return sorted(usage_count.items(), key=lambda x: x[1], reverse=True)[:limit]

    def _get_high_satisfaction_contexts(
        self, threshold: float = 0.8
    ) -> list[dict[str, Any]]:
        """Get contexts that lead to high satisfaction."""
        high_sat_interactions = [
            i for i in self.interactions if i.satisfaction_score >= threshold
        ]

        context_patterns = defaultdict(int)
        for interaction in high_sat_interactions:
            context_key = f"{interaction.context.get('framework', 'unknown')}_{interaction.context.get('project_stage', 'unknown')}"
            context_patterns[context_key] += 1

        return [
            {"context": ctx, "frequency": freq}
            for ctx, freq in sorted(
                context_patterns.items(), key=lambda x: x[1], reverse=True
            )
        ]

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend
        x = list(range(len(values)))
        correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0

        if correlation > 0.1:
            return "improving"
        elif correlation < -0.1:
            return "declining"
        else:
            return "stable"

    def _get_satisfaction_distribution(
        self, interactions: list[UserInteraction]
    ) -> dict[str, int]:
        """Get satisfaction score distribution."""
        distribution = {"low": 0, "medium": 0, "high": 0, "very_high": 0}

        for interaction in interactions:
            score = interaction.satisfaction_score
            if score < 0.4:
                distribution["low"] += 1
            elif score < 0.6:
                distribution["medium"] += 1
            elif score < 0.8:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1

        return distribution

    async def _clean_old_data(self):
        """Clean data older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)

        self.interactions = [i for i in self.interactions if i.timestamp >= cutoff_date]

        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_date]


class ContinuousImprovement:
    """System for continuous improvement through A/B testing and feedback processing."""

    def __init__(self, analytics: UsageAnalytics):
        self.analytics = analytics
        self.active_tests: dict[str, ABTest] = {}
        self.completed_tests: dict[str, ABTest] = {}
        self.improvement_suggestions: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def create_ab_test(self, test: ABTest) -> str:
        """Create a new A/B test."""
        async with self._lock:
            self.active_tests[test.test_id] = test
            return test.test_id

    async def assign_user_to_variant(self, user_id: str, test_id: str) -> str:
        """Assign a user to a test variant based on consistent hashing."""
        test = self.active_tests.get(test_id)
        if not test or test.status != ABTestStatus.RUNNING:
            return "control"  # Default to control if test not found

        # Use consistent hashing to ensure same user gets same variant
        hash_input = f"{user_id}_{test_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Determine variant based on hash and traffic split
        if (hash_value % 100) < (test.traffic_split * 100):
            return "variant_b"
        else:
            return "variant_a"

    async def record_test_interaction(
        self, user_id: str, test_id: str, variant: str, interaction: UserInteraction
    ):
        """Record interaction for A/B test analysis."""
        test = self.active_tests.get(test_id)
        if not test:
            return

        # Store interaction with test context
        interaction.context = {
            **interaction.context,
            "test_id": test_id,
            "variant": variant,
        }

        await self.analytics.record_interaction(interaction)

    async def analyze_test_results(self, test_id: str) -> dict[str, Any]:
        """Analyze A/B test results."""
        test = self.active_tests.get(test_id)
        if not test:
            return {"error": "Test not found"}

        # Get test interactions
        test_interactions = [
            i
            for i in self.analytics.interactions
            if i.context.get("test_id") == test_id
        ]

        if not test_interactions:
            return {"error": "No test data available"}

        # Separate by variant
        variant_a_interactions = [
            i for i in test_interactions if i.context.get("variant") == "variant_a"
        ]
        variant_b_interactions = [
            i for i in test_interactions if i.context.get("variant") == "variant_b"
        ]

        # Calculate metrics for each variant
        results = {}
        for metric in test.metrics:
            results[metric.value] = {
                "variant_a": self._calculate_metric(variant_a_interactions, metric),
                "variant_b": self._calculate_metric(variant_b_interactions, metric),
                "difference": 0.0,
                "confidence": 0.0,
            }

        # Statistical significance testing
        for metric, data in results.items():
            a_values = self._get_metric_values(variant_a_interactions, metric)
            b_values = self._get_metric_values(variant_b_interactions, metric)

            if a_values and b_values:
                # Simple t-test approximation
                mean_a = statistics.mean(a_values)
                mean_b = statistics.mean(b_values)
                std_a = statistics.stdev(a_values) if len(a_values) > 1 else 0
                std_b = statistics.stdev(b_values) if len(b_values) > 1 else 0

                data["difference"] = mean_b - mean_a
                data["confidence"] = self._calculate_confidence(
                    mean_a, mean_b, std_a, std_b, len(a_values), len(b_values)
                )

        return {
            "test_id": test_id,
            "test_name": test.name,
            "sample_sizes": {
                "variant_a": len(variant_a_interactions),
                "variant_b": len(variant_b_interactions),
            },
            "results": results,
            "recommendation": self._generate_recommendation(results),
        }

    def _calculate_metric(
        self, interactions: list[UserInteraction], metric: MetricType
    ) -> float:
        """Calculate a specific metric for interactions."""
        if not interactions:
            return 0.0

        if metric == MetricType.SUCCESS_RATE:
            successful = sum(
                1 for i in interactions if i.outcome in ["success", "partial_success"]
            )
            return successful / len(interactions)
        elif metric == MetricType.SATISFACTION_SCORE:
            return statistics.mean([i.satisfaction_score for i in interactions])
        elif metric == MetricType.RESPONSE_TIME:
            return statistics.mean([i.duration for i in interactions])
        elif metric == MetricType.PRODUCTIVITY_IMPACT:
            return statistics.mean([i.actual_benefit for i in interactions])
        else:
            return 0.0

    def _get_metric_values(
        self, interactions: list[UserInteraction], metric: MetricType
    ) -> list[float]:
        """Get values for a specific metric."""
        return [self._get_single_metric_value(i, metric) for i in interactions]

    def _get_single_metric_value(
        self, interaction: UserInteraction, metric: MetricType
    ) -> float:
        """Get a single metric value from an interaction."""
        if metric == MetricType.SUCCESS_RATE:
            return 1.0 if interaction.outcome in ["success", "partial_success"] else 0.0
        elif metric == MetricType.SATISFACTION_SCORE:
            return interaction.satisfaction_score
        elif metric == MetricType.RESPONSE_TIME:
            return interaction.duration
        elif metric == MetricType.PRODUCTIVITY_IMPACT:
            return interaction.actual_benefit
        else:
            return 0.0

    def _calculate_confidence(
        self,
        mean_a: float,
        mean_b: float,
        std_a: float,
        std_b: float,
        n_a: int,
        n_b: int,
    ) -> float:
        """Calculate confidence level using simplified t-test."""
        if n_a < 2 or n_b < 2 or (std_a == 0 and std_b == 0):
            return 0.0

        # Simplified confidence calculation
        pooled_std = math.sqrt(
            ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2)
        )
        if pooled_std == 0:
            return 1.0 if abs(mean_b - mean_a) > 0 else 0.0

        t_stat = abs(mean_b - mean_a) / (pooled_std * math.sqrt(1 / n_a + 1 / n_b))

        # Convert t-statistic to confidence (simplified)
        confidence = min(1.0, t_stat / 2.0)
        return confidence

    def _generate_recommendation(self, results: dict[str, Any]) -> str:
        """Generate a recommendation based on test results."""
        winning_metrics = 0
        total_metrics = len(results)

        for metric, data in results.items():
            if data["confidence"] > 0.95 and data["difference"] > 0:
                winning_metrics += 1

        if winning_metrics == total_metrics:
            return "implement_b"
        elif winning_metrics == 0:
            return "keep_a"
        else:
            return "inconclusive"

    async def generate_improvement_suggestions(self) -> list[dict[str, Any]]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []

        # Analyze underperforming primitives
        success_rates = await self.analytics.calculate_success_rates()
        low_performance = [
            (primitive, rate)
            for primitive, rate in success_rates.items()
            if rate < 0.6 and primitive.startswith("primitive_")
        ]

        for primitive, rate in low_performance:
            suggestions.append(
                {
                    "type": "primitive_improvement",
                    "primitive": primitive.replace("primitive_", ""),
                    "issue": f"Low success rate: {rate:.2%}",
                    "recommendation": "Improve documentation or implementation",
                    "priority": "high" if rate < 0.4 else "medium",
                }
            )

        # Analyze satisfaction trends
        satisfaction_trends = await self.analytics.track_satisfaction_trends()
        if satisfaction_trends["overall_trend"] == "declining":
            suggestions.append(
                {
                    "type": "satisfaction_decline",
                    "issue": "Overall satisfaction is declining",
                    "recommendation": "Investigate recent changes and user feedback",
                    "priority": "high",
                }
            )

        # Analyze productivity impact
        productivity = await self.analytics.analyze_productivity_impact()
        if productivity["efficiency_ratio"] < 1.0:
            suggestions.append(
                {
                    "type": "low_roi",
                    "issue": f"Low efficiency ratio: {productivity['efficiency_ratio']:.2f}",
                    "recommendation": "Focus on high-impact primitives and improve onboarding",
                    "priority": "high",
                }
            )

        return suggestions

    async def start_test(self, test_id: str):
        """Start an A/B test."""
        if test_id in self.active_tests:
            self.active_tests[test_id].status = ABTestStatus.RUNNING

    async def stop_test(self, test_id: str):
        """Stop an A/B test."""
        if test_id in self.active_tests:
            test = self.active_tests[test_id]
            test.status = ABTestStatus.COMPLETED
            test.end_date = datetime.now()

            # Calculate and store results
            test.results = await self.analyze_test_results(test_id)

            # Move to completed tests
            self.completed_tests[test_id] = test
            del self.active_tests[test_id]


class LearningAlgorithms:
    """System for machine learning models and adaptive algorithms."""

    def __init__(self, analytics: UsageAnalytics):
        self.analytics = analytics
        self.models: dict[str, LearningModel] = {}
        self.prediction_cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def create_model(
        self, model_type: LearningMethod, features: list[str], name: str
    ) -> str:
        """Create a new machine learning model."""
        model = LearningModel(
            model_id=str(uuid.uuid4()),
            name=name,
            model_type=model_type,
            version="1.0",
            training_data={},
            performance_metrics={},
            features=features,
            predictions=[],
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status="created",
        )

        async with self._lock:
            self.models[model.model_id] = model

        return model.model_id

    async def train_model(
        self, model_id: str, training_data: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Train a machine learning model."""
        model = self.models.get(model_id)
        if not model:
            raise ValueError("Model not found")

        model.status = "training"
        model.training_data = {
            "samples": len(training_data),
            "features": model.features,
        }

        # Simulate model training (in real implementation, this would use actual ML libraries)
        await asyncio.sleep(1)  # Simulate training time

        # Calculate performance metrics
        performance_metrics = await self._calculate_performance_metrics(
            training_data, model
        )
        model.performance_metrics = performance_metrics
        model.status = "trained"
        model.last_updated = datetime.now()

        return performance_metrics

    async def predict(
        self, model_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a prediction using a trained model."""
        model = self.models.get(model_id)
        if not model or model.status != "trained":
            raise ValueError("Model not found or not trained")

        # Cache prediction for performance
        cache_key = f"{model_id}_{hashlib.sha256(str(input_data).encode()).hexdigest()}"
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]

        # Simulate prediction (in real implementation, this would use actual ML model)
        prediction = await self._simulate_prediction(input_data, model)

        # Store prediction
        prediction_record = {
            "input": input_data,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat(),
            "confidence": prediction.get("confidence", 0.5),
        }

        model.predictions.append(prediction_record)

        # Cache the result
        self.prediction_cache[cache_key] = prediction

        return prediction

    async def adapt_suggestions(
        self, context: ProjectContext, user_history: list[UserInteraction]
    ) -> list[dict[str, Any]]:
        """Adapt suggestions based on learned patterns."""
        # Get or create adaptive model
        model_id = await self._get_or_create_adaptive_model()

        # Prepare input features
        features = self._extract_features(context, user_history)

        # Get prediction
        prediction = await self.predict(model_id, features)

        # Adapt suggestions based on prediction
        adapted_suggestions = self._adapt_suggestions_from_prediction(
            prediction, context
        )

        return adapted_suggestions

    async def reinforcement_learning_update(
        self, interaction: UserInteraction, reward: float
    ):
        """Update model based on reinforcement learning feedback."""
        # This would implement Q-learning or similar RL algorithms
        # For now, we'll simulate the update process

        model_id = await self._get_or_create_adaptive_model()
        model = self.models.get(model_id)

        if model and model.status == "trained":
            # Simulate RL update
            model.performance_metrics["rl_updates"] = (
                model.performance_metrics.get("rl_updates", 0) + 1
            )
            model.last_updated = datetime.now()

            logging.info(
                f"RL update: interaction={interaction.interaction_id}, reward={reward}"
            )

    async def federated_learning_update(self, model_updates: list[dict[str, Any]]):
        """Update model using federated learning from multiple clients."""
        model_id = await self._get_or_create_adaptive_model()
        model = self.models.get(model_id)

        if model:
            # Aggregate updates from multiple clients
            aggregated_update = await self._aggregate_federated_updates(model_updates)

            # Update model parameters
            model.training_data["federated_updates"] = (
                model.training_data.get("federated_updates", 0) + 1
            )
            model.last_updated = datetime.now()

            logging.info(f"Federated learning update with {len(model_updates)} clients")

    async def _get_or_create_adaptive_model(self) -> str:
        """Get or create the adaptive suggestion model."""
        for model_id, model in self.models.items():
            if model.name == "adaptive_suggestions":
                return model_id

        # Create new adaptive model
        features = [
            "user_experience_level",
            "project_complexity",
            "framework_type",
            "development_stage",
            "success_rate_history",
            "satisfaction_trend",
        ]

        return await self.create_model(
            LearningMethod.SUPERVISED, features, "adaptive_suggestions"
        )

    def _extract_features(
        self, context: ProjectContext, user_history: list[UserInteraction]
    ) -> dict[str, Any]:
        """Extract features for ML model."""
        # User experience level
        experience_level = len(user_history) / 100.0  # Normalize to 0-1
        experience_level = min(1.0, experience_level)

        # Project complexity
        complexity = context.complexity_score

        # Framework type (encoded as number)
        framework_encoding = {
            "react": 1.0,
            "django": 2.0,
            "fastapi": 3.0,
            "flask": 4.0,
            "unknown": 0.0,
        }
        framework_type = framework_encoding.get(
            context.frameworks[0].framework.value if context.frameworks else "unknown",
            0.0,
        )

        # Development stage
        stage_encoding = {
            "prototyping": 1.0,
            "development": 2.0,
            "production": 3.0,
            "maintenance": 4.0,
        }
        development_stage = stage_encoding.get(context.stage.value, 0.0)

        # Success rate history
        successful_interactions = [
            i for i in user_history if i.outcome in ["success", "partial_success"]
        ]
        success_rate_history = len(successful_interactions) / max(len(user_history), 1)

        # Satisfaction trend
        recent_satisfaction = [
            i.satisfaction_score
            for i in user_history[-10:]  # Last 10 interactions
        ]
        satisfaction_trend = (
            statistics.mean(recent_satisfaction) if recent_satisfaction else 0.5
        )

        return {
            "user_experience_level": experience_level,
            "project_complexity": complexity,
            "framework_type": framework_type,
            "development_stage": development_stage,
            "success_rate_history": success_rate_history,
            "satisfaction_trend": satisfaction_trend,
        }

    async def _simulate_prediction(
        self, input_data: dict[str, Any], model: LearningModel
    ) -> dict[str, Any]:
        """Simulate ML model prediction."""
        # Simple heuristic-based prediction (in real implementation, would use actual ML)

        # Calculate suggestion preferences based on input features
        experience = input_data.get("user_experience_level", 0.5)
        complexity = input_data.get("project_complexity", 0.5)
        stage = input_data.get("development_stage", 2.0)

        # Generate suggestions based on context
        suggestions = []

        # Basic primitives for beginners
        if experience < 0.3:
            suggestions.extend(
                [
                    {
                        "primitive": "cache_primitive",
                        "confidence": 0.8,
                        "reasoning": "Good for beginners",
                    },
                    {
                        "primitive": "sequential_primitive",
                        "confidence": 0.7,
                        "reasoning": "Easy to understand",
                    },
                ]
            )

        # Advanced primitives for complex projects
        if complexity > 0.7:
            suggestions.extend(
                [
                    {
                        "primitive": "parallel_primitive",
                        "confidence": 0.9,
                        "reasoning": "Handles complexity well",
                    },
                    {
                        "primitive": "router_primitive",
                        "confidence": 0.8,
                        "reasoning": "Good for complex architectures",
                    },
                ]
            )

        # Stage-specific recommendations
        if stage >= 3.0:  # Production/Maintenance
            suggestions.extend(
                [
                    {
                        "primitive": "fallback_primitive",
                        "confidence": 0.9,
                        "reasoning": "Essential for production",
                    },
                    {
                        "primitive": "retry_primitive",
                        "confidence": 0.8,
                        "reasoning": "Improves reliability",
                    },
                ]
            )

        return {
            "suggestions": suggestions,
            "confidence": 0.75,
            "model_version": model.version,
            "features_used": model.features,
        }

    def _adapt_suggestions_from_prediction(
        self, prediction: dict[str, Any], context: ProjectContext
    ) -> list[dict[str, Any]]:
        """Adapt suggestions based on ML prediction."""
        base_suggestions = prediction.get("suggestions", [])

        # Add context-specific adjustments
        adapted_suggestions = []

        for suggestion in base_suggestions:
            # Adjust confidence based on context
            adjusted_confidence = suggestion["confidence"]

            # Boost for framework matches
            if context.frameworks:
                framework = context.frameworks[0].framework.value
                framework_boosts = {
                    "react": {"cache_primitive": 0.1, "fallback_primitive": 0.1},
                    "django": {"cache_primitive": 0.2, "retry_primitive": 0.1},
                    "fastapi": {"timeout_primitive": 0.2, "sequential_primitive": 0.1},
                }

                if framework in framework_boosts:
                    primitive = suggestion["primitive"]
                    if primitive in framework_boosts[framework]:
                        adjusted_confidence += framework_boosts[framework][primitive]

            # Ensure confidence is between 0 and 1
            adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))

            adapted_suggestion = {
                **suggestion,
                "confidence": adjusted_confidence,
                "context_relevance": self._calculate_context_relevance(
                    suggestion["primitive"], context
                ),
            }

            adapted_suggestions.append(adapted_suggestion)

        # Sort by confidence and context relevance
        adapted_suggestions.sort(
            key=lambda x: (x["confidence"] + x["context_relevance"]) / 2, reverse=True
        )

        return adapted_suggestions

    def _calculate_context_relevance(
        self, primitive: str, context: ProjectContext
    ) -> float:
        """Calculate how relevant a primitive is to the current context."""
        relevance = 0.5  # Base relevance

        # Framework-specific relevance
        if context.frameworks:
            framework = context.frameworks[0].framework.value
            framework_relevance = {
                "react": {
                    "cache_primitive": 0.9,
                    "fallback_primitive": 0.8,
                    "retry_primitive": 0.7,
                },
                "django": {
                    "cache_primitive": 0.9,
                    "retry_primitive": 0.8,
                    "fallback_primitive": 0.7,
                },
                "fastapi": {
                    "timeout_primitive": 0.9,
                    "retry_primitive": 0.8,
                    "sequential_primitive": 0.7,
                },
                "flask": {"cache_primitive": 0.8, "fallback_primitive": 0.7},
            }

            if (
                framework in framework_relevance
                and primitive in framework_relevance[framework]
            ):
                relevance = framework_relevance[framework][primitive]

        # Stage-specific relevance
        stage_relevance = {
            "production": {
                "fallback_primitive": 0.9,
                "retry_primitive": 0.8,
                "timeout_primitive": 0.8,
            },
            "development": {"cache_primitive": 0.7, "sequential_primitive": 0.6},
            "prototyping": {"cache_primitive": 0.5, "fallback_primitive": 0.3},
        }

        if (
            context.stage.value in stage_relevance
            and primitive in stage_relevance[context.stage.value]
        ):
            relevance = max(relevance, stage_relevance[context.stage.value][primitive])

        # Complexity-based relevance
        if context.complexity_score > 0.7 and primitive in [
            "parallel_primitive",
            "router_primitive",
        ]:
            relevance += 0.2

        return min(1.0, relevance)

    async def _calculate_performance_metrics(
        self, training_data: list[dict[str, Any]], model: LearningModel
    ) -> dict[str, float]:
        """Calculate performance metrics for a model."""
        # Simulate performance calculation
        metrics = {
            "accuracy": 0.85 + np.random.normal(0, 0.05),  # Random variation
            "precision": 0.82 + np.random.normal(0, 0.05),
            "recall": 0.88 + np.random.normal(0, 0.05),
            "f1_score": 0.85 + np.random.normal(0, 0.05),
        }

        # Ensure metrics are between 0 and 1
        for key, value in metrics.items():
            metrics[key] = max(0.0, min(1.0, value))

        return metrics

    async def _aggregate_federated_updates(
        self, updates: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Aggregate federated learning updates."""
        # Simple average aggregation
        if not updates:
            return {}

        # This would be more sophisticated in a real implementation
        aggregated = {
            "client_count": len(updates),
            "avg_performance": statistics.mean(
                [u.get("performance", 0.5) for u in updates]
            ),
            "update_count": sum(u.get("updates", 0) for u in updates),
        }

        return aggregated


class AnalyticsSystem:
    """Main analytics and learning system."""

    def __init__(self, data_retention_days: int = 90):
        self.analytics = UsageAnalytics(data_retention_days)
        self.improvement = ContinuousImprovement(self.analytics)
        self.learning = LearningAlgorithms(self.analytics)
        self._running = False

    async def start(self):
        """Start the analytics system."""
        self._running = True
        logging.info("Analytics system started")

        # Start background tasks
        asyncio.create_task(self._periodic_analysis())
        asyncio.create_task(self._model_maintenance())

    async def stop(self):
        """Stop the analytics system."""
        self._running = False
        logging.info("Analytics system stopped")

    async def record_user_interaction(
        self,
        user_id: str,
        action: str,
        context: dict[str, Any],
        outcome: str,
        satisfaction_score: float,
        duration: float,
        primitive_used: str | None = None,
    ) -> str:
        """Record a user interaction."""
        interaction = UserInteraction(
            interaction_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.now(),
            action=action,
            context=context,
            outcome=outcome,
            satisfaction_score=satisfaction_score,
            duration=duration,
            primitive_used=primitive_used,
        )

        await self.analytics.record_interaction(interaction)

        # Trigger learning update if outcome indicates success/failure
        if outcome in ["success", "partial_success"]:
            reward = satisfaction_score
        else:
            reward = -satisfaction_score

        await self.learning.reinforcement_learning_update(interaction, reward)

        return interaction.interaction_id

    async def get_comprehensive_report(self) -> dict[str, Any]:
        """Get a comprehensive analytics report."""
        # Gather all analytics data
        success_rates = await self.analytics.calculate_success_rates()
        productivity_impact = await self.analytics.analyze_productivity_impact()
        satisfaction_trends = await self.analytics.track_satisfaction_trends()
        improvement_suggestions = (
            await self.improvement.generate_improvement_suggestions()
        )

        # Get model performance
        model_status = {}
        for model_id, model in self.learning.models.items():
            model_status[model.name] = {
                "status": model.status,
                "performance": model.performance_metrics,
                "predictions_count": len(model.predictions),
            }

        return {
            "summary": {
                "total_interactions": len(self.analytics.interactions),
                "active_users": len(self.analytics.user_profiles),
                "active_ab_tests": len(self.improvement.active_tests),
                "trained_models": len(
                    [m for m in self.learning.models.values() if m.status == "trained"]
                ),
            },
            "success_rates": success_rates,
            "productivity_impact": productivity_impact,
            "satisfaction_trends": satisfaction_trends,
            "improvement_suggestions": improvement_suggestions,
            "model_status": model_status,
            "ab_test_results": {
                test_id: test.results
                for test_id, test in self.improvement.completed_tests.items()
            },
            "generated_at": datetime.now().isoformat(),
        }

    async def create_productivity_test(self) -> str:
        """Create an A/B test for productivity features."""
        test = ABTest(
            test_id=str(uuid.uuid4()),
            name="Productivity Feature Test",
            description="Test the impact of enhanced productivity features",
            status=ABTestStatus.DESIGN,
            variant_a={"features": ["basic_suggestions"]},
            variant_b={
                "features": ["basic_suggestions", "productivity_tips", "smart_defaults"]
            },
            metrics=[
                MetricType.SUCCESS_RATE,
                MetricType.SATISFACTION_SCORE,
                MetricType.PRODUCTIVITY_IMPACT,
            ],
            start_date=datetime.now(),
            traffic_split=0.5,
            sample_size_target=500,
        )

        return await self.improvement.create_ab_test(test)

    async def _periodic_analysis(self):
        """Periodic analysis and improvement."""
        while self._running:
            try:
                # Generate improvement suggestions every hour
                await asyncio.sleep(3600)  # 1 hour

                suggestions = await self.improvement.generate_improvement_suggestions()
                logging.info(f"Generated {len(suggestions)} improvement suggestions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Periodic analysis error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _model_maintenance(self):
        """Periodic model maintenance and retraining."""
        while self._running:
            try:
                # Retrain models every 24 hours
                await asyncio.sleep(86400)  # 24 hours

                # Check for models that need retraining
                for model_id, model in self.learning.models.items():
                    if model.status == "trained":
                        # Simulate retraining trigger
                        time_since_update = datetime.now() - model.last_updated
                        if time_since_update.days > 7:  # Retrain if older than 7 days
                            logging.info(f"Retraining model {model.name}")
                            # In real implementation, would trigger retraining

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Model maintenance error: {str(e)}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying


# Utility functions
def create_analytics_system(data_retention_days: int = 90) -> AnalyticsSystem:
    """Create a configured analytics system."""
    return AnalyticsSystem(data_retention_days)


async def quick_analytics_report(analytics_system: AnalyticsSystem) -> dict[str, Any]:
    """Generate a quick analytics report."""
    return await analytics_system.get_comprehensive_report()


# Example usage and testing
if __name__ == "__main__":

    async def test_analytics_system():
        """Test the analytics system."""
        system = create_analytics_system()
        await system.start()

        # Simulate some user interactions
        await system.record_user_interaction(
            user_id="user_123",
            action="suggest_primitive",
            context={"framework": "django", "project_stage": "development"},
            outcome="success",
            satisfaction_score=0.8,
            duration=120.0,
            primitive_used="cache_primitive",
        )

        await system.record_user_interaction(
            user_id="user_456",
            action="suggest_primitive",
            context={"framework": "react", "project_stage": "production"},
            outcome="partial_success",
            satisfaction_score=0.6,
            duration=180.0,
            primitive_used="fallback_primitive",
        )

        # Get report
        report = await system.get_comprehensive_report()
        print(f"Analytics Report: {json.dumps(report, indent=2, default=str)}")

        await system.stop()
        print("Analytics system test completed")

    # Run the test
    asyncio.run(test_analytics_system())
