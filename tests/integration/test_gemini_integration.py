"""Integration test for the Gemini provider in UniversalLLMPrimitive.

Skipped automatically when neither GOOGLE_API_KEY nor GEMINI_API_KEY is set.
GOOGLE_API_KEY is the canonical variable (matches Google AI Studio convention);
GEMINI_API_KEY is accepted as a deprecated fallback for backward compatibility.

Requires:  pip install 'ttadev[gemini]'
"""

from __future__ import annotations

import os
import warnings

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

# Prefer GOOGLE_API_KEY (canonical); fall back to GEMINI_API_KEY for backward compat.
_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if _GEMINI_API_KEY and not _GOOGLE_API_KEY:
    warnings.warn(
        "GEMINI_API_KEY is deprecated; set GOOGLE_API_KEY instead "
        "(matches Google AI Studio convention). "
        "Support for GEMINI_API_KEY will be removed in a future release.",
        DeprecationWarning,
        stacklevel=1,
    )

GOOGLE_API_KEY: str | None = _GOOGLE_API_KEY or _GEMINI_API_KEY

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not GOOGLE_API_KEY,
    reason="Neither GOOGLE_API_KEY nor GEMINI_API_KEY set — skipping integration test",
)
@pytest.mark.asyncio
async def test_gemini_integration_basic_response() -> None:
    """End-to-end: UniversalLLMPrimitive(GEMINI) returns a non-empty response.

    Arrange: real GOOGLE_API_KEY (or legacy GEMINI_API_KEY) from environment;
             simple 'say hi' prompt.
    Act:     execute() against the live Gemini API.
    Assert:  LLMResponse with non-empty content and provider == 'google'.
    """
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GOOGLE,
        api_key=GOOGLE_API_KEY,
    )
    request = LLMRequest(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
    )
    ctx = WorkflowContext(workflow_id="gemini-integration-test")

    result = await primitive.execute(request, ctx)

    assert isinstance(result, LLMResponse)
    assert result.content.strip()
    assert result.provider == "google"
    assert result.model == "gemini-2.0-flash"
