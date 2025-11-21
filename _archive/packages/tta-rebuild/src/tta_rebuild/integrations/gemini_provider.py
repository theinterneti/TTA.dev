"""Gemini LLM Provider with cost tracking and retry logic.

Production-ready Google Gemini API integration for TTA.dev narrative generation.
"""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import google.generativeai as genai

from tta_rebuild.core.base_primitive import TTAContext
from tta_rebuild.integrations.llm_provider import LLMConfig, LLMProvider, LLMResponse


@dataclass
class LLMUsageStats:
    """Track LLM usage for cost monitoring."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class GeminiLLMProvider(LLMProvider):
    """Production Gemini API integration with error handling and cost tracking."""

    # Pricing per 1K tokens (as of Nov 2025)
    INPUT_COST_PER_1K = 0.00015  # $0.15 per 1M tokens
    OUTPUT_COST_PER_1K = 0.0006  # $0.60 per 1M tokens

    def __init__(
        self,
        config: LLMConfig | None = None,
        api_key: str | None = None,
        model_name: str = "gemini-1.5-flash",
    ) -> None:
        """Initialize Gemini provider.

        Args:
            config: LLM configuration (optional - will create default if not provided)
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model to use (gemini-1.5-flash or gemini-1.5-pro)
        """
        # Use provided config or create default
        if config is None:
            config = LLMConfig(model=model_name)

        super().__init__(config)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(config.model)

        # Usage tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0

    async def generate(
        self,
        prompt: str,
        context: TTAContext,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using Gemini API.

        Args:
            prompt: Input prompt
            context: Workflow context for tracing
            **kwargs: Additional generation parameters (max_tokens, temperature, etc.)

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            Exception: On API errors after retries
        """
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
        }

        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Generate content (sync call - Gemini SDK doesn't have async yet)
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config,
                )

                # Extract text
                text = response.text

                # Track usage
                stats = self._track_usage(prompt, text)

                self.call_count += 1

                return LLMResponse(
                    text=text,
                    tokens_used=stats.total_tokens,
                    model=self.config.model,
                    finish_reason="stop",
                    metadata={
                        "prompt_tokens": stats.prompt_tokens,
                        "completion_tokens": stats.completion_tokens,
                        "cost_usd": stats.estimated_cost_usd,
                    },
                )

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise Exception(f"Gemini API failed after {max_retries} attempts: {e}") from e

                # Wait before retry (exponential backoff)
                wait_time = 2**attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)

        # Should never reach here
        raise Exception("Unexpected error in generate()")

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

        Note:
            Currently implements non-streaming (Gemini streaming is complex).
            Yields the complete response as a single chunk.
        """
        # For now, implement as non-streaming
        # Gemini streaming requires different API patterns
        response = await self.generate(prompt, context, **kwargs)
        yield response.text

    async def generate_json(
        self,
        prompt: str,
        context: TTAContext,
        max_tokens: int = 2000,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Generate JSON output using Gemini.

        Args:
            prompt: Input prompt (should request JSON output)
            context: Workflow context for tracing
            max_tokens: Maximum tokens to generate
            temperature: Override default temperature

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, just the JSON object."""

        response = await self.generate(
            json_prompt, context, max_tokens=max_tokens, temperature=temperature
        )
        text = response.text

        # Try to extract JSON from response
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```

        if text.endswith("```"):
            text = text[:-3]  # Remove closing ```

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}\n\nResponse: {text}") from e

    def _track_usage(self, prompt: str, completion: str) -> LLMUsageStats:
        """Track token usage and costs.

        Args:
            prompt: Input prompt
            completion: Generated completion

        Returns:
            Usage statistics
        """
        # Rough token estimation (4 chars ≈ 1 token)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(completion) // 4
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        prompt_cost = (prompt_tokens / 1000) * self.INPUT_COST_PER_1K
        completion_cost = (completion_tokens / 1000) * self.OUTPUT_COST_PER_1K
        total_cost = prompt_cost + completion_cost

        # Update totals
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_usd += total_cost

        return LLMUsageStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=total_cost,
        )

    def get_usage_stats(self) -> dict[str, Any]:
        """Get cumulative usage statistics.

        Returns:
            Dict with usage stats
        """
        return {
            "call_count": self.call_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_per_call": (
                self.total_cost_usd / self.call_count if self.call_count > 0 else 0.0
            ),
        }

    def reset_usage_stats(self) -> None:
        """Reset usage tracking."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0
