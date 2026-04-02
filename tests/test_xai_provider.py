"""Tests for xAI/Grok provider normalization (GitHub issue #281).

Covers:
- xAI entry in PROVIDERS registry
- xAI ProviderSpec field values
- Missing XAI_API_KEY raises ValueError
- xAI wired into UniversalLLMPrimitive dispatch table
- Gemini still uses its OpenAI-compatible base URL
- GoogleAIStudioPrimitive emits DeprecationWarning on import
- openai_compat_providers() includes xAI
"""

from __future__ import annotations

import sys
import warnings
from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives import WorkflowContext
from ttadev.primitives.llm.providers import PROVIDERS, openai_compat_providers
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

# ── Provider registry ─────────────────────────────────────────────────────────


def test_xai_in_providers():
    """xAI must be registered in the PROVIDERS dict."""
    assert "xai" in PROVIDERS


def test_xai_spec_fields():
    """xAI ProviderSpec must expose correct base_url, env_var, and default_model."""
    spec = PROVIDERS["xai"]
    assert spec.base_url == "https://api.x.ai/v1"
    assert spec.env_var == "XAI_API_KEY"
    assert spec.default_model == "grok-3-mini"
    assert spec.openai_compat is True


def test_openai_compat_providers_includes_xai():
    """openai_compat_providers() must include the xAI provider."""
    compat_names = [p.name for p in openai_compat_providers()]
    assert "xai" in compat_names


def test_gemini_uses_openai_compat_url():
    """Gemini ProviderSpec must point at Google's OpenAI-compatible endpoint."""
    spec = PROVIDERS["gemini"]
    assert "generativelanguage.googleapis.com" in spec.base_url
    assert spec.openai_compat is True


# ── UniversalLLMPrimitive dispatch ────────────────────────────────────────────


async def test_xai_in_dispatch_table():
    """LLMProvider.XAI must route execute() calls to _call_xai."""
    mock_response = LLMResponse(content="grok reply", model="grok-3-mini", provider="xai")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key="test-key")
    ctx = WorkflowContext()
    request = LLMRequest(model="grok-3-mini", messages=[{"role": "user", "content": "hello"}])

    with patch.object(primitive, "_call_xai", new=AsyncMock(return_value=mock_response)):
        result = await primitive.execute(request, ctx)

    assert result.content == "grok reply"
    assert result.provider == "xai"


async def test_xai_missing_key_raises():
    """_call_xai must raise ValueError when XAI_API_KEY is absent from the environment."""
    primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI)  # no api_key supplied
    ctx = WorkflowContext()
    request = LLMRequest(model="grok-3-mini", messages=[{"role": "user", "content": "hello"}])

    # Wipe the entire environment so XAI_API_KEY cannot be present.
    # The method only reads XAI_API_KEY, so clearing is safe for this test.
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="XAI_API_KEY"):
            await primitive._call_xai(request, ctx)


# ── GoogleAIStudioPrimitive deprecation ───────────────────────────────────────


def test_google_ai_studio_deprecated():
    """Importing google_ai_studio_primitive must emit a DeprecationWarning."""
    module_name = "ttadev.primitives.integrations.google_ai_studio_primitive"
    # Pop the cached module so the module-level warning fires on the fresh import.
    sys.modules.pop(module_name, None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            import ttadev.primitives.integrations.google_ai_studio_primitive  # noqa: F401
        except ImportError:
            pytest.skip("google-generativeai is not installed — skipping deprecation import test")

    deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deprecation_warnings, (
        "Expected a DeprecationWarning when importing google_ai_studio_primitive, got none. "
        f"All warnings captured: {[str(w.message) for w in caught]}"
    )
    assert any("UniversalLLMPrimitive" in str(w.message) for w in deprecation_warnings), (
        "DeprecationWarning must mention UniversalLLMPrimitive as the replacement. "
        f"Got: {[str(w.message) for w in deprecation_warnings]}"
    )
