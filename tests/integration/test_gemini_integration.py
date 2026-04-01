"""Integration test for the Gemini provider in UniversalLLMPrimitive.

Skipped automatically when GEMINI_API_KEY is not set in the environment.
Requires:  pip install 'ttadev[gemini]'
"""

from __future__ import annotations

import os

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not set — skipping integration test")
@pytest.mark.asyncio
async def test_gemini_integration_basic_response() -> None:
    """End-to-end: UniversalLLMPrimitive(GEMINI) returns a non-empty response.

    Arrange: real GEMINI_API_KEY from environment; simple 'say hi' prompt.
    Act:     execute() against the live Gemini API.
    Assert:  LLMResponse with non-empty content and provider == 'gemini'.
    """
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GEMINI,
        api_key=GEMINI_API_KEY,
    )
    request = LLMRequest(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
    )
    ctx = WorkflowContext(workflow_id="gemini-integration-test")

    result = await primitive.execute(request, ctx)

    assert isinstance(result, LLMResponse)
    assert result.content.strip()
    assert result.provider == "gemini"
    assert result.model == "gemini-2.0-flash"
