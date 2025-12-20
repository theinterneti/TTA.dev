"""
Tests for InfrastructureManager - L2 Domain Manager for Infrastructure Operations

Tests coverage:
- Initialization and configuration
- Container orchestration workflows
- Image management (build, pull)
- Resource cleanup operations
- Health check monitoring
- Error handling and validation
- Integration with DockerExpert

IMPORTANT: All fixtures use actual DockerExpert API structure:
- DockerOperation(operation=str, params=dict)
- DockerResult(success=bool, operation=str, data=dict|None, error=str|None)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts.docker_expert import DockerResult
from tta_agent_coordination.managers.infrastructure_manager import (
    InfrastructureManager,
    InfrastructureManagerConfig,
    InfrastructureOperation,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def default_config():
    """Default InfrastructureManager configuration."""
    return InfrastructureManagerConfig(
        default_network="bridge",
        auto_remove_containers=True,
        auto_pull_images=True,
        container_start_timeout=30.0,
        health_check_retries=3,
        health_check_interval=5.0,
        cleanup_on_failure=True,
        volume_driver="local",
    )


@pytest.fixture
def mock_docker_expert():
    """Mock DockerExpert for testing."""
    expert = MagicMock()
    expert.execute = AsyncMock()
    return expert


@pytest.fixture
def workflow_context():
    """Workflow context for testing."""
    return WorkflowContext(correlation_id="infra-test-123")


@pytest.fixture
def mock_docker_result_container_started():
    """Mock DockerResult for successful container start."""
    return DockerResult(
        success=True,
        operation="run_container",
        data={
            "container_id": "abc123def456",
            "name": "test-container",
            "image": "nginx:latest",
            "status": "running",
        },
        error=None,
    )


@pytest.fixture
def mock_docker_result_container_failed():
    """Mock DockerResult for failed container start."""
    return DockerResult(
        success=False,
        operation="run_container",
        data=None,
        error="Failed to start container: image not found",
    )


@pytest.fixture
def mock_docker_result_image_pulled():
    """Mock DockerResult for successful image pull."""
    return DockerResult(
        success=True,
        operation="pull_image",
        data={
            "image": "nginx:latest",
            "status": "pulled",
        },
        error=None,
    )


@pytest.fixture
def mock_docker_result_image_built():
    """Mock DockerResult for successful image build."""
    return DockerResult(
        success=True,
        operation="build_image",
        data={
            "image_id": "sha256:abc123...",
            "tag": "myapp:latest",
        },
        error=None,
    )


@pytest.fixture
def mock_docker_result_containers_list():
    """Mock DockerResult for container list operation."""
    return DockerResult(
        success=True,
        operation="list_containers",
        data={
            "containers": [
                {
                    "id": "container1",
                    "state": "running",
                    "status": "Up 5 minutes",
                    "name": "web",
                },
                {
                    "id": "container2",
                    "state": "exited",
                    "status": "Exited (0) 1 hour ago",
                    "name": "worker",
                },
            ]
        },
        error=None,
    )


@pytest.fixture
def mock_docker_result_container_removed():
    """Mock DockerResult for container removal."""
    return DockerResult(
        success=True,
        operation="remove_container",
        data={
            "container_id": "container2",
            "removed": True,
        },
        error=None,
    )


# ============================================================================
# Initialization Tests
# ============================================================================


@pytest.mark.asyncio
async def test_infrastructure_manager_init_with_config(default_config):
    """Test InfrastructureManager initialization with custom config."""
    manager = InfrastructureManager(config=default_config)

    assert manager.config == default_config
    assert manager.docker_expert is not None
    assert manager.config.default_network == "bridge"
    assert manager.config.auto_remove_containers is True


@pytest.mark.asyncio
async def test_infrastructure_manager_init_with_custom_expert(
    default_config, mock_docker_expert
):
    """Test InfrastructureManager initialization with custom DockerExpert."""
    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    assert manager.docker_expert == mock_docker_expert


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_containers_invalid_operation(
    default_config, workflow_context
):
    """Test validation for invalid operation type."""
    manager = InfrastructureManager(config=default_config)

    operation = InfrastructureOperation(operation="invalid_operation")

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "Invalid operation" in result.error


@pytest.mark.asyncio
async def test_orchestrate_containers_empty_list(default_config, workflow_context):
    """Test validation for empty containers list."""
    manager = InfrastructureManager(config=default_config)

    operation = InfrastructureOperation(
        operation="orchestrate_containers", containers=[]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "requires containers list" in result.error


@pytest.mark.asyncio
async def test_orchestrate_containers_missing_image(default_config, workflow_context):
    """Test validation for container without image."""
    manager = InfrastructureManager(config=default_config)

    operation = InfrastructureOperation(
        operation="orchestrate_containers",
        containers=[{"name": "test", "command": "echo hello"}],  # Missing 'image'
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "must specify an image" in result.error


@pytest.mark.asyncio
async def test_manage_images_missing_params(default_config, workflow_context):
    """Test validation for image management without required params."""
    manager = InfrastructureManager(config=default_config)

    operation = InfrastructureOperation(
        operation="manage_images"
        # Missing both image_name and build_path
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "requires image_name or build_path" in result.error


@pytest.mark.asyncio
async def test_health_check_missing_container_ids(default_config, workflow_context):
    """Test validation for health check without container IDs."""
    manager = InfrastructureManager(config=default_config)

    operation = InfrastructureOperation(
        operation="health_check",
        container_ids=[],  # Empty list
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "requires container_ids list" in result.error


# ============================================================================
# Container Orchestration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_single_container_success(
    default_config,
    mock_docker_expert,
    mock_docker_result_container_started,
    workflow_context,
):
    """Test successful single container orchestration."""
    # Configure mock
    mock_docker_expert.execute.return_value = mock_docker_result_container_started

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="orchestrate_containers",
        containers=[{"image": "nginx:latest", "name": "web", "detach": True}],
    )

    result = await manager.execute(operation, workflow_context)

    # Verify result
    assert result.success is True
    assert result.operation == "orchestrate_containers"
    assert len(result.containers_started) == 1
    assert "abc123def456" in result.containers_started  # pragma: allowlist secret (mock container ID)
    assert result.error is None

    # Verify DockerExpert was called correctly
    assert mock_docker_expert.execute.call_count == 1
    call_args = mock_docker_expert.execute.call_args
    docker_operation = call_args[0][0]

    # Verify DockerOperation structure matches actual API
    assert docker_operation.operation == "run_container"
    assert docker_operation.params["image"] == "nginx:latest"
    assert docker_operation.params["name"] == "web"
    assert docker_operation.params["detach"] is True


@pytest.mark.asyncio
async def test_orchestrate_multiple_containers_success(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test successful multi-container orchestration."""
    # Configure mock to return different container IDs
    mock_docker_expert.execute.side_effect = [
        DockerResult(
            success=True,
            operation="run_container",
            data={"container_id": "web123"},
            error=None,
        ),
        DockerResult(
            success=True,
            operation="run_container",
            data={"container_id": "db456"},
            error=None,
        ),
    ]

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="orchestrate_containers",
        containers=[
            {"image": "nginx", "name": "web"},
            {"image": "postgres", "name": "db"},
        ],
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert len(result.containers_started) == 2
    assert "web123" in result.containers_started
    assert "db456" in result.containers_started


