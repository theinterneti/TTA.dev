"""Google AI Studio integration primitive.

Wraps the official Google Generative AI SDK as a TTA.dev WorkflowPrimitive.
Provides free access to Gemini Pro and Flash models.
"""

from typing import Any

import google.generativeai as genai
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class GoogleAIStudioRequest(BaseModel):
    """Request model for Google AI Studio primitive."""

    messages: list[dict[str, str]] = Field(
        description="List of messages in chat format (role: user/model, content: text)"
    )
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature (0-2)")
    max_tokens: int | None = Field(default=None, description="Maximum tokens to generate")


class GoogleAIStudioResponse(BaseModel):
    """Response model for Google AI Studio primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")


class GoogleAIStudioPrimitive(WorkflowPrimitive[GoogleAIStudioRequest, GoogleAIStudioResponse]):
    """Wrapper around official Google Generative AI SDK.

    This primitive provides a consistent TTA.dev interface for Google AI Studio's
    Gemini models, with built-in observability and error handling.

    **Free Tier Access:**
    - Gemini 2.5 Pro: FREE (89/100 quality, 2M context window)
    - Gemini 2.5 Flash: FREE (85/100 quality, 1M context window)
    - 1500 requests per day (RPD) free tier
    - No credit card required

    Example:
        ```python
        from tta_dev_primitives.integrations import GoogleAIStudioPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive (free Gemini Pro access)
        llm = GoogleAIStudioPrimitive(
            model="gemini-2.5-pro",
            api_key="your-google-ai-studio-key"
        )

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = GoogleAIStudioRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        model: Default model to use for completions
        api_key: Google AI Studio API key
    """

    def __init__(
        self,
        model: str = "gemini-2.5-pro",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Google AI Studio primitive.

        Args:
            model: Default model to use (e.g., "gemini-2.5-pro", "gemini-2.5-flash")
            api_key: Google AI Studio API key (defaults to GOOGLE_API_KEY env var)
            **kwargs: Additional arguments for configuration
        """
        super().__init__()
        genai.configure(api_key=api_key)
        self.model = model
        self.generation_config = kwargs.get("generation_config", {})

    async def execute(
        self, input_data: GoogleAIStudioRequest, context: WorkflowContext
    ) -> GoogleAIStudioResponse:
        """Execute Google AI Studio chat completion.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            Exception: If API call fails
        """
        # Use model from request or fall back to default
        model_name = input_data.model or self.model

        # Create model instance
        model = genai.GenerativeModel(model_name)

        # Convert messages to Gemini format
        # Gemini expects alternating user/model messages
        contents = []
        for msg in input_data.messages:
            role = msg["role"]
            # Map "user" to "user", "assistant"/"model" to "model"
            if role in ("assistant", "model"):
                role = "model"
            contents.append({"role": role, "parts": [msg["content"]]})

        # Build generation config
        generation_config = self.generation_config.copy()
        if input_data.temperature is not None:
            generation_config["temperature"] = input_data.temperature
        if input_data.max_tokens is not None:
            generation_config["max_output_tokens"] = input_data.max_tokens

        # Call Google AI Studio API
        response = await model.generate_content_async(
            contents=contents, generation_config=generation_config or None
        )

        # Extract response data
        content = response.text if hasattr(response, "text") else ""

        # Extract usage metadata (if available)
        usage_metadata = getattr(response, "usage_metadata", None)
        usage = {
            "prompt_tokens": getattr(usage_metadata, "prompt_token_count", 0)
            if usage_metadata
            else 0,
            "completion_tokens": getattr(usage_metadata, "candidates_token_count", 0)
            if usage_metadata
            else 0,
            "total_tokens": getattr(usage_metadata, "total_token_count", 0)
            if usage_metadata
            else 0,
        }

        # Extract finish reason
        finish_reason = "unknown"
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "finish_reason"):
                finish_reason = str(candidate.finish_reason)

        return GoogleAIStudioResponse(
            content=content,
            model=model_name,
            usage=usage,
            finish_reason=finish_reason,
        )
