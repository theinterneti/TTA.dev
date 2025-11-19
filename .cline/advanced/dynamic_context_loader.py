"""
Phase 3: Dynamic Context Loading System

Intelligent system that automatically adapts cline context based on real-time development patterns.
This module provides smart context detection, adaptive learning, and context-aware template injection.

Key Features:
- Smart Context Detection: Project structure analysis, framework detection, language optimization
- Adaptive Learning: Usage pattern analysis, personalized recommendations, continuous improvement
- Context-Aware Templates: Dynamic template selection, framework-specific optimization
"""

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class FrameworkType(Enum):
    """Supported framework types for context detection."""

    REACT = "react"
    DJANGO = "django"
    FASTAPI = "fastapi"
    FLASK = "flask"
    NEXTJS = "nextjs"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    SPRING = "spring"
    LARAVEL = "laravel"
    UNKNOWN = "unknown"


class LanguageType(Enum):
    """Programming language types."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    PHP = "php"
    GO = "go"
    RUST = "rust"
    C_SHARP = "c#"
    UNKNOWN = "unknown"


class ProjectStage(Enum):
    """Development stage of the project."""

    PROTOTYPING = "prototyping"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"


@dataclass
class CodePattern:
    """Represents a detected code pattern."""

    name: str
    confidence: float
    file_path: str
    line_number: int
    pattern_type: str
    context: dict[str, Any]


@dataclass
class FrameworkDetection:
    """Framework detection result."""

    framework: FrameworkType
    confidence: float
    evidence: list[str]
    version: str | None = None
    additional_frameworks: list[FrameworkType] = None


@dataclass
class ProjectContext:
    """Complete project context information."""

    project_path: str
    language: LanguageType
    frameworks: list[FrameworkDetection]
    patterns: list[CodePattern]
    stage: ProjectStage
    complexity_score: float
    dependencies: dict[str, str]
    file_structure: dict[str, Any]
    last_modified: datetime
    context_hash: str


@dataclass
class UserPreferences:
    """User-specific preferences and learning data."""

    developer_id: str
    preferred_primitives: list[str]
    usage_patterns: dict[str, int]
    success_rates: dict[str, float]
    preferred_frameworks: list[FrameworkType]
    last_updated: datetime


class SmartContextDetector:
    """Intelligent context detection and analysis system."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.cache: dict[str, ProjectContext] = {}
        self.detection_rules = self._load_detection_rules()
        self.pattern_matcher = self._initialize_pattern_matcher()

    def _load_detection_rules(self) -> dict[str, Any]:
        """Load framework and pattern detection rules."""
        return {
            "frameworks": {
                "react": {
                    "files": ["package.json", "tsconfig.json"],
                    "patterns": ["import React", "function Component", "jsx", "tsx"],
                    "dependencies": ["react", "react-dom", "@types/react"],
                    "confidence_threshold": 0.7,
                },
                "django": {
                    "files": ["manage.py", "settings.py", "urls.py"],
                    "patterns": [
                        "from django",
                        "import django",
                        "@app.route",
                        "models.py",
                    ],
                    "dependencies": ["django"],
                    "confidence_threshold": 0.8,
                },
                "fastapi": {
                    "files": ["main.py", "app.py"],
                    "patterns": ["from fastapi", "FastAPI", "@app.get", "@app.post"],
                    "dependencies": ["fastapi", "uvicorn"],
                    "confidence_threshold": 0.8,
                },
                "flask": {
                    "files": ["app.py", "wsgi.py"],
                    "patterns": ["from flask", "Flask", "@app.route"],
                    "dependencies": ["flask"],
                    "confidence_threshold": 0.7,
                },
            },
            "languages": {
                "python": [".py"],
                "javascript": [".js"],
                "typescript": [".ts", ".tsx"],
                "java": [".java"],
                "php": [".php"],
                "go": [".go"],
                "rust": [".rs"],
                "c#": [".cs"],
            },
        }

    def _initialize_pattern_matcher(self) -> dict[str, Any]:
        """Initialize pattern matching rules."""
        return {
            "performance_patterns": [
                (r"for\s+\w+\s+in\s+\w+.*:\s*$", "loop_optimization"),
                (r"async\s+def\s+\w+", "async_pattern"),
                (r"@cache", "caching_pattern"),
                (r"async with", "async_context_manager"),
            ],
            "error_patterns": [
                (r"try:\s*$", "exception_handling"),
                (r"except\s+\w+", "exception_handling"),
                (r"finally:\s*$", "exception_handling"),
            ],
            "architectural_patterns": [
                (r"class\s+\w+.*:", "class_definition"),
                (r"def\s+\w+\(.*\):\s*$", "function_definition"),
                (r"import\s+\w+", "import_statement"),
            ],
        }

    def analyze_project_context(self, force_refresh: bool = False) -> ProjectContext:
        """Analyze the complete project context."""
        context_hash = self._calculate_context_hash()

        if not force_refresh and context_hash in self.cache:
            return self.cache[context_hash]

        # Analyze project structure
        file_structure = self._analyze_file_structure()

        # Detect language
        language = self._detect_language()

        # Detect frameworks
        frameworks = self._detect_frameworks()

        # Extract code patterns
        patterns = self._extract_code_patterns()

        # Determine project stage
        stage = self._determine_project_stage(file_structure, patterns)

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(file_structure, patterns)

        # Extract dependencies
        dependencies = self._extract_dependencies()

        # Create project context
        context = ProjectContext(
            project_path=str(self.project_path),
            language=language,
            frameworks=frameworks,
            patterns=patterns,
            stage=stage,
            complexity_score=complexity_score,
            dependencies=dependencies,
            file_structure=file_structure,
            last_modified=datetime.now(),
            context_hash=context_hash,
        )

        self.cache[context_hash] = context
        return context

    def _analyze_file_structure(self) -> dict[str, Any]:
        """Analyze project file structure."""
        structure = {
            "total_files": 0,
            "directories": set(),
            "file_types": Counter(),
            "depth": 0,
            "largest_files": [],
            "test_files": 0,
            "config_files": 0,
        }

        max_depth = 0
        file_sizes = []

        try:
            for file_path in self.project_path.rglob("*"):
                if file_path.is_file():
                    structure["total_files"] += 1
                    structure["file_types"][file_path.suffix] += 1

                    depth = len(file_path.relative_to(self.project_path).parts)
                    max_depth = max(max_depth, depth)

                    try:
                        size = file_path.stat().st_size
                        file_sizes.append((file_path, size))
                    except (OSError, PermissionError):
                        continue

                    if "test" in str(file_path).lower():
                        structure["test_files"] += 1

                    if file_path.suffix in [
                        ".json",
                        ".yaml",
                        ".yml",
                        ".toml",
                        ".ini",
                        ".conf",
                        ".config",
                    ]:
                        structure["config_files"] += 1

                elif file_path.is_dir():
                    structure["directories"].add(file_path.name)

        except (OSError, PermissionError):
            pass

        structure["depth"] = max_depth
        structure["largest_files"] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
        structure["directories"] = list(structure["directories"])

        return structure

    def _detect_language(self) -> LanguageType:
        """Detect primary programming language."""
        language_counts = Counter()

        for ext, languages in self.detection_rules["languages"].items():
            for extension in languages:
                count = len(list(self.project_path.glob(f"**/*{extension}")))
                if count > 0:
                    language_counts[ext] += count

        if not language_counts:
            return LanguageType.UNKNOWN

        primary_language = language_counts.most_common(1)[0][0]
        return LanguageType(primary_language)

    def _detect_frameworks(self) -> list[FrameworkDetection]:
        """Detect frameworks used in the project."""
        detections = []

        for framework_key, rules in self.detection_rules["frameworks"].items():
            framework = FrameworkType(framework_key)
            confidence, evidence = self._calculate_framework_confidence(framework, rules)

            if confidence >= rules["confidence_threshold"]:
                detection = FrameworkDetection(
                    framework=framework, confidence=confidence, evidence=evidence
                )
                detections.append(detection)

        return detections

    def _calculate_framework_confidence(
        self, framework: FrameworkType, rules: dict[str, Any]
    ) -> tuple[float, list[str]]:
        """Calculate confidence score for framework detection."""
        evidence = []
        total_score = 0.0
        max_score = 0.0

        # File presence scoring (30% weight)
        file_score = 0.0
        for expected_file in rules.get("files", []):
            if (self.project_path / expected_file).exists():
                file_score += 1.0
                evidence.append(f"Found {expected_file}")
        if rules.get("files"):
            file_score /= len(rules["files"])
            total_score += file_score * 0.3
            max_score += 0.3

        # Pattern matching scoring (40% weight)
        pattern_score = 0.0
        if "patterns" in rules:
            total_patterns = len(rules["patterns"])
            matched_patterns = 0

            for pattern in rules["patterns"]:
                if self._search_pattern_in_project(pattern):
                    matched_patterns += 1
                    evidence.append(f"Matched pattern: {pattern}")

            if total_patterns > 0:
                pattern_score = matched_patterns / total_patterns
                total_score += pattern_score * 0.4
                max_score += 0.4

        # Dependencies scoring (30% weight)
        dep_score = 0.0
        if "dependencies" in rules:
            total_deps = len(rules["dependencies"])
            found_deps = 0

            for dep in rules["dependencies"]:
                if self._find_dependency(dep):
                    found_deps += 1
                    evidence.append(f"Found dependency: {dep}")

            if total_deps > 0:
                dep_score = found_deps / total_deps
                total_score += dep_score * 0.3
                max_score += 0.3

        # Calculate final confidence
        confidence = total_score / max_score if max_score > 0 else 0.0
        return min(confidence, 1.0), evidence

    def _search_pattern_in_project(self, pattern: str) -> bool:
        """Search for a pattern in project files."""
        try:
            for file_path in self.project_path.rglob("*.py"):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        if re.search(pattern, content):
                            return True
                except (UnicodeDecodeError, OSError):
                    continue
        except (OSError, PermissionError):
            pass

        return False

    def _find_dependency(self, dependency: str) -> bool:
        """Check if dependency is present in project files."""
        # Check common dependency files
        dependency_files = [
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "Pipfile",
            "poetry.lock",
        ]

        for dep_file in dependency_files:
            dep_path = self.project_path / dep_file
            if dep_path.exists():
                try:
                    with open(dep_path, encoding="utf-8") as f:
                        content = f.read()
                        if dependency in content:
                            return True
                except (UnicodeDecodeError, OSError):
                    continue

        return False

    def _extract_code_patterns(self) -> list[CodePattern]:
        """Extract code patterns from project files."""
        patterns = []

        for category, pattern_list in self.pattern_matcher.items():
            for regex_pattern, pattern_name in pattern_list:
                for file_path in self.project_path.rglob("*.py"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            lines = f.readlines()

                        for line_num, line in enumerate(lines, 1):
                            if re.search(regex_pattern, line):
                                pattern = CodePattern(
                                    name=pattern_name,
                                    confidence=0.8,
                                    file_path=str(file_path.relative_to(self.project_path)),
                                    line_number=line_num,
                                    pattern_type=category,
                                    context={
                                        "line_content": line.strip(),
                                        "category": category,
                                    },
                                )
                                patterns.append(pattern)
                    except (UnicodeDecodeError, OSError):
                        continue

        return patterns

    def _determine_project_stage(
        self, file_structure: dict[str, Any], patterns: list[CodePattern]
    ) -> ProjectStage:
        """Determine the development stage of the project."""
        test_file_ratio = file_structure.get("test_files", 0) / max(
            file_structure.get("total_files", 1), 1
        )
        config_file_ratio = file_structure.get("config_files", 0) / max(
            file_structure.get("total_files", 1), 1
        )

        # Production indicators
        production_indicators = [
            test_file_ratio > 0.3,  # High test coverage
            config_file_ratio > 0.1,  # Configuration files present
            len(patterns) > 50,  # Complex codebase
            file_structure.get("depth", 0) > 3,  # Deep directory structure
        ]

        # Maintenance indicators
        maintenance_indicators = [
            test_file_ratio > 0.5,  # Very high test coverage
            config_file_ratio > 0.2,  # Lots of configuration
            file_structure.get("total_files", 0) > 100,  # Large codebase
        ]

        if sum(maintenance_indicators) >= 2:
            return ProjectStage.MAINTENANCE
        elif sum(production_indicators) >= 2:
            return ProjectStage.PRODUCTION
        elif file_structure.get("total_files", 0) > 20:
            return ProjectStage.DEVELOPMENT
        else:
            return ProjectStage.PROTOTYPING

    def _calculate_complexity_score(
        self, file_structure: dict[str, Any], patterns: list[CodePattern]
    ) -> float:
        """Calculate project complexity score (0.0 to 1.0)."""
        factors = {
            "file_count": min(file_structure.get("total_files", 0) / 100, 1.0),
            "depth": min(file_structure.get("depth", 0) / 10, 1.0),
            "pattern_density": min(len(patterns) / 50, 1.0),
            "file_type_diversity": min(len(file_structure.get("file_types", {})) / 10, 1.0),
        }

        return sum(factors.values()) / len(factors)

    def _extract_dependencies(self) -> dict[str, str]:
        """Extract project dependencies."""
        dependencies = {}

        # Try to extract from different dependency files
        dep_files = [
            ("requirements.txt", self._parse_requirements_txt),
            ("package.json", self._parse_package_json),
            ("pyproject.toml", self._parse_pyproject_toml),
            ("Pipfile", self._parse_pipfile),
        ]

        for dep_file, parser in dep_files:
            dep_path = self.project_path / dep_file
            if dep_path.exists():
                try:
                    deps = parser(dep_path)
                    dependencies.update(deps)
                except (OSError, ValueError):
                    continue

        return dependencies

    def _parse_requirements_txt(self, file_path: Path) -> dict[str, str]:
        """Parse requirements.txt file."""
        dependencies = {}
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        dependencies[name.strip()] = version.strip()
                    else:
                        dependencies[line] = "unknown"
        return dependencies

    def _parse_package_json(self, file_path: Path) -> dict[str, str]:
        """Parse package.json file."""
        import json

        dependencies = {}
        with open(file_path) as f:
            data = json.load(f)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            dependencies.update(deps)
            dependencies.update(dev_deps)
        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> dict[str, str]:
        """Parse pyproject.toml file."""
        import tomli

        dependencies = {}
        with open(file_path, "rb") as f:
            data = tomli.load(f)
            deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            if "python" in deps:
                del deps["python"]
            dependencies.update({k: str(v) for k, v in deps.items()})
        return dependencies

    def _parse_pipfile(self, file_path: Path) -> dict[str, str]:
        """Parse Pipfile."""
        import tomli

        dependencies = {}
        with open(file_path, "rb") as f:
            data = tomli.load(f)
            deps = data.get("packages", {})
            dev_deps = data.get("dev-packages", {})
            dependencies.update({k: str(v) for k, v in deps.items()})
            dependencies.update({k: str(v) for k, v in dev_deps.items()})
        return dependencies

    def _calculate_context_hash(self) -> str:
        """Calculate hash of current project context."""
        context_data = {"project_path": str(self.project_path), "modified_times": []}

        try:
            for file_path in self.project_path.rglob("*"):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        context_data["modified_times"].append(
                            (str(file_path.relative_to(self.project_path)), mtime)
                        )
                    except (OSError, PermissionError):
                        continue

            context_data["modified_times"].sort()
            hash_input = json.dumps(context_data, sort_keys=True)
            return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        except (OSError, PermissionError):
            return "fallback_hash"


class AdaptiveLearningSystem:
    """System for learning from user interactions and improving recommendations."""

    def __init__(self, data_path: str = "/tmp/cline_learning_data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        self.user_profiles: dict[str, UserPreferences] = {}
        self.interaction_history: list[dict[str, Any]] = []
        self.load_user_data()

    def record_interaction(
        self,
        developer_id: str,
        context: ProjectContext,
        primitive_suggested: str,
        outcome: str,
        feedback: float = 0.5,
    ):
        """Record a user interaction for learning."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "developer_id": developer_id,
            "context_hash": context.context_hash,
            "primitive_suggested": primitive_suggested,
            "outcome": outcome,
            "feedback": feedback,
            "context_summary": {
                "language": context.language.value,
                "frameworks": [f.framework.value for f in context.frameworks],
                "stage": context.stage.value,
                "complexity_score": context.complexity_score,
            },
        }

        self.interaction_history.append(interaction)
        self._update_user_profile(developer_id, interaction)
        self._save_user_data()

    def _update_user_profile(self, developer_id: str, interaction: dict[str, Any]):
        """Update user profile based on interaction."""
        if developer_id not in self.user_profiles:
            self.user_profiles[developer_id] = UserPreferences(
                developer_id=developer_id,
                preferred_primitives=[],
                usage_patterns=defaultdict(int),
                success_rates=defaultdict(float),
                preferred_frameworks=[],
                last_updated=datetime.now(),
            )

        profile = self.user_profiles[developer_id]
        primitive = interaction["primitive_suggested"]
        outcome = interaction["outcome"]
        feedback = interaction["feedback"]

        # Update usage patterns
        profile.usage_patterns[primitive] += 1

        # Update success rates (simple moving average)
        if primitive in profile.success_rates:
            current_rate = profile.success_rates[primitive]
            new_rate = (current_rate + feedback) / 2
        else:
            new_rate = feedback
        profile.success_rates[primitive] = new_rate

        # Add to preferred primitives if success rate is high
        if new_rate > 0.7 and primitive not in profile.preferred_primitives:
            profile.preferred_primitives.append(primitive)

        # Update preferred frameworks
        for framework in interaction["context_summary"]["frameworks"]:
            if framework not in [f.value for f in profile.preferred_frameworks]:
                profile.preferred_frameworks.append(FrameworkType(framework))

        profile.last_updated = datetime.now()

    def get_recommendation_weights(
        self, developer_id: str, context: ProjectContext
    ) -> dict[str, float]:
        """Get recommendation weights based on user profile and context."""
        if developer_id not in self.user_profiles:
            return {}

        profile = self.user_profiles[developer_id]
        weights = {}

        # Base weights from success rates
        for primitive, rate in profile.success_rates.items():
            weights[primitive] = rate

        # Context-aware adjustments
        context_frameworks = [f.framework.value for f in context.frameworks]

        # Boost primitives for preferred frameworks
        for primitive, count in profile.usage_patterns.items():
            framework_boost = 0.0
            for framework in context_frameworks:
                if self._primitive_matches_framework(primitive, framework):
                    framework_boost += 0.1

            if primitive in weights:
                weights[primitive] += framework_boost * (
                    count / max(sum(profile.usage_patterns.values()), 1)
                )

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _primitive_matches_framework(self, primitive: str, framework: str) -> bool:
        """Check if primitive matches the framework."""
        # This would be expanded with actual framework-primitive mappings
        framework_primitives = {
            "react": ["cache_primitive", "retry_primitive", "timeout_primitive"],
            "django": ["cache_primitive", "fallback_primitive", "retry_primitive"],
            "fastapi": ["timeout_primitive", "retry_primitive", "sequential_primitive"],
            "flask": ["cache_primitive", "fallback_primitive"],
        }

        return primitive in framework_primitives.get(framework, [])

    def get_improvement_suggestions(self) -> list[dict[str, Any]]:
        """Generate improvement suggestions based on learning data."""
        suggestions = []

        # Analyze low-performing primitives
        for developer_id, profile in self.user_profiles.items():
            low_performers = [(p, rate) for p, rate in profile.success_rates.items() if rate < 0.5]
            if low_performers:
                suggestions.append(
                    {
                        "type": "primitive_improvement",
                        "developer": developer_id,
                        "primitives": low_performers,
                        "action": "review_primitives",
                    }
                )

        # Analyze underutilized high-quality patterns
        all_primitives = set()
        for interaction in self.interaction_history:
            all_primitives.add(interaction["primitive_suggested"])

        primitive_performance = defaultdict(list)
        for interaction in self.interaction_history:
            primitive_performance[interaction["primitive_suggested"]].append(
                interaction["feedback"]
            )

        avg_performance = {
            p: sum(scores) / len(scores)
            for p, scores in primitive_performance.items()
            if len(scores) > 3
        }
        underutilized = [p for p, score in avg_performance.items() if score > 0.8]

        if underutilized:
            suggestions.append(
                {
                    "type": "promote_primitives",
                    "primitives": underutilized,
                    "action": "increase_visibility",
                }
            )

        return suggestions

    def load_user_data(self):
        """Load user data from disk."""
        data_file = self.data_path / "user_profiles.json"
        interactions_file = self.data_path / "interaction_history.json"

        if data_file.exists():
            try:
                with open(data_file) as f:
                    data = json.load(f)
                    for dev_id, profile_data in data.items():
                        profile = UserPreferences(**profile_data)
                        # Convert sets and defaults back
                        profile.usage_patterns = defaultdict(int, profile.usage_patterns)
                        self.user_profiles[dev_id] = profile
            except (OSError, json.JSONDecodeError):
                pass

        if interactions_file.exists():
            try:
                with open(interactions_file) as f:
                    self.interaction_history = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

    def _save_user_data(self):
        """Save user data to disk."""
        data_file = self.data_path / "user_profiles.json"
        interactions_file = self.data_path / "interaction_history.json"

        # Convert user profiles for JSON serialization
        profiles_data = {}
        for dev_id, profile in self.user_profiles.items():
            profile_dict = asdict(profile)
            # Convert defaultdicts to regular dicts
            profile_dict["usage_patterns"] = dict(profile.usage_patterns)
            profiles_data[dev_id] = profile_dict

        try:
            with open(data_file, "w") as f:
                json.dump(profiles_data, f, indent=2, default=str)

            with open(interactions_file, "w") as f:
                json.dump(self.interaction_history, f, indent=2, default=str)
        except OSError:
            pass  # Silently fail if can't write to disk


class DynamicContextLoader:
    """Main class for dynamic context loading and management."""

    def __init__(self, project_path: str, developer_id: str = "default"):
        self.project_path = project_path
        self.developer_id = developer_id
        self.detector = SmartContextDetector(project_path)
        self.learning_system = AdaptiveLearningSystem()
        self.current_context: ProjectContext | None = None
        self.templates_cache: dict[str, Any] = {}

    def load_context(self, force_refresh: bool = False) -> ProjectContext:
        """Load and analyze current project context."""
        self.current_context = self.detector.analyze_project_context(force_refresh=force_refresh)
        return self.current_context

    def get_primitive_recommendations(
        self, context: ProjectContext | None = None
    ) -> list[tuple[str, float]]:
        """Get personalized primitive recommendations based on context."""
        if context is None:
            context = self.current_context or self.load_context()

        # Get base recommendations based on context
        base_recommendations = self._get_base_recommendations(context)

        # Get personalized weights
        weights = self.learning_system.get_recommendation_weights(self.developer_id, context)

        # Combine base and personalized recommendations
        combined_recommendations = []
        all_primitives = set(base_recommendations.keys()) | set(weights.keys())

        for primitive in all_primitives:
            base_score = base_recommendations.get(primitive, 0.0)
            personal_score = weights.get(primitive, 0.0)
            combined_score = (base_score * 0.7) + (personal_score * 0.3)
            combined_recommendations.append((primitive, combined_score))

        # Sort by score and return top recommendations
        combined_recommendations.sort(key=lambda x: x[1], reverse=True)
        return combined_recommendations[:10]  # Top 10 recommendations

    def _get_base_recommendations(self, context: ProjectContext) -> dict[str, float]:
        """Get base recommendations based on project context."""
        recommendations = {}

        # Language-based recommendations
        language_recommendations = {
            LanguageType.PYTHON: [
                "cache_primitive",
                "retry_primitive",
                "sequential_primitive",
                "timeout_primitive",
            ],
            LanguageType.JAVASCRIPT: [
                "cache_primitive",
                "fallback_primitive",
                "parallel_primitive",
            ],
            LanguageType.TYPESCRIPT: [
                "cache_primitive",
                "fallback_primitive",
                "retry_primitive",
            ],
            LanguageType.JAVA: [
                "fallback_primitive",
                "timeout_primitive",
                "retry_primitive",
            ],
            LanguageType.PHP: ["cache_primitive", "fallback_primitive"],
            LanguageType.GO: ["cache_primitive", "retry_primitive"],
            LanguageType.RUST: ["cache_primitive", "timeout_primitive"],
            LanguageType.C_SHARP: ["fallback_primitive", "retry_primitive"],
        }

        # Framework-based recommendations
        framework_recommendations = {}
        for detection in context.frameworks:
            framework = detection.framework
            if framework == FrameworkType.REACT:
                framework_recommendations.update(
                    {
                        "cache_primitive": 0.9,
                        "fallback_primitive": 0.8,
                        "retry_primitive": 0.7,
                    }
                )
            elif framework == FrameworkType.DJANGO:
                framework_recommendations.update(
                    {
                        "cache_primitive": 0.9,
                        "retry_primitive": 0.8,
                        "fallback_primitive": 0.7,
                    }
                )
            elif framework == FrameworkType.FASTAPI:
                framework_recommendations.update(
                    {
                        "timeout_primitive": 0.9,
                        "retry_primitive": 0.8,
                        "sequential_primitive": 0.7,
                    }
                )
            elif framework == FrameworkType.FLASK:
                framework_recommendations.update(
                    {"cache_primitive": 0.8, "fallback_primitive": 0.7}
                )

        # Stage-based recommendations
        stage_recommendations = {
            ProjectStage.PROTOTYPING: {
                "cache_primitive": 0.5,
                "fallback_primitive": 0.3,
            },
            ProjectStage.DEVELOPMENT: {"cache_primitive": 0.7, "retry_primitive": 0.6},
            ProjectStage.PRODUCTION: {
                "cache_primitive": 0.9,
                "fallback_primitive": 0.8,
                "retry_primitive": 0.9,
            },
            ProjectStage.MAINTENANCE: {
                "fallback_primitive": 0.9,
                "timeout_primitive": 0.8,
            },
        }

        # Complexity-based recommendations
        complexity = context.complexity_score
        if complexity > 0.7:
            recommendations.update(
                {
                    "parallel_primitive": complexity * 0.8,
                    "sequential_primitive": complexity * 0.7,
                    "router_primitive": complexity * 0.6,
                }
            )

        # Combine all recommendations
        language_primitives = language_recommendations.get(context.language, [])
        for primitive in language_primitives:
            recommendations[primitive] = max(recommendations.get(primitive, 0.0), 0.6)

        recommendations.update(framework_recommendations)
        stage_rec = stage_recommendations.get(context.stage, {})
        for primitive, score in stage_rec.items():
            recommendations[primitive] = max(recommendations.get(primitive, 0.0), score)

        return recommendations

    def record_outcome(self, primitive: str, outcome: str, feedback: float = 0.5):
        """Record the outcome of a primitive recommendation."""
        if self.current_context:
            self.learning_system.record_interaction(
                self.developer_id, self.current_context, primitive, outcome, feedback
            )

    def get_context_insights(self) -> dict[str, Any]:
        """Get insights about the current project context."""
        if not self.current_context:
            self.load_context()

        context = self.current_context

        insights = {
            "project_overview": {
                "language": context.language.value,
                "frameworks": [f.framework.value for f in context.frameworks],
                "stage": context.stage.value,
                "complexity_score": context.complexity_score,
            },
            "recommendations": {
                "top_primitives": self.get_primitive_recommendations()[:5],
                "personalized": True,
            },
            "patterns": {
                "total_patterns": len(context.patterns),
                "pattern_types": list(set(p.pattern_type for p in context.patterns)),
                "performance_patterns": [
                    p.name for p in context.patterns if p.pattern_type == "performance_patterns"
                ],
                "error_patterns": [
                    p.name for p in context.patterns if p.pattern_type == "error_patterns"
                ],
            },
            "structure": {
                "file_count": context.file_structure.get("total_files", 0),
                "test_coverage_ratio": context.file_structure.get("test_files", 0)
                / max(context.file_structure.get("total_files", 1), 1),
                "depth": context.file_structure.get("depth", 0),
            },
        }

        return insights


# Utility functions for external integration
def create_context_loader(project_path: str, developer_id: str = "default") -> DynamicContextLoader:
    """Create a configured DynamicContextLoader instance."""
    return DynamicContextLoader(project_path, developer_id)


def quick_context_analysis(project_path: str) -> dict[str, Any]:
    """Perform a quick context analysis and return insights."""
    loader = create_context_loader(project_path)
    context = loader.load_context()
    return loader.get_context_insights()


# Example usage and testing
if __name__ == "__main__":
    # Test the dynamic context loader
    project_path = "/home/thein/repos/TTA.dev"
    loader = create_context_loader(project_path)

    # Load and analyze context
    context = loader.load_context()
    print(f"Project Language: {context.language.value}")
    print(f"Detected Frameworks: {[f.framework.value for f in context.frameworks]}")
    print(f"Project Stage: {context.stage.value}")
    print(f"Complexity Score: {context.complexity_score:.2f}")

    # Get recommendations
    recommendations = loader.get_primitive_recommendations()
    print(f"Top Primitive Recommendations: {recommendations[:5]}")

    # Get insights
    insights = loader.get_context_insights()
    print(f"Context Insights: {json.dumps(insights, indent=2, default=str)}")
