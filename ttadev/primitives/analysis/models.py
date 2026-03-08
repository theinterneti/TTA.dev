"""Data models for TTA.dev code analysis.

Pure dataclasses with no external dependencies.
Used by both CLI and MCP server.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CodeAnalysisResult:
    """Result of analyzing code for patterns.

    Attributes:
        detected_patterns: List of pattern names found (e.g., "async_operations", "api_calls")
        inferred_requirements: List of inferred needs (e.g., "error_recovery", "api_resilience")
        complexity_level: Code complexity assessment ("low", "medium", "high")
        performance_critical: Whether performance optimization is likely needed
        error_handling_needed: Whether error recovery patterns are needed
        concurrency_needed: Whether concurrent execution patterns are needed
    """

    detected_patterns: list[str] = field(default_factory=list)
    inferred_requirements: list[str] = field(default_factory=list)
    complexity_level: str = "low"
    performance_critical: bool = False
    error_handling_needed: bool = False
    concurrency_needed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class RecommendationContext:
    """Context for making recommendations.

    Provides additional information about the code being analyzed
    to improve recommendation quality.
    """

    file_path: str = ""
    code_content: str = ""
    project_type: str = "general"  # "web", "api", "data_processing", "ml", "general"
    development_stage: str = "development"  # "development", "testing", "production"
    detected_issues: list[str] = field(default_factory=list)
    optimization_opportunities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class PrimitiveRecommendation:
    """A recommendation for a specific TTA.dev primitive.

    Attributes:
        primitive_name: Name of the recommended primitive (e.g., "RetryPrimitive")
        confidence_score: Confidence level from 0.0 to 1.0
        reasoning: Human-readable explanation for the recommendation
        code_template: Ready-to-use code template
        use_cases: List of example use cases
        related_primitives: Other primitives that work well with this one
        import_path: Python import path for the primitive
    """

    primitive_name: str
    confidence_score: float
    reasoning: str
    code_template: str = ""
    use_cases: list[str] = field(default_factory=list)
    related_primitives: list[str] = field(default_factory=list)
    import_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @property
    def confidence_percent(self) -> str:
        """Confidence as percentage string."""
        return f"{self.confidence_score:.0%}"


@dataclass
class AnalysisReport:
    """Complete analysis report with recommendations.

    This is the main output of TTAAnalyzer.analyze().
    Provides methods for different output formats.
    """

    analysis: CodeAnalysisResult
    recommendations: list[PrimitiveRecommendation]
    context: RecommendationContext
    timestamp: datetime = field(default_factory=datetime.now)
    analyzer_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/MCP output."""
        return {
            "success": True,
            "analysis": self.analysis.to_dict(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "context": self.context.to_dict(),
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "analyzer_version": self.analyzer_version,
                "recommendations_count": len(self.recommendations),
                "highest_confidence": max(
                    (r.confidence_score for r in self.recommendations), default=0.0
                ),
            },
        }

    def to_table(self, min_confidence: float = 0.0) -> str:
        """Format as ASCII table for CLI output.

        Args:
            min_confidence: Minimum confidence to include (0.0 to 1.0)

        Returns:
            Formatted table string
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"TTA.dev Analysis Report - {self.context.file_path or 'unknown'}")
        lines.append("=" * 70)
        lines.append("")

        # Detected patterns
        lines.append("Detected Patterns:")
        if self.analysis.detected_patterns:
            for pattern in self.analysis.detected_patterns:
                lines.append(f"  • {pattern.replace('_', ' ').title()}")
        else:
            lines.append("  (none detected)")
        lines.append("")

        # Recommendations
        lines.append("Recommendations:")
        lines.append("-" * 70)
        lines.append(f"{'Primitive':<25} {'Confidence':<12} {'Reasoning':<30}")
        lines.append("-" * 70)

        filtered = [r for r in self.recommendations if r.confidence_score >= min_confidence]
        if filtered:
            for rec in filtered:
                # Truncate reasoning if too long
                reasoning = rec.reasoning[:27] + "..." if len(rec.reasoning) > 30 else rec.reasoning
                lines.append(
                    f"{rec.primitive_name:<25} {rec.confidence_percent:<12} {reasoning:<30}"
                )
        else:
            lines.append("  (no recommendations above threshold)")

        lines.append("-" * 70)
        lines.append("")

        return "\n".join(lines)

    def get_top_recommendation(self) -> PrimitiveRecommendation | None:
        """Get the highest confidence recommendation."""
        if not self.recommendations:
            return None
        return max(self.recommendations, key=lambda r: r.confidence_score)

    def filter_by_confidence(self, min_confidence: float) -> list[PrimitiveRecommendation]:
        """Get recommendations above a confidence threshold."""
        return [r for r in self.recommendations if r.confidence_score >= min_confidence]
