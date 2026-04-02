"""Tests for OllamaPrimitive, OllamaModelManagerPrimitive, OllamaEmbeddingsPrimitive.

All tests use mocks — no live Ollama daemon required.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.ollama_primitive import (
    OllamaEmbeddingsPrimitive,
    OllamaEmbeddingsRequest,
    OllamaManagerRequest,
    OllamaModelManagerPrimitive,
    OllamaPrimitive,
    OllamaRequest,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-ollama")


def _make_chat_response(content: str = "Hello!", thinking: str | None = None) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    msg.thinking = thinking
    msg.tool_calls = None
    resp = MagicMock()
    resp.message = msg
    resp.model = "qwen3:1.7b"
    resp.done_reason = "stop"
    resp.total_duration = 1_000_000_000
    resp.prompt_eval_count = 10
    resp.eval_count = 5
    return resp


# ── OllamaPrimitive ───────────────────────────────────────────────────────────


class TestOllamaPrimitive:
    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Arrange: mock AsyncClient.chat → Act: execute → Assert: content."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response("Hello from Ollama!")

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = AsyncMock(return_value=mock_resp)
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen3:1.7b",
            )
            result = await primitive.execute(request, _ctx())

        assert result.content == "Hello from Ollama!"
        assert result.model == "qwen3:1.7b"
        assert result.done_reason == "stop"
        assert result.eval_count == 5

    @pytest.mark.asyncio
    async def test_execute_injects_system_message(self):
        """System prompt is prepended if not already in messages."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response("OK")
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen3:1.7b",
                system="You are a helpful assistant.",
            )
            await primitive.execute(request, _ctx())

        messages = captured_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_execute_no_duplicate_system(self):
        """System prompt is NOT injected if one already exists in messages."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response("OK")
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[
                    {"role": "system", "content": "Existing system."},
                    {"role": "user", "content": "Hi"},
                ],
                model="qwen3:1.7b",
                system="Should not duplicate.",
            )
            await primitive.execute(request, _ctx())

        system_msgs = [m for m in captured_kwargs["messages"] if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == "Existing system."

    @pytest.mark.asyncio
    async def test_execute_think_mode(self):
        """think=True is forwarded and thinking field is returned."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response(content="42", thinking="Let me think...")
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "What is 6x7?"}],
                model="qwen3:1.7b",
                think=True,
            )
            result = await primitive.execute(request, _ctx())

        assert captured_kwargs["think"] is True
        assert result.content == "42"
        assert result.thinking == "Let me think..."

    @pytest.mark.asyncio
    async def test_execute_passes_options(self):
        """num_ctx and max_tokens are forwarded as Ollama options."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response("OK")
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Hi"}],
                model="llama3.2:latest",
                max_tokens=512,
                options={"num_ctx": 8192, "top_p": 0.9},
            )
            await primitive.execute(request, _ctx())

        opts = captured_kwargs["options"]
        assert opts["num_predict"] == 512
        assert opts["num_ctx"] == 8192
        assert opts["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_execute_format_json(self):
        """format='json' is forwarded for structured output."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response('{"name": "Ollama"}')
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "What is your name?"}],
                model="qwen3:1.7b",
                format="json",
            )
            await primitive.execute(request, _ctx())

        assert captured_kwargs.get("format") == "json"

    @pytest.mark.asyncio
    async def test_execute_keep_alive(self):
        """keep_alive is forwarded for memory management."""
        primitive = OllamaPrimitive()
        mock_resp = _make_chat_response("OK")
        captured_kwargs: dict[str, Any] = {}

        async def fake_chat(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = fake_chat
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen3:1.7b",
                keep_alive="0",  # unload immediately after
            )
            await primitive.execute(request, _ctx())

        assert captured_kwargs.get("keep_alive") == "0"

    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self):
        """stream() yields content tokens from NDJSON chunks."""
        primitive = OllamaPrimitive()

        def _chunk(content: str, thinking: str | None = None) -> MagicMock:
            msg = MagicMock()
            msg.content = content
            msg.thinking = thinking
            c = MagicMock()
            c.message = msg
            return c

        chunks = [_chunk("Hello"), _chunk(" world"), _chunk("!")]

        async def fake_aiter():
            for c in chunks:
                yield c

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            # chat with stream=True returns an async generator
            client.chat = AsyncMock(return_value=fake_aiter())
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen3:1.7b",
            )
            tokens = []
            async for token in primitive.stream(request, _ctx()):
                tokens.append(token)

        assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_stream_yields_thinking_when_enabled(self):
        """When think=True, thinking tokens are also yielded."""
        primitive = OllamaPrimitive()

        def _chunk(content: str = "", thinking: str | None = None) -> MagicMock:
            msg = MagicMock()
            msg.content = content or None
            msg.thinking = thinking
            c = MagicMock()
            c.message = msg
            return c

        chunks = [
            _chunk(thinking="hmm..."),
            _chunk(content="Answer"),
        ]

        async def fake_aiter():
            for c in chunks:
                yield c

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.chat = AsyncMock(return_value=fake_aiter())
            mock_client_fn.return_value = client

            request = OllamaRequest(
                messages=[{"role": "user", "content": "Think hard"}],
                model="qwen3:1.7b",
                think=True,
            )
            tokens = []
            async for token in primitive.stream(request, _ctx()):
                tokens.append(token)

        assert "hmm..." in tokens
        assert "Answer" in tokens


