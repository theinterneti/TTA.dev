"""TTAAnalyzer - Main entry point for TTA.dev code analysis.

This is the high-level orchestrator that combines pattern detection,
primitive matching, and template generation into a single API.

Used by both CLI and MCP server.
"""

from datetime import datetime
from typing import Any

import structlog

from tta_dev_primitives.analysis.matcher import PrimitiveMatcher
from tta_dev_primitives.analysis.models import (
    AnalysisReport,
    CodeAnalysisResult,
    PrimitiveRecommendation,
    RecommendationContext,
)
from tta_dev_primitives.analysis.patterns import PatternDetector
from tta_dev_primitives.analysis.templates import TemplateProvider

logger = structlog.get_logger("tta_dev.analysis")


class TTAAnalyzer:
    """Main entry point for TTA.dev code analysis.

    Combines pattern detection, primitive matching, and template generation
    to provide actionable recommendations for improving code with TTA.dev primitives.

    Example:
        analyzer = TTAAnalyzer()

        # Analyze code
        report = analyzer.analyze(code, file_path="api_client.py")

        # Get recommendations
        for rec in report.recommendations:
            print(f"{rec.primitive_name}: {rec.confidence_percent}")
            print(rec.code_template)

        # Output for CLI
        print(report.to_table())

        # Output for MCP/JSON
        data = report.to_dict()
    """

    VERSION = "1.0.0"

    def __init__(self) -> None:
        """Initialize the analyzer with default components."""
        self.pattern_detector = PatternDetector()
        self.primitive_matcher = PrimitiveMatcher()
        self.template_provider = TemplateProvider()

    def analyze(
        self,
        code: str,
        file_path: str = "",
        project_type: str = "general",
        development_stage: str = "development",
        min_confidence: float = 0.3,
    ) -> AnalysisReport:
        """Analyze code and generate recommendations.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context
            project_type: Type of project ("web", "api", "data_processing", "ml", "general")
            development_stage: Stage ("development", "testing", "production")
            min_confidence: Minimum confidence for recommendations (0.0 to 1.0)

        Returns:
            AnalysisReport with patterns, recommendations, and metadata
        """
        log = logger.bind(file_path=file_path, project_type=project_type)
        log.debug("starting_analysis", code_length=len(code))

        # Step 1: Detect patterns in the code
        analysis = self.pattern_detector.analyze(code, file_path)
        log.debug("patterns_detected", patterns=analysis.detected_patterns)

        # Step 2: Create context for matching
        context = RecommendationContext(
            file_path=file_path,
            code_content=code,
            project_type=project_type,
            development_stage=development_stage,
            detected_issues=self._detect_issues(code, analysis),
            optimization_opportunities=self._detect_optimizations(code, analysis),
        )

        # Step 3: Find matching primitives
        matches = self.primitive_matcher.find_matches(
            analysis, context, min_confidence=min_confidence
        )
        log.debug("primitives_matched", matches=len(matches))

        # Step 4: Build recommendations with templates
        recommendations = [
            self._build_recommendation(name, score, analysis) for name, score in matches
        ]

        log.info(
            "analysis_complete",
            patterns_found=len(analysis.detected_patterns),
            recommendations=len(recommendations),
            complexity=analysis.complexity_level,
        )

        return AnalysisReport(
            analysis=analysis,
            recommendations=recommendations,
            context=context,
            timestamp=datetime.now(),
            analyzer_version=self.VERSION,
        )

    def analyze_file(
        self,
        file_path: str,
        **kwargs: Any,
    ) -> AnalysisReport:
        """Analyze a file by path.

        Args:
            file_path: Path to the file to analyze
            **kwargs: Additional arguments passed to analyze()

        Returns:
            AnalysisReport

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        with open(file_path) as f:
            code = f.read()

        return self.analyze(code, file_path=file_path, **kwargs)

    def _build_recommendation(
        self,
        primitive_name: str,
        confidence: float,
        analysis: CodeAnalysisResult,
    ) -> PrimitiveRecommendation:
        """Build a complete recommendation with template and examples."""
        # Get primitive info from matcher
        info = self.primitive_matcher.get_primitive_info(primitive_name) or {}

        # Get template
        template = self.template_provider.get_template(primitive_name) or ""

        # Get examples
        examples = self.template_provider.get_examples(primitive_name)

        # Get related primitives
        related = self.primitive_matcher.get_related_primitives(primitive_name)

        # Generate reasoning
        reasoning = self._generate_reasoning(primitive_name, analysis, info)

        return PrimitiveRecommendation(
            primitive_name=primitive_name,
            confidence_score=confidence,
            reasoning=reasoning,
            code_template=template,
            use_cases=examples,
            related_primitives=related,
            import_path=info.get("import_path", ""),
        )

    def _generate_reasoning(
        self,
        primitive_name: str,
        analysis: CodeAnalysisResult,
        info: dict[str, Any],
    ) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []

        # Check which patterns triggered this recommendation
        primitive_patterns = info.get("patterns", [])
        matched_patterns = [p for p in analysis.detected_patterns if p in primitive_patterns]

        if matched_patterns:
            pattern_names = [p.replace("_", " ") for p in matched_patterns]
            reasons.append(f"Found {', '.join(pattern_names)}")

        # Add requirement-based reasons
        requirements = info.get("requirements", [])
        matched_reqs = [r for r in analysis.inferred_requirements if r in requirements]

        if "api_resilience" in matched_reqs:
            reasons.append("API calls need protection")
        if "error_recovery" in matched_reqs:
            reasons.append("Error handling can be improved")
        if "performance_optimization" in matched_reqs:
            reasons.append("Performance optimization opportunity")
        if "concurrent_execution" in matched_reqs:
            reasons.append("Concurrency patterns detected")

        # Fallback if no specific reasons
        if not reasons:
            description = info.get("description", "")
            if description:
                reasons.append(description)
            else:
                reasons.append("Matches code patterns")

        return "; ".join(reasons[:2])  # Limit to 2 reasons for brevity

    def _detect_issues(
        self,
        code: str,
        analysis: CodeAnalysisResult,
    ) -> list[str]:
        """Detect potential issues in the code."""
        issues = []

        # Check for API calls without error handling
        if "api_calls" in analysis.detected_patterns:
            if "error_handling" not in analysis.detected_patterns:
                issues.append("API calls without explicit error handling")

        # Check for async without timeout
        if "async_operations" in analysis.detected_patterns:
            if "timeout_patterns" not in analysis.detected_patterns:
                issues.append("Async operations without timeout protection")

        # Check for retry loops without backoff
        if "retry_patterns" in analysis.detected_patterns:
            if "exponential" not in code.lower() and "backoff" not in code.lower():
                issues.append("Retry logic may lack exponential backoff")

        return issues

    def _detect_optimizations(
        self,
        code: str,
        analysis: CodeAnalysisResult,
    ) -> list[str]:
        """Detect optimization opportunities."""
        opportunities = []

        # LLM calls could benefit from caching
        if "llm_patterns" in analysis.detected_patterns:
            if "caching_patterns" not in analysis.detected_patterns:
                opportunities.append("LLM calls could be cached to reduce costs")

        # Multiple API calls could be parallelized
        if "api_calls" in analysis.detected_patterns:
            if "parallel_patterns" not in analysis.detected_patterns:
                # Count potential parallel opportunities
                import re

                api_calls = len(re.findall(r"(requests\.|httpx\.|aiohttp|\.get\(|\.post\()", code))
                if api_calls >= 2:
                    opportunities.append(f"Found {api_calls} API calls that could be parallelized")

        return opportunities

    def get_primitive_info(self, primitive_name: str) -> dict[str, Any]:
        """Get detailed information about a specific primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dict with primitive details including all templates
        """
        info = self.primitive_matcher.get_primitive_info(primitive_name)
        if not info:
            return {"error": f"Unknown primitive: {primitive_name}"}

        templates = self.template_provider.get_all_templates(primitive_name)
        examples = self.template_provider.get_examples(primitive_name)

        return {
            "name": primitive_name,
            "description": info.get("description", ""),
            "import_path": info.get("import_path", ""),
            "use_cases": info.get("use_cases", []),
            "related_primitives": info.get("related_primitives", []),
            "templates": templates,
            "examples": examples,
        }

    def list_primitives(self) -> list[dict[str, Any]]:
        """List all available primitives.

        Returns:
            List of primitive info dicts
        """
        return self.primitive_matcher.list_primitives()

    def search_templates(self, query: str) -> list[dict[str, Any]]:
        """Search templates by keyword.

        Args:
            query: Search query

        Returns:
            List of matching template info
        """
        return self.template_provider.search_templates(query)
