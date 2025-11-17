#!/usr/bin/env python3
"""
Logseq Integration for Adaptive Primitives

This module provides a LogseqStrategyIntegration class to persist learned
strategies and performance metrics to a Logseq knowledge base.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives.adaptive.base import (
    LearningStrategy,
    StrategyMetrics,
)

logger = logging.getLogger(__name__)


# Helper functions for Logseq filesystem operations
async def create_logseq_page(logseq_path: str, page_title: str, content: str) -> None:
    """
    Creates a Logseq page in the pages directory.

    Args:
        logseq_path: Path to the Logseq graph directory
        page_title: Title of the page (will be used as filename)
        content: Markdown content for the page
    """
    pages_dir = Path(logseq_path) / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename - replace spaces with underscores, keep only safe characters
    safe_filename = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in page_title)
    page_path = pages_dir / f"Strategies____{safe_filename}.md"

    # Write content
    page_path.write_text(content, encoding="utf-8")
    logger.debug(f"Created Logseq page: {page_path}")


async def create_logseq_journal_entry(logseq_path: str, entry: str) -> None:
    """
    Appends an entry to today's Logseq journal.

    Args:
        logseq_path: Path to the Logseq graph directory
        entry: Journal entry content to append
    """
    journals_dir = Path(logseq_path) / "journals"
    journals_dir.mkdir(parents=True, exist_ok=True)

    # Use today's date for journal filename (Logseq format: YYYY_MM_DD.md)
    today = datetime.now().strftime("%Y_%m_%d")
    journal_path = journals_dir / f"{today}.md"

    # Append to journal (or create if doesn't exist)
    with journal_path.open("a", encoding="utf-8") as f:
        f.write(f"\n{entry}\n")
    logger.debug(f"Added entry to Logseq journal: {journal_path}")


class LogseqStrategyIntegration:
    """
    Integrates TTA.dev primitives with Logseq for strategy persistence and discovery.

    This class handles saving learned strategies, performance metrics, and
    learning events to Logseq pages and journals.
    """

    def __init__(self, service_name: str, logseq_path: str | None = None) -> None:
        """
        Initializes the LogseqStrategyIntegration.

        Args:
            service_name: The name of the service or primitive being integrated.
            logseq_path: Optional path to the Logseq graph directory. If not provided,
                         it defaults to a common location or environment variable.
        """
        self.service_name = service_name
        self.logseq_path = logseq_path or os.environ.get("LOGSEQ_GRAPH_PATH", "./logseq")
        logger.info(f"Initializing Logseq integration for '{service_name}' at: {self.logseq_path}")

    async def save_learned_strategy(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        context: str,
        notes: str | None = None,
    ) -> None:
        """
        Saves a newly learned strategy to Logseq.

        Creates a dedicated page for the strategy and logs the learning event.

        Args:
            strategy: The LearningStrategy object to save.
            primitive_type: The type of the primitive (e.g., "AdaptiveRetryPrimitive").
            context: The context in which the strategy was learned.
            notes: Optional additional notes about the learning event.
        """
        page_title = f"{self.service_name}_{strategy.name}"
        page_content = self._format_strategy_page(
            strategy=strategy,
            primitive_type=primitive_type,
            context=context,
            notes=notes,
            service_name=self.service_name,
        )

        try:
            await create_logseq_page(self.logseq_path, page_title, page_content)
            logger.info(f"Saved strategy '{strategy.name}' for '{self.service_name}' to Logseq.")

            # Log the learning event to the daily journal
            journal_entry = self._format_journal_entry(
                strategy_name=strategy.name,
                primitive_type=primitive_type,
                context=context,
                notes=notes,
                event_type="Strategy Learned",
            )
            await create_logseq_journal_entry(self.logseq_path, journal_entry)
            logger.info(f"Logged learning event for '{strategy.name}' to Logseq journal.")

        except Exception as e:
            logger.error(f"Failed to save strategy '{strategy.name}' to Logseq: {e}")

    async def update_strategy_performance(
        self,
        strategy_name: str,
        new_metrics: StrategyMetrics,
        primitive_type: str,
        context: str,
        notes: str | None = None,
    ) -> None:
        """
        Updates the performance metrics of an existing strategy in Logseq.

        Args:
            strategy_name: The name of the strategy to update.
            new_metrics: The updated StrategyMetrics object.
            primitive_type: The type of the primitive.
            context: The context of the strategy.
            notes: Optional notes for the update.
        """
        # In a real implementation, this would involve reading the existing page,
        # appending the new metrics, and writing back. For simplicity, we'll
        # just log the update and create a journal entry.
        logger.info(f"Updating performance for strategy '{strategy_name}' in Logseq.")

        journal_entry = self._format_journal_entry(
            strategy_name=strategy_name,
            primitive_type=primitive_type,
            context=context,
            notes=notes,
            event_type="Strategy Performance Updated",
            metrics=new_metrics,
        )
        try:
            await create_logseq_journal_entry(self.logseq_path, journal_entry)
            logger.info(f"Logged performance update for '{strategy_name}' to Logseq journal.")
        except Exception as e:
            logger.error(f"Failed to update strategy performance in Logseq: {e}")

    def _format_strategy_page(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        context: str,
        notes: str | None,
        service_name: str,
    ) -> str:
        """Formats the content for a Logseq strategy page."""
        # Basic table for performance history - could be more sophisticated
        performance_history_table = f"""
