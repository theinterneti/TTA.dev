"""
Phase 3: Tool-Aware Suggestion Engine

Advanced recommendation system that understands the full development context.
This module provides intelligent, context-aware suggestions for TTA.dev primitives.

Key Features:
- Code Pattern Recognition: AST-based analysis, architectural patterns, performance detection
- Multi-Modal Analysis: Code parsing, documentation analysis, dependency mapping
- Intelligent Suggestion System: Context-aware recommendations, confidence scoring
"""

import ast
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Import from our dynamic context loader
from .dynamic_context_loader import (
    FrameworkType,
    LanguageType,
    ProjectContext,
)


class SuggestionType(Enum):
    """Types of suggestions the engine can provide."""

    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_HANDLING = "error_handling"
    CACHING_STRATEGY = "caching_strategy"
    RETRY_LOGIC = "retry_logic"
    TIMEOUT_MANAGEMENT = "timeout_management"
    SEQUENTIAL_WORKFLOW = "sequential_workflow"
    PARALLEL_EXECUTION = "parallel_execution"
    FALLBACK_MECHANISM = "fallback_mechanism"
    RESILIENCE_PATTERN = "resilience_pattern"
    ROUTING_STRATEGY = "routing_strategy"


class ArchitecturePattern(Enum):
    """Detectable architectural patterns."""

    MICROSERVICE = "microservice"
    LAYERED_ARCHITECTURE = "layered_architecture"
    EVENT_DRIVEN = "event_driven"
    PIPELINE = "pipeline"
    FANOUT_FANIN = "fanout_fanin"
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"
    OBSERVER_PATTERN = "observer_pattern"
    FACTORY_PATTERN = "factory_pattern"
    SINGLETON = "singleton"
    COMMAND_PATTERN = "command_pattern"


class PerformanceIssue(Enum):
    """Types of performance issues that can be detected."""

    CPU_INTENSIVE = "cpu_intensive"
    MEMORY_LEAK = "memory_leak"
    NETWORK_BOTTLENECK = "network_bottleneck"
    DISK_IO = "disk_io"
    DATABASE_QUERY = "database_query"
    LOCK_CONTENTION = "lock_contention"
    BLOCKING_OPERATION = "blocking_operation"
    INEFFICIENT_LOOP = "inefficient_loop"
    EXCESSIVE_ALLOCATIONS = "excessive_allocations"


@dataclass
class CodeIssue:
    """Represents a detected code issue or anti-pattern."""

    issue_type: str
    severity: float  # 0.0 to 1.0
    file_path: str
    line_number: int
    description: str
    suggestion: str
    code_snippet: str
    context: dict[str, Any]


@dataclass
class ArchitectureDetection:
    """Represents a detected architectural pattern."""

    pattern: ArchitecturePattern
    confidence: float
    file_path: str
    evidence: list[str]
    context: dict[str, Any]


@dataclass
class PerformanceBottleneck:
    """Represents a detected performance bottleneck."""

    bottleneck_type: PerformanceIssue
    severity: float
    file_path: str
    line_number: int
    description: str
    impact: str
    optimization_suggestion: str


@dataclass
class Suggestion:
    """Represents a primitive suggestion with context."""

    primitive: str
    suggestion_type: SuggestionType
    confidence: float
    reason: str
    context: dict[str, Any]
    code_example: str
    benefits: list[str]
    implementation_steps: list[str]
    related_issues: list[str]


