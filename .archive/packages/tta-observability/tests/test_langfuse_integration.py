"""Tests for LangFuse integration."""

from unittest.mock import MagicMock, patch

import pytest

from observability_integration.langfuse_integration import (
    LangFuseIntegration,
    get_langfuse,
    initialize_langfuse,
)


@pytest.fixture
def mock_langfuse_client():
    """Mock LangFuse client."""
    with patch("observability_integration.langfuse_integration.Langfuse") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def langfuse_integration(mock_langfuse_client):
    """Create LangFuse integration with mocked client."""
    return LangFuseIntegration(
        public_key="test-pk",
        secret_key="test-sk",
        host="https://test.langfuse.com",
    )


class TestLangFuseIntegration:
    """Test LangFuse integration functionality."""

    def test_initialization(self, mock_langfuse_client):
        """Test LangFuse client initialization."""
        integration = LangFuseIntegration(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://custom.host",
        )

        assert integration.client is not None

    def test_initialization_from_env(self, mock_langfuse_client, monkeypatch):
        """Test initialization from environment variables."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "env-pk")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "env-sk")
        monkeypatch.setenv("LANGFUSE_HOST", "https://env.host")

        integration = LangFuseIntegration()
        assert integration.client is not None

    @pytest.mark.asyncio
    async def test_trace_llm_call(self, langfuse_integration):
        """Test tracing LLM calls."""
        result = await langfuse_integration.trace_llm_call(
            workflow_id="test-workflow",
            primitive_name="TestPrimitive",
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
            tokens_used=100,
            cost_usd=0.003,
            latency_ms=250.5,
            metadata={"custom": "value"},
        )

        # Verify trace data is returned
        assert result["workflow_id"] == "test-workflow"
        assert result["primitive"] == "TestPrimitive"
        assert result["model"] == "gpt-4"
        assert result["tokens_used"] == 100
        assert result["cost_usd"] == 0.003
        assert result["latency_ms"] == 250.5
        assert result["custom"] == "value"

    @pytest.mark.asyncio
    async def test_trace_workflow_stage(self, langfuse_integration):
        """Test tracing workflow stages."""
        result = await langfuse_integration.trace_workflow_stage(
            workflow_id="test-workflow",
            stage_name="validation",
            primitive_name="ValidatorPrimitive",
            input_data={"data": "input"},
            output_data={"result": "output"},
            quality_score=0.95,
        )

        # Verify stage data is returned
        assert result["workflow_id"] == "test-workflow"
        assert result["stage"] == "validation"
        assert result["primitive"] == "ValidatorPrimitive"
        assert result["quality_score"] == 0.95
        assert result["input"] == {"data": "input"}
        assert result["output"] == {"result": "output"}

    @pytest.mark.asyncio
    async def test_trace_workflow_stage_without_quality(self, langfuse_integration):
        """Test tracing workflow stages without quality score."""
        result = await langfuse_integration.trace_workflow_stage(
            workflow_id="test-workflow",
            stage_name="processing",
            primitive_name="ProcessorPrimitive",
            input_data={"data": "input"},
            output_data={"result": "output"},
        )

        # Verify stage data is returned without quality score
        assert result["workflow_id"] == "test-workflow"
        assert result["quality_score"] is None

    def test_create_dataset(self, langfuse_integration, mock_langfuse_client):
        """Test creating evaluation datasets."""
        mock_dataset = MagicMock()
        mock_dataset.id = "dataset-123"
        mock_langfuse_client.create_dataset.return_value = mock_dataset

        items = [
            {
                "input": {"prompt": "test1"},
                "expected_output": {"response": "output1"},
                "metadata": {"test": "value"},
            },
            {
                "input": {"prompt": "test2"},
                "expected_output": {"response": "output2"},
            },
        ]

        dataset_id = langfuse_integration.create_dataset(
            name="test-dataset",
            description="Test dataset",
            items=items,
        )

        assert dataset_id == "dataset-123"
        mock_langfuse_client.create_dataset.assert_called_once_with(
            name="test-dataset",
            description="Test dataset",
        )
        assert mock_langfuse_client.create_dataset_item.call_count == 2

    def test_flush(self, langfuse_integration, mock_langfuse_client):
        """Test flushing pending events."""
        langfuse_integration.flush()
        mock_langfuse_client.flush.assert_called_once()


class TestGlobalIntegration:
    """Test global LangFuse integration singleton."""

    def test_get_langfuse_creates_singleton(self, mock_langfuse_client):
        """Test get_langfuse creates singleton instance."""
        # Reset global state
        import observability_integration.langfuse_integration as module

        module._langfuse_integration = None

        integration1 = get_langfuse()
        integration2 = get_langfuse()

        assert integration1 is integration2

    def test_initialize_langfuse(self, mock_langfuse_client):
        """Test explicit initialization."""
        integration = initialize_langfuse(
            public_key="init-pk",
            secret_key="init-sk",
            host="https://init.host",
        )

        assert integration is not None
        assert get_langfuse() is integration
