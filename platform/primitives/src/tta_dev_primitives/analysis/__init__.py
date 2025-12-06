"""TTA.dev Code Analysis Module.

Shared analysis core for CLI and MCP server.
Provides pattern detection, primitive matching, and recommendation generation.

Usage:
    from tta_dev_primitives.analysis import TTAAnalyzer, AnalysisReport

    analyzer = TTAAnalyzer()
    report = analyzer.analyze(code, file_path="my_file.py")

    # For CLI (human-readable)
    print(report.to_table())

    # For MCP (structured)
    data = report.to_dict()
"""

from tta_dev_primitives.analysis.analyzer import TTAAnalyzer
from tta_dev_primitives.analysis.matcher import PrimitiveMatcher
from tta_dev_primitives.analysis.models import (
    AnalysisReport,
    CodeAnalysisResult,
    PrimitiveRecommendation,
    RecommendationContext,
)
from tta_dev_primitives.analysis.patterns import PatternDetector
from tta_dev_primitives.analysis.templates import TemplateProvider

__all__ = [
    # Main entry point
    "TTAAnalyzer",
    # Data models
    "AnalysisReport",
    "CodeAnalysisResult",
    "PrimitiveRecommendation",
    "RecommendationContext",
    # Components (for advanced use)
    "PatternDetector",
    "PrimitiveMatcher",
    "TemplateProvider",
]
