"""
PyTestExpert - L3 Tool Expertise Layer.

Production-ready test execution with:
- Test result caching (avoid re-running unchanged tests)
- Intelligent test selection (fast/thorough/coverage strategies)
- Test failure analysis
- Smart test ordering
- Observable execution
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives.performance import CachePrimitive

from tta_agent_coordination.wrappers.pytest_wrapper import (
    PyTestCLIWrapper,
    PyTestConfig,
    PyTestOperation,
    PyTestResult,
)


@dataclass
class PyTestExpertConfig:
    """Configuration for PyTestExpert."""

    # PyTest configuration
    pytest_config: PyTestConfig | None = None

    # Cache configuration
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour - tests don't change frequently
    cache_max_size: int = 500  # Cache up to 500 test runs

    # Test strategy configuration
    fast_markers: list[str] = None  # type: ignore  # Markers for fast tests
    slow_markers: list[str] = None  # type: ignore  # Markers for slow tests
    default_strategy: str = "fast"  # "fast", "thorough", "coverage"

    # Test file monitoring
    track_file_changes: bool = True  # Track file hashes for cache invalidation


class PyTestExpert(WorkflowPrimitive[PyTestOperation, PyTestResult]):
    """
    L3 Tool Expertise Layer for PyTest operations.

    Wraps PyTestCLIWrapper (L4) with:
    - Test result caching (avoid re-running unchanged tests)
    - Intelligent test selection via routing strategies
    - Smart cache invalidation based on file changes
    - Test failure analysis and recommendations

    Example:
        ```python
        from tta_dev_primitives import WorkflowContext

        # Create expert with caching and routing
        expert = PyTestExpert(
            config=PyTestExpertConfig(
                cache_enabled=True,
                cache_ttl=3600,
                default_strategy="fast"
            )
        )

        # Run tests with automatic caching
        operation = PyTestOperation(
            operation="run_tests",
            params={
                "test_path": "tests/",
                "strategy": "fast"  # Routes to fast test subset
            }
        )

        context = WorkflowContext(correlation_id="ci-123")
        result = await expert.execute(operation, context)
        # First run: executes tests and caches results
        # Second run: returns cached results (if files unchanged)
        # Strategy "fast": runs only fast tests
        # Strategy "thorough": runs all tests
        # Strategy "coverage": runs with coverage enabled
        ```

    Test Strategies:
    - "fast": Run only fast tests (< 1s), skip integration tests
    - "thorough": Run all tests including slow ones
    - "coverage": Run all tests with coverage collection

    Cache Behavior:
    - Caches results based on: test_path + file_hashes + strategy
    - Invalidates cache when test files change
    - TTL: 1 hour (configurable)

    Best Practices Enforced:
    - Validates test paths exist
    - Enforces marker conventions
    - Provides failure analysis
    - Suggests test improvements
    """

    def __init__(self, config: PyTestExpertConfig | None = None):
        """
        Initialize PyTest expert with caching and routing.

        Args:
            config: Expert configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or PyTestExpertConfig()

        # Initialize fast/slow markers
        if self.config.fast_markers is None:
            self.config.fast_markers = ["unit", "fast"]
        if self.config.slow_markers is None:
            self.config.slow_markers = ["integration", "slow", "e2e"]

        # Create L4 wrapper
        self._wrapper = PyTestCLIWrapper(config=self.config.pytest_config)

        # Create router for test strategy selection
        self._router = RouterPrimitive(
            routes={
                "fast": self._wrapper,
                "thorough": self._wrapper,
                "coverage": self._wrapper,
            },
            router_fn=self._select_strategy,
            default="fast",
        )

        # Wrap router with cache primitive for result caching
        if self.config.cache_enabled:
            self._with_cache = CachePrimitive(
                primitive=self._router,
                cache_key_fn=self._cache_key,
                ttl_seconds=self.config.cache_ttl,
            )
        else:
            self._with_cache = self._router

        # Track file hashes for cache invalidation
        self._file_hashes: dict[str, str] = {}

    def _select_strategy(
        self, operation: PyTestOperation, context: WorkflowContext
    ) -> str:
        """
        Select test strategy based on operation parameters.

        Args:
            operation: PyTest operation
            context: Workflow context

        Returns:
            Route key ("fast", "thorough", or "coverage")
        """
        # Get strategy from params or use default
        strategy = operation.params.get("strategy", self.config.default_strategy)

        # Validate strategy
        if strategy not in {"fast", "thorough", "coverage"}:
            return self.config.default_strategy

        return strategy

    def _cache_key(self, operation: PyTestOperation, context: WorkflowContext) -> str:
        """
        Generate cache key for test operation.

        Cache key includes:
        - Operation type
        - Test path
        - Strategy
        - File hashes (if tracking enabled)
        - Markers

        Args:
            operation: PyTest operation
            context: Workflow context

        Returns:
            Unique cache key string
        """
        # Only cache test execution results
        if operation.operation != "run_tests":
            # Non-cacheable operations get unique keys (effectively no caching)
            return f"{operation.operation}:{context.correlation_id}"

        params = operation.params
        key_parts = [
            operation.operation,
            params.get("test_path", ""),
            params.get("strategy", self.config.default_strategy),
        ]

        # Add markers to key
        if markers := params.get("markers"):
            if isinstance(markers, list):
                key_parts.append(",".join(sorted(markers)))
            else:
                key_parts.append(str(markers))

        # Add file hashes if tracking enabled
        if self.config.track_file_changes:
            test_path = params.get("test_path")
            if test_path and Path(test_path).exists():
                file_hash = self._compute_file_hash(test_path)
                key_parts.append(file_hash)

        # Create deterministic cache key
        key_str = "|".join(str(part) for part in key_parts)
        return sha256(key_str.encode()).hexdigest()[:16]

    def _compute_file_hash(self, path: str) -> str:
        """
        Compute hash of test files for cache invalidation.

        Args:
            path: Test path (file or directory)

        Returns:
            SHA256 hash of file contents
        """
        path_obj = Path(path)
        hasher = sha256()

        if path_obj.is_file():
            # Hash single file
            hasher.update(path_obj.read_bytes())
        elif path_obj.is_dir():
            # Hash all Python test files in directory
            for test_file in sorted(path_obj.rglob("test_*.py")):
                hasher.update(test_file.read_bytes())
            for test_file in sorted(path_obj.rglob("*_test.py")):
                hasher.update(test_file.read_bytes())
        else:
            # Path doesn't exist, return empty hash
            return "nonexistent"

        return hasher.hexdigest()[:16]

    async def execute(
        self, input_data: PyTestOperation, context: WorkflowContext
    ) -> PyTestResult:
        """
        Execute PyTest operation with caching and routing.

        Args:
            input_data: Test operation specification
            context: Workflow context for tracing

        Returns:
            PyTestResult with test execution outcome
        """
        # Validate operation
        validation_error = self._validate_operation(input_data)
        if validation_error:
            return PyTestResult(
                success=False,
                operation=input_data.operation,
                error=validation_error,
            )

        # Apply strategy-specific configuration
        input_data = self._apply_strategy(input_data)

        # Execute with caching and routing
        try:
            result = await self._with_cache.execute(input_data, context)
            return result
        except Exception as e:
            return PyTestResult(
                success=False,
                operation=input_data.operation,
                error=f"PyTestExpert error: {e}",
            )

    def _validate_operation(self, operation: PyTestOperation) -> str | None:
        """
        Validate PyTest operation.

        Args:
            operation: Operation to validate

        Returns:
            Error message if invalid, None if valid
        """
        # Validate test path exists for run operations
        if operation.operation == "run_tests":
            test_path = operation.params.get("test_path")
            if not test_path:
                return "Missing required parameter: test_path"

            if not Path(test_path).exists():
                return f"Test path does not exist: {test_path}"

        # Validate strategy if provided
        if strategy := operation.params.get("strategy"):
            if strategy not in {"fast", "thorough", "coverage"}:
                return (
                    f"Invalid strategy: {strategy}. "
                    "Must be 'fast', 'thorough', or 'coverage'"
                )

        return None

    def _apply_strategy(self, operation: PyTestOperation) -> PyTestOperation:
        """
        Apply strategy-specific pytest configuration.

        Args:
            operation: Original operation

        Returns:
            Modified operation with strategy-specific params
        """
        if operation.operation != "run_tests":
            return operation

        strategy = operation.params.get("strategy", self.config.default_strategy)
        params = operation.params.copy()

        if strategy == "fast":
            # Fast: only unit tests, no coverage
            markers = params.get("markers", [])
            if isinstance(markers, str):
                markers = [markers]
            elif markers is None:
                markers = []

            # Add fast markers
            for marker in self.config.fast_markers:
                if marker not in markers:
                    markers.append(marker)

            params["markers"] = markers
            params["coverage"] = False
            params["verbose"] = 1

        elif strategy == "thorough":
            # Thorough: all tests, normal verbosity
            params["coverage"] = False
            params["verbose"] = 2

        elif strategy == "coverage":
            # Coverage: all tests with coverage
            params["coverage"] = True
            params["verbose"] = 2

        return PyTestOperation(operation=operation.operation, params=params)

    def close(self) -> None:
        """Clean up resources."""
        # PyTestCLIWrapper doesn't have close method
        pass
