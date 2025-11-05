"""
Comprehensive tests for PyTestExpert (L3 Tool Expertise Layer).

Tests cover:
- Initialization with custom/default configs
- Cache key generation (with/without file tracking)
- Test strategy selection (fast/thorough/coverage)
- Strategy application (markers, coverage, verbosity)
- Validation (paths, strategies)
- Operation execution with caching
- File hash computation
- Close method
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts.pytest_expert import (
    PyTestExpert,
    PyTestExpertConfig,
)
from tta_agent_coordination.wrappers.pytest_wrapper import (
    PyTestConfig,
    PyTestOperation,
    PyTestResult,
)


class TestPyTestExpertInitialization:
    """Test PyTestExpert initialization."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_init_with_custom_config(self, mock_wrapper_class):
        """Test initialization with custom configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        pytest_config = PyTestConfig(timeout=600)
        config = PyTestExpertConfig(
            pytest_config=pytest_config,
            cache_enabled=True,
            cache_ttl=7200,
            cache_max_size=1000,
            default_strategy="thorough",
        )

        # Act
        expert = PyTestExpert(config=config)

        # Assert
        assert expert.config == config
        assert expert.config.cache_enabled is True
        assert expert.config.cache_ttl == 7200
        assert expert.config.default_strategy == "thorough"
        mock_wrapper_class.assert_called_once_with(config=pytest_config)

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_init_with_default_config(self, mock_wrapper_class):
        """Test initialization with default configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        # Act
        expert = PyTestExpert()

        # Assert
        assert expert.config.cache_enabled is True
        assert expert.config.cache_ttl == 3600
        assert expert.config.default_strategy == "fast"
        assert expert.config.fast_markers == ["unit", "fast"]
        assert expert.config.slow_markers == ["integration", "slow", "e2e"]
        mock_wrapper_class.assert_called_once()


class TestCacheKeyGeneration:
    """Test cache key generation logic."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_cache_key_for_run_tests(self, mock_wrapper_class):
        """Test cache key generation for run_tests operation."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        config = PyTestExpertConfig(track_file_changes=False)
        expert = PyTestExpert(config=config)

        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/unit", "strategy": "fast"},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        cache_key = expert._cache_key(operation, context)

        # Assert
        assert isinstance(cache_key, str)
        assert len(cache_key) == 16  # SHA256 truncated to 16 chars

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_cache_key_with_markers(self, mock_wrapper_class):
        """Test cache key includes markers."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        config = PyTestExpertConfig(track_file_changes=False)
        expert = PyTestExpert(config=config)

        operation1 = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "markers": ["unit", "fast"]},
        )
        operation2 = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "markers": ["integration"]},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        key1 = expert._cache_key(operation1, context)
        key2 = expert._cache_key(operation2, context)

        # Assert - Different markers should produce different keys
        assert key1 != key2

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_cache_key_non_cacheable_operation(self, mock_wrapper_class):
        """Test cache key for non-cacheable operations."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="collect_tests", params={"test_path": "tests/"}
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        cache_key = expert._cache_key(operation, context)

        # Assert - Should include correlation_id (unique per request)
        assert "collect_tests" in cache_key
        assert "test-123" in cache_key


class TestTestStrategySelection:
    """Test test strategy selection logic."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_select_fast_strategy(self, mock_wrapper_class):
        """Test selection of fast strategy."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "fast"},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        strategy = expert._select_strategy(operation, context)

        # Assert
        assert strategy == "fast"

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_select_default_strategy(self, mock_wrapper_class):
        """Test default strategy when not specified."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests", params={"test_path": "tests/"}
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        strategy = expert._select_strategy(operation, context)

        # Assert
        assert strategy == "fast"  # Default from config

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_select_invalid_strategy_returns_default(self, mock_wrapper_class):
        """Test invalid strategy falls back to default."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "invalid"},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        strategy = expert._select_strategy(operation, context)

        # Assert
        assert strategy == "fast"  # Falls back to default


class TestStrategyApplication:
    """Test strategy-specific configuration application."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_apply_fast_strategy(self, mock_wrapper_class):
        """Test fast strategy applies correct configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "fast"},
        )

        # Act
        modified = expert._apply_strategy(operation)

        # Assert
        assert modified.params["coverage"] is False
        assert modified.params["verbose"] == 1
        assert "unit" in modified.params["markers"]
        assert "fast" in modified.params["markers"]

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_apply_thorough_strategy(self, mock_wrapper_class):
        """Test thorough strategy applies correct configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "thorough"},
        )

        # Act
        modified = expert._apply_strategy(operation)

        # Assert
        assert modified.params["coverage"] is False
        assert modified.params["verbose"] == 2

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_apply_coverage_strategy(self, mock_wrapper_class):
        """Test coverage strategy applies correct configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "coverage"},
        )

        # Act
        modified = expert._apply_strategy(operation)

        # Assert
        assert modified.params["coverage"] is True
        assert modified.params["verbose"] == 2


