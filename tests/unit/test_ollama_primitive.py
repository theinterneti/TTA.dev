"""Unit tests for ttadev/primitives/llm/ollama_primitive.py.

Covers:
- OllamaRequest / OllamaResponse dataclass defaults
- OllamaPrimitive._build_options: temperature, max_tokens, options override
- OllamaPrimitive._build_messages: system injection, no-dup system
- OllamaPrimitive.execute: basic, think=True, tool_calls, keep_alive, format, error
- OllamaPrimitive.stream: basic, think=True, thinking-only chunks, empty chunks
- OllamaModelManagerPrimitive: health ok/fail, list, running, show, pull,
  delete, copy, unknown action
- OllamaEmbeddingsPrimitive: execute single, batch, embed_one, embed_batch
- OllamaModelInfo / RunningModel dataclasses
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.ollama_primitive import (
    OllamaEmbeddingsPrimitive,
    OllamaEmbeddingsRequest,
    OllamaManagerRequest,
    OllamaModelInfo,
    OllamaModelManagerPrimitive,
    OllamaPrimitive,
    OllamaRequest,
    OllamaResponse,
    RunningModel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "ollama-test") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


def _make_msg(content: str = "Hello!", thinking: str | None = None):
    """Build a fake ollama message object without tool_calls."""
    msg = MagicMock()
    msg.content = content
    msg.thinking = thinking
    # Make hasattr(msg, "tool_calls") return False
    del msg.tool_calls
    return msg


def _make_response(
    content: str = "Hello!",
    thinking: str | None = None,
    model: str = "qwen3:1.7b",
):
    resp = MagicMock()
    resp.message = _make_msg(content=content, thinking=thinking)
    resp.model = model
    resp.done_reason = "stop"
    resp.total_duration = 1_000_000
    resp.prompt_eval_count = 10
    resp.eval_count = 20
    return resp


# ---------------------------------------------------------------------------
# OllamaRequest defaults
# ---------------------------------------------------------------------------


class TestOllamaRequest:
    def test_default_model(self):
        req = OllamaRequest(messages=[{"role": "user", "content": "hi"}])
        assert req.model == "qwen3:1.7b"

    def test_default_temperature(self):
        req = OllamaRequest(messages=[])
        assert req.temperature == 0.7

    def test_default_think_false(self):
        req = OllamaRequest(messages=[])
        assert req.think is False

    def test_default_stream_false(self):
        req = OllamaRequest(messages=[])
        assert req.stream is False

    def test_default_options_empty(self):
        req = OllamaRequest(messages=[])
        assert req.options == {}

    def test_custom_fields(self):
        req = OllamaRequest(
            messages=[{"role": "user", "content": "hi"}],
            model="llama3.2",
            temperature=0.2,
            max_tokens=512,
            think=True,
            stream=True,
            keep_alive="10m",
            format="json",
        )
        assert req.model == "llama3.2"
        assert req.temperature == 0.2
        assert req.max_tokens == 512
        assert req.think is True
        assert req.stream is True
        assert req.keep_alive == "10m"
        assert req.format == "json"


# ---------------------------------------------------------------------------
# OllamaResponse defaults
# ---------------------------------------------------------------------------


class TestOllamaResponse:
    def test_defaults(self):
        r = OllamaResponse(content="hi")
        assert r.content == "hi"
        assert r.thinking is None
        assert r.model == ""
        assert r.tool_calls is None
        assert r.done_reason is None
        assert r.total_duration_ns is None
        assert r.prompt_eval_count is None
        assert r.eval_count is None


# ---------------------------------------------------------------------------
# OllamaPrimitive._build_options
# ---------------------------------------------------------------------------


class TestBuildOptions:
    def setup_method(self):
        self.p = OllamaPrimitive()

    def test_temperature_included(self):
        req = OllamaRequest(messages=[], temperature=0.5)
        opts = self.p._build_options(req)
        assert opts["temperature"] == 0.5

    def test_max_tokens_maps_to_num_predict(self):
        req = OllamaRequest(messages=[], max_tokens=256)
        opts = self.p._build_options(req)
        assert opts["num_predict"] == 256

    def test_no_num_predict_when_max_tokens_none(self):
        req = OllamaRequest(messages=[])
        opts = self.p._build_options(req)
        assert "num_predict" not in opts

    def test_options_dict_merged(self):
        req = OllamaRequest(messages=[], temperature=0.7, options={"num_ctx": 4096, "seed": 42})
        opts = self.p._build_options(req)
        assert opts["num_ctx"] == 4096
        assert opts["seed"] == 42
        assert opts["temperature"] == 0.7

    def test_options_overrides_temperature(self):
        req = OllamaRequest(messages=[], temperature=0.7, options={"temperature": 0.0})
        opts = self.p._build_options(req)
        assert opts["temperature"] == 0.0


# ---------------------------------------------------------------------------
# OllamaPrimitive._build_messages
# ---------------------------------------------------------------------------


class TestBuildMessages:
    def setup_method(self):
        self.p = OllamaPrimitive()

    def test_system_injected_first(self):
        req = OllamaRequest(
            messages=[{"role": "user", "content": "hi"}],
            system="You are helpful.",
        )
        msgs = self.p._build_messages(req)
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "You are helpful."
        assert len(msgs) == 2

    def test_no_system_when_not_set(self):
        req = OllamaRequest(messages=[{"role": "user", "content": "hi"}])
        msgs = self.p._build_messages(req)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_no_duplicate_system(self):
        req = OllamaRequest(
            messages=[
                {"role": "system", "content": "existing"},
                {"role": "user", "content": "hi"},
            ],
            system="new system",
        )
        msgs = self.p._build_messages(req)
        system_msgs = [m for m in msgs if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == "existing"

    def test_messages_not_mutated(self):
        original = [{"role": "user", "content": "hi"}]
        req = OllamaRequest(messages=original, system="sys")
        self.p._build_messages(req)
        assert len(original) == 1  # original unchanged


# ---------------------------------------------------------------------------
# OllamaPrimitive.execute
# ---------------------------------------------------------------------------


class TestOllamaPrimitiveExecute:
    def _primitive(self, fake_response):
        p = OllamaPrimitive(base_url="http://localhost:11434")
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=fake_response)
        p._get_client = MagicMock(return_value=mock_client)
        return p, mock_client

    @pytest.mark.asyncio
    async def test_basic_chat_returns_content(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("Hello!"))
        req = OllamaRequest(
            messages=[{"role": "user", "content": "Hi"}],
            model="qwen3:1.7b",
        )
        # Act
        result = await p.execute(req, _ctx())
        # Assert
        assert result.content == "Hello!"
        assert result.model == "qwen3:1.7b"
        assert result.thinking is None
        mock_client.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_think_flag_forwarded(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("Answer", thinking="My reasoning"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Solve"}], think=True)
        # Act
        result = await p.execute(req, _ctx())
        # Assert
        assert result.thinking == "My reasoning"
        assert mock_client.chat.call_args.kwargs["think"] is True

    @pytest.mark.asyncio
    async def test_execute_think_defaults_false(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert mock_client.chat.call_args.kwargs["think"] is False

    @pytest.mark.asyncio
    async def test_execute_keep_alive_forwarded(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}], keep_alive="10m")
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert mock_client.chat.call_args.kwargs["keep_alive"] == "10m"

    @pytest.mark.asyncio
    async def test_execute_keep_alive_omitted_when_none(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert "keep_alive" not in mock_client.chat.call_args.kwargs

    @pytest.mark.asyncio
    async def test_execute_format_forwarded(self):
        # Arrange
        p, mock_client = self._primitive(_make_response('{"x": 1}'))
        req = OllamaRequest(messages=[{"role": "user", "content": "JSON"}], format="json")
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert mock_client.chat.call_args.kwargs["format"] == "json"

    @pytest.mark.asyncio
    async def test_execute_format_omitted_when_none(self):
        # Arrange
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert "format" not in mock_client.chat.call_args.kwargs

    @pytest.mark.asyncio
    async def test_execute_tools_forwarded(self):
        # Arrange
        tools = [{"type": "function", "function": {"name": "search"}}]
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}], tools=tools)
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert mock_client.chat.call_args.kwargs["tools"] == tools

    @pytest.mark.asyncio
    async def test_execute_tool_calls_parsed(self):
        # Arrange
        tc = MagicMock()
        tc.function.name = "search"
        tc.function.arguments = {"query": "test"}

        fake_resp = MagicMock()
        fake_resp.message = MagicMock()
        fake_resp.message.content = "OK"
        fake_resp.message.thinking = None
        fake_resp.message.tool_calls = [tc]
        fake_resp.model = "qwen3:1.7b"
        fake_resp.done_reason = "stop"
        fake_resp.total_duration = 0
        fake_resp.prompt_eval_count = 0
        fake_resp.eval_count = 0

        p, _ = self._primitive(fake_resp)
        req = OllamaRequest(messages=[{"role": "user", "content": "Search"}])
        # Act
        result = await p.execute(req, _ctx())
        # Assert
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "search"
        assert result.tool_calls[0]["function"]["arguments"] == {"query": "test"}

    @pytest.mark.asyncio
    async def test_execute_metadata_fields_populated(self):
        # Arrange
        fake_resp = _make_response("OK")
        fake_resp.done_reason = "stop"
        fake_resp.total_duration = 5_000_000
        fake_resp.prompt_eval_count = 15
        fake_resp.eval_count = 30
        p, _ = self._primitive(fake_resp)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        result = await p.execute(req, _ctx())
        # Assert
        assert result.done_reason == "stop"
        assert result.total_duration_ns == 5_000_000
        assert result.prompt_eval_count == 15
        assert result.eval_count == 30

    @pytest.mark.asyncio
    async def test_execute_propagates_client_error(self):
        # Arrange
        p = OllamaPrimitive()
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(side_effect=ConnectionError("refused"))
        p._get_client = MagicMock(return_value=mock_client)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act & Assert
        with pytest.raises(ConnectionError):
            await p.execute(req, _ctx())

    @pytest.mark.asyncio
    async def test_execute_always_passes_stream_false(self):
        # Arrange — even with stream=True on request, execute uses stream=False
        p, mock_client = self._primitive(_make_response("OK"))
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}], stream=True)
        # Act
        await p.execute(req, _ctx())
        # Assert
        assert mock_client.chat.call_args.kwargs["stream"] is False

    @pytest.mark.asyncio
    async def test_base_url_stripped(self):
        # Arrange
        p = OllamaPrimitive(base_url="http://localhost:11434/")
        assert p._base_url == "http://localhost:11434"


# ---------------------------------------------------------------------------
# OllamaPrimitive.stream
# ---------------------------------------------------------------------------


def _stream_chunk(content: str = "", thinking: str = ""):
    chunk = MagicMock()
    chunk.message = MagicMock()
    chunk.message.content = content
    chunk.message.thinking = thinking
    return chunk


class TestOllamaPrimitiveStream:
    def _primitive_with_chunks(self, chunks: list):
        async def fake_aiter(*args, **kwargs):
            for c in chunks:
                yield c

        p = OllamaPrimitive()
        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=fake_aiter())
        p._get_client = MagicMock(return_value=mock_client)
        return p, mock_client

    @pytest.mark.asyncio
    async def test_stream_yields_content_tokens(self):
        # Arrange
        chunks = [_stream_chunk("Hello"), _stream_chunk(" world"), _stream_chunk("!")]
        p, _ = self._primitive_with_chunks(chunks)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        result = [tok async for tok in p.stream(req, _ctx())]
        # Assert
        assert result == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_stream_skips_empty_chunks(self):
        # Arrange
        chunks = [_stream_chunk("Hi"), _stream_chunk(""), _stream_chunk("!")]
        p, _ = self._primitive_with_chunks(chunks)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        result = [tok async for tok in p.stream(req, _ctx())]
        # Assert
        assert result == ["Hi", "!"]

    @pytest.mark.asyncio
    async def test_stream_think_mode_yields_thinking_then_content(self):
        # Arrange — chunk with no content but thinking text, think=True
        chunks = [
            _stream_chunk(content="", thinking="Let me think"),
            _stream_chunk(content="Answer", thinking=""),
        ]
        p, _ = self._primitive_with_chunks(chunks)
        req = OllamaRequest(messages=[{"role": "user", "content": "Think hard"}], think=True)
        # Act
        result = [tok async for tok in p.stream(req, _ctx())]
        # Assert
        assert "Let me think" in result
        assert "Answer" in result

    @pytest.mark.asyncio
    async def test_stream_think_false_ignores_thinking_tokens(self):
        # Arrange — chunk has thinking text but think=False
        chunks = [_stream_chunk(content="", thinking="secret")]
        p, _ = self._primitive_with_chunks(chunks)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}], think=False)
        # Act
        result = [tok async for tok in p.stream(req, _ctx())]
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_stream_passes_stream_true_to_client(self):
        # Arrange
        async def empty_gen():
            return
            yield  # noqa: unreachable — makes it an async generator

        p = OllamaPrimitive()
        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=empty_gen())
        p._get_client = MagicMock(return_value=mock_client)
        req = OllamaRequest(messages=[{"role": "user", "content": "Hi"}])
        # Act
        async for _ in p.stream(req, _ctx()):
            pass
        # Assert
        assert mock_client.chat.call_args.kwargs["stream"] is True


# ---------------------------------------------------------------------------
# OllamaModelManagerPrimitive
# ---------------------------------------------------------------------------


class TestOllamaModelManagerHealth:
    @pytest.mark.asyncio
    async def test_health_returns_true_on_200(self):
        # Arrange
        manager = OllamaModelManagerPrimitive()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_http):
            result = await manager.execute(OllamaManagerRequest(action="health"), _ctx())

        assert result.healthy is True
        assert result.action == "health"

    @pytest.mark.asyncio
    async def test_health_returns_false_on_non_200(self):
        # Arrange
        manager = OllamaModelManagerPrimitive()
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_http):
            result = await manager.execute(OllamaManagerRequest(action="health"), _ctx())

        assert result.healthy is False

    @pytest.mark.asyncio
    async def test_health_returns_false_on_connection_error(self):
        # Arrange
        manager = OllamaModelManagerPrimitive()
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(side_effect=ConnectionError("refused"))

        with patch("httpx.AsyncClient", return_value=mock_http):
            result = await manager.execute(OllamaManagerRequest(action="health"), _ctx())

        assert result.healthy is False


class TestOllamaModelManagerActions:
    def _manager(self, mock_client):
        manager = OllamaModelManagerPrimitive(base_url="http://localhost:11434")
        manager._get_client = MagicMock(return_value=mock_client)
        return manager

    @pytest.mark.asyncio
    async def test_list_models(self):
        # Arrange
        m = MagicMock()
        m.model = "qwen3:1.7b"
        m.size = 1_000_000
        m.details = MagicMock()
        m.details.parameter_size = "1.7B"
        m.details.quantization_level = "Q4_K_M"
        m.details.family = "qwen3"
        m.details.format = "gguf"
        m.modified_at = "2024-01-01"
        m.digest = "abc123"

        list_resp = MagicMock()
        list_resp.models = [m]
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=list_resp)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(OllamaManagerRequest(action="list"), _ctx())

        # Assert
        assert result.action == "list"
        assert len(result.models) == 1
        assert result.models[0].name == "qwen3:1.7b"
        assert result.models[0].parameter_size == "1.7B"
        assert result.models[0].quantization == "Q4_K_M"
        assert result.models[0].family == "qwen3"

    @pytest.mark.asyncio
    async def test_list_models_no_details(self):
        # Arrange
        m = MagicMock()
        m.model = "llama3.2"
        m.size = 500_000
        m.details = None
        m.modified_at = ""
        m.digest = ""

        list_resp = MagicMock()
        list_resp.models = [m]
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=list_resp)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(OllamaManagerRequest(action="list"), _ctx())

        # Assert — no details → empty strings
        assert result.models[0].parameter_size == ""

    @pytest.mark.asyncio
    async def test_running_models(self):
        # Arrange
        rm = MagicMock()
        rm.model = "qwen3:1.7b"
        rm.size = 2_000_000
        rm.expires_at = "2024-12-31T00:00:00"
        rm.digest = "def456"

        ps_resp = MagicMock()
        ps_resp.models = [rm]
        mock_client = AsyncMock()
        mock_client.ps = AsyncMock(return_value=ps_resp)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(OllamaManagerRequest(action="running"), _ctx())

        # Assert
        assert result.action == "running"
        assert len(result.running) == 1
        assert result.running[0].name == "qwen3:1.7b"
        assert "2024-12-31" in result.running[0].expires_at

    @pytest.mark.asyncio
    async def test_show_model(self):
        # Arrange
        show_resp = MagicMock()
        show_resp.details = MagicMock()
        show_resp.details.parameter_size = "7B"
        show_resp.details.quantization_level = "Q8"
        show_resp.details.family = "llama"
        show_resp.details.format = "gguf"

        mock_client = AsyncMock()
        mock_client.show = AsyncMock(return_value=show_resp)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(
            OllamaManagerRequest(action="show", model="llama3.2:7b"), _ctx()
        )

        # Assert
        assert result.action == "show"
        assert result.info is not None
        assert result.info.name == "llama3.2:7b"
        assert result.info.parameter_size == "7B"

    @pytest.mark.asyncio
    async def test_pull_model(self):
        # Arrange
        c1 = MagicMock()
        c1.status = "pulling manifest"
        c2 = MagicMock()
        c2.status = "done"

        async def fake_pull(*args, **kwargs):
            for c in [c1, c2]:
                yield c

        mock_client = MagicMock()
        mock_client.pull = AsyncMock(return_value=fake_pull())
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(
            OllamaManagerRequest(action="pull", model="llama3.2:latest"), _ctx()
        )

        # Assert
        assert result.action == "pull"
        assert result.status == "success"
        assert "pulling manifest" in result.progress_messages
        assert "done" in result.progress_messages

    @pytest.mark.asyncio
    async def test_delete_model(self):
        # Arrange
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=None)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(
            OllamaManagerRequest(action="delete", model="old:latest"), _ctx()
        )

        # Assert
        assert result.action == "delete"
        assert result.status == "deleted"
        mock_client.delete.assert_awaited_once_with("old:latest")

    @pytest.mark.asyncio
    async def test_copy_model(self):
        # Arrange
        mock_client = AsyncMock()
        mock_client.copy = AsyncMock(return_value=None)
        manager = self._manager(mock_client)

        # Act
        result = await manager.execute(
            OllamaManagerRequest(action="copy", model="src:latest", destination="dst:v1"),
            _ctx(),
        )

        # Assert
        assert result.action == "copy"
        assert result.status == "copied"
        mock_client.copy.assert_awaited_once_with("src:latest", "dst:v1")

    @pytest.mark.asyncio
    async def test_unknown_action_raises_value_error(self):
        manager = OllamaModelManagerPrimitive()
        with pytest.raises(ValueError, match="Unknown action"):
            await manager.execute(OllamaManagerRequest(action="explode"), _ctx())


# ---------------------------------------------------------------------------
# OllamaEmbeddingsPrimitive
# ---------------------------------------------------------------------------


class TestOllamaEmbeddingsPrimitive:
    def _embedder(self, embeddings: list[list[float]], model: str = "nomic-embed-text"):
        embedder = OllamaEmbeddingsPrimitive()
        embed_resp = MagicMock()
        embed_resp.embeddings = embeddings
        embed_resp.model = model
        embed_resp.prompt_eval_count = len(embeddings)

        mock_client = AsyncMock()
        mock_client.embed = AsyncMock(return_value=embed_resp)
        embedder._get_client = MagicMock(return_value=mock_client)
        return embedder, mock_client

    @pytest.mark.asyncio
    async def test_execute_single_string_wrapped_in_list(self):
        # Arrange
        embedder, mock_client = self._embedder([[0.1, 0.2, 0.3]])
        req = OllamaEmbeddingsRequest(input="Hello world")
        # Act
        result = await embedder.execute(req, _ctx())
        # Assert
        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3]
        # String input should be wrapped in a list
        assert mock_client.embed.call_args.kwargs["input"] == ["Hello world"]

    @pytest.mark.asyncio
    async def test_execute_batch_strings(self):
        # Arrange
        vecs = [[0.1, 0.2], [0.3, 0.4]]
        embedder, mock_client = self._embedder(vecs)
        req = OllamaEmbeddingsRequest(input=["text1", "text2"])
        # Act
        result = await embedder.execute(req, _ctx())
        # Assert
        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2]
        assert result.embeddings[1] == [0.3, 0.4]

    @pytest.mark.asyncio
    async def test_execute_passes_options_and_keep_alive(self):
        # Arrange
        embedder, mock_client = self._embedder([[0.1]])
        req = OllamaEmbeddingsRequest(input="text", options={"num_ctx": 512}, keep_alive="5m")
        # Act
        await embedder.execute(req, _ctx())
        # Assert
        kw = mock_client.embed.call_args.kwargs
        assert kw["options"] == {"num_ctx": 512}
        assert kw["keep_alive"] == "5m"

    @pytest.mark.asyncio
    async def test_execute_omits_options_when_empty(self):
        # Arrange
        embedder, mock_client = self._embedder([[0.1]])
        req = OllamaEmbeddingsRequest(input="text")
        # Act
        await embedder.execute(req, _ctx())
        # Assert
        assert "options" not in mock_client.embed.call_args.kwargs

    @pytest.mark.asyncio
    async def test_execute_model_in_response(self):
        # Arrange
        embedder, _ = self._embedder([[0.5, 0.6]], model="mxbai-embed-large")
        req = OllamaEmbeddingsRequest(input="hello", model="mxbai-embed-large")
        # Act
        result = await embedder.execute(req, _ctx())
        # Assert
        assert result.model == "mxbai-embed-large"

    @pytest.mark.asyncio
    async def test_embed_one_returns_single_vector(self):
        # Arrange
        embedder, _ = self._embedder([[1.0, 2.0, 3.0]])
        # Act
        vec = await embedder.embed_one("hello")
        # Assert
        assert vec == [1.0, 2.0, 3.0]

    @pytest.mark.asyncio
    async def test_embed_one_creates_ctx_when_none(self):
        # Arrange — ctx=None path
        embedder, _ = self._embedder([[0.1, 0.2]])
        # Act
        vec = await embedder.embed_one("test", ctx=None)
        # Assert
        assert len(vec) == 2

    @pytest.mark.asyncio
    async def test_embed_batch_returns_multiple_vectors(self):
        # Arrange
        embedder, _ = self._embedder([[0.1], [0.2], [0.3]])
        # Act
        vecs = await embedder.embed_batch(["a", "b", "c"])
        # Assert
        assert len(vecs) == 3

    @pytest.mark.asyncio
    async def test_embed_batch_creates_ctx_when_none(self):
        # Arrange
        embedder, _ = self._embedder([[0.1], [0.2]])
        # Act
        vecs = await embedder.embed_batch(["x", "y"], ctx=None)
        # Assert
        assert len(vecs) == 2


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class TestDataclasses:
    def test_model_info_defaults(self):
        info = OllamaModelInfo(name="qwen3:1.7b")
        assert info.size_bytes == 0
        assert info.parameter_size == ""
        assert info.quantization == ""
        assert info.family == ""
        assert info.format == ""
        assert info.modified_at == ""
        assert info.digest == ""

    def test_running_model_defaults(self):
        rm = RunningModel(name="qwen3:1.7b")
        assert rm.size_bytes == 0
        assert rm.expires_at == ""
        assert rm.digest == ""