# ── OllamaModelManagerPrimitive ───────────────────────────────────────────────


class TestOllamaModelManagerPrimitive:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """health action returns healthy=True when server responds 200."""
        manager = OllamaModelManagerPrimitive()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            resp = MagicMock()
            resp.status_code = 200
            mock_client.get = AsyncMock(return_value=resp)
            mock_client_cls.return_value = mock_client

            result = await manager.execute(OllamaManagerRequest(action="health"), _ctx())

        assert result.healthy is True
        assert result.action == "health"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """health action returns healthy=False when connection fails."""
        manager = OllamaModelManagerPrimitive()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=ConnectionRefusedError())
            mock_client_cls.return_value = mock_client

            result = await manager.execute(OllamaManagerRequest(action="health"), _ctx())

        assert result.healthy is False

    @pytest.mark.asyncio
    async def test_list_models(self):
        """list action returns OllamaModelInfo list from /api/tags."""
        manager = OllamaModelManagerPrimitive()

        # Build mock model objects
        details = MagicMock()
        details.parameter_size = "1.7B"
        details.quantization_level = "Q4_K_M"
        details.family = "qwen3"
        details.format = "gguf"

        model = MagicMock()
        model.model = "qwen3:1.7b"
        model.size = 1_200_000_000
        model.details = details
        model.modified_at = "2025-01-01T00:00:00Z"
        model.digest = "sha256:abc123"

        list_resp = MagicMock()
        list_resp.models = [model]

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.list = AsyncMock(return_value=list_resp)
            mock_client_fn.return_value = client

            result = await manager.execute(OllamaManagerRequest(action="list"), _ctx())

        assert len(result.models) == 1
        m = result.models[0]
        assert m.name == "qwen3:1.7b"
        assert m.parameter_size == "1.7B"
        assert m.quantization == "Q4_K_M"
        assert m.family == "qwen3"

    @pytest.mark.asyncio
    async def test_running_models(self):
        """running action returns RunningModel list from /api/ps."""
        manager = OllamaModelManagerPrimitive()

        running_model = MagicMock()
        running_model.model = "llama3.2:latest"
        running_model.size = 4_000_000_000
        running_model.expires_at = "2025-01-01T01:00:00Z"
        running_model.digest = "sha256:def456"

        ps_resp = MagicMock()
        ps_resp.models = [running_model]

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.ps = AsyncMock(return_value=ps_resp)
            mock_client_fn.return_value = client

            result = await manager.execute(OllamaManagerRequest(action="running"), _ctx())

        assert len(result.running) == 1
        assert result.running[0].name == "llama3.2:latest"

    @pytest.mark.asyncio
    async def test_show_model(self):
        """show action returns OllamaModelInfo for the specified model."""
        manager = OllamaModelManagerPrimitive()

        details = MagicMock()
        details.parameter_size = "8B"
        details.quantization_level = "Q4_0"
        details.family = "llama"
        details.format = "gguf"

        show_resp = MagicMock()
        show_resp.details = details

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.show = AsyncMock(return_value=show_resp)
            mock_client_fn.return_value = client

            result = await manager.execute(
                OllamaManagerRequest(action="show", model="llama3.2:latest"), _ctx()
            )

        assert result.info is not None
        assert result.info.name == "llama3.2:latest"
        assert result.info.parameter_size == "8B"
        assert result.info.family == "llama"

    @pytest.mark.asyncio
    async def test_delete_model(self):
        """delete action calls client.delete and returns status='deleted'."""
        manager = OllamaModelManagerPrimitive()

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.delete = AsyncMock(return_value=None)
            mock_client_fn.return_value = client

            result = await manager.execute(
                OllamaManagerRequest(action="delete", model="qwen3:1.7b"), _ctx()
            )

        assert result.status == "deleted"
        client.delete.assert_called_once_with("qwen3:1.7b")

    @pytest.mark.asyncio
    async def test_invalid_action_raises(self):
        """Unknown action raises ValueError."""
        manager = OllamaModelManagerPrimitive()
        with pytest.raises(ValueError, match="Unknown action"):
            await manager.execute(OllamaManagerRequest(action="explode"), _ctx())

    @pytest.mark.asyncio
    async def test_pull_model_collects_progress(self):
        """pull action streams progress messages and returns status='success'."""
        manager = OllamaModelManagerPrimitive()

        progress_chunks = [
            MagicMock(status="pulling manifest"),
            MagicMock(status="downloading weights"),
            MagicMock(status="verifying sha256"),
            MagicMock(status="success"),
        ]

        async def fake_pull(*args, **kwargs):
            for chunk in progress_chunks:
                yield chunk

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.pull = AsyncMock(return_value=fake_pull())
            mock_client_fn.return_value = client

            result = await manager.execute(
                OllamaManagerRequest(action="pull", model="llama3.2:latest"), _ctx()
            )

        assert result.status == "success"
        assert "pulling manifest" in result.progress_messages
        assert "success" in result.progress_messages