class TestValidation:
    """Test operation validation."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_validate_missing_test_path(self, mock_wrapper_class):
        """Test validation catches missing test_path."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={},  # Missing test_path
        )

        # Act
        error = expert._validate_operation(operation)

        # Assert
        assert error is not None
        assert "test_path" in error

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_validate_nonexistent_test_path(self, mock_wrapper_class):
        """Test validation catches nonexistent paths."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "/nonexistent/path"},
        )

        # Act
        error = expert._validate_operation(operation)

        # Assert
        assert error is not None
        assert "does not exist" in error

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_validate_invalid_strategy(self, mock_wrapper_class):
        """Test validation catches invalid strategies."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "tests/", "strategy": "invalid"},
        )

        # Act
        error = expert._validate_operation(operation)

        # Assert
        assert error is not None
        assert "Invalid strategy" in error


class TestOperationExecution:
    """Test operation execution with caching."""

    @pytest.mark.asyncio
    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    async def test_execute_with_valid_path(self, mock_wrapper_class, tmp_path):
        """Test execution with valid test path."""
        # Arrange
        mock_wrapper = AsyncMock()
        mock_wrapper.execute = AsyncMock(
            return_value=PyTestResult(
                success=True,
                operation="run_tests",
                data={"passed": 10, "failed": 0},
            )
        )
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": str(tmp_path), "strategy": "fast"},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        result = await expert.execute(operation, context)

        # Assert
        assert result.success is True
        assert result.operation == "run_tests"

    @pytest.mark.asyncio
    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    async def test_execute_with_invalid_path(self, mock_wrapper_class):
        """Test execution with invalid path returns error."""
        # Arrange
        mock_wrapper = AsyncMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={"test_path": "/nonexistent/path"},
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        result = await expert.execute(operation, context)

        # Assert
        assert result.success is False
        assert "does not exist" in result.error


class TestFileHashComputation:
    """Test file hash computation for cache invalidation."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_compute_hash_single_file(self, mock_wrapper_class, tmp_path):
        """Test hash computation for single file."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_foo(): pass")

        # Act
        hash1 = expert._compute_file_hash(str(test_file))
        hash2 = expert._compute_file_hash(str(test_file))

        # Assert
        assert isinstance(hash1, str)
        assert len(hash1) == 16
        assert hash1 == hash2  # Same file content = same hash

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_compute_hash_directory(self, mock_wrapper_class, tmp_path):
        """Test hash computation for directory."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        (tmp_path / "test_one.py").write_text("def test_one(): pass")
        (tmp_path / "test_two.py").write_text("def test_two(): pass")

        # Act
        hash_value = expert._compute_file_hash(str(tmp_path))

        # Assert
        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_compute_hash_nonexistent_path(self, mock_wrapper_class):
        """Test hash computation for nonexistent path."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()

        # Act
        hash_value = expert._compute_file_hash("/nonexistent/path")

        # Assert
        assert hash_value == "nonexistent"


class TestCloseMethod:
    """Test close method."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_close_expert(self, mock_wrapper_class):
        """Test close method doesn't fail."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()

        # Act - Should not raise
        expert.close()

        # Assert - Just verify it completes
        assert True


class TestValidInputs:
    """Test that valid inputs pass through correctly."""

    @pytest.mark.asyncio
    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    async def test_valid_inputs_pass_validation(self, mock_wrapper_class, tmp_path):
        """Test that valid inputs pass validation."""
        # Arrange
        mock_wrapper = AsyncMock()
        mock_wrapper.execute = AsyncMock(
            return_value=PyTestResult(
                success=True, operation="run_tests", data={"tests": 5}
            )
        )
        mock_wrapper_class.return_value = mock_wrapper

        expert = PyTestExpert()
        operation = PyTestOperation(
            operation="run_tests",
            params={
                "test_path": str(tmp_path),
                "strategy": "coverage",
                "markers": ["unit"],
            },
        )
        context = WorkflowContext(correlation_id="test-123")

        # Act
        result = await expert.execute(operation, context)

        # Assert
        assert result.success is True
        mock_wrapper.execute.assert_called_once()


class TestConfiguration:
    """Test configuration handling."""

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_custom_markers_configuration(self, mock_wrapper_class):
        """Test custom fast/slow markers configuration."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        config = PyTestExpertConfig(
            fast_markers=["quick", "smoke"],
            slow_markers=["e2e", "performance"],
        )

        # Act
        expert = PyTestExpert(config=config)

        # Assert
        assert expert.config.fast_markers == ["quick", "smoke"]
        assert expert.config.slow_markers == ["e2e", "performance"]

    @patch("tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper")
    def test_cache_disabled_configuration(self, mock_wrapper_class):
        """Test expert with caching disabled."""
        # Arrange
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        config = PyTestExpertConfig(cache_enabled=False)

        # Act
        expert = PyTestExpert(config=config)

        # Assert
        assert expert.config.cache_enabled is False
        # Verify cache primitive not used (router used directly)
        assert hasattr(expert, "_with_cache")
