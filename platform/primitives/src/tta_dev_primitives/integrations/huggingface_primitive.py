"""Hugging Face integration primitive.

Wraps the Hugging Face Inference API as a TTA.dev WorkflowPrimitive.
Provides access to thousands of open-source models.
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class HuggingFaceRequest(BaseModel):
    """Request model for Hugging Face primitive."""

    messages: list[dict[str, str]] = Field(
        description="List of messages in chat format"
    )
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature (0-2)"
    )
    max_tokens: int | None = Field(
        default=None, description="Maximum tokens to generate"
    )


class HuggingFaceResponse(BaseModel):
    """Response model for Hugging Face primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics (estimated)")
    finish_reason: str = Field(description="Reason for completion")


class HuggingFacePrimitive(WorkflowPrimitive[HuggingFaceRequest, HuggingFaceResponse]):
    """Wrapper around Hugging Face Inference API.

    This primitive provides a consistent TTA.dev interface for Hugging Face's
    Inference API, with built-in observability and error handling.

    **Free Tier Access:**
    - Access to thousands of models (Llama, Mistral, Falcon, etc.)
    - 300 requests/hour (registered users)
    - No credit card required
    - Best for model variety and experimentation

    Example:
        ```python
        from tta_dev_primitives.integrations import HuggingFacePrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive (free access to thousands of models)
        llm = HuggingFacePrimitive(
            model="meta-llama/Llama-3.3-70B-Instruct",
            api_key="your-hf-token"  # pragma: allowlist secret
        )

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = HuggingFaceRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: httpx AsyncClient instance
        model: Default model to use for completions
        api_key: Hugging Face API token
    """

    def __init__(
        self,
        model: str = "meta-llama/Llama-3.3-70B-Instruct",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Hugging Face primitive.

        Args:
            model: Default model to use (e.g., "meta-llama/Llama-3.3-70B-Instruct")
            api_key: Hugging Face API token (defaults to HF_TOKEN env var)
            **kwargs: Additional arguments for configuration
        """
        super().__init__()
        self.client = httpx.AsyncClient()
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"

    async def execute(
        self, input_data: HuggingFaceRequest, context: WorkflowContext
    ) -> HuggingFaceResponse:
        """Execute Hugging Face inference.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            Exception: If API call fails
        """
        # Use model from request or fall back to default
        model = input_data.model or self.model

        # Convert messages to prompt format
        # Most HF models expect a single prompt string
        prompt = self._messages_to_prompt(input_data.messages)

        # Build request parameters
        params: dict[str, Any] = {
            "inputs": prompt,
            "parameters": {},
        }

        # Add optional parameters if provided
        if input_data.temperature is not None:
            params["parameters"]["temperature"] = input_data.temperature
        if input_data.max_tokens is not None:
            params["parameters"]["max_new_tokens"] = input_data.max_tokens

        # Call Hugging Face API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"{self.base_url}/{model}", json=params, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Extract response data
        # HF API returns different formats depending on model
        if isinstance(data, list) and len(data) > 0:
            content = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            content = data.get("generated_text", "")
        else:
            content = str(data)

        # Remove the original prompt from the response if present
        if content.startswith(prompt):
            content = content[len(prompt) :].strip()

        # Estimate token usage (HF doesn't provide this)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(content.split())

        return HuggingFaceResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason="stop",
        )

    def _messages_to_prompt(self, messages: list[dict[str, str]]) -> str:
        """Convert chat messages to a single prompt string.

        Args:
            messages: List of messages in chat format

        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role in ("assistant", "model"):
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts) + "\n\nAssistant:"

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