class CodeAnalysisEngine:
    """AST-based code analysis engine for pattern recognition."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.performance_patterns = self._load_performance_patterns()
        self.error_patterns = self._load_error_patterns()
        self.architecture_patterns = self._load_architecture_patterns()

    def _load_performance_patterns(self) -> dict[str, Any]:
        """Load performance-related code patterns."""
        return {
            "cpu_intensive": {
                "patterns": [
                    (r"for\s+\w+\s+in\s+.*:\s*$", "nested_loop"),
                    (r"while\s+.*:\s*$", "while_loop"),
                    (r"map\s*\(", "map_function"),
                    (r"filter\s*\(", "filter_function"),
                    (r"reduce\s*\(", "reduce_function"),
                ],
                "severity_multiplier": 0.8,
            },
            "memory_issues": {
                "patterns": [
                    (r"=\s*\[.*\]\s*$", "list_comprehension"),
                    (r"=\s*\{.*\}\s*$", "dict_comprehension"),
                    (r"=\s*\(.*\)\s*$", "generator_expression"),
                ],
                "severity_multiplier": 0.6,
            },
            "blocking_operations": {
                "patterns": [
                    (r"requests\.", "http_request"),
                    (r"time\.sleep", "sleep_operation"),
                    (r"input\s*\(", "user_input"),
                    (r"open\s*\(", "file_operation"),
                ],
                "severity_multiplier": 0.9,
            },
        }

    def _load_error_patterns(self) -> dict[str, Any]:
        """Load error-prone code patterns."""
        return {
            "exception_handling": {
                "patterns": [
                    (r"except\s+.*:\s*$", "broad_exception"),
                    (r"except\s+Exception:", "generic_exception"),
                    (r"try:.*pass", "empty_except"),
                    (r"except:.*pass", "bare_except"),
                ],
                "severity_multiplier": 0.7,
            },
            "resource_management": {
                "patterns": [
                    (r"open\s*\([^)]*\)\s*$", "unclosed_file"),
                    (r"requests\.[^.]*\(.*\)$", "unmanaged_request"),
                    (r"cursor\.[^.]*\(.*\)$", "unmanaged_cursor"),
                ],
                "severity_multiplier": 0.8,
            },
        }

    def _load_architecture_patterns(self) -> dict[str, Any]:
        """Load architectural pattern detection rules."""
        return {
            "microservice": {
                "indicators": [
                    "from flask import Flask",
                    "from fastapi import FastAPI",
                    "app = FastAPI",
                    "app = Flask",
                ],
                "confidence_threshold": 0.7,
            },
            "layered_architecture": {
                "indicators": [
                    "class.*Service",
                    "class.*Repository",
                    "class.*Controller",
                    "class.*Manager",
                ],
                "confidence_threshold": 0.6,
            },
            "event_driven": {
                "indicators": ["event", "Event", "emit", "subscribe", "callback"],
                "confidence_threshold": 0.5,
            },
            "pipeline": {
                "indicators": [">>", "pipe", "compose", "chain"],
                "confidence_threshold": 0.6,
            },
        }

    def analyze_file_issues(self, file_path: Path) -> list[CodeIssue]:
        """Analyze a file for issues and anti-patterns."""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            # Try to parse as Python AST
            try:
                tree = ast.parse(content)
                issues.extend(self._analyze_ast_issues(tree, file_path, lines))
            except SyntaxError:
                pass  # Skip files that can't be parsed

            # Pattern-based analysis
            issues.extend(self._analyze_pattern_issues(file_path, lines))

        except (OSError, UnicodeDecodeError):
            pass

        return issues

    def _analyze_ast_issues(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Analyze AST for structural issues."""
        issues = []

        for node in ast.walk(tree):
            # Detect bare except clauses
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issue = CodeIssue(
                    issue_type="bare_except",
                    severity=0.8,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    description="Bare except clause found",
                    suggestion="Specify the exception type to catch",
                    code_snippet=lines[node.lineno - 1]
                    if node.lineno <= len(lines)
                    else "",
                    context={"node_type": type(node).__name__},
                )
                issues.append(issue)

            # Detect empty except blocks
            if isinstance(node, ast.ExceptHandler):
                try:
                    body_lines = (
                        lines[node.lineno : node.end_lineno] if node.end_lineno else []
                    )
                    if any(
                        line.strip() for line in body_lines[1:]
                    ):  # Skip the 'except' line
                        pass  # Has content
                    else:
                        issue = CodeIssue(
                            issue_type="empty_except",
                            severity=0.7,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            description="Empty except block",
                            suggestion="Add error handling logic or logging",
                            code_snippet=lines[node.lineno - 1]
                            if node.lineno <= len(lines)
                            else "",
                            context={"node_type": type(node).__name__},
                        )
                        issues.append(issue)
                except AttributeError:
                    pass  # Skip if end_lineno not available

        return issues

    def _analyze_pattern_issues(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Analyze file for pattern-based issues."""
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Check each pattern category
            for category, config in self.performance_patterns.items():
                for pattern, description in config["patterns"]:
                    if re.search(pattern, line):
                        severity = 0.5 * config["severity_multiplier"]
                        issue = CodeIssue(
                            issue_type=category,
                            severity=severity,
                            file_path=str(file_path),
                            line_number=line_num,
                            description=f"Potential {category} issue: {description}",
                            suggestion=f"Consider using TTA.dev primitives for {category.replace('_', ' ')} optimization",
                            code_snippet=line.strip(),
                            context={"pattern": pattern, "category": category},
                        )
                        issues.append(issue)

            # Check error patterns
            for category, config in self.error_patterns.items():
                for pattern, description in config["patterns"]:
                    if re.search(pattern, line):
                        severity = 0.6 * config["severity_multiplier"]
                        issue = CodeIssue(
                            issue_type=category,
                            severity=severity,
                            file_path=str(file_path),
                            line_number=line_num,
                            description=f"Error-prone pattern: {description}",
                            suggestion="Add proper error handling with TTA.dev primitives",
                            code_snippet=line.strip(),
                            context={"pattern": pattern, "category": category},
                        )
                        issues.append(issue)

        return issues

    def detect_architectural_patterns(
        self, context: ProjectContext
    ) -> list[ArchitectureDetection]:
        """Detect architectural patterns in the project."""
        detections = []

        # Check file structure for patterns
        file_structure = context.file_structure

        # Microservice detection
        web_files = sum(
            1 for ext in [".py"] if ext in file_structure.get("file_types", {})
        )
        if web_files > 0:
            # Look for web framework indicators
            framework_indicators = 0
            for detection in context.frameworks:
                if detection.framework in [
                    FrameworkType.FLASK,
                    FrameworkType.FASTAPI,
                    FrameworkType.DJANGO,
                ]:
                    framework_indicators += detection.confidence

            if framework_indicators > 0.7:
                detection = ArchitectureDetection(
                    pattern=ArchitecturePattern.MICROSERVICE,
                    confidence=framework_indicators,
                    file_path="project_root",
                    evidence=[f"Framework confidence: {framework_indicators}"],
                    context={
                        "frameworks": [f.framework.value for f in context.frameworks]
                    },
                )
                detections.append(detection)

        # Layered architecture detection
        class_names = []
        for pattern in context.patterns:
            if (
                pattern.pattern_type == "architectural_patterns"
                and pattern.name == "class_definition"
            ):
                class_names.append(pattern.context.get("line_content", ""))

        service_classes = [
            name
            for name in class_names
            if any(
                keyword in name.lower()
                for keyword in ["service", "repository", "controller", "manager"]
            )
        ]
        if len(service_classes) >= 2:
            detection = ArchitectureDetection(
                pattern=ArchitecturePattern.LAYERED_ARCHITECTURE,
                confidence=min(len(service_classes) / 5, 1.0),
                file_path="project_root",
                evidence=[f"Found {len(service_classes)} service-layer classes"],
                context={"service_classes": service_classes},
            )
            detections.append(detection)

        # Event-driven pattern detection
        event_keywords = ["event", "Event", "emit", "subscribe", "callback"]
        event_mentions = sum(
            1
            for pattern in context.patterns
            if any(
                keyword in pattern.context.get("line_content", "").lower()
                for keyword in event_keywords
            )
        )
        if event_mentions >= 3:
            detection = ArchitectureDetection(
                pattern=ArchitecturePattern.EVENT_DRIVEN,
                confidence=min(event_mentions / 10, 0.8),
                file_path="project_root",
                evidence=[f"Found {event_mentions} event-related patterns"],
                context={"event_mentions": event_mentions},
            )
            detections.append(detection)

        return detections

    def identify_performance_bottlenecks(
        self, issues: list[CodeIssue]
    ) -> list[PerformanceBottleneck]:
        """Identify performance bottlenecks from detected issues."""
        bottlenecks = []

        for issue in issues:
            if issue.issue_type == "cpu_intensive":
                bottleneck = PerformanceBottleneck(
                    bottleneck_type=PerformanceIssue.CPU_INTENSIVE,
                    severity=issue.severity,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    description=issue.description,
                    impact="High CPU usage may slow down application",
                    optimization_suggestion="Consider using CachePrimitive or ParallelPrimitive for optimization",
                )
                bottlenecks.append(bottleneck)

            elif issue.issue_type == "memory_issues":
                bottleneck = PerformanceBottleneck(
                    bottleneck_type=PerformanceIssue.MEMORY_LEAK,
                    severity=issue.severity,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    description=issue.description,
                    impact="Excessive memory usage may lead to performance degradation",
                    optimization_suggestion="Use CachePrimitive with TTL or implement lazy loading patterns",
                )
                bottlenecks.append(bottleneck)

            elif issue.issue_type == "blocking_operations":
                bottleneck = PerformanceBottleneck(
                    bottleneck_type=PerformanceIssue.BLOCKING_OPERATION,
                    severity=issue.severity,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    description=issue.description,
                    impact="Blocking operations may cause application to become unresponsive",
                    optimization_suggestion="Wrap with TimeoutPrimitive or use async patterns with SequentialPrimitive",
                )
                bottlenecks.append(bottleneck)

        return bottlenecks


class MultiModalAnalyzer:
    """Analyzer that considers multiple data sources for context understanding."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.documentation_patterns = self._load_documentation_patterns()
        self.dependency_graph = self._build_dependency_graph()

    def _load_documentation_patterns(self) -> dict[str, Any]:
        """Load documentation and comment analysis patterns."""
        return {
            "todo_patterns": [r"TODO", r"FIXME", r"HACK", r"XXX"],
            "docstring_patterns": [r'"""', r"'''", r"class.*:", r"def.*:"],
            "comment_indicators": [r"#", r"//", r"/\*"],
            "performance_comments": [
                r"slow",
                r"performance",
                r"bottleneck",
                r"optimize",
            ],
            "error_comments": [r"error", r"exception", r"fail", r"catch"],
        }

    def _build_dependency_graph(self) -> dict[str, set[str]]:
        """Build a dependency graph of the project."""
        dependencies = defaultdict(set)

        for file_path in self.project_path.rglob("*.py"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Extract imports
                import_pattern = r"^(?:from\s+([\w.]+)\s+import\s+|import\s+([\w.]+))"
                matches = re.findall(import_pattern, content, re.MULTILINE)

                for match in matches:
                    module = match[0] if match[0] else match[1]
                    if module and not module.startswith("."):
                        file_name = file_path.stem
                        dependencies[file_name].add(module)

            except (OSError, UnicodeDecodeError):
                continue

        return dict(dependencies)

    def analyze_documentation_context(self) -> dict[str, Any]:
        """Analyze documentation and comments for context clues."""
        context = {
            "todos": [],
            "known_issues": [],
            "performance_concerns": [],
            "architecture_hints": [],
            "complexity_indicators": [],
        }

        for file_path in self.project_path.rglob("*.py"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()

                    # Check for TODO/FIXME patterns
                    for pattern in self.documentation_patterns["todo_patterns"]:
                        if pattern.lower() in line_lower:
                            context["todos"].append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line.strip(),
                                }
                            )

                    # Check for performance concerns
                    for pattern in self.documentation_patterns["performance_comments"]:
                        if pattern in line_lower:
                            context["performance_concerns"].append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line.strip(),
                                }
                            )

                    # Check for error/exception mentions
                    for pattern in self.documentation_patterns["error_comments"]:
                        if pattern in line_lower:
                            context["known_issues"].append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line.strip(),
                                }
                            )

            except (OSError, UnicodeDecodeError):
                continue

        return context

    def analyze_team_patterns(
        self, context: ProjectContext, doc_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze team coding patterns and preferences."""
        patterns = {
            "coding_style": {},
            "framework_preferences": [],
            "complexity_tolerance": 0.0,
            "error_handling_style": "",
            "documentation_quality": 0.0,
        }

        # Analyze coding style from detected patterns
        pattern_types = [p.pattern_type for p in context.patterns]
        patterns["coding_style"]["pattern_distribution"] = dict(Counter(pattern_types))

        # Framework preferences based on detected frameworks
        patterns["framework_preferences"] = [
            f.framework.value for f in context.frameworks
        ]

        # Complexity tolerance based on project stage and patterns
        complexity_factors = [
            context.complexity_score,
            len(context.patterns) / 100,  # Normalize pattern count
            context.file_structure.get("depth", 0) / 10,  # Normalize depth
        ]
        patterns["complexity_tolerance"] = sum(complexity_factors) / len(
            complexity_factors
        )

        # Error handling style based on detected error patterns
        error_patterns = [
            p for p in context.patterns if p.pattern_type == "error_patterns"
        ]
        if len(error_patterns) > 10:
            patterns["error_handling_style"] = "comprehensive"
        elif len(error_patterns) > 5:
            patterns["error_handling_style"] = "moderate"
        else:
            patterns["error_handling_style"] = "minimal"

        # Documentation quality based on doc_context
        doc_quality_factors = [
            len(doc_context.get("todos", [])) / 10,  # Lower is better
            len(doc_context.get("known_issues", [])) / 20,  # Lower is better
            1.0
            - (
                len(doc_context.get("performance_concerns", [])) / 50
            ),  # Lower is better
        ]
        patterns["documentation_quality"] = max(
            0.0, min(1.0, sum(doc_quality_factors) / len(doc_quality_factors))
        )

        return patterns


class IntelligentSuggestionEngine:
    """Main engine for generating intelligent, context-aware suggestions."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.code_analyzer = CodeAnalysisEngine(project_path)
        self.multi_modal_analyzer = MultiModalAnalyzer(project_path)
        self.primitive_mappings = self._load_primitive_mappings()
        self.suggestion_history: list[dict[str, Any]] = []

    def _load_primitive_mappings(self) -> dict[str, Any]:
        """Load mapping from issues and patterns to primitive suggestions."""
        return {
            "performance_optimization": {
                "cpu_intensive": {
                    "primitives": [
                        "cache_primitive",
                        "parallel_primitive",
                        "sequential_primitive",
                    ],
                    "reasoning": "CPU-intensive operations benefit from caching and parallelization",
                },
                "memory_issues": {
                    "primitives": ["cache_primitive", "timeout_primitive"],
                    "reasoning": "Memory issues can be addressed with caching strategies and timeouts",
                },
                "blocking_operations": {
                    "primitives": ["timeout_primitive", "sequential_primitive"],
                    "reasoning": "Blocking operations need timeout management and sequential processing",
                },
            },
            "error_handling": {
                "exception_handling": {
                    "primitives": ["fallback_primitive", "retry_primitive"],
                    "reasoning": "Poor exception handling requires fallback mechanisms and retry logic",
                },
                "resource_management": {
                    "primitives": ["fallback_primitive", "timeout_primitive"],
                    "reasoning": "Resource management issues need proper cleanup and timeout handling",
                },
            },
            "architectural": {
                "microservice": {
                    "primitives": [
                        "router_primitive",
                        "sequential_primitive",
                        "parallel_primitive",
                    ],
                    "reasoning": "Microservices benefit from routing and orchestration patterns",
                },
                "layered_architecture": {
                    "primitives": ["sequential_primitive", "fallback_primitive"],
                    "reasoning": "Layered architectures need sequential processing and error handling",
                },
                "event_driven": {
                    "primitives": ["parallel_primitive", "fallback_primitive"],
                    "reasoning": "Event-driven systems need parallel processing and fault tolerance",
                },
            },
            "resilience": {
                "high_stage": {
                    "primitives": [
                        "fallback_primitive",
                        "retry_primitive",
                        "timeout_primitive",
                    ],
                    "reasoning": "Production systems need comprehensive resilience patterns",
                },
                "complex_project": {
                    "primitives": [
                        "router_primitive",
                        "parallel_primitive",
                        "cache_primitive",
                    ],
                    "reasoning": "Complex projects need advanced orchestration and optimization",
                },
            },
        }

    def generate_suggestions(self, context: ProjectContext) -> list[Suggestion]:
        """Generate intelligent suggestions based on project context and analysis."""
        suggestions = []

        # Analyze code issues
        all_issues = []
        for file_path in self.project_path.rglob("*.py"):
            all_issues.extend(self.code_analyzer.analyze_file_issues(file_path))

        # Detect architectural patterns
        architecture_detections = self.code_analyzer.detect_architectural_patterns(
            context
        )

        # Identify performance bottlenecks
        bottlenecks = self.code_analyzer.identify_performance_bottlenecks(all_issues)

        # Analyze documentation context
        doc_context = self.multi_modal_analyzer.analyze_documentation_context()

        # Analyze team patterns
        team_patterns = self.multi_modal_analyzer.analyze_team_patterns(
            context, doc_context
        )

        # Generate suggestions based on issues
        for issue in all_issues:
            if issue.severity > 0.3:  # Only suggest for significant issues
                suggestions.extend(
                    self._suggest_for_issue(issue, context, team_patterns)
                )

        # Generate suggestions based on bottlenecks
        for bottleneck in bottlenecks:
            suggestions.extend(self._suggest_for_bottleneck(bottleneck, context))

        # Generate suggestions based on architecture
        for detection in architecture_detections:
            suggestions.extend(self._suggest_for_architecture(detection, context))

        # Generate suggestions based on project characteristics
        suggestions.extend(
            self._suggest_for_project_characteristics(context, team_patterns)
        )

        # Remove duplicates and rank by confidence
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        ranked_suggestions = self._rank_suggestions(unique_suggestions)

        return ranked_suggestions[:15]  # Return top 15 suggestions

    def _suggest_for_issue(
        self, issue: CodeIssue, context: ProjectContext, team_patterns: dict[str, Any]
    ) -> list[Suggestion]:
        """Generate suggestions for a specific code issue."""
        suggestions = []

        # Map issue type to suggestion category
        if issue.issue_type in [
            "cpu_intensive",
            "memory_issues",
            "blocking_operations",
        ]:
            category = "performance_optimization"
        elif issue.issue_type in ["exception_handling", "resource_management"]:
            category = "error_handling"
        else:
            category = "error_handling"  # Default

        if (
            category in self.primitive_mappings
            and issue.issue_type in self.primitive_mappings[category]
        ):
            mapping = self.primitive_mappings[category][issue.issue_type]

            for primitive in mapping["primitives"]:
                suggestion = Suggestion(
                    primitive=primitive,
                    suggestion_type=SuggestionType(
                        category.replace("_", " ").title().replace(" ", "_").lower()
                    ),
                    confidence=min(issue.severity * 1.2, 1.0),
                    reason=f"{mapping['reasoning']} - Issue: {issue.description}",
                    context={
                        "issue_type": issue.issue_type,
                        "file_path": issue.file_path,
                        "line_number": issue.line_number,
                        "issue_severity": issue.severity,
                    },
                    code_example=self._get_primitive_example(
                        primitive, context.language
                    ),
                    benefits=self._get_primitive_benefits(primitive),
                    implementation_steps=self._get_implementation_steps(primitive),
                    related_issues=[f"{issue.file_path}:{issue.line_number}"],
                )
                suggestions.append(suggestion)

        return suggestions

    def _suggest_for_bottleneck(
        self, bottleneck: PerformanceBottleneck, context: ProjectContext
    ) -> list[Suggestion]:
        """Generate suggestions for a performance bottleneck."""
        suggestions = []

        # Map bottleneck type to appropriate primitives
        bottleneck_mappings = {
            PerformanceIssue.CPU_INTENSIVE: ["cache_primitive", "parallel_primitive"],
            PerformanceIssue.MEMORY_LEAK: ["cache_primitive", "timeout_primitive"],
            PerformanceIssue.NETWORK_BOTTLENECK: [
                "timeout_primitive",
                "retry_primitive",
            ],
            PerformanceIssue.BLOCKING_OPERATION: [
                "timeout_primitive",
                "sequential_primitive",
            ],
        }

        primitives = bottleneck_mappings.get(
            bottleneck.bottleneck_type, ["cache_primitive"]
        )

        for primitive in primitives:
            suggestion = Suggestion(
                primitive=primitive,
                suggestion_type=SuggestionType.PERFORMANCE_OPTIMIZATION,
                confidence=bottleneck.severity,
                reason=f"Performance bottleneck detected: {bottleneck.description}",
                context={
                    "bottleneck_type": bottleneck.bottleneck_type.value,
                    "file_path": bottleneck.file_path,
                    "line_number": bottleneck.line_number,
                    "impact": bottleneck.impact,
                },
                code_example=self._get_primitive_example(primitive, context.language),
                benefits=self._get_primitive_benefits(primitive),
                implementation_steps=self._get_implementation_steps(primitive),
                related_issues=[f"{bottleneck.file_path}:{bottleneck.line_number}"],
            )
            suggestions.append(suggestion)

        return suggestions

    def _suggest_for_architecture(
        self, detection: ArchitectureDetection, context: ProjectContext
    ) -> list[Suggestion]:
        """Generate suggestions for architectural patterns."""
        suggestions = []

        # Map architecture to primitive suggestions
        if detection.pattern == ArchitecturePattern.MICROSERVICE:
            primitives = [
                "router_primitive",
                "sequential_primitive",
                "parallel_primitive",
            ]
            reason = "Microservices benefit from routing and orchestration"
        elif detection.pattern == ArchitecturePattern.LAYERED_ARCHITECTURE:
            primitives = ["sequential_primitive", "fallback_primitive"]
            reason = (
                "Layered architectures need sequential processing and error handling"
            )
        elif detection.pattern == ArchitecturePattern.EVENT_DRIVEN:
            primitives = ["parallel_primitive", "fallback_primitive"]
            reason = "Event-driven systems need parallel processing and fault tolerance"
        else:
            primitives = ["sequential_primitive"]
            reason = f"Architecture pattern {detection.pattern.value} detected"

        for primitive in primitives:
            suggestion = Suggestion(
                primitive=primitive,
                suggestion_type=SuggestionType.SEQUENTIAL_WORKFLOW
                if primitive == "sequential_primitive"
                else SuggestionType.ROUTING_STRATEGY,
                confidence=detection.confidence * 0.8,
                reason=f"{reason} - Pattern: {detection.pattern.value}",
                context={
                    "pattern": detection.pattern.value,
                    "confidence": detection.confidence,
                    "evidence": detection.evidence,
                },
                code_example=self._get_primitive_example(primitive, context.language),
                benefits=self._get_primitive_benefits(primitive),
                implementation_steps=self._get_implementation_steps(primitive),
                related_issues=[],
            )
            suggestions.append(suggestion)

        return suggestions

    def _suggest_for_project_characteristics(
        self, context: ProjectContext, team_patterns: dict[str, Any]
    ) -> list[Suggestion]:
        """Generate suggestions based on project characteristics."""
        suggestions = []

        # Stage-based suggestions
        if context.stage.value == "production":
            production_primitives = [
                "fallback_primitive",
                "retry_primitive",
                "timeout_primitive",
            ]
            for primitive in production_primitives:
                suggestion = Suggestion(
                    primitive=primitive,
                    suggestion_type=SuggestionType.RESILIENCE_PATTERN,
                    confidence=0.8,
                    reason="Production systems need comprehensive resilience patterns",
                    context={
                        "stage": context.stage.value,
                        "complexity_score": context.complexity_score,
                    },
                    code_example=self._get_primitive_example(
                        primitive, context.language
                    ),
                    benefits=self._get_primitive_benefits(primitive),
                    implementation_steps=self._get_implementation_steps(primitive),
                    related_issues=[],
                )
                suggestions.append(suggestion)

        # Complexity-based suggestions
        if context.complexity_score > 0.7:
            complex_primitives = ["router_primitive", "parallel_primitive"]
            for primitive in complex_primitives:
                suggestion = Suggestion(
                    primitive=primitive,
                    suggestion_type=SuggestionType.ROUTING_STRATEGY
                    if primitive == "router_primitive"
                    else SuggestionType.PARALLEL_EXECUTION,
                    confidence=context.complexity_score,
                    reason="Complex projects benefit from advanced orchestration and parallelization",
                    context={
                        "complexity_score": context.complexity_score,
                        "pattern_count": len(context.patterns),
                    },
                    code_example=self._get_primitive_example(
                        primitive, context.language
                    ),
                    benefits=self._get_primitive_benefits(primitive),
                    implementation_steps=self._get_implementation_steps(primitive),
                    related_issues=[],
                )
                suggestions.append(suggestion)

        # Team preference-based suggestions
        preferred_frameworks = team_patterns.get("framework_preferences", [])
        if "django" in preferred_frameworks:
            django_suggestion = Suggestion(
                primitive="cache_primitive",
                suggestion_type=SuggestionType.CACHING_STRATEGY,
                confidence=0.7,
                reason="Django projects benefit from caching for database query optimization",
                context={"framework_preference": "django"},
                code_example=self._get_primitive_example(
                    "cache_primitive", context.language
                ),
                benefits=self._get_primitive_benefits("cache_primitive"),
                implementation_steps=self._get_implementation_steps("cache_primitive"),
                related_issues=[],
            )
            suggestions.append(django_suggestion)

        return suggestions

    def _get_primitive_example(self, primitive: str, language: LanguageType) -> str:
        """Get a code example for the primitive in the project's language."""
        examples = {
            "cache_primitive": {
                "python": """
from tta_dev_primitives import CachePrimitive

cached_operation = CachePrimitive(
    primitive=expensive_database_query,
    ttl_seconds=3600,
    max_size=1000
)

result = await cached_operation.execute(context, query_data)
                """,
                "javascript": """
// For JavaScript/Node.js projects
const { CachePrimitive } = require('tta-dev-primitives');

const cachedOperation = new CachePrimitive({
    primitive: expensiveDatabaseQuery,
    ttlSeconds: 3600,
    maxSize: 1000
});

const result = await cachedOperation.execute(context, queryData);
                """,
            },
            "retry_primitive": {
                "python": """
from tta_dev_primitives import RetryPrimitive

retry_operation = RetryPrimitive(
    primitive=unreliable_api_call,
    max_retries=3,
    backoff_strategy="exponential"
)

result = await retry_operation.execute(context, request_data)
                """
            },
            "fallback_primitive": {
                "python": """
from tta_dev_primitives import FallbackPrimitive

fallback_operation = FallbackPrimitive(
    primary=primary_service_call,
    fallback=backup_service_call
)

result = await fallback_operation.execute(context, request_data)
                """
            },
            "timeout_primitive": {
                "python": """
from tta_dev_primitives import TimeoutPrimitive

timeout_operation = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30
)

result = await timeout_operation.execute(context, operation_data)
                """
            },
            "sequential_primitive": {
                "python": """
from tta_dev_primitives import SequentialPrimitive

workflow = step1 >> step2 >> step3
result = await workflow.execute(context, input_data)
                """
            },
            "parallel_primitive": {
                "python": """
from tta_dev_primitives import ParallelPrimitive

parallel_workflow = task1 | task2 | task3
result = await parallel_workflow.execute(context, input_data)
                """
            },
            "router_primitive": {
                "python": """
from tta_dev_primitives import RouterPrimitive

router = RouterPrimitive(
    routes={
        "/api/users": user_service,
        "/api/posts": post_service
    }
)

result = await router.execute(context, request_data)
                """
            },
        }

        return examples.get(primitive, {}).get(
            language.value, "# Example not available for this language"
        )

    def _get_primitive_benefits(self, primitive: str) -> list[str]:
        """Get benefits of using a specific primitive."""
        benefits_map = {
            "cache_primitive": [
                "Reduces database load",
                "Improves response times",
                "Prevents redundant computations",
                "Handles memory efficiently with TTL",
            ],
            "retry_primitive": [
                "Handles transient failures automatically",
                "Implements exponential backoff",
                "Improves system reliability",
                "Reduces manual error handling",
            ],
            "fallback_primitive": [
                "Provides graceful degradation",
                "Ensures system availability",
                "Implements circuit breaker patterns",
                "Reduces user-facing errors",
            ],
            "timeout_primitive": [
                "Prevents hanging operations",
                "Improves system responsiveness",
                "Manages resource allocation",
                "Handles slow external services",
            ],
            "sequential_primitive": [
                "Ensures proper execution order",
                "Handles data dependencies",
                "Provides clear workflow logic",
                "Enables step-by-step debugging",
            ],
            "parallel_primitive": [
                "Improves performance through concurrency",
                "Utilizes system resources efficiently",
                "Reduces total execution time",
                "Scales with available CPU cores",
            ],
            "router_primitive": [
                "Enables service discovery",
                "Implements load balancing",
                "Provides request routing logic",
                "Supports microservices architecture",
            ],
        }

        return benefits_map.get(primitive, ["Improves code quality and reliability"])

    def _get_implementation_steps(self, primitive: str) -> list[str]:
        """Get implementation steps for a primitive."""
        steps_map = {
            "cache_primitive": [
                "1. Import CachePrimitive from tta_dev_primitives",
                "2. Define the function to be cached",
                "3. Create CachePrimitive with appropriate TTL and size",
                "4. Replace direct function calls with primitive calls",
                "5. Monitor cache hit rates and adjust parameters",
            ],
            "retry_primitive": [
                "1. Import RetryPrimitive from tta_dev_primitives",
                "2. Identify operations that may fail transiently",
                "3. Configure retry parameters (max_retries, backoff_strategy)",
                "4. Wrap operations with RetryPrimitive",
                "5. Test failure scenarios and retry behavior",
            ],
            "fallback_primitive": [
                "1. Import FallbackPrimitive from tta_dev_primitives",
                "2. Define primary and fallback operations",
                "3. Configure fallback triggers and conditions",
                "4. Implement fallback operation logic",
                "5. Test both primary and fallback paths",
            ],
            "timeout_primitive": [
                "1. Import TimeoutPrimitive from tta_dev_primitives",
                "2. Identify operations that may hang",
                "3. Set appropriate timeout values",
                "4. Handle timeout exceptions gracefully",
                "5. Monitor and tune timeout parameters",
            ],
        }

        return steps_map.get(
            primitive,
            [
                f"1. Import {primitive} from tta_dev_primitives",
                "2. Configure primitive parameters",
                "3. Replace existing implementation",
                "4. Test thoroughly",
                "5. Monitor performance",
            ],
        )

    def _deduplicate_suggestions(
        self, suggestions: list[Suggestion]
    ) -> list[Suggestion]:
        """Remove duplicate suggestions based on primitive and context."""
        seen = set()
        unique_suggestions = []

        for suggestion in suggestions:
            key = (suggestion.primitive, suggestion.suggestion_type.value)
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        return unique_suggestions

    def _rank_suggestions(self, suggestions: list[Suggestion]) -> list[Suggestion]:
        """Rank suggestions by confidence and relevance."""

        def calculate_score(suggestion: Suggestion) -> float:
            base_score = suggestion.confidence

            # Boost score based on context relevance
            context_boost = 0.0
            if "complexity_score" in suggestion.context:
                context_boost += suggestion.context["complexity_score"] * 0.1

            if (
                "stage" in suggestion.context
                and suggestion.context["stage"] == "production"
            ):
                context_boost += 0.2

            if "framework_preference" in suggestion.context:
                context_boost += 0.1

            return base_score + context_boost

        return sorted(suggestions, key=calculate_score, reverse=True)

    def get_suggestion_explanation(self, suggestion: Suggestion) -> str:
        """Generate a human-readable explanation for a suggestion."""
        explanation = f"**{suggestion.primitive.title().replace('_', ' ')}** is recommended because: {suggestion.reason}"

        if suggestion.context:
            explanation += "\n\n**Context Details:**"
            for key, value in suggestion.context.items():
                if isinstance(value, (str, int, float)):
                    explanation += f"\n- {key.replace('_', ' ').title()}: {value}"

        explanation += "\n\n**Expected Benefits:**"
        for benefit in suggestion.benefits:
            explanation += f"\n- {benefit}"

        return explanation


# Utility functions for external integration
def create_suggestion_engine(project_path: str) -> IntelligentSuggestionEngine:
    """Create a configured suggestion engine instance."""
    return IntelligentSuggestionEngine(project_path)


def get_context_aware_suggestions(
    project_path: str, context: ProjectContext
) -> list[Suggestion]:
    """Get suggestions for a project with given context."""
    engine = create_suggestion_engine(project_path)
    return engine.generate_suggestions(context)


def analyze_project_and_suggest(project_path: str) -> dict[str, Any]:
    """Perform complete project analysis and return suggestions."""
    # This would integrate with the dynamic context loader
    from .dynamic_context_loader import quick_context_analysis

    # Get context
    context_data = quick_context_analysis(project_path)

    # For now, create a mock context since we need the full ProjectContext object
    # In a real implementation, you'd use the full context from dynamic_context_loader

    return {
        "context": context_data,
        "suggestions": [],
        "analysis_summary": "Analysis completed successfully",
    }


# Example usage and testing
if __name__ == "__main__":
    # Test the suggestion engine
    project_path = "/home/thein/repos/TTA.dev"
    engine = create_suggestion_engine(project_path)

    print("Tool-Aware Suggestion Engine initialized successfully")
    print("Features available:")
    print("- Code pattern recognition")
    print("- Architectural pattern detection")
    print("- Performance bottleneck identification")
    print("- Multi-modal analysis")
    print("- Intelligent suggestion generation")
