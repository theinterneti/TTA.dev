"""TTA.dev Code Analysis Module.

Shared analysis core for CLI and MCP server.
Provides pattern detection, primitive matching, and recommendation generation.

Usage:
    from primitives.analysis import TTAAnalyzer, AnalysisReport

    analyzer = TTAAnalyzer()
    report = analyzer.analyze(code, file_path="my_file.py")

    # For CLI (human-readable)
    print(report.to_table())

    # For MCP (structured)
    data = report.to_dict()
"""

from primitives.analysis.analyzer import TTAAnalyzer
from primitives.analysis.matcher import PrimitiveMatcher
from primitives.analysis.models import (
    AnalysisReport,
    CodeAnalysisResult,
    PrimitiveRecommendation,
    RecommendationContext,
)
from primitives.analysis.patterns import PatternDetector
from primitives.analysis.templates import TemplateProvider

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
