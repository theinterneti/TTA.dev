"""Logseq integration for adaptive primitive strategy persistence.

This module enables strategy playbooks to be persisted in Logseq knowledge base,
creating a rich, searchable, and interconnected record of learned strategies.

Key Features:
- Strategy → Logseq page conversion
- Automatic strategy network graph updates
- Performance metrics tracking
- Learning history documentation
- Query templates for strategy analysis

Integration Points:
- Strategy discovery and sharing
- Performance pattern analysis
- Context-aware strategy recommendations
- Learning pathway documentation
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives.adaptive.base import LearningStrategy
from tta_dev_primitives.core.base import WorkflowContext

logger = logging.getLogger(__name__)


class LogseqStrategyIntegration:
    """Integrates adaptive primitive strategies with Logseq knowledge base."""

    def __init__(self, logseq_base_path: Path | str = "logseq"):
        self.logseq_base_path = Path(logseq_base_path)
        self.strategies_path = self.logseq_base_path / "pages" / "Strategies"
        self.journals_path = self.logseq_base_path / "journals"

        # Ensure directories exist
        self.strategies_path.mkdir(parents=True, exist_ok=True)
        self.journals_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized Logseq integration: {self.logseq_base_path}")

    async def save_learned_strategy(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        context: WorkflowContext,
        performance_data: dict[str, Any] | None = None,
    ) -> Path:
        """Save a learned strategy to Logseq knowledge base."""

        # Create strategy page content
        strategy_page_content = self._create_strategy_page(
            strategy, primitive_type, context, performance_data
        )

        # Save strategy page
        strategy_file = self.strategies_path / f"{strategy.name}.md"
        strategy_file.write_text(strategy_page_content, encoding="utf-8")

        # Update daily journal with strategy learning event
        await self._log_strategy_event(strategy, primitive_type, "learned")

        # Update strategy network (for visualization)
        await self._update_strategy_network(strategy, primitive_type)

        logger.info(f"Saved strategy '{strategy.name}' to Logseq: {strategy_file}")
        return strategy_file

    async def update_strategy_performance(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        execution_result: dict[str, Any],
    ) -> None:
        """Update strategy performance metrics in Logseq."""

        # Load existing page
        strategy_file = self.strategies_path / f"{strategy.name}.md"
        if not strategy_file.exists():
            logger.warning(f"Strategy file not found: {strategy_file}")
            return

        content = strategy_file.read_text(encoding="utf-8")

        # Update performance section
        updated_content = self._update_performance_section(
            content, strategy, execution_result
        )

        # Save updated content
        strategy_file.write_text(updated_content, encoding="utf-8")

        # Log performance update in daily journal
        await self._log_strategy_event(strategy, primitive_type, "performance_update")

    def _create_strategy_page(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        context: WorkflowContext,
        performance_data: dict[str, Any] | None = None,
    ) -> str:
        """Create Logseq page content for a strategy."""

        performance_data = performance_data or {}
        created_date = datetime.fromtimestamp(strategy.created_at).strftime("%Y-%m-%d")

        # Build related strategies section
        related_strategies = self._find_related_strategies(strategy, primitive_type)

        page_content = f"""# Strategy: {strategy.name}

## Overview
- **Type:** #strategy #adaptive #{primitive_type.lower().replace("_", "-")}
- **Primitive:** [[TTA Primitives/{primitive_type}]]
- **Created:** [[{created_date}]]
- **Status:** {"🟢 Active" if strategy.is_validated else "🟡 Learning"}

## Description
{strategy.description}

## Context Pattern
- **Pattern:** `{strategy.context_pattern}`
- **Matches:** Contexts containing "{strategy.context_pattern}"

## Strategy Parameters
```json
{json.dumps(strategy.parameters, indent=2)}
```

