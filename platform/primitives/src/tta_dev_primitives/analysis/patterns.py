"""Pattern detection for TTA.dev code analysis.

Detects code patterns using regex matching to identify
opportunities for TTA.dev primitives.
"""

import re
from typing import Any

from tta_dev_primitives.analysis.models import CodeAnalysisResult


class PatternDetector:
    """Detects code patterns and requirements from source code.

    Uses regex-based pattern matching to identify:
    - Async operations
    - Error handling patterns
    - API calls
    - Caching patterns
    - Retry logic
    - And more...

    Example:
        detector = PatternDetector()
        result = detector.analyze("async def fetch(): await api.get(...)")
        print(result.detected_patterns)  # ["async_operations", "api_calls"]
    """

    def __init__(self) -> None:
        """Initialize with default pattern definitions."""
        self.patterns: dict[str, list[str]] = {
            "async_operations": [
                r"async def",
                r"await\s+",
                r"asyncio\.",
                r"gather\(",
                r"create_task\(",
                r"TaskGroup",
                r"anyio\.",
            ],
            "error_handling": [
                r"try:",
                r"except\s+",
                r"raise\s+",
                r"finally:",
                r"TimeoutError",
                r"ConnectionError",
                r"Exception\s*:",
                r"BaseException",
            ],
            "api_calls": [
                r"requests\.",
                r"aiohttp",
                r"httpx",
                r"fetch\(",
                r"\.get\(",
                r"\.post\(",
                r"urllib",
                r"client\.",
                r"session\.",
            ],
            "data_processing": [
                r"for\s+\w+\s+in\s+",
                r"map\(",
                r"filter\(",
                r"list\(\w+\)",
                r"\[\w+\s+for\s+\w+\s+in",
                r"pandas",
                r"\.apply\(",
                r"\.transform\(",
            ],
            "caching_patterns": [
                r"cache",
                r"memoize",
                r"lru_cache",
                r"@cached",
                r"get.*cache",
                r"set.*cache",
                r"redis",
                r"memcached",
            ],
            "timeout_patterns": [
                r"timeout",
                r"asyncio\.wait_for",
                r"signal\.alarm",
                r"deadline",
                r"max_time",
                r"time_limit",
            ],
            "retry_patterns": [
                r"retry",
                r"backoff",
                r"exponential",
                r"max_retries",
                r"attempt",
                r"tenacity",
                r"retrying",
            ],
            "fallback_patterns": [
                r"fallback",
                r"backup",
                r"alternative",
                r"default.*response",
                r"or\s+default",
                r"except.*return",
                r"fail.*safe",
            ],
            "parallel_patterns": [
                r"asyncio\.gather\(",
                r"concurrent\.futures",
                r"ThreadPoolExecutor",
                r"ProcessPoolExecutor",
                r"multiprocessing",
                r"ray\.",
                r"dask\.",
            ],
            "routing_patterns": [
                r"if.*==.*:",
                r"match\s+\w+:",
                r"route",
                r"select.*provider",
                r"switch",
                r"dispatch",
                r"router",
            ],
            "llm_patterns": [
                r"openai",
                r"anthropic",
                r"langchain",
                r"llm",
                r"chat.*completion",
                r"generate\(",
                r"google.*genai",
                r"gemini",
                r"claude",
                r"gpt",
                r"embedding",
            ],
            "database_patterns": [
                r"cursor\.",
                r"execute\(",
                r"SELECT\s+",
                r"INSERT\s+",
                r"sqlalchemy",
                r"\.query\(",
                r"prisma",
                r"supabase",
                r"mongodb",
                r"postgres",
            ],
            # New patterns for better detection
            "rate_limiting": [
                r"rate.*limit",
                r"throttle",
                r"ratelimit",
                r"Too Many Requests",
                r"429",
                r"quota",
                r"tokens.*per.*minute",
            ],
            "streaming_patterns": [
                r"yield\s+",
                r"async.*for",
                r"stream",
                r"iter\(",
                r"__aiter__",
                r"__anext__",
                r"AsyncIterator",
                r"generator",
            ],
            "validation_patterns": [
                r"validate",
                r"pydantic",
                r"schema",
                r"assert\s+",
                r"isinstance\(",
                r"type.*check",
                r"\.model_validate",
            ],
            "logging_patterns": [
                r"logging\.",
                r"logger\.",
                r"\.info\(",
                r"\.debug\(",
                r"\.error\(",
                r"structlog",
                r"print\(",
            ],
            "configuration_patterns": [
                r"environ",
                r"\.env",
                r"config",
                r"settings",
                r"getenv\(",
                r"dotenv",
                r"pydantic.*settings",
            ],
            "authentication_patterns": [
                r"auth",
                r"token",
                r"api.*key",
                r"bearer",
                r"jwt",
                r"oauth",
                r"credential",
            ],
            "workflow_patterns": [
                r"workflow",
                r"pipeline",
                r"chain",
                r"sequence",
                r"step",
                r"stage",
                r"orchestrat",
            ],
            "testing_patterns": [
                r"@pytest",
                r"unittest",
                r"mock",
                r"patch",
                r"fixture",
                r"assert",
                r"test_",
            ],
        }

        # Pattern to requirement mapping
        self._requirement_map: dict[str, str] = {
            "async_operations": "asynchronous_processing",
            "error_handling": "error_recovery",
            "api_calls": "api_resilience",
            "caching_patterns": "performance_optimization",
            "timeout_patterns": "timeout_handling",
            "retry_patterns": "retry_logic",
            "fallback_patterns": "fallback_strategy",
            "parallel_patterns": "concurrent_execution",
            "routing_patterns": "intelligent_routing",
            "llm_patterns": "llm_reliability",
            "database_patterns": "data_persistence",
            # New requirement mappings
            "rate_limiting": "rate_limit_handling",
            "streaming_patterns": "streaming_support",
            "validation_patterns": "input_validation",
            "logging_patterns": "observability",
            "configuration_patterns": "configuration_management",
            "authentication_patterns": "security",
            "workflow_patterns": "workflow_orchestration",
            "testing_patterns": "testing_support",
        }

        # Additional requirement inference rules (pattern combinations)
        self._combination_requirements: list[tuple[set[str], str]] = [
            # Multi-agent detected from LLM + workflow + routing
            ({"llm_patterns", "workflow_patterns", "routing_patterns"}, "multi_agent"),
            # Self-improvement detected from LLM + retry + logging
            (
                {"llm_patterns", "retry_patterns", "logging_patterns"},
                "self_improvement",
            ),
            # Transaction management from error handling + workflow
            ({"error_handling", "workflow_patterns"}, "transaction_management"),
        ]

    def analyze(self, code: str, file_path: str = "") -> CodeAnalysisResult:
        """Analyze code and detect patterns.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context

        Returns:
            CodeAnalysisResult with detected patterns and inferred requirements
        """
        detected_patterns = self._detect_patterns(code)
        inferred_requirements = self._infer_requirements(detected_patterns)
        complexity_level = self._assess_complexity(code, detected_patterns)

        return CodeAnalysisResult(
            detected_patterns=detected_patterns,
            inferred_requirements=inferred_requirements,
            complexity_level=complexity_level,
            performance_critical="performance_optimization" in inferred_requirements,
            error_handling_needed="error_recovery" in inferred_requirements,
            concurrency_needed="concurrent_execution" in inferred_requirements,
        )

    def _detect_patterns(self, code: str) -> list[str]:
        """Detect which patterns are present in the code."""
        detected = []

        for pattern_name, regex_list in self.patterns.items():
            for regex in regex_list:
                if re.search(regex, code, re.IGNORECASE | re.MULTILINE):
                    detected.append(pattern_name)
                    break  # Found this pattern, move to next

        return detected

    def _infer_requirements(self, detected_patterns: list[str]) -> list[str]:
        """Infer requirements from detected patterns."""
        requirements = []

        # First, map individual patterns to requirements
        for pattern in detected_patterns:
            if pattern in self._requirement_map:
                req = self._requirement_map[pattern]
                if req not in requirements:
                    requirements.append(req)

        # Then, check for combination requirements
        pattern_set = set(detected_patterns)
        for required_patterns, requirement in self._combination_requirements:
            if required_patterns.issubset(pattern_set):
                if requirement not in requirements:
                    requirements.append(requirement)

        return requirements

    def _assess_complexity(self, code: str, patterns: list[str]) -> str:
        """Assess code complexity level.

        Args:
            code: Source code
            patterns: Detected patterns

        Returns:
            "low", "medium", or "high"
        """
        lines_of_code = len([line for line in code.split("\n") if line.strip()])
        pattern_count = len(patterns)

        # Count other complexity indicators
        nested_depth = self._estimate_nesting(code)
        function_count = len(re.findall(r"def\s+\w+", code))
        class_count = len(re.findall(r"class\s+\w+", code))

        complexity_score = (
            (1 if lines_of_code > 200 else 0)
            + (1 if lines_of_code > 500 else 0)
            + (1 if pattern_count >= 6 else 0)
            + (1 if pattern_count >= 3 else 0)
            + (1 if nested_depth > 4 else 0)
            + (1 if function_count > 10 else 0)
            + (1 if class_count > 3 else 0)
        )

        if complexity_score >= 4:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"

    def _estimate_nesting(self, code: str) -> int:
        """Estimate maximum nesting depth."""
        max_indent = 0
        for line in code.split("\n"):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                spaces_per_level = 4  # Assume 4-space indentation
                level = indent // spaces_per_level
                max_indent = max(max_indent, level)
        return max_indent

    def add_pattern(
        self, name: str, regexes: list[str], requirement: str | None = None
    ) -> None:
        """Add a custom pattern for detection.

        Args:
            name: Pattern name (e.g., "custom_pattern")
            regexes: List of regex patterns to match
            requirement: Optional requirement this pattern implies
        """
        self.patterns[name] = regexes
        if requirement:
            self._requirement_map[name] = requirement

    def get_pattern_info(self) -> dict[str, Any]:
        """Get information about all registered patterns."""
        return {
            "pattern_count": len(self.patterns),
            "patterns": list(self.patterns.keys()),
            "requirements": list(set(self._requirement_map.values())),
        }
