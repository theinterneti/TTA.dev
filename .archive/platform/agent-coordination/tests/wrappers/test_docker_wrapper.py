"""
Tests for Docker SDK Wrapper (L4 Execution Layer).

Comprehensive test coverage for DockerSDKWrapper including:
- Container operations
- Image operations
- Volume operations
- Network operations
- Error handling
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from docker.errors import APIError, ImageNotFound, NotFound
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.wrappers.docker_wrapper import (
    DockerConfig,
    DockerOperation,
    DockerSDKWrapper,
)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client."""
    with patch(
        "tta_agent_coordination.wrappers.docker_wrapper.docker.DockerClient"
    ) as mock:
        client_instance = MagicMock()
        client_instance.ping.return_value = True
        mock.return_value = client_instance
        yield mock


@pytest.fixture
def wrapper(mock_docker_client):
    """Create Docker wrapper with mock client."""
    config = DockerConfig()
    wrapper = DockerSDKWrapper(config=config)
    return wrapper


@pytest.fixture
def context():
    """Create workflow context."""
    return WorkflowContext(correlation_id="test-123")


class TestDockerSDKWrapper:
    """Test suite for DockerSDKWrapper."""

    def test_init_with_config(self, mock_docker_client):
        """Test initialization with explicit config."""
        config = DockerConfig(timeout=120, version="1.43")
        wrapper = DockerSDKWrapper(config=config)

        assert wrapper.config.timeout == 120
        assert wrapper.config.version == "1.43"

    def test_init_connection_error(self):
        """Test initialization with connection error."""
        with patch(
            "tta_agent_coordination.wrappers.docker_wrapper.docker.DockerClient"
        ) as mock:
            mock.side_effect = Exception("Connection refused")

            with pytest.raises(
                ConnectionError, match="Failed to connect to Docker daemon"
            ):
                DockerSDKWrapper()

    @pytest.mark.asyncio
    async def test_run_container_success(self, wrapper, context):
        """Test successful container run."""
        # Setup mock
        mock_container = MagicMock()
        mock_container.id = "container123"
        mock_container.name = "test-container"
        mock_container.logs.return_value = b"Hello World\n"

        wrapper.client.containers.run = MagicMock(return_value=mock_container)

        # Execute
        operation = DockerOperation(
            operation="run_container",
            params={
                "image": "python:3.11",
                "command": "python --version",
                "remove": True,
            },
        )

        result = await wrapper.execute(operation, context)

        # Assert
        assert result.success is True
        assert result.data["container_id"] == "container123"
        assert "Hello World" in result.data["logs"]

    @pytest.mark.asyncio
    async def test_run_container_detached(self, wrapper, context):
        """Test running container in detached mode."""
        mock_container = MagicMock()
        mock_container.id = "container456"
        mock_container.name = "detached-container"
        mock_container.status = "running"

        wrapper.client.containers.run = MagicMock(return_value=mock_container)

        operation = DockerOperation(
            operation="run_container",
            params={"image": "nginx:latest", "detach": True, "ports": {"80/tcp": 8080}},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["status"] == "running"

    @pytest.mark.asyncio
    async def test_run_container_missing_image(self, wrapper, context):
        """Test container run with missing image parameter."""
        operation = DockerOperation(
            operation="run_container", params={"command": "echo test"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: image" in result.error

    @pytest.mark.asyncio
    async def test_stop_container_success(self, wrapper, context):
        """Test stopping container."""
        mock_container = MagicMock()
        mock_container.id = "container123"
        mock_container.status = "exited"

        wrapper.client.containers.get = MagicMock(return_value=mock_container)

        operation = DockerOperation(
            operation="stop_container",
            params={"container_id": "container123", "timeout": 5},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["status"] == "exited"
        mock_container.stop.assert_called_once_with(timeout=5)

    @pytest.mark.asyncio
    async def test_remove_container_success(self, wrapper, context):
        """Test removing container."""
        mock_container = MagicMock()
        mock_container.id = "container123"

        wrapper.client.containers.get = MagicMock(return_value=mock_container)

        operation = DockerOperation(
            operation="remove_container",
            params={"container_id": "container123", "force": True},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["removed"] is True
        mock_container.remove.assert_called_once_with(force=True, v=False)

    @pytest.mark.asyncio
    async def test_list_containers_success(self, wrapper, context):
        """Test listing containers."""
        mock_container1 = MagicMock()
        mock_container1.id = "c1"
        mock_container1.name = "container1"
        mock_container1.status = "running"
        mock_container1.image.tags = ["python:3.11"]

        mock_container2 = MagicMock()
        mock_container2.id = "c2"
        mock_container2.name = "container2"
        mock_container2.status = "exited"
        mock_container2.image.tags = ["nginx:latest"]

        wrapper.client.containers.list = MagicMock(
            return_value=[mock_container1, mock_container2]
        )

        operation = DockerOperation(
            operation="list_containers",
            params={"all": True, "filters": {"status": "running"}},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 2
        assert result.data["containers"][0]["name"] == "container1"

    @pytest.mark.asyncio
    async def test_get_container_logs_success(self, wrapper, context):
        """Test getting container logs."""
        mock_container = MagicMock()
        mock_container.id = "container123"
        mock_container.logs.return_value = b"Log line 1\nLog line 2\n"

        wrapper.client.containers.get = MagicMock(return_value=mock_container)

        operation = DockerOperation(
            operation="get_container_logs",
            params={"container_id": "container123", "tail": 100},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert "Log line 1" in result.data["logs"]
        assert "Log line 2" in result.data["logs"]

    @pytest.mark.asyncio
    async def test_build_image_success(self, wrapper, context):
        """Test building image."""
        mock_image = MagicMock()
        mock_image.id = "sha256:abc123"
        mock_image.tags = ["myapp:latest"]
        mock_image.attrs = {"Size": 1024000}

        build_logs = [
            {"stream": "Step 1/3 : FROM python:3.11"},
            {"stream": "Step 2/3 : COPY . /app"},
            {"stream": "Successfully built abc123"},
        ]

        wrapper.client.images.build = MagicMock(return_value=(mock_image, build_logs))

        operation = DockerOperation(
            operation="build_image",
            params={"path": "/path/to/dockerfile", "tag": "myapp:latest"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["image_id"] == "sha256:abc123"
        assert "Successfully built" in result.data["build_logs"]

    @pytest.mark.asyncio
    async def test_pull_image_success(self, wrapper, context):
        """Test pulling image."""
        mock_image = MagicMock()
        mock_image.id = "sha256:xyz789"
        mock_image.tags = ["python:3.11"]
        mock_image.attrs = {"Size": 2048000}

        wrapper.client.images.pull = MagicMock(return_value=mock_image)

        operation = DockerOperation(
            operation="pull_image", params={"repository": "python", "tag": "3.11"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["image_id"] == "sha256:xyz789"
        assert "python:3.11" in result.data["tags"]

    @pytest.mark.asyncio
    async def test_push_image_success(self, wrapper, context):
        """Test pushing image."""
        wrapper.client.images.push = MagicMock(return_value="Push complete")

        operation = DockerOperation(
            operation="push_image", params={"repository": "myrepo/myapp", "tag": "v1.0"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["pushed"] is True
        assert result.data["repository"] == "myrepo/myapp"

    @pytest.mark.asyncio
    async def test_remove_image_success(self, wrapper, context):
        """Test removing image."""
        wrapper.client.images.remove = MagicMock()

        operation = DockerOperation(
            operation="remove_image", params={"image": "myapp:latest", "force": True}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["removed"] is True

    @pytest.mark.asyncio
    async def test_list_images_success(self, wrapper, context):
        """Test listing images."""
        mock_image1 = MagicMock()
        mock_image1.id = "img1"
        mock_image1.tags = ["python:3.11"]
        mock_image1.attrs = {"Size": 1024000, "Created": "2025-01-01"}

        mock_image2 = MagicMock()
        mock_image2.id = "img2"
        mock_image2.tags = ["nginx:latest"]
        mock_image2.attrs = {"Size": 512000, "Created": "2025-01-02"}

        wrapper.client.images.list = MagicMock(return_value=[mock_image1, mock_image2])

        operation = DockerOperation(operation="list_images", params={"all": False})

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 2
        assert result.data["images"][0]["tags"] == ["python:3.11"]

    @pytest.mark.asyncio
    async def test_create_volume_success(self, wrapper, context):
        """Test creating volume."""
        mock_volume = MagicMock()
        mock_volume.name = "myvolume"
        mock_volume.attrs = {
            "Driver": "local",
            "Mountpoint": "/var/lib/docker/volumes/myvolume",
        }

        wrapper.client.volumes.create = MagicMock(return_value=mock_volume)

        operation = DockerOperation(
            operation="create_volume",
            params={"name": "myvolume", "driver": "local"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["name"] == "myvolume"
        assert result.data["driver"] == "local"

    @pytest.mark.asyncio
    async def test_remove_volume_success(self, wrapper, context):
        """Test removing volume."""
        mock_volume = MagicMock()
        wrapper.client.volumes.get = MagicMock(return_value=mock_volume)

        operation = DockerOperation(
            operation="remove_volume", params={"name": "myvolume", "force": False}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["removed"] is True

    @pytest.mark.asyncio
    async def test_list_volumes_success(self, wrapper, context):
        """Test listing volumes."""
        mock_volume1 = MagicMock()
        mock_volume1.name = "vol1"
        mock_volume1.attrs = {"Driver": "local", "Mountpoint": "/path/to/vol1"}

        mock_volume2 = MagicMock()
        mock_volume2.name = "vol2"
        mock_volume2.attrs = {"Driver": "local", "Mountpoint": "/path/to/vol2"}

        wrapper.client.volumes.list = MagicMock(
            return_value=[mock_volume1, mock_volume2]
        )

        operation = DockerOperation(operation="list_volumes", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 2

    @pytest.mark.asyncio
    async def test_create_network_success(self, wrapper, context):
        """Test creating network."""
        mock_network = MagicMock()
        mock_network.id = "net123"
        mock_network.name = "mynetwork"
        mock_network.attrs = {"Driver": "bridge"}

        wrapper.client.networks.create = MagicMock(return_value=mock_network)

        operation = DockerOperation(
            operation="create_network",
            params={"name": "mynetwork", "driver": "bridge"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["name"] == "mynetwork"
        assert result.data["driver"] == "bridge"

    @pytest.mark.asyncio
    async def test_remove_network_success(self, wrapper, context):
        """Test removing network."""
        mock_network = MagicMock()
        wrapper.client.networks.get = MagicMock(return_value=mock_network)

        operation = DockerOperation(
            operation="remove_network", params={"name": "mynetwork"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["removed"] is True

    @pytest.mark.asyncio
    async def test_api_error_handling(self, wrapper, context):
        """Test Docker API error handling."""
        wrapper.client.containers.get = MagicMock(
            side_effect=APIError("Container not found")
        )

        operation = DockerOperation(
            operation="stop_container", params={"container_id": "nonexistent"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Docker error" in result.error

    @pytest.mark.asyncio
    async def test_container_not_found(self, wrapper, context):
        """Test container not found error."""
        wrapper.client.containers.get = MagicMock(
            side_effect=NotFound("Container not found")
        )

        operation = DockerOperation(
            operation="get_container_logs", params={"container_id": "missing"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Docker error" in result.error

    @pytest.mark.asyncio
    async def test_image_not_found(self, wrapper, context):
        """Test image not found error."""
        wrapper.client.images.pull = MagicMock(
            side_effect=ImageNotFound("Image not found")
        )

        operation = DockerOperation(
            operation="pull_image",
            params={"repository": "nonexistent", "tag": "latest"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Docker error" in result.error

    @pytest.mark.asyncio
    async def test_invalid_operation(self, wrapper, context):
        """Test invalid operation handling."""
        operation = DockerOperation(operation="invalid_operation", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Unknown operation" in result.error

    def test_close_client(self, wrapper):
        """Test client cleanup."""
        wrapper.close()
        wrapper.client.close.assert_called_once()
