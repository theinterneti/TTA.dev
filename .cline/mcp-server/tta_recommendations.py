#!/usr/bin/env python3
"""
TTA.dev MCP Server for Automatic Primitive Recommendations

This MCP server provides intelligent, context-aware recommendations for TTA.dev primitives
based on code patterns and development tasks. It revolutionizes how clines discover and
use TTA.dev primitives by offering automatic suggestions.

Key Features:
- Automatic primitive detection from code patterns
- Context-aware recommendations based on development tasks
- Dynamic template loading system
- Performance metrics collection
- Sub-100ms response time target
"""

import asyncio
import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any

# MCP server imports
try:
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
except ImportError:
    # Fallback for development/testing
    Server = None
    types = None


@dataclass
class PrimitiveRecommendation:
    """Recommendation for a specific primitive"""

    primitive_name: str
    confidence_score: float
    reasoning: str
    code_template: str
    use_cases: list[str]
    related_primitives: list[str]
    example_files: list[str]


@dataclass
class CodeAnalysisResult:
    """Result of code pattern analysis"""

    detected_patterns: list[str]
    inferred_requirements: list[str]
    complexity_level: str
    performance_critical: bool
    error_handling_needed: bool
    concurrency_needed: bool


@dataclass
class RecommendationContext:
    """Context for making recommendations"""

    file_path: str
    code_content: str
    project_type: str
    development_stage: str
    detected_issues: list[str]
    optimization_opportunities: list[str]


class PatternDetector:
    """Detects code patterns and requirements from source code"""

    def __init__(self):
        self.patterns = {
            "async_operations": [
                r"async def",
                r"await\s+",
                r"asyncio\.",
                r"gather\(",
                r"create_task\(",
            ],
            "error_handling": [
                r"try:",
                r"except\s+",
                r"raise\s+",
                r"finally:",
                r"TimeoutError",
                r"ConnectionError",
            ],
            "api_calls": [r"requests\.", r"aiohttp", r"httpx", r"fetch\(", r"curl"],
            "data_processing": [
                r"for\s+\w+\s+in\s+",
                r"map\(",
                r"filter\(",
                r"list\(\w+\)",
                r"\[\w+\s+for\s+\w+\s+in",
            ],
            "caching_patterns": [
                r"cache",
                r"memoize",
                r"lru_cache",
                r"@cached",
                r"get.*cache",
                r"set.*cache",
            ],
            "timeout_patterns": [
                r"timeout",
                r"asyncio\.wait_for",
                r"signal\.alarm",
                r"deadline",
            ],
            "retry_patterns": [
                r"retry",
                r"backoff",
                r"exponential",
                r"for\s+i\s+in\s+range",
                r"max_retries",
            ],
            "fallback_patterns": [
                r"fallback",
                r"backup",
                r"alternative",
                r"default.*response",
            ],
            "parallel_patterns": [
                r"asyncio\.gather\(",
                r"concurrent\.futures",
                r"ThreadPoolExecutor",
                r"ProcessPoolExecutor",
            ],
            "routing_patterns": [
                r"if.*==.*:",
                r"switch",
                r"match",
                r"route",
                r"select.*provider",
            ],
        }

    def analyze_code(self, code: str, file_path: str) -> CodeAnalysisResult:
        """Analyze code and detect patterns"""
        detected_patterns = []
        inferred_requirements = []

        # Detect patterns
        for pattern_name, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    detected_patterns.append(pattern_name)
                    break

        # Infer requirements from patterns
        if "async_operations" in detected_patterns:
            inferred_requirements.append("asynchronous_processing")

        if "error_handling" in detected_patterns:
            inferred_requirements.append("error_recovery")

        if "api_calls" in detected_patterns:
            inferred_requirements.append("api_resilience")

        if "caching_patterns" in detected_patterns:
            inferred_requirements.append("performance_optimization")

        if "timeout_patterns" in detected_patterns:
            inferred_requirements.append("timeout_handling")

        if "retry_patterns" in detected_patterns:
            inferred_requirements.append("retry_logic")

        if "fallback_patterns" in detected_patterns:
            inferred_requirements.append("fallback_strategy")

        if "parallel_patterns" in detected_patterns:
            inferred_requirements.append("concurrent_execution")

        if "routing_patterns" in detected_patterns:
            inferred_requirements.append("intelligent_routing")

        # Determine complexity level
        complexity_level = self._assess_complexity(code, detected_patterns)

        # Assess criticality
        performance_critical = "performance_optimization" in inferred_requirements
        error_handling_needed = "error_recovery" in inferred_requirements
        concurrency_needed = "concurrent_execution" in inferred_requirements

        return CodeAnalysisResult(
            detected_patterns=detected_patterns,
            inferred_requirements=inferred_requirements,
            complexity_level=complexity_level,
            performance_critical=performance_critical,
            error_handling_needed=error_handling_needed,
            concurrency_needed=concurrency_needed,
        )

    def _assess_complexity(self, code: str, patterns: list[str]) -> str:
        """Assess code complexity level"""
        lines_of_code = len([line for line in code.split("\n") if line.strip()])
        pattern_count = len(patterns)

        if lines_of_code > 200 or pattern_count >= 6:
            return "high"
        elif lines_of_code > 50 or pattern_count >= 3:
            return "medium"
        else:
            return "low"


