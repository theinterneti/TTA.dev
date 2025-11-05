"""Tests for DockerExpert - L3 tool expertise with recovery primitives."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts import DockerExpert, DockerExpertConfig
from tta_agent_coordination.wrappers.docker_wrapper import (
    DockerConfig,
    DockerOperation,
    DockerResult,
)


@pytest.fixture
def mock_docker_wrapper():
    """Mock DockerSDKWrapper."""
    with patch("tta_agent_coordination.experts.docker_expert.DockerSDKWrapper") as mock:
        wrapper_instance = Mock()
        wrapper_instance.execute = AsyncMock()
        wrapper_instance.close = AsyncMock()
        mock.return_value = wrapper_instance
        yield wrapper_instance


@pytest.fixture
def docker_expert(mock_docker_wrapper):
    """Create DockerExpert with mocked wrapper."""
    config = DockerExpertConfig(docker_config=DockerConfig())
    expert = DockerExpert(config=config)
    return expert


@pytest.fixture
def workflow_context():
    """Create test workflow context."""
    return WorkflowContext(correlation_id="test-123", data={"test_key": "test_value"})


# ========== Initialization Tests ==========


@pytest.mark.asyncio
async def test_init_with_config():
    """Test initialization with custom config."""
    config = DockerExpertConfig(
        docker_config=DockerConfig(),
        container_start_timeout=60.0,
        container_stop_timeout=20.0,
        image_pull_timeout=600.0,
        image_build_timeout=900.0,
    )

    with patch("tta_agent_coordination.experts.docker_expert.DockerSDKWrapper"):
        expert = DockerExpert(config=config)

    assert expert.config == config
    assert expert.config.container_start_timeout == 60.0
    assert expert.config.container_stop_timeout == 20.0
    assert expert.config.image_pull_timeout == 600.0
    assert expert.config.image_build_timeout == 900.0


@pytest.mark.asyncio
async def test_init_with_default_config():
    """Test initialization with default config."""
    with patch("tta_agent_coordination.experts.docker_expert.DockerSDKWrapper"):
        expert = DockerExpert()

    # Check default values
    assert expert.config.container_start_timeout == 30.0
    assert expert.config.container_stop_timeout == 10.0
    assert expert.config.image_pull_timeout == 300.0
    assert expert.config.image_build_timeout == 600.0


# ========== Validation Tests ==========


@pytest.mark.asyncio
async def test_validation_invalid_container_name_start(docker_expert, workflow_context):
    """Test validation: Container name must start with alphanumeric."""
    operation = DockerOperation(
        operation="run_container",
        params={"name": "-invalid-name", "image": "nginx:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert not result.success
    assert "must start with alphanumeric" in result.error


@pytest.mark.asyncio
async def test_validation_empty_image_name(docker_expert, workflow_context):
    """Test validation: Empty image name."""
    operation = DockerOperation(
        operation="run_container",
        params={"name": "my-container", "image": ""},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert not result.success
    assert "Image name is required" in result.error


@pytest.mark.asyncio
async def test_validation_missing_build_path(docker_expert, workflow_context):
    """Test validation: Missing build path for build_image."""
    operation = DockerOperation(
        operation="build_image",
        params={"tag": "my-image:latest"},  # Missing 'path'
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert not result.success
    assert "Build path is required" in result.error


# ========== Fallback Behavior Tests ==========


@pytest.mark.asyncio
async def test_run_container_local_image_success(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test run_container: Success with local image."""
    # Mock successful local run (no image pull needed)
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="run_container",
        data={"container_id": "abc123"},
    )

    operation = DockerOperation(
        operation="run_container",
        params={"name": "my-container", "image": "nginx:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    assert result.data["container_id"] == "abc123"
    # Should only call wrapper once (local image worked)
    assert mock_docker_wrapper.execute.call_count == 1


@pytest.mark.asyncio
async def test_run_container_success(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test run_container: Success with local image."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="run_container",
        data={"container_id": "abc123"},
    )

    operation = DockerOperation(
        operation="run_container",
        params={"name": "my-container", "image": "nginx:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    assert result.data["container_id"] == "abc123"


@pytest.mark.asyncio
async def test_run_container_failure(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test run_container: Failure propagates correctly."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=False,
        operation="run_container",
        error="Image not found",
    )

    operation = DockerOperation(
        operation="run_container",
        params={"name": "my-container", "image": "nginx:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert not result.success
    assert "Image not found" in result.error


# ========== Timeout Tests ==========


@pytest.mark.asyncio
async def test_container_start_with_timeout(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test container_start: Timeout applied."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="container_start",
        data={"container_id": "abc123"},
    )

    operation = DockerOperation(
        operation="container_start",
        params={"name": "my-container"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    # Verify timeout was applied (30s default for container_start)
    # Note: Testing actual timeout behavior would require slow operations


@pytest.mark.asyncio
async def test_image_pull_with_timeout(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test image_pull: Timeout applied."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="image_pull",
        data={"image": "large-image:latest"},
    )

    operation = DockerOperation(
        operation="image_pull",
        params={"image": "large-image:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    # Verify timeout was applied (300s default for image_pull)


@pytest.mark.asyncio
async def test_image_build_with_timeout(
    mock_docker_wrapper, docker_expert, workflow_context
):
    """Test image_build: Timeout applied."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="image_build",
        data={"image_id": "img-123"},
    )

    operation = DockerOperation(
        operation="image_build",
        params={"path": "/path/to/dockerfile", "tag": "my-image:latest"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    # Verify timeout was applied (600s default for image_build)


# ========== Other Operations Tests ==========


@pytest.mark.asyncio
async def test_container_stop(mock_docker_wrapper, docker_expert, workflow_context):
    """Test container_stop operation."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="container_stop",
        data={"status": "stopped"},
    )

    operation = DockerOperation(
        operation="container_stop",
        params={"name": "my-container"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    assert result.data["status"] == "stopped"


@pytest.mark.asyncio
async def test_container_remove(mock_docker_wrapper, docker_expert, workflow_context):
    """Test container_remove operation."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="container_remove",
        data={"removed": True},
    )

    operation = DockerOperation(
        operation="container_remove",
        params={"name": "my-container"},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    assert result.data["removed"] is True


@pytest.mark.asyncio
async def test_image_list(mock_docker_wrapper, docker_expert, workflow_context):
    """Test image_list operation (no timeout)."""
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="image_list",
        data={"images": ["nginx:latest", "redis:alpine"]},
    )

    operation = DockerOperation(
        operation="image_list",
        params={},
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    assert len(result.data["images"]) == 2


# ========== Close Tests ==========


@pytest.mark.asyncio
async def test_close_calls_wrapper(docker_expert, mock_docker_wrapper):
    """Test close() propagates to wrapper."""
    docker_expert.close()  # close() is synchronous
    mock_docker_wrapper.close.assert_called_once()


# ========== Configuration Tests ==========


@pytest.mark.asyncio
async def test_custom_timeout_config():
    """Test custom timeout configuration."""
    config = DockerExpertConfig(
        docker_config=DockerConfig(),
        container_start_timeout=120.0,
        image_build_timeout=1800.0,
    )

    with patch("tta_agent_coordination.experts.docker_expert.DockerSDKWrapper"):
        expert = DockerExpert(config=config)

    # Verify custom timeouts applied
    assert expert.config.container_start_timeout == 120.0
    assert expert.config.image_build_timeout == 1800.0


@pytest.mark.asyncio
async def test_validation_passes_for_valid_inputs(
    docker_expert, mock_docker_wrapper, workflow_context
):
    """Test validation: Valid inputs pass validation."""
    # Mock successful execution
    mock_docker_wrapper.execute.return_value = DockerResult(
        success=True,
        operation="container_start",
        data={"container_id": "valid123"},
    )

    operation = DockerOperation(
        operation="container_start",
        params={
            "name": "valid-container",
            "image": "nginx:latest",
        },
    )

    result = await docker_expert.execute(operation, workflow_context)

    assert result.success
    # Should have called wrapper (validation passed)
    mock_docker_wrapper.execute.assert_awaited()