| Date | Success Rate | Avg Latency | Observations |
|------|--------------|-------------|--------------|
| {datetime.now().strftime("%Y-%m-%d")} | {strategy.metrics.success_rate:.1%} | {strategy.metrics.avg_latency_ms:.1f}ms | {strategy.metrics.contexts_seen} |
"""
        # Query for related strategies - adjust query as needed
        related_strategies_query = f"{{query (and [[Strategies]] [[{service_name}]])}}"

        content = f"""
# Strategy - {service_name}_{strategy.name}

**Type:** {primitive_type}
**Context:** {context}
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Performance:** {strategy.metrics.success_rate:.1%} success, {strategy.metrics.avg_latency_ms:.1f}ms avg latency

## Parameters

- name: {strategy.name}
- description: {strategy.description}
{self._format_parameters(strategy.parameters)}

## Performance History
{performance_history_table}

## Related Strategies

{related_strategies_query}

## Notes
{notes if notes else "No additional notes."}
"""
        return content

    def _format_journal_entry(
        self,
        strategy_name: str,
        primitive_type: str,
        context: str,
        notes: str | None,
        event_type: str,
        metrics: StrategyMetrics | None = None,
    ) -> str:
        """Formats a Logseq journal entry for a learning event."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- **{event_type}** for **{strategy_name}** ({primitive_type} in context '{context}') at {timestamp}\n"
        if notes:
            entry += f"  - Notes: {notes}\n"
        if metrics:
            entry += f"  - Metrics: Success Rate={metrics.success_rate:.1%}, Avg Latency={metrics.avg_latency_ms:.1f}ms, Observations={metrics.contexts_seen}\n"
        return entry

    def _format_parameters(self, parameters: dict[str, Any]) -> str:
        """Formats strategy parameters into a markdown list."""
        if not parameters:
            return ""
        param_list = ""
        for key, value in parameters.items():
            param_list += f"- {key}: {value}\n"
        return param_list


# Example Usage (for demonstration purposes, not executed directly)
async def _example_usage() -> None:
    # This is a placeholder to show how the class might be used.
    # In a real scenario, this would be part of an AdaptivePrimitive.

    # Mock data
    mock_strategy = LearningStrategy(
        name="test_strategy_v1",
        description="A test strategy",
        parameters={"timeout": 10, "retries": 2},
        metrics=StrategyMetrics(success_rate=0.95, avg_latency_ms=500, contexts_seen=5),
    )
    mock_metrics = StrategyMetrics(success_rate=0.98, avg_latency_ms=450, contexts_seen=10)

    # Initialize integration
    logseq_integration = LogseqStrategyIntegration("example_service")

    # Save a new strategy
    await logseq_integration.save_learned_strategy(
        strategy=mock_strategy,
        primitive_type="AdaptivePrimitive",
        context="development",
        notes="Initial test strategy.",
    )

    # Update performance of an existing strategy
    await logseq_integration.update_strategy_performance(
        strategy_name="test_strategy_v1",
        new_metrics=mock_metrics,
        primitive_type="AdaptivePrimitive",
        context="development",
        notes="Performance improved.",
    )


if __name__ == "__main__":
    # To run this example, you would need to have Logseq installed and
    # a graph path configured (e.g., via LOGSEQ_GRAPH_PATH env var).
    # You would also need the tta_dev_primitives package installed.
    # import asyncio
    # asyncio.run(_example_usage())
    pass