class PrimitiveMatcher:
    """Matches requirements to appropriate TTA.dev primitives"""

    def __init__(self):
        self.primitive_catalog = {
            "TimeoutPrimitive": {
                "requirements": ["timeout_handling", "api_resilience"],
                "patterns": ["timeout_patterns", "async_operations"],
                "use_cases": [
                    "API calls that may hang",
                    "Database queries with time limits",
                    "Webhook processing",
                    "Long-running operations",
                ],
                "confidence_factors": {
                    "timeout_handling": 0.9,
                    "api_resilience": 0.7,
                    "async_operations": 0.5,
                },
            },
            "ParallelPrimitive": {
                "requirements": ["concurrent_execution", "performance_optimization"],
                "patterns": ["parallel_patterns", "async_operations"],
                "use_cases": [
                    "Multiple API calls",
                    "Data processing pipelines",
                    "Concurrent LLM calls",
                    "Batch processing",
                ],
                "confidence_factors": {
                    "concurrent_execution": 0.9,
                    "performance_optimization": 0.8,
                    "async_operations": 0.6,
                },
            },
            "RouterPrimitive": {
                "requirements": ["intelligent_routing"],
                "patterns": ["routing_patterns"],
                "use_cases": [
                    "Multi-provider selection",
                    "Cost optimization",
                    "Performance-based routing",
                    "Geographic routing",
                ],
                "confidence_factors": {"intelligent_routing": 0.95},
            },
            "CachePrimitive": {
                "requirements": ["performance_optimization"],
                "patterns": ["caching_patterns"],
                "use_cases": [
                    "Expensive computations",
                    "API response caching",
                    "Data lookup optimization",
                    "Session management",
                ],
                "confidence_factors": {
                    "performance_optimization": 0.8,
                    "caching_patterns": 0.7,
                },
            },
            "RetryPrimitive": {
                "requirements": ["retry_logic", "error_recovery"],
                "patterns": ["retry_patterns", "error_handling"],
                "use_cases": [
                    "Unstable API calls",
                    "Network issues",
                    "Rate limiting",
                    "Temporary failures",
                ],
                "confidence_factors": {
                    "retry_logic": 0.9,
                    "error_recovery": 0.8,
                    "error_handling": 0.6,
                },
            },
            "FallbackPrimitive": {
                "requirements": ["fallback_strategy", "error_recovery"],
                "patterns": ["fallback_patterns", "error_handling"],
                "use_cases": [
                    "Service degradation",
                    "Graceful degradation",
                    "Multiple providers",
                    "Circuit breaker pattern",
                ],
                "confidence_factors": {
                    "fallback_strategy": 0.9,
                    "error_recovery": 0.7,
                    "error_handling": 0.5,
                },
            },
            "SequentialPrimitive": {
                "requirements": ["asynchronous_processing"],
                "patterns": ["async_operations"],
                "use_cases": [
                    "Step-by-step workflows",
                    "Data processing pipelines",
                    "Multi-stage operations",
                    "Chained operations",
                ],
                "confidence_factors": {"asynchronous_processing": 0.7},
            },
        }

    def find_matches(
        self, analysis: CodeAnalysisResult, context: RecommendationContext
    ) -> list[tuple[str, float]]:
        """Find matching primitives with confidence scores"""
        matches = []

        for primitive_name, info in self.primitive_catalog.items():
            score = 0.0

            # Score based on requirements match
            for requirement in analysis.inferred_requirements:
                if requirement in info["confidence_factors"]:
                    score += info["confidence_factors"][requirement]

            # Bonus for pattern matches
            pattern_bonus = 0
            for pattern in analysis.detected_patterns:
                if pattern in info["patterns"]:
                    pattern_bonus += 0.1
            score += pattern_bonus

            # Context bonuses
            if analysis.performance_critical and "performance_optimization" in info.get(
                "requirements", []
            ):
                score += 0.2

            if analysis.error_handling_needed and "error_recovery" in info.get(
                "requirements", []
            ):
                score += 0.15

            if analysis.concurrency_needed and "concurrent_execution" in info.get(
                "requirements", []
            ):
                score += 0.2

            # Normalize score
            max_possible_score = len(analysis.inferred_requirements) * 0.9 + 0.5
            normalized_score = (
                min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
            )

            if normalized_score > 0.3:  # Minimum threshold
                matches.append((primitive_name, normalized_score))

        # Sort by confidence score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