@pytest.mark.asyncio
async def test_orchestrate_containers_partial_failure(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test orchestration with partial failures."""
    # First container succeeds, second fails
    mock_docker_expert.execute.side_effect = [
        DockerResult(
            success=True,
            operation="run_container",
            data={"container_id": "web123"},
            error=None,
        ),
        DockerResult(
            success=False,
            operation="run_container",
            data=None,
            error="Image not found",
        ),
    ]

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="orchestrate_containers",
        containers=[
            {"image": "nginx", "name": "web"},
            {"image": "invalid:latest", "name": "app"},
        ],
    )

    result = await manager.execute(operation, workflow_context)

    # Operation fails if any container fails
    assert result.success is False
    assert len(result.containers_started) == 1  # First one succeeded
    assert "Image not found" in result.error


# ============================================================================
# Image Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_manage_images_pull_success(
    default_config,
    mock_docker_expert,
    mock_docker_result_image_pulled,
    workflow_context,
):
    """Test successful image pull."""
    mock_docker_expert.execute.return_value = mock_docker_result_image_pulled

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="manage_images", image_name="nginx", image_tag="latest"
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert result.operation == "manage_images"
    assert len(result.images_pulled) == 1
    assert "nginx:latest" in result.images_pulled

    # Verify DockerExpert called with correct API
    call_args = mock_docker_expert.execute.call_args
    docker_operation = call_args[0][0]
    assert docker_operation.operation == "pull_image"
    assert docker_operation.params["image"] == "nginx:latest"


@pytest.mark.asyncio
async def test_manage_images_build_success(
    default_config,
    mock_docker_expert,
    mock_docker_result_image_built,
    workflow_context,
):
    """Test successful image build."""
    mock_docker_expert.execute.return_value = mock_docker_result_image_built

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="manage_images",
        build_path="./Dockerfile",
        image_name="myapp",
        image_tag="v1.0",
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert len(result.images_built) == 1
    assert "sha256:abc123..." in result.images_built

    # Verify DockerExpert called with correct API
    call_args = mock_docker_expert.execute.call_args
    docker_operation = call_args[0][0]
    assert docker_operation.operation == "build_image"
    assert docker_operation.params["path"] == "./Dockerfile"
    assert docker_operation.params["tag"] == "myapp:v1.0"


@pytest.mark.asyncio
async def test_manage_images_pull_failure(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test image pull failure."""
    mock_docker_expert.execute.return_value = DockerResult(
        success=False,
        operation="pull_image",
        data=None,
        error="Image not found in registry",
    )

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="manage_images", image_name="nonexistent", image_tag="latest"
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert "Image not found in registry" in result.error


# ============================================================================
# Resource Cleanup Tests
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup_resources_success(
    default_config,
    mock_docker_expert,
    mock_docker_result_containers_list,
    mock_docker_result_container_removed,
    workflow_context,
):
    """Test successful resource cleanup."""
    # First call returns container list, second call removes stopped container
    mock_docker_expert.execute.side_effect = [
        mock_docker_result_containers_list,
        mock_docker_result_container_removed,
    ]

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="cleanup_resources", cleanup_stopped=True
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert result.operation == "cleanup_resources"
    assert len(result.containers_removed) == 1
    assert "container2" in result.containers_removed
    assert result.cleanup_summary["containers_removed"] == 1

    # Verify two calls: list_containers and remove_container
    assert mock_docker_expert.execute.call_count == 2


@pytest.mark.asyncio
async def test_cleanup_resources_no_stopped_containers(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test cleanup when no stopped containers exist."""
    # All containers are running
    mock_docker_expert.execute.return_value = DockerResult(
        success=True,
        operation="list_containers",
        data={
            "containers": [
                {"id": "container1", "state": "running"},
                {"id": "container2", "state": "running"},
            ]
        },
        error=None,
    )

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="cleanup_resources", cleanup_stopped=True
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert len(result.containers_removed) == 0


# ============================================================================
# Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_health_check_all_healthy(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test health check with all containers healthy."""
    mock_docker_expert.execute.return_value = DockerResult(
        success=True,
        operation="list_containers",
        data={
            "containers": [
                {"id": "container1", "state": "running", "status": "Up 5 minutes"},
                {"id": "container2", "state": "running", "status": "Up 10 minutes"},
            ]
        },
        error=None,
    )

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="health_check", container_ids=["container1", "container2"]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True
    assert result.operation == "health_check"
    assert len(result.health_status) == 2
    assert result.health_status["container1"]["healthy"] is True
    assert result.health_status["container2"]["healthy"] is True


@pytest.mark.asyncio
async def test_health_check_some_unhealthy(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test health check with some containers unhealthy."""
    mock_docker_expert.execute.return_value = DockerResult(
        success=True,
        operation="list_containers",
        data={
            "containers": [
                {"id": "container1", "state": "running", "status": "Up 5 minutes"},
                {"id": "container2", "state": "exited", "status": "Exited (1)"},
            ]
        },
        error=None,
    )

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="health_check", container_ids=["container1", "container2"]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False  # Not all healthy
    assert result.health_status["container1"]["healthy"] is True
    assert result.health_status["container2"]["healthy"] is False


@pytest.mark.asyncio
async def test_health_check_container_not_found(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test health check when container doesn't exist."""
    mock_docker_expert.execute.return_value = DockerResult(
        success=True, operation="list_containers", data={"containers": []}, error=None
    )

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="health_check", container_ids=["nonexistent"]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert result.health_status["nonexistent"]["state"] == "not_found"
    assert result.health_status["nonexistent"]["healthy"] is False


# ============================================================================
# Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_custom_network_configuration(
    mock_docker_expert,
    mock_docker_result_container_started,
    workflow_context,
):
    """Test container orchestration with custom network."""
    mock_docker_expert.execute.return_value = mock_docker_result_container_started

    config = InfrastructureManagerConfig(default_network="custom-net")
    manager = InfrastructureManager(config=config, docker_expert=mock_docker_expert)

    operation = InfrastructureOperation(
        operation="orchestrate_containers", containers=[{"image": "nginx"}]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is True

    # Verify network parameter passed correctly
    call_args = mock_docker_expert.execute.call_args
    docker_operation = call_args[0][0]
    assert docker_operation.params["network"] == "custom-net"


@pytest.mark.asyncio
async def test_auto_pull_disabled(
    mock_docker_expert,
    workflow_context,
):
    """Test image management with auto_pull disabled."""
    config = InfrastructureManagerConfig(auto_pull_images=False)
    manager = InfrastructureManager(config=config, docker_expert=mock_docker_expert)

    operation = InfrastructureOperation(
        operation="manage_images", image_name="nginx", image_tag="latest"
    )

    result = await manager.execute(operation, workflow_context)

    # Should not attempt pull when auto_pull is disabled and no build_path
    assert result.success is False
    assert mock_docker_expert.execute.call_count == 0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_docker_expert_exception_handling(
    default_config,
    mock_docker_expert,
    workflow_context,
):
    """Test handling of DockerExpert exceptions."""
    # Simulate DockerExpert raising an exception
    mock_docker_expert.execute.side_effect = Exception("Docker daemon not available")

    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    operation = InfrastructureOperation(
        operation="orchestrate_containers", containers=[{"image": "nginx"}]
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success is False
    assert result.error is not None
    assert "Docker daemon not available" in result.error


@pytest.mark.asyncio
async def test_close_manager(default_config, mock_docker_expert):
    """Test manager cleanup."""
    manager = InfrastructureManager(
        config=default_config, docker_expert=mock_docker_expert
    )

    # Add close method to mock
    mock_docker_expert.close = MagicMock()

    manager.close()

    # Verify close was called on expert
    mock_docker_expert.close.assert_called_once()