## Performance Metrics
- **Success Rate:** {strategy.metrics.success_rate:.1%} ({strategy.metrics.success_count}/{strategy.metrics.total_executions})
- **Average Latency:** {strategy.metrics.avg_latency:.3f}s
- **Total Executions:** {strategy.metrics.total_executions}
- **Contexts Seen:** {len(strategy.metrics.contexts_seen)}
- **Last Updated:** {datetime.fromtimestamp(strategy.metrics.last_updated).strftime("%Y-%m-%d %H:%M")}

### Validation Status
- **Validation Attempts:** {strategy.validation_attempts}
- **Validation Successes:** {strategy.validation_successes}
- **Validated:** {"✅ Yes" if strategy.is_validated else "⏳ In Progress"}

{self._format_performance_data(performance_data)}

## Learning Context
- **Correlation ID:** {context.correlation_id}
- **Environment:** {context.metadata.get("environment", "unknown")}
- **Priority:** {context.metadata.get("priority", "normal")}
- **Time Sensitive:** {context.metadata.get("time_sensitive", False)}

## Learning History
{self._format_learning_history(strategy)}

## Related Strategies
{related_strategies}

## Usage Examples
```python
# Context where this strategy applies
context = WorkflowContext(metadata={{
    "environment": "{context.metadata.get("environment", "example")}",
    "priority": "{context.metadata.get("priority", "normal")}"
}})

# Strategy parameters
strategy_params = {json.dumps(strategy.parameters, indent=2)}
```

## Performance Analysis
### Success Patterns
- Most successful in: {self._analyze_success_patterns(strategy)}
- Best performance time: {self._analyze_timing_patterns(strategy)}

### Failure Analysis
- Common failure modes: {self._analyze_failure_patterns(strategy)}
- Context sensitivity: {self._analyze_context_sensitivity(strategy)}

## Strategy Evolution
{self._format_strategy_evolution(strategy)}

---
*Generated by Adaptive Primitives Learning System*
*Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

#learning #performance #adaptive-primitives
"""

        return page_content

    def _format_performance_data(self, performance_data: dict[str, Any]) -> str:
        """Format additional performance data for display."""
        if not performance_data:
            return ""

        sections = []
        if "latency_percentiles" in performance_data:
            sections.append("### Latency Distribution")
            for percentile, value in performance_data["latency_percentiles"].items():
                sections.append(f"- **P{percentile}:** {value:.3f}s")

        if "error_breakdown" in performance_data:
            sections.append("\n### Error Breakdown")
            for error_type, count in performance_data["error_breakdown"].items():
                sections.append(f"- **{error_type}:** {count} occurrences")

        return "\n".join(sections) if sections else ""

    def _format_learning_history(self, strategy: LearningStrategy) -> str:
        """Format learning history for display."""
        history_items = [
            f"- **Created:** {datetime.fromtimestamp(strategy.created_at).strftime('%Y-%m-%d %H:%M')}",
            f"- **Last Used:** {datetime.fromtimestamp(strategy.last_used).strftime('%Y-%m-%d %H:%M')}",
            f"- **Total Usage:** {strategy.metrics.total_executions} executions",
        ]

        if strategy.validation_attempts > 0:
            validation_rate = (
                strategy.validation_successes / strategy.validation_attempts
            )
            history_items.append(f"- **Validation Rate:** {validation_rate:.1%}")

        return "\n".join(history_items)

    def _find_related_strategies(
        self, strategy: LearningStrategy, primitive_type: str
    ) -> str:
        """Find and format related strategies."""
        # In a full implementation, this would query existing strategies
        # For now, provide template for manual linking
        return f"""- [[Strategies/baseline_{primitive_type.lower()}]] - Baseline comparison