class TemplateProvider:
    """Provides code templates and examples for primitives"""

    def __init__(self):
        self.templates = {
            "TimeoutPrimitive": {
                "basic_template": """from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create timeout primitive
timeout_primitive = TimeoutPrimitive(
    primitive=your_function,
    timeout_seconds=30.0,
    fallback=fallback_function,
    track_timeouts=True
)

# Use in workflow
context = WorkflowContext(workflow_id="timeout_example")
result = await timeout_primitive.execute(data, context)""",
                "circuit_breaker_template": """from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext

class CircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.failure_threshold = 5
        self.timeout_primitive = TimeoutPrimitive(
            primitive=self._api_call,
            timeout_seconds=30.0,
            track_timeouts=True
        )

    async def call_with_protection(self, data):
        context = WorkflowContext(workflow_id="circuit_breaker")
        return await self.timeout_primitive.execute(data, context)""",
                "examples": [
                    "Circuit breaker for API resilience",
                    "Database query timeouts",
                    "Webhook processing with timeout",
                    "LLM call with fallback",
                ],
            },
            "ParallelPrimitive": {
                "basic_template": """from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create parallel execution
parallel_workflow = ParallelPrimitive([
    function1,
    function2,
    function3
])

# Use in workflow
context = WorkflowContext(workflow_id="parallel_example")
results = await parallel_workflow.execute(data, context)

# Or use the | operator
workflow = function1 | function2 | function3""",
                "examples": [
                    "Concurrent LLM calls",
                    "Multiple API aggregations",
                    "Parallel data processing",
                    "Multi-provider comparisons",
                ],
            },
            "RouterPrimitive": {
                "basic_template": """from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create router
router = RouterPrimitive(
    routes={
        "provider_a": service_a,
        "provider_b": service_b,
        "local": local_service
    },
    router_fn=lambda data, ctx: routing_logic(data, ctx),
    default="local"
)

# Use in workflow
context = WorkflowContext(workflow_id="routing_example")
result = await router.execute(data, context)""",
                "examples": [
                    "Cost-optimized provider selection",
                    "Performance-based routing",
                    "Geographic routing",
                    "Intelligent request routing",
                ],
            },
            "CachePrimitive": {
                "basic_template": """from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create cache primitive
cached_function = CachePrimitive(
    primitive=expensive_function,
    ttl_seconds=3600,  # 1 hour
    max_size=1000,
    key_fn=lambda data, ctx: generate_cache_key(data, ctx)
)

# Use in workflow
context = WorkflowContext(workflow_id="cache_example")
result = await cached_function.execute(data, context)""",
                "examples": [
                    "API response caching",
                    "Expensive computation caching",
                    "Data lookup optimization",
                    "Session data caching",
                ],
            },
        }

    def get_template(
        self, primitive_name: str, template_type: str = "basic"
    ) -> str | None:
        """Get code template for a primitive"""
        if primitive_name in self.templates:
            return self.templates[primitive_name].get(template_type + "_template")
        return None

    def get_examples(self, primitive_name: str) -> list[str]:
        """Get example use cases for a primitive"""
        if primitive_name in self.templates:
            return self.templates[primitive_name].get("examples", [])
        return []


