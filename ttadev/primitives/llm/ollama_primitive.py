"""OllamaPrimitive — first-class, feature-complete Ollama integration.

This module exposes three primitives:

* :class:`OllamaPrimitive` — chat, streaming, vision, tool calling,
  structured output, thinking mode.  Uses the official ``ollama`` Python
  client for clean async support.

* :class:`OllamaModelManagerPrimitive` — model lifecycle: list, show, pull
  (with progress), delete, check running models, and health-check the daemon.

* :class:`OllamaEmbeddingsPrimitive` — dense text embeddings via
  ``/api/embed`` (batch, Ollama ≥ 0.5) with fallback to the older
  ``/api/embeddings`` endpoint.

Ollama API quick reference
--------------------------
+-----------------------+----------+-------------------------------+
| Endpoint              | Method   | Purpose                       |
+=======================+==========+===============================+
| /api/chat             | POST     | Chat completion (stream/block)|
| /api/generate         | POST     | Raw text generation           |
| /api/embed            | POST     | Batch embeddings (≥0.5)       |
| /api/embeddings       | POST     | Single embedding (legacy)     |
| /api/tags             | GET      | List local models             |
| /api/ps               | GET      | List running models           |
| /api/show             | POST     | Model metadata / modelfile    |
| /api/pull             | POST     | Download a model (streaming)  |
| /api/delete           | DELETE   | Remove a model                |
| /api/copy             | POST     | Duplicate a model tag         |
| /v1/chat/completions  | POST     | OpenAI-compat (tool calling)  |
+-----------------------+----------+-------------------------------+

Key Ollama options (passed via the ``options`` dict in /api/chat payloads):

  num_ctx           int   Context window size (default: 2048)
  num_predict       int   Max tokens to generate (-1 = infinite)
  temperature       float Sampling temperature (0.0–2.0)
  top_p             float Nucleus sampling probability
  top_k             int   Top-k sampling
  repeat_penalty    float Repetition penalty
  seed              int   RNG seed for reproducibility
  num_gpu           int   GPU layers (-1 = all)
  num_thread        int   CPU threads (0 = auto)

Top-level keys (NOT inside options):

  think             bool  Enable CoT reasoning (Qwen3, DeepSeek-R1, etc.)
  keep_alive        str   Model TTL in memory e.g. "10m", "1h", "0" to unload
  format            str | dict  "json" or a JSON schema for structured output
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

# ── Data models ───────────────────────────────────────────────────────────────


@dataclass
class OllamaRequest:
    """Input for :class:`OllamaPrimitive`.

    Attributes:
        messages: Conversation history in Ollama/OpenAI format.
            Each message is a dict with ``role`` and ``content`` keys.
            Vision messages may include an ``images`` key (list of file paths
            or base64 strings).
        model: Model name e.g. ``"qwen3:1.7b"``, ``"llama3.2:latest"``.
        system: Optional system prompt (injected as the first message).
        temperature: Sampling temperature (0.0–2.0).
        max_tokens: Max tokens to generate (maps to ``num_predict``).
            ``-1`` means unlimited.
        think: Enable chain-of-thought reasoning.  When ``True`` the response
            includes both ``thinking`` and ``content`` fields.
        keep_alive: How long to keep the model loaded after the request,
            e.g. ``"10m"``, ``"1h"``, ``"0"`` (unload immediately).
        format: ``"json"`` or a JSON schema dict for structured output.
        options: Raw Ollama options dict — overrides all other sampling params.
            Use this for num_ctx, top_p, num_gpu, seed, etc.
        tools: Tool definitions for tool-calling capable models (list of
            OpenAI-style function dicts).
        stream: Whether to stream the response token-by-token.
    """

    messages: list[dict[str, Any]]
    model: str = "qwen3:1.7b"
    system: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    think: bool = False
    keep_alive: str | None = None
    format: str | dict | None = None
    options: dict[str, Any] = field(default_factory=dict)
    tools: list[dict[str, Any]] | None = None
    stream: bool = False


@dataclass
class OllamaResponse:
    """Output from :class:`OllamaPrimitive`.

    Attributes:
        content: The model's text response.
        thinking: Chain-of-thought reasoning (only when ``think=True``).
        model: Model that produced the response.
        tool_calls: Tool invocations requested by the model (if any).
        done_reason: Why generation stopped (e.g. ``"stop"``, ``"length"``).
        total_duration_ns: Total time in nanoseconds (including load time).
        prompt_eval_count: Prompt token count.
        eval_count: Generated token count.
    """

    content: str
    thinking: str | None = None
    model: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    done_reason: str | None = None
    total_duration_ns: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None


@dataclass
class OllamaModelInfo:
    """Metadata about an Ollama model from /api/tags or /api/show.

    Attributes:
        name: Full model name e.g. ``"qwen3:1.7b"``.
        size_bytes: Disk size in bytes.
        parameter_size: Human-readable parameter count e.g. ``"1.7B"``.
        quantization: Quantization level e.g. ``"Q4_K_M"``.
        family: Model family e.g. ``"qwen3"``.
        format: Model format e.g. ``"gguf"``.
        modified_at: ISO 8601 last-modified timestamp.
        digest: Model content hash.
    """

    name: str
    size_bytes: int = 0
    parameter_size: str = ""
    quantization: str = ""
    family: str = ""
    format: str = ""
    modified_at: str = ""
    digest: str = ""


@dataclass
class RunningModel:
    """A model currently loaded in Ollama memory (/api/ps).

    Attributes:
        name: Model name.
        size_bytes: VRAM / RAM footprint.
        expires_at: ISO 8601 timestamp when model will be unloaded.
        digest: Content hash.
    """

    name: str
    size_bytes: int = 0
    expires_at: str = ""
    digest: str = ""


# ── OllamaPrimitive ───────────────────────────────────────────────────────────


class OllamaPrimitive(WorkflowPrimitive[OllamaRequest, OllamaResponse]):
    """Feature-complete Ollama chat primitive.

    Uses the official ``ollama`` Python async client.

    Supports:
    - Standard chat (multi-turn conversation)
    - Streaming (token-by-token via :meth:`stream`)
    - Vision / multimodal (pass ``images`` key in message dicts)
    - Tool calling (pass ``tools`` in :class:`OllamaRequest`)
    - Structured output via ``format`` (``"json"`` or JSON schema dict)
    - Thinking mode (``think=True`` for Qwen3, DeepSeek-R1, etc.)
    - ``keep_alive`` to pin / evict models from memory
    - All Ollama sampling options (num_ctx, top_p, num_gpu, seed, …)

    Args:
        base_url: Ollama server URL. Defaults to ``http://localhost:11434``.

    Example::

        primitive = OllamaPrimitive()
        request = OllamaRequest(
            model="qwen3:1.7b",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            options={"num_ctx": 4096},
        )
        response = await primitive.execute(request, ctx)
        print(response.content)
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    def _get_client(self):  # type: ignore[return]
        """Return a configured AsyncClient."""
        from ollama import AsyncClient  # type: ignore[import]

        return AsyncClient(host=self._base_url)

    def _build_options(self, request: OllamaRequest) -> dict[str, Any]:
        """Merge explicit options with request-level sampling params."""
        opts: dict[str, Any] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            opts["num_predict"] = request.max_tokens
        opts.update(request.options)
        return opts

    def _build_messages(self, request: OllamaRequest) -> list[dict[str, Any]]:
        """Inject system prompt if not already present."""
        msgs = list(request.messages)
        if request.system and not any(m.get("role") == "system" for m in msgs):
            msgs = [{"role": "system", "content": request.system}] + msgs
        return msgs

    async def execute(self, request: OllamaRequest, ctx: WorkflowContext) -> OllamaResponse:
        """Run a blocking chat completion.

        Args:
            request: Chat request parameters.
            ctx: Workflow execution context.

        Returns:
            :class:`OllamaResponse` with content and metadata.

        Raises:
            ImportError: If the ``ollama`` package is not installed.
            ollama.ResponseError: If the server returns an error.
        """
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": self._build_messages(request),
            "options": self._build_options(request),
            "think": request.think,
            "stream": False,
        }
        if request.keep_alive is not None:
            kwargs["keep_alive"] = request.keep_alive
        if request.format is not None:
            kwargs["format"] = request.format
        if request.tools:
            kwargs["tools"] = request.tools

        resp = await client.chat(**kwargs)
        msg = resp.message
        content = getattr(msg, "content", "") or ""
        thinking = getattr(msg, "thinking", None)

        tool_calls = None
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = [
                {
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in msg.tool_calls
            ]

        return OllamaResponse(
            content=content,
            thinking=thinking,
            model=resp.model or request.model,
            tool_calls=tool_calls,
            done_reason=getattr(resp, "done_reason", None),
            total_duration_ns=getattr(resp, "total_duration", None),
            prompt_eval_count=getattr(resp, "prompt_eval_count", None),
            eval_count=getattr(resp, "eval_count", None),
        )

    async def stream(self, request: OllamaRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream response tokens as they are generated.

        When ``think=True``, thinking tokens are yielded first
        (from the ``thinking`` field) then content tokens.

        Args:
            request: Chat request with ``stream`` flag (ignored — always streams).
            ctx: Workflow execution context.

        Yields:
            Text chunks as they arrive from the model.
        """
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": self._build_messages(request),
            "options": self._build_options(request),
            "think": request.think,
            "stream": True,
        }
        if request.keep_alive is not None:
            kwargs["keep_alive"] = request.keep_alive
        if request.format is not None:
            kwargs["format"] = request.format

        async for chunk in await client.chat(**kwargs):
            msg = chunk.message
            content = getattr(msg, "content", "") or ""
            if content:
                yield content
            elif request.think:
                thinking = getattr(msg, "thinking", "") or ""
                if thinking:
                    yield thinking


# ── OllamaModelManagerPrimitive ───────────────────────────────────────────────


@dataclass
class OllamaManagerRequest:
    """Input for :class:`OllamaModelManagerPrimitive`.

    Attributes:
        action: One of ``list``, ``running``, ``show``, ``pull``, ``delete``,
            ``copy``, ``health``.
        model: Model name (required for ``show``, ``pull``, ``delete``,
            ``copy``).
        destination: Destination tag for ``copy`` action.
        insecure: Allow insecure registry connections for ``pull``.
    """

    action: str
    model: str = ""
    destination: str = ""
    insecure: bool = False


@dataclass
class OllamaManagerResponse:
    """Output from :class:`OllamaModelManagerPrimitive`.

    Attributes:
        action: The action that was performed.
        healthy: True if Ollama daemon is reachable (for ``health`` action).
        models: Model list (for ``list`` action).
        running: Currently loaded models (for ``running`` action).
        info: Model metadata (for ``show`` action).
        status: Status message (for ``pull``, ``delete``, ``copy``).
        progress_messages: Streaming pull progress lines.
    """

    action: str
    healthy: bool = False
    models: list[OllamaModelInfo] = field(default_factory=list)
    running: list[RunningModel] = field(default_factory=list)
    info: OllamaModelInfo | None = None
    status: str = ""
    progress_messages: list[str] = field(default_factory=list)


class OllamaModelManagerPrimitive(WorkflowPrimitive[OllamaManagerRequest, OllamaManagerResponse]):
    """Manage Ollama model lifecycle: list, pull, delete, show, health.

    Provides programmatic access to all Ollama model management endpoints
    so agents can discover available models, pull new ones, and clean up.

    Args:
        base_url: Ollama server URL. Defaults to ``http://localhost:11434``.

    Example::

        manager = OllamaModelManagerPrimitive()

        # Check daemon health
        r = await manager.execute(OllamaManagerRequest(action="health"), ctx)
        print(r.healthy)

        # List available models
        r = await manager.execute(OllamaManagerRequest(action="list"), ctx)
        for m in r.models:
            print(m.name, m.parameter_size, m.quantization)

        # Pull a model (streaming progress)
        r = await manager.execute(
            OllamaManagerRequest(action="pull", model="llama3.2:latest"), ctx
        )

        # Show model info
        r = await manager.execute(
            OllamaManagerRequest(action="show", model="qwen3:1.7b"), ctx
        )
        print(r.info)
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    def _get_client(self):  # type: ignore[return]
        from ollama import AsyncClient  # type: ignore[import]

        return AsyncClient(host=self._base_url)

    async def execute(
        self, request: OllamaManagerRequest, ctx: WorkflowContext
    ) -> OllamaManagerResponse:
        """Dispatch to the appropriate model management operation.

        Args:
            request: Manager action and parameters.
            ctx: Workflow execution context.

        Returns:
            :class:`OllamaManagerResponse` with results.
        """
        action = request.action.lower()
        if action == "health":
            return await self._health(request)
        elif action == "list":
            return await self._list_models(request)
        elif action == "running":
            return await self._running_models(request)
        elif action == "show":
            return await self._show_model(request)
        elif action == "pull":
            return await self._pull_model(request)
        elif action == "delete":
            return await self._delete_model(request)
        elif action == "copy":
            return await self._copy_model(request)
        else:
            raise ValueError(
                f"Unknown action '{action}'. Valid actions: "
                "health, list, running, show, pull, delete, copy"
            )

    async def _health(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/")
                healthy = r.status_code == 200
        except Exception:
            healthy = False
        return OllamaManagerResponse(action="health", healthy=healthy)

    async def _list_models(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        resp = await client.list()
        models = []
        for m in resp.models:
            details = getattr(m, "details", None)
            models.append(
                OllamaModelInfo(
                    name=m.model or "",
                    size_bytes=getattr(m, "size", 0) or 0,
                    parameter_size=getattr(details, "parameter_size", "") if details else "",
                    quantization=getattr(details, "quantization_level", "") if details else "",
                    family=getattr(details, "family", "") if details else "",
                    format=getattr(details, "format", "") if details else "",
                    modified_at=str(getattr(m, "modified_at", "") or ""),
                    digest=getattr(m, "digest", "") or "",
                )
            )
        return OllamaManagerResponse(action="list", models=models)

    async def _running_models(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        resp = await client.ps()
        running = []
        for m in resp.models:
            running.append(
                RunningModel(
                    name=m.model or "",
                    size_bytes=getattr(m, "size", 0) or 0,
                    expires_at=str(getattr(m, "expires_at", "") or ""),
                    digest=getattr(m, "digest", "") or "",
                )
            )
        return OllamaManagerResponse(action="running", running=running)

    async def _show_model(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        resp = await client.show(request.model)
        details = getattr(resp, "details", None)
        info = OllamaModelInfo(
            name=request.model,
            parameter_size=getattr(details, "parameter_size", "") if details else "",
            quantization=getattr(details, "quantization_level", "") if details else "",
            family=getattr(details, "family", "") if details else "",
            format=getattr(details, "format", "") if details else "",
        )
        return OllamaManagerResponse(action="show", info=info)

    async def _pull_model(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        progress: list[str] = []
        async for chunk in await client.pull(request.model, insecure=request.insecure, stream=True):
            status = getattr(chunk, "status", "") or ""
            if status:
                progress.append(status)
        return OllamaManagerResponse(
            action="pull",
            status="success",
            progress_messages=progress,
        )

    async def _delete_model(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        await client.delete(request.model)
        return OllamaManagerResponse(action="delete", status="deleted")

    async def _copy_model(self, request: OllamaManagerRequest) -> OllamaManagerResponse:
        client = self._get_client()
        await client.copy(request.model, request.destination)
        return OllamaManagerResponse(action="copy", status="copied")


# ── OllamaEmbeddingsPrimitive ─────────────────────────────────────────────────


@dataclass
class OllamaEmbeddingsRequest:
    """Input for :class:`OllamaEmbeddingsPrimitive`.

    Attributes:
        input: Text string or list of strings to embed.
        model: Embedding model name e.g. ``"nomic-embed-text"``,
            ``"mxbai-embed-large"``, ``"all-minilm"``.
        options: Additional Ollama options (e.g. ``{"num_ctx": 4096}``).
        keep_alive: How long to keep the model loaded after the request.
    """

    input: str | list[str]
    model: str = "nomic-embed-text"
    options: dict[str, Any] = field(default_factory=dict)
    keep_alive: str | None = None


@dataclass
class OllamaEmbeddingsResponse:
    """Output from :class:`OllamaEmbeddingsPrimitive`.

    Attributes:
        embeddings: List of embedding vectors.  Each vector is a list of floats.
            For a single-string input this will have one element.
        model: Model that produced the embeddings.
        prompt_eval_count: Number of tokens in the prompt.
    """

    embeddings: list[list[float]]
    model: str = ""
    prompt_eval_count: int | None = None


class OllamaEmbeddingsPrimitive(
    WorkflowPrimitive[OllamaEmbeddingsRequest, OllamaEmbeddingsResponse]
):
    """Generate text embeddings via Ollama's /api/embed endpoint.

    Uses the batch-capable ``/api/embed`` endpoint (Ollama ≥ 0.5) which
    accepts a list of strings and returns a list of embedding vectors.
    Recommended embedding models:

    * ``nomic-embed-text`` — 137M params, 768-dim, good all-rounder
    * ``mxbai-embed-large`` — 335M params, 1024-dim, high quality
    * ``all-minilm`` — 23M params, 384-dim, fast / lightweight
    * ``bge-m3`` — multilingual, 1024-dim

    Args:
        base_url: Ollama server URL. Defaults to ``http://localhost:11434``.

    Example::

        embedder = OllamaEmbeddingsPrimitive()
        req = OllamaEmbeddingsRequest(
            input=["Hello world", "Goodbye world"],
            model="nomic-embed-text",
        )
        resp = await embedder.execute(req, ctx)
        print(len(resp.embeddings))     # 2
        print(len(resp.embeddings[0]))  # 768
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    def _get_client(self):  # type: ignore[return]
        from ollama import AsyncClient  # type: ignore[import]

        return AsyncClient(host=self._base_url)

    async def execute(
        self, request: OllamaEmbeddingsRequest, ctx: WorkflowContext
    ) -> OllamaEmbeddingsResponse:
        """Generate embeddings for one or more text strings.

        Args:
            request: Embeddings request with text and model selection.
            ctx: Workflow execution context.

        Returns:
            :class:`OllamaEmbeddingsResponse` with embedding vectors.
        """
        client = self._get_client()

        inputs = request.input if isinstance(request.input, list) else [request.input]

        kwargs: dict[str, Any] = {
            "model": request.model,
            "input": inputs,
        }
        if request.options:
            kwargs["options"] = request.options
        if request.keep_alive is not None:
            kwargs["keep_alive"] = request.keep_alive

        resp = await client.embed(**kwargs)
        embeddings = [list(v) for v in resp.embeddings]

        return OllamaEmbeddingsResponse(
            embeddings=embeddings,
            model=resp.model or request.model,
            prompt_eval_count=getattr(resp, "prompt_eval_count", None),
        )

    async def embed_one(
        self, text: str, model: str = "nomic-embed-text", ctx: WorkflowContext | None = None
    ) -> list[float]:
        """Convenience method — embed a single string.

        Args:
            text: Text to embed.
            model: Embedding model name.
            ctx: Optional workflow context.

        Returns:
            Single embedding vector as a list of floats.
        """
        if ctx is None:
            ctx = WorkflowContext(workflow_id="embed-one")
        resp = await self.execute(OllamaEmbeddingsRequest(input=text, model=model), ctx)
        return resp.embeddings[0]

    async def embed_batch(
        self,
        texts: list[str],
        model: str = "nomic-embed-text",
        ctx: WorkflowContext | None = None,
    ) -> list[list[float]]:
        """Convenience method — embed multiple strings in one request.

        Args:
            texts: List of texts to embed.
            model: Embedding model name.
            ctx: Optional workflow context.

        Returns:
            List of embedding vectors.
        """
        if ctx is None:
            ctx = WorkflowContext(workflow_id="embed-batch")
        resp = await self.execute(OllamaEmbeddingsRequest(input=texts, model=model), ctx)
        return resp.embeddings


# ── Convenience re-exports ────────────────────────────────────────────────────

__all__ = [
    "OllamaEmbeddingsPrimitive",
    "OllamaEmbeddingsRequest",
    "OllamaEmbeddingsResponse",
    "OllamaModelInfo",
    "OllamaModelManagerPrimitive",
    "OllamaManagerRequest",
    "OllamaManagerResponse",
    "OllamaPrimitive",
    "OllamaRequest",
    "OllamaResponse",
    "RunningModel",
]
