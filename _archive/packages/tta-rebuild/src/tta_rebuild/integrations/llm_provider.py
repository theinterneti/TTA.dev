"""LLM provider abstraction for TTA story generation.

This module provides a unified interface for different LLM providers,
enabling flexible backend selection while maintaining consistent interfaces.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ..core import TTAContext


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    text: str
    tokens_used: int
    model: str
    finish_reason: str
    metadata: dict[str, Any]


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""

    model: str
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 1.0
    timeout_seconds: float = 30.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """Initialize provider with configuration.

        Args:
            config: LLM configuration settings
        """
        self.config = config

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from prompt.

        Args:
            prompt: Input prompt for generation
            context: Workflow context for tracing
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            Exception: If generation fails
        """

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate text from prompt with streaming.

        Args:
            prompt: Input prompt for generation
            context: Workflow context for tracing
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of generated text

        Raises:
            Exception: If generation fails
        """


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(
        self,
        config: LLMConfig | None = None,
        response: str = "Generated story content...",
        latency_ms: int = 100,
        should_fail: bool = False,
    ):
        """Initialize mock provider.

        Args:
            config: LLM configuration (optional, uses defaults)
            response: Text to return from generation
            latency_ms: Simulated latency in milliseconds
            should_fail: Whether to simulate failures
        """
        super().__init__(config or LLMConfig(model="mock-model", max_tokens=1000))
        self.response = response
        self.latency_ms = latency_ms
        self.should_fail = should_fail
        self.call_count = 0
        self.last_prompt: str | None = None

    async def generate(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate mock response.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Ignored

        Returns:
            Mock LLMResponse

        Raises:
            Exception: If should_fail is True
        """
        self.call_count += 1
        self.last_prompt = prompt

        if self.should_fail:
            raise Exception("Mock LLM provider failure")

        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)

        return LLMResponse(
            text=self.response,
            tokens_used=len(self.response.split()),
            model=self.config.model,
            finish_reason="stop",
            metadata={
                "call_count": self.call_count,
                "simulated_latency_ms": self.latency_ms,
            },
        )

    async def generate_stream(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate mock streaming response.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Ignored

        Yields:
            Chunks of mock response
        """
        self.call_count += 1
        self.last_prompt = prompt

        if self.should_fail:
            raise Exception("Mock LLM provider failure")

        # Simulate streaming by yielding words
        words = self.response.split()
        for word in words:
            await asyncio.sleep(self.latency_ms / 1000.0 / len(words))
            yield word + " "


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: LLMConfig | None = None):
        """Initialize Anthropic provider.

        Args:
            config: LLM configuration (uses Claude 3.5 Sonnet by default)
        """
        super().__init__(
            config
            or LLMConfig(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
            )
        )
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Import here to make it optional
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: uv pip install anthropic"
            )

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using Claude.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Additional Anthropic parameters

        Returns:
            LLMResponse with Claude output

        Raises:
            Exception: If API call fails
        """
        try:
            message = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
            )

            return LLMResponse(
                text=message.content[0].text,
                tokens_used=message.usage.input_tokens + message.usage.output_tokens,
                model=message.model,
                finish_reason=message.stop_reason,
                metadata={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "correlation_id": context.correlation_id,
                },
            )
        except Exception as e:
            raise Exception(f"Anthropic API call failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming text using Claude.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Additional Anthropic parameters

        Yields:
            Chunks of generated text
        """
        try:
            async with self.client.messages.stream(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise Exception(f"Anthropic streaming failed: {e}")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, config: LLMConfig | None = None):
        """Initialize OpenAI provider.

        Args:
            config: LLM configuration (uses GPT-4 Turbo by default)
        """
        super().__init__(
            config
            or LLMConfig(
                model="gpt-4-turbo-preview",
                max_tokens=4000,
                temperature=0.7,
            )
        )
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Import here to make it optional
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed. Install with: uv pip install openai")

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using GPT.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Additional OpenAI parameters

        Returns:
            LLMResponse with GPT output

        Raises:
            Exception: If API call fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
            )

            choice = response.choices[0]
            return LLMResponse(
                text=choice.message.content,
                tokens_used=response.usage.total_tokens,
                model=response.model,
                finish_reason=choice.finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "correlation_id": context.correlation_id,
                },
            )
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming text using GPT.

        Args:
            prompt: Input prompt
            context: Workflow context
            **kwargs: Additional OpenAI parameters

        Yields:
            Chunks of generated text
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"OpenAI streaming failed: {e}")