- Query: {{{{query (and [[#strategy]] [[#{primitive_type.lower()}]])}}}}
- Similar contexts: {{{{query (and [[#strategy]] (property context-pattern *{strategy.context_pattern.split(":")[0] if ":" in strategy.context_pattern else strategy.context_pattern}*))}}}}"""

    def _analyze_success_patterns(self, strategy: LearningStrategy) -> str:
        """Analyze and format success patterns."""
        if not strategy.metrics.contexts_seen:
            return "Insufficient data"

        # Analyze context patterns - in full implementation would use ML
        contexts = list(strategy.metrics.contexts_seen)
        if len(contexts) == 1:
            return f"Single context: {contexts[0]}"
        else:
            return f"{len(contexts)} different contexts"

    def _analyze_timing_patterns(self, strategy: LearningStrategy) -> str:
        """Analyze timing patterns."""
        if strategy.metrics.avg_latency < 1.0:
            return "Fast execution (< 1s)"
        elif strategy.metrics.avg_latency < 5.0:
            return "Moderate execution (1-5s)"
        else:
            return "Slow execution (> 5s)"

    def _analyze_failure_patterns(self, strategy: LearningStrategy) -> str:
        """Analyze failure patterns."""
        if strategy.metrics.failure_rate == 0:
            return "No failures observed"
        elif strategy.metrics.failure_rate < 0.1:
            return "Occasional failures (< 10%)"
        else:
            return f"Significant failures ({strategy.metrics.failure_rate:.1%})"

    def _analyze_context_sensitivity(self, strategy: LearningStrategy) -> str:
        """Analyze context sensitivity."""
        num_contexts = len(strategy.metrics.contexts_seen)
        if num_contexts <= 1:
            return "Single context - high sensitivity"
        elif num_contexts <= 3:
            return "Low context diversity"
        else:
            return "High context diversity"

    def _format_strategy_evolution(self, strategy: LearningStrategy) -> str:
        """Format strategy evolution timeline."""
        timeline = [
            f"- **{datetime.fromtimestamp(strategy.created_at).strftime('%Y-%m-%d')}:** Strategy created",
        ]

        if strategy.validation_attempts > 0:
            timeline.append(
                f"- **Validation:** {strategy.validation_successes}/{strategy.validation_attempts} attempts successful"
            )

        if strategy.is_validated:
            timeline.append("- **Status:** ✅ Validated and active")

        return "\n".join(timeline)

    async def _log_strategy_event(
        self, strategy: LearningStrategy, primitive_type: str, event_type: str
    ) -> None:
        """Log strategy event in daily journal."""

        today = datetime.now().strftime("%Y_%m_%d")
        journal_file = self.journals_path / f"{today}.md"

        # Create or append to today's journal
        if journal_file.exists():
            content = journal_file.read_text(encoding="utf-8")
        else:
            content = f"# {datetime.now().strftime('%Y-%m-%d')}\n\n"

        # Add strategy event
        timestamp = datetime.now().strftime("%H:%M")
        event_entry = f"""
## {timestamp} - Strategy {event_type.title()}

- **Strategy:** [[Strategies/{strategy.name}]]
- **Primitive:** [[TTA Primitives/{primitive_type}]]
- **Success Rate:** {strategy.metrics.success_rate:.1%}
- **Executions:** {strategy.metrics.total_executions}
- **Event:** {event_type} #strategy-learning

"""

        content += event_entry
        journal_file.write_text(content, encoding="utf-8")

    async def _update_strategy_network(
        self, strategy: LearningStrategy, primitive_type: str
    ) -> None:
        """Update strategy network visualization."""

        # Create/update strategy network page
        network_file = self.logseq_base_path / "pages" / "Strategy Network.md"

        if network_file.exists():
            content = network_file.read_text(encoding="utf-8")
        else:
            content = """# Strategy Network

This page visualizes the relationships between learned strategies.

## Strategy Graph
"""

        # Add network entry
        network_entry = f"""
### {strategy.name}
- **Type:** {primitive_type}
- **Performance:** {strategy.metrics.success_rate:.1%} success rate
- **Contexts:** {len(strategy.metrics.contexts_seen)}
- **Link:** [[Strategies/{strategy.name}]]
"""

        content += network_entry
        network_file.write_text(content, encoding="utf-8")

    def _update_performance_section(
        self, content: str, strategy: LearningStrategy, execution_result: dict[str, Any]
    ) -> str:
        """Update performance section in existing strategy page."""

        # Find and update performance metrics section
        lines = content.split("\n")
        updated_lines = []
        in_performance_section = False

        for line in lines:
            if line.startswith("## Performance Metrics"):
                in_performance_section = True
                updated_lines.append(line)
                # Add updated metrics
                updated_lines.extend(
                    [
                        f"- **Success Rate:** {strategy.metrics.success_rate:.1%} ({strategy.metrics.success_count}/{strategy.metrics.total_executions})",
                        f"- **Average Latency:** {strategy.metrics.avg_latency:.3f}s",
                        f"- **Total Executions:** {strategy.metrics.total_executions}",
                        f"- **Contexts Seen:** {len(strategy.metrics.contexts_seen)}",
                        f"- **Last Updated:** {datetime.fromtimestamp(strategy.metrics.last_updated).strftime('%Y-%m-%d %H:%M')}",
                    ]
                )
                # Skip old metrics lines
                continue
            elif in_performance_section and line.startswith("##"):
                in_performance_section = False

            if not in_performance_section or not line.startswith("- "):
                updated_lines.append(line)

        return "\n".join(updated_lines)

    def generate_strategy_queries(self) -> dict[str, str]:
        """Generate useful Logseq queries for strategy analysis."""

        return {
            "high_performance_strategies": """{{query (and [[#strategy]] (property success-rate > 0.8))}}""",
            "recent_strategies": """{{query (and [[#strategy]] (between [[7 days ago]] [[today]]))}}""",
            "strategies_by_primitive": {
                "retry": """{{query (and [[#strategy]] [[#retry]])}}""",
                "cache": """{{query (and [[#strategy]] [[#cache]])}}""",
                "routing": """{{query (and [[#strategy]] [[#routing]])}}""",
            },
            "learning_events": """{{query (and [[#strategy-learning]] (between [[today]] [[tomorrow]]))}}""",
            "validation_pending": """{{query (and [[#strategy]] (property validated false))}}""",
        }


# Template for strategy dashboard page
STRATEGY_DASHBOARD_TEMPLATE = """# Strategy Learning Dashboard

**Real-time view of adaptive primitive learning progress**

## 🎯 Performance Summary

### High-Performance Strategies (>80% success rate)
{{query (and [[#strategy]] (property success-rate > 0.8))}}

### Recently Learned (Last 7 days)
{{query (and [[#strategy]] (between [[7 days ago]] [[today]]))}}

### Validation Pending
{{query (and [[#strategy]] (property validated false))}}

## 📊 Strategy Breakdown by Primitive

### Retry Strategies
{{query (and [[#strategy]] [[#retry]])}}

### Cache Strategies
{{query (and [[#strategy]] [[#cache]])}}

### Routing Strategies
{{query (and [[#strategy]] [[#routing]])}}

## 🔍 Learning Activity

### Today's Learning Events
{{query (and [[#strategy-learning]] (between [[today]] [[tomorrow]]))}}

### Strategy Performance Updates
{{query (and [[#strategy-learning]] (property event-type "performance_update"))}}

## 🧠 Learning Insights

### Most Successful Contexts
{{query (and [[#strategy]] (property context-pattern *production*))}}

### Error-Specific Strategies
{{query (and [[#strategy]] (property context-pattern *error*))}}

### Time-Sensitive Optimizations
{{query (and [[#strategy]] (property context-pattern *time_sensitive*))}}

## 📈 Performance Trends

Use these queries to analyze learning trends:

- **Weekly Learning Rate:** How many strategies learned per week?
- **Validation Success Rate:** What percentage of new strategies get validated?
- **Context Diversity:** How many different contexts are we learning from?
- **Performance Improvements:** Are strategies actually improving over baselines?

---
*Auto-updated by Adaptive Primitives Learning System*
"""


# Export classes and templates
__all__ = [
    "LogseqStrategyIntegration",
    "STRATEGY_DASHBOARD_TEMPLATE",
]