class TTAdevMCPService:
    """Main TTA.dev MCP service for primitive recommendations"""

    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.primitive_matcher = PrimitiveMatcher()
        self.template_provider = TemplateProvider()
        self.metrics = {
            "total_recommendations": 0,
            "average_response_time": 0.0,
            "confidence_scores": [],
            "popular_primitives": {},
        }
        self.performance_history = []

    async def get_primitive_recommendations(
        self,
        code: str,
        file_path: str = "unknown",
        project_type: str = "general",
        development_stage: str = "development",
    ) -> dict[str, Any]:
        """Get intelligent primitive recommendations"""
        start_time = time.time()

        try:
            # Analyze code patterns
            analysis = self.pattern_detector.analyze_code(code, file_path)

            # Create recommendation context
            context = RecommendationContext(
                file_path=file_path,
                code_content=code,
                project_type=project_type,
                development_stage=development_stage,
                detected_issues=self._detect_issues(code),
                optimization_opportunities=self._detect_optimizations(code, analysis),
            )

            # Find matching primitives
            matches = self.primitive_matcher.find_matches(analysis, context)

            # Create recommendations
            recommendations = []
            for primitive_name, confidence in matches:
                template = self.template_provider.get_template(primitive_name)
                examples = self.template_provider.get_examples(primitive_name)

                # Find related primitives
                related = self._find_related_primitives(primitive_name, analysis)

                recommendation = PrimitiveRecommendation(
                    primitive_name=primitive_name,
                    confidence_score=confidence,
                    reasoning=self._generate_reasoning(
                        primitive_name, analysis, context
                    ),
                    code_template=template or "",
                    use_cases=examples,
                    related_primitives=related,
                    example_files=self._find_example_files(primitive_name),
                )
                recommendations.append(recommendation)

            # Update metrics
            response_time = (time.time() - start_time) * 1000  # ms
            self._update_metrics(recommendations, response_time)

            return {
                "success": True,
                "recommendations": [asdict(rec) for rec in recommendations],
                "analysis": asdict(analysis),
                "context": asdict(context),
                "metrics": {
                    "response_time_ms": response_time,
                    "recommendations_count": len(recommendations),
                    "highest_confidence": max(
                        [r.confidence_score for r in recommendations]
                    )
                    if recommendations
                    else 0.0,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000,
            }

    async def get_primitive_info(self, primitive_name: str) -> dict[str, Any]:
        """Get detailed information about a specific primitive"""
        template = self.template_provider.get_template(primitive_name)
        examples = self.template_provider.get_examples(primitive_name)

        return {
            "primitive_name": primitive_name,
            "template": template,
            "examples": examples,
            "documentation_path": f".cline/examples/primitives/{primitive_name.lower()}.md",
        }

    async def search_examples(self, query: str) -> list[dict[str, Any]]:
        """Search for examples based on query"""
        # Simple search implementation
        # In production, this would use more sophisticated search
        results = []

        for primitive_name, info in self.template_provider.templates.items():
            if any(
                query.lower() in example.lower() for example in info.get("examples", [])
            ):
                results.append(
                    {
                        "primitive_name": primitive_name,
                        "matched_examples": [
                            ex
                            for ex in info.get("examples", [])
                            if query.lower() in ex.lower()
                        ],
                        "template_preview": info.get("basic_template", "")[:200]
                        + "...",
                    }
                )

        return results

    def _detect_issues(self, code: str) -> list[str]:
        """Detect potential issues in code"""
        issues = []

        # Check for common issues
        if "time.sleep" in code and "async" in code:
            issues.append(
                "Blocking sleep in async function - use asyncio.sleep instead"
            )

        if "except:" in code and "Exception" not in code:
            issues.append("Bare except clause - specify exception types")

        if "while True:" in code and "break" not in code:
            issues.append("Potential infinite loop detected")

        if "requests." in code and "timeout" not in code:
            issues.append("API calls without timeout - consider TimeoutPrimitive")

        if "for i in range" in code and "retry" in code.lower():
            issues.append("Manual retry loop detected - consider RetryPrimitive")

        return issues

    def _detect_optimizations(
        self, code: str, analysis: CodeAnalysisResult
    ) -> list[str]:
        """Detect optimization opportunities"""
        optimizations = []

        if analysis.performance_critical:
            optimizations.append("Consider CachePrimitive for expensive operations")

        if analysis.concurrency_needed:
            optimizations.append("Consider ParallelPrimitive for concurrent operations")

        if analysis.error_handling_needed:
            optimizations.append(
                "Consider RetryPrimitive or FallbackPrimitive for resilience"
            )

        if "api" in code.lower() and "timeout" not in code.lower():
            optimizations.append("Add timeout handling with TimeoutPrimitive")

        if analysis.inferred_requirements and len(analysis.inferred_requirements) > 3:
            optimizations.append(
                "Consider wrapping in SequentialPrimitive for complex workflows"
            )

        return optimizations

    def _find_related_primitives(
        self, primitive_name: str, analysis: CodeAnalysisResult
    ) -> list[str]:
        """Find related primitives that work well together"""
        relationships = {
            "TimeoutPrimitive": [
                "RetryPrimitive",
                "FallbackPrimitive",
                "CachePrimitive",
            ],
            "ParallelPrimitive": ["TimeoutPrimitive", "CachePrimitive"],
            "RouterPrimitive": ["TimeoutPrimitive", "FallbackPrimitive"],
            "CachePrimitive": ["TimeoutPrimitive", "SequentialPrimitive"],
            "RetryPrimitive": ["TimeoutPrimitive", "FallbackPrimitive"],
            "FallbackPrimitive": ["TimeoutPrimitive", "RouterPrimitive"],
            "SequentialPrimitive": ["CachePrimitive", "ParallelPrimitive"],
        }

        related = relationships.get(primitive_name, [])

        # Filter based on current analysis
        if "performance_optimization" not in analysis.inferred_requirements:
            related = [r for r in related if r != "CachePrimitive"]

        if "error_recovery" not in analysis.inferred_requirements:
            related = [
                r for r in related if r not in ["RetryPrimitive", "FallbackPrimitive"]
            ]

        return related

    def _generate_reasoning(
        self,
        primitive_name: str,
        analysis: CodeAnalysisResult,
        context: RecommendationContext,
    ) -> str:
        """Generate reasoning for the recommendation"""
        reasoning_parts = []

        if primitive_name == "TimeoutPrimitive":
            if "timeout_handling" in analysis.inferred_requirements:
                reasoning_parts.append("Detected timeout-related patterns in your code")
            if "api_resilience" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "API calls detected - timeouts prevent hanging operations"
                )

        elif primitive_name == "ParallelPrimitive":
            if "concurrent_execution" in analysis.inferred_requirements:
                reasoning_parts.append("Parallel execution patterns detected")
            if "performance_optimization" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Performance optimization needed - parallel execution can help"
                )

        elif primitive_name == "RouterPrimitive":
            if "intelligent_routing" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Routing logic detected - RouterPrimitive can optimize selection"
                )

        elif primitive_name == "CachePrimitive":
            if "performance_optimization" in analysis.inferred_requirements:
                reasoning_parts.append("Performance optimization opportunity detected")

        elif primitive_name == "RetryPrimitive":
            if "retry_logic" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Retry patterns detected - automatic retry logic recommended"
                )
            if "error_recovery" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Error handling needed - RetryPrimitive provides resilience"
                )

        elif primitive_name == "FallbackPrimitive":
            if "fallback_strategy" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Fallback patterns detected - graceful degradation recommended"
                )

        elif primitive_name == "SequentialPrimitive":
            if "asynchronous_processing" in analysis.inferred_requirements:
                reasoning_parts.append(
                    "Async operations detected - SequentialPrimitive for workflow composition"
                )

        if not reasoning_parts:
            reasoning_parts.append(
                f"Based on code patterns and {analysis.complexity_level} complexity level"
            )

        return ". ".join(reasoning_parts) + "."

    def _find_example_files(self, primitive_name: str) -> list[str]:
        """Find example files for a primitive"""
        examples = {
            "TimeoutPrimitive": [".cline/examples/primitives/timeout_primitive.md"],
            "ParallelPrimitive": [".cline/examples/primitives/parallel_primitive.md"],
            "RouterPrimitive": [".cline/examples/primitives/router_primitive.md"],
            "CachePrimitive": [".cline/examples/primitives/cache_primitive.md"],
            "RetryPrimitive": [".cline/examples/primitives/retry_primitive.md"],
            "FallbackPrimitive": [".cline/examples/primitives/fallback_primitive.md"],
            "SequentialPrimitive": [
                ".cline/examples/primitives/sequential_primitive.md"
            ],
        }

        return examples.get(primitive_name, [])

    def _update_metrics(
        self, recommendations: list[PrimitiveRecommendation], response_time: float
    ):
        """Update performance metrics"""
        self.metrics["total_recommendations"] += 1

        # Update average response time
        current_avg = self.metrics["average_response_time"]
        total_requests = self.metrics["total_recommendations"]
        self.metrics["average_response_time"] = (
            current_avg * (total_requests - 1) + response_time
        ) / total_requests

        # Store confidence scores
        for rec in recommendations:
            self.metrics["confidence_scores"].append(rec.confidence_score)
            self.metrics["popular_primitives"][rec.primitive_name] = (
                self.metrics["popular_primitives"].get(rec.primitive_name, 0) + 1
            )

        # Keep performance history (last 100 requests)
        self.performance_history.append(response_time)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics"""
        return {
            "total_recommendations": self.metrics["total_recommendations"],
            "average_response_time_ms": self.metrics["average_response_time"],
            "performance_history": self.performance_history[-10:],  # Last 10 requests
            "popular_primitives": dict(
                sorted(
                    self.metrics["popular_primitives"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ),
            "average_confidence": sum(self.metrics["confidence_scores"])
            / len(self.metrics["confidence_scores"])
            if self.metrics["confidence_scores"]
            else 0.0,
        }


# MCP Server Implementation
if Server is not None:
    app = Server("tta-dev-primitive-recommendations")
    tta_service = TTAdevMCPService()

    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="get_primitive_recommendations",
                description="Get intelligent TTA.dev primitive recommendations based on code analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Source code to analyze for primitive recommendations",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path for context (optional)",
                        },
                        "project_type": {
                            "type": "string",
                            "description": "Type of project (web, api, data_processing, etc.)",
                            "enum": ["web", "api", "data_processing", "ml", "general"],
                        },
                        "development_stage": {
                            "type": "string",
                            "description": "Current development stage",
                            "enum": ["development", "testing", "production"],
                        },
                    },
                    "required": ["code"],
                },
            ),
            types.Tool(
                name="get_primitive_info",
                description="Get detailed information about a specific TTA.dev primitive",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "primitive_name": {
                            "type": "string",
                            "description": "Name of the primitive to get info about",
                        }
                    },
                    "required": ["primitive_name"],
                },
            ),
            types.Tool(
                name="search_examples",
                description="Search for TTA.dev primitive examples",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for examples",
                        }
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="get_performance_metrics",
                description="Get MCP server performance metrics",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool calls"""
        try:
            if name == "get_primitive_recommendations":
                result = await tta_service.get_primitive_recommendations(
                    code=arguments["code"],
                    file_path=arguments.get("file_path", "unknown"),
                    project_type=arguments.get("project_type", "general"),
                    development_stage=arguments.get("development_stage", "development"),
                )

                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            elif name == "get_primitive_info":
                result = await tta_service.get_primitive_info(
                    primitive_name=arguments["primitive_name"]
                )

                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            elif name == "search_examples":
                result = await tta_service.search_examples(query=arguments["query"])

                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            elif name == "get_performance_metrics":
                result = tta_service.get_performance_metrics()

                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def main():
        """Main entry point for MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="tta-dev-primitive-recommendations",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={},
                    ),
                ),
            )


if __name__ == "__main__":
    if Server is not None:
        asyncio.run(main())
    else:
        # Development/testing mode
        async def test_service():
            service = TTAdevMCPService()

            # Test code
            test_code = """
import asyncio
import requests

async def call_api():
    response = requests.get("https://api.example.com/data")
    return response.json()

async def process_data():
    data = await call_api()
    return [item for item in data if item['active']]
"""

            result = await service.get_primitive_recommendations(test_code, "test.py")
            print(json.dumps(result, indent=2))

            # Test performance
            metrics = service.get_performance_metrics()
            print(f"Response time: {metrics['average_response_time_ms']:.2f}ms")

        asyncio.run(test_service())