# ── OllamaEmbeddingsPrimitive ─────────────────────────────────────────────────


class TestOllamaEmbeddingsPrimitive:
    @pytest.mark.asyncio
    async def test_embed_single_string(self):
        """execute() returns one embedding vector for a single string."""
        primitive = OllamaEmbeddingsPrimitive()
        fake_vector = [0.1, 0.2, 0.3, 0.4]

        embed_resp = MagicMock()
        embed_resp.embeddings = [fake_vector]
        embed_resp.model = "nomic-embed-text"
        embed_resp.prompt_eval_count = 4

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaEmbeddingsPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.embed = AsyncMock(return_value=embed_resp)
            mock_client_fn.return_value = client

            request = OllamaEmbeddingsRequest(
                input="The sky is blue",
                model="nomic-embed-text",
            )
            result = await primitive.execute(request, _ctx())

        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3, 0.4]
        assert result.model == "nomic-embed-text"
        assert result.prompt_eval_count == 4

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """execute() returns multiple vectors for a list of strings."""
        primitive = OllamaEmbeddingsPrimitive()

        embed_resp = MagicMock()
        embed_resp.embeddings = [[0.1, 0.2], [0.3, 0.4]]
        embed_resp.model = "nomic-embed-text"
        embed_resp.prompt_eval_count = 8

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaEmbeddingsPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.embed = AsyncMock(return_value=embed_resp)
            mock_client_fn.return_value = client

            request = OllamaEmbeddingsRequest(
                input=["text one", "text two"],
                model="nomic-embed-text",
            )
            result = await primitive.execute(request, _ctx())

        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2]
        assert result.embeddings[1] == [0.3, 0.4]

    @pytest.mark.asyncio
    async def test_embed_one_convenience(self):
        """embed_one() returns a flat list of floats."""
        primitive = OllamaEmbeddingsPrimitive()

        embed_resp = MagicMock()
        embed_resp.embeddings = [[0.5, 0.6, 0.7]]
        embed_resp.model = "all-minilm"
        embed_resp.prompt_eval_count = 2

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaEmbeddingsPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.embed = AsyncMock(return_value=embed_resp)
            mock_client_fn.return_value = client

            vector = await primitive.embed_one("Hello", model="all-minilm")

        assert vector == [0.5, 0.6, 0.7]

    @pytest.mark.asyncio
    async def test_embed_batch_convenience(self):
        """embed_batch() returns a list of vectors."""
        primitive = OllamaEmbeddingsPrimitive()

        embed_resp = MagicMock()
        embed_resp.embeddings = [[0.1], [0.2], [0.3]]
        embed_resp.model = "nomic-embed-text"
        embed_resp.prompt_eval_count = 6

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaEmbeddingsPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.embed = AsyncMock(return_value=embed_resp)
            mock_client_fn.return_value = client

            vectors = await primitive.embed_batch(["a", "b", "c"])

        assert len(vectors) == 3
        assert vectors[0] == [0.1]

    @pytest.mark.asyncio
    async def test_single_string_input_wrapped_in_list(self):
        """Single string input is wrapped in a list before calling the API."""
        primitive = OllamaEmbeddingsPrimitive()
        captured_kwargs: dict[str, Any] = {}

        embed_resp = MagicMock()
        embed_resp.embeddings = [[0.1]]
        embed_resp.model = "nomic-embed-text"
        embed_resp.prompt_eval_count = 1

        async def fake_embed(**kwargs: Any):
            captured_kwargs.update(kwargs)
            return embed_resp

        with patch(
            "ttadev.primitives.llm.ollama_primitive.OllamaEmbeddingsPrimitive._get_client"
        ) as mock_client_fn:
            client = AsyncMock()
            client.embed = fake_embed
            mock_client_fn.return_value = client

            await primitive.execute(OllamaEmbeddingsRequest(input="just one string"), _ctx())

        # API always receives a list
        assert isinstance(captured_kwargs["input"], list)
        assert captured_kwargs["input"] == ["just one string"]
