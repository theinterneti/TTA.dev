"""Tests for LLM provider abstraction."""

import pytest

from tta_rebuild.integrations import (
    LLMConfig,
    LLMResponse,
    MockLLMProvider,
)


class TestLLMConfig:
    """Test LLMConfig dataclass."""

    def test_default_config(self) -> None:
        """Test creating config with defaults."""
        config = LLMConfig(model="test-model")

        assert config.model == "test-model"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.top_p == 1.0
        assert config.timeout_seconds == 30.0

    def test_custom_config(self) -> None:
        """Test creating config with custom values."""
        config = LLMConfig(
            model="custom-model",
            max_tokens=4000,
            temperature=0.9,
            top_p=0.95,
            timeout_seconds=60.0,
        )

        assert config.model == "custom-model"
        assert config.max_tokens == 4000
        assert config.temperature == 0.9
        assert config.top_p == 0.95
        assert config.timeout_seconds == 60.0


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_response_creation(self) -> None:
        """Test creating LLM response."""
        response = LLMResponse(
            text="Generated text",
            tokens_used=150,
            model="test-model",
            finish_reason="stop",
            metadata={"test": "data"},
        )

        assert response.text == "Generated text"
        assert response.tokens_used == 150
        assert response.model == "test-model"
        assert response.finish_reason == "stop"
        assert response.metadata == {"test": "data"}


class TestMockLLMProvider:
    """Test MockLLMProvider."""

    @pytest.mark.asyncio
    async def test_basic_generation(self, mock_llm_provider: MockLLMProvider, test_context) -> None:
        """Test basic text generation."""
        response = await mock_llm_provider.generate(
            "Tell me a story",
            test_context,
        )

        assert isinstance(response, LLMResponse)
        assert "brave adventurer" in response.text
        assert response.tokens_used > 0
        assert response.model == "mock-model"
        assert response.finish_reason == "stop"
        assert response.metadata["call_count"] == 1
        assert response.metadata["simulated_latency_ms"] == 50

    @pytest.mark.asyncio
    async def test_tracks_calls(self, mock_llm_provider: MockLLMProvider, test_context) -> None:
        """Test that provider tracks call count."""
        assert mock_llm_provider.call_count == 0

        await mock_llm_provider.generate("First prompt", test_context)
        assert mock_llm_provider.call_count == 1
        assert mock_llm_provider.last_prompt == "First prompt"

        await mock_llm_provider.generate("Second prompt", test_context)
        assert mock_llm_provider.call_count == 2
        assert mock_llm_provider.last_prompt == "Second prompt"

    @pytest.mark.asyncio
    async def test_failure_simulation(
        self, failing_mock_llm: MockLLMProvider, test_context
    ) -> None:
        """Test simulated failures."""
        with pytest.raises(Exception, match="Mock LLM provider failure"):
            await failing_mock_llm.generate("Prompt", test_context)

    @pytest.mark.asyncio
    async def test_streaming_generation(
        self, mock_llm_provider: MockLLMProvider, test_context
    ) -> None:
        """Test streaming text generation."""
        chunks = []
        async for chunk in mock_llm_provider.generate_stream(
            "Tell me a story",
            test_context,
        ):
            chunks.append(chunk)

        # Should have streamed words
        assert len(chunks) > 0
        full_text = "".join(chunks).strip()
        assert "brave adventurer" in full_text

    @pytest.mark.asyncio
    async def test_streaming_failure(self, failing_mock_llm: MockLLMProvider, test_context) -> None:
        """Test streaming with failures."""
        with pytest.raises(Exception, match="Mock LLM provider failure"):
            async for _ in failing_mock_llm.generate_stream("Prompt", test_context):
                pass

    @pytest.mark.asyncio
    async def test_custom_response(self, test_context) -> None:
        """Test provider with custom response."""
        provider = MockLLMProvider(
            response="Custom story content here!",
            latency_ms=10,
        )

        response = await provider.generate("Prompt", test_context)

        assert response.text == "Custom story content here!"
        assert response.metadata["simulated_latency_ms"] == 10


# Mark tests requiring live API keys
@pytest.mark.llm
@pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY")
class TestAnthropicProvider:
    """Test AnthropicProvider with live API.

    These tests are skipped by default. To run them:
    1. Set ANTHROPIC_API_KEY environment variable
    2. Run: pytest -v -m llm packages/tta-rebuild/tests/
    """

    @pytest.mark.asyncio
    async def test_anthropic_generation(self, test_context) -> None:
        """Test Claude generation."""
        from tta_rebuild.integrations import AnthropicProvider

        provider = AnthropicProvider()
        response = await provider.generate(
            "Write a single sentence about courage.",
            test_context,
        )

        assert len(response.text) > 0
        assert response.tokens_used > 0
        assert "claude" in response.model.lower()


@pytest.mark.llm
@pytest.mark.skip(reason="Requires OPENAI_API_KEY")
class TestOpenAIProvider:
    """Test OpenAIProvider with live API.

    These tests are skipped by default. To run them:
    1. Set OPENAI_API_KEY environment variable
    2. Run: pytest -v -m llm packages/tta-rebuild/tests/
    """

    @pytest.mark.asyncio
    async def test_openai_generation(self, test_context) -> None:
        """Test GPT generation."""
        from tta_rebuild.integrations import OpenAIProvider

        provider = OpenAIProvider()
        response = await provider.generate(
            "Write a single sentence about bravery.",
            test_context,
        )

        assert len(response.text) > 0
        assert response.tokens_used > 0
        assert "gpt" in response.model.lower()
