# Ollama Integration Guide

> **Audience:** AI agents and developers working in TTA.dev
> **Source:** Ollama API docs + official Python client v0.6.1 + TTA.dev primitives

---

## What Ollama is

Ollama runs LLMs locally as a daemonized HTTP server (default `http://localhost:11434`).
Models are downloaded on-demand and cached on disk. No API keys required — it is purely local.

---

## Quick Reference: API Endpoints

| Endpoint              | Method | Purpose                                 |
|-----------------------|--------|-----------------------------------------|
| `/`                   | GET    | Health check (returns 200 + "Ollama is running") |
| `/api/chat`           | POST   | Chat completion (blocking or streaming) |
| `/api/generate`       | POST   | Raw text generation                     |
| `/api/embed`          | POST   | Batch embeddings (Ollama ≥ 0.5)         |
| `/api/embeddings`     | POST   | Single embedding (legacy)               |
| `/api/tags`           | GET    | List locally downloaded models          |
| `/api/ps`             | GET    | List currently loaded models in memory  |
| `/api/show`           | POST   | Model metadata / modelfile              |
| `/api/pull`           | POST   | Download a model (streaming progress)   |
| `/api/delete`         | DELETE | Remove a model from disk                |
| `/api/copy`           | POST   | Duplicate a model under a new tag       |
| `/v1/chat/completions`| POST   | OpenAI-compatible (tool calling, functions) |

---

## `/api/chat` payload shape

```json
{
  "model": "qwen3:1.7b",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user",   "content": "Hello"}
  ],
  "stream": false,
  "think": false,
  "keep_alive": "10m",
  "format": "json",
  "options": {
    "num_ctx":        4096,
    "num_predict":    512,
    "temperature":    0.7,
    "top_p":          0.9,
    "top_k":          40,
    "repeat_penalty": 1.1,
    "seed":           42,
    "num_gpu":        -1,
    "num_thread":     0
  }
}
```

### Critical rules

- `options` is a **nested dict** — never place sampling params at the top level
- `think`, `keep_alive`, `format`, `tools` **are** top-level keys (not inside `options`)
- `max_tokens` does NOT exist — use `options.num_predict`

---

## Thinking / Chain-of-Thought mode

Supported by models: Qwen3 family, DeepSeek-R1, DeepSeek-R2.

```json
{"think": true}
```

When `think: true`, the response contains two fields:
- `message.thinking` — the model's scratchpad (CoT tokens)
- `message.content` — the final answer

**Gotcha with Qwen3:** Qwen3 models default to `think: true` even without setting it.
When `think: true` implicitly, `message.content` may be empty and all output lives in `message.thinking`.

**Fix:** explicitly send `"think": false` to suppress thinking and get normal output.

```python
# TTA.dev OllamaPrimitive defaults think=False
request = OllamaRequest(model="qwen3:1.7b", messages=[...])  # safe default

# Opt in explicitly
request = OllamaRequest(model="qwen3:1.7b", messages=[...], think=True)
```

---

## `keep_alive` — model memory management

```
keep_alive: "10m"   # keep loaded for 10 minutes (default behaviour)
keep_alive: "1h"    # keep loaded for 1 hour
keep_alive: "0"     # unload immediately after request
keep_alive: "-1"    # keep loaded indefinitely until restart
```

Use `keep_alive="0"` for one-shot requests to free VRAM. Use `"-1"` for hot models.

---

## Structured output (format)

```json
{"format": "json"}               // any valid JSON
{"format": {"type": "object", "properties": {...}}}  // strict schema
```

The model will always emit valid JSON matching the schema when format is a JSON Schema dict.

---

## Tool calling

Use `/v1/chat/completions` (OpenAI-compat) for tool calling, or pass `tools` to `/api/chat`:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"}
          },
          "required": ["city"]
        }
      }
    }
  ]
}
```

When the model decides to call a tool, `message.tool_calls` will be populated instead of `message.content`.

---

## Vision / multimodal

Pass images as base64 strings or file paths in the `images` key of a user message:

```json
{
  "role": "user",
  "content": "What is in this image?",
  "images": ["base64encodedstring=="]
}
```

Models that support vision: `llava`, `bakllava`, `moondream`, `llava-phi3`.

---

## Embeddings

### Batch endpoint (recommended, Ollama ≥ 0.5)

```http
POST /api/embed
{"model": "nomic-embed-text", "input": ["text1", "text2"]}
```

Response: `{"embeddings": [[...], [...]], "model": "...", "prompt_eval_count": N}`

### Legacy single-string endpoint

```http
POST /api/embeddings
{"model": "nomic-embed-text", "prompt": "text1"}
```

Response: `{"embedding": [...]}`  (singular)

### Recommended embedding models

| Model             | Dimensions | Notes                      |
|-------------------|-----------|----------------------------|
| `nomic-embed-text`| 768       | Good all-rounder, fast     |
| `mxbai-embed-large`| 1024     | High quality               |
| `bge-m3`          | 1024      | Multilingual               |
| `all-minilm`      | 384       | Very fast, smaller vectors |

---

## Model management API

### List local models

```http
GET /api/tags
```

```json
{
  "models": [
    {
      "name": "qwen3:1.7b",
      "model": "qwen3:1.7b",
      "size": 1200000000,
      "digest": "sha256:...",
      "details": {
        "parameter_size": "1.7B",
        "quantization_level": "Q4_K_M",
        "family": "qwen3",
        "format": "gguf"
      }
    }
  ]
}
```

### List running models

```http
GET /api/ps
```

Returns models currently loaded in memory with `expires_at` timestamps.

### Pull a model (streaming progress)

```http
POST /api/pull
{"model": "llama3.2:latest", "stream": true}
```

Each line is a JSON progress object with a `status` field:
```json
{"status": "pulling manifest"}
{"status": "downloading weights", "completed": 512, "total": 4096}
{"status": "verifying sha256"}
{"status": "success"}
```

### Show model info

```http
POST /api/show
{"model": "qwen3:1.7b"}
```

Returns modelfile, parameters, template, and details.

---

## Python client (ollama 0.6.1)

### AsyncClient

```python
from ollama import AsyncClient

client = AsyncClient(host="http://localhost:11434")

# Chat
resp = await client.chat(
    model="qwen3:1.7b",
    messages=[{"role": "user", "content": "Hello"}],
    options={"num_ctx": 4096, "temperature": 0.7},
    think=False,
    keep_alive="10m",
    stream=False,
)
print(resp.message.content)

# Streaming
async for chunk in await client.chat(..., stream=True):
    print(chunk.message.content, end="", flush=True)

# Embeddings
resp = await client.embed(model="nomic-embed-text", input=["text1", "text2"])
vectors = resp.embeddings  # list[list[float]]

# Model management
await client.list()                     # → resp.models
await client.ps()                       # → resp.models (running)
await client.show("qwen3:1.7b")         # → resp.details
await client.pull("llama3.2:latest", stream=True)  # async iterator
await client.delete("qwen3:1.7b")
await client.copy("qwen3:1.7b", "mymodel:v1")
```

---

## TTA.dev Primitives

### OllamaPrimitive — chat

```python
from ttadev.primitives.llm.ollama_primitive import OllamaPrimitive, OllamaRequest
from ttadev.primitives.core.base import WorkflowContext

primitive = OllamaPrimitive()  # base_url defaults to http://localhost:11434
ctx = WorkflowContext(workflow_id="my-workflow")

# Basic chat
request = OllamaRequest(
    model="qwen3:1.7b",
    messages=[{"role": "user", "content": "Hello"}],
    options={"num_ctx": 4096},
)
response = await primitive.execute(request, ctx)
print(response.content)

# Thinking mode
request = OllamaRequest(
    model="qwen3:1.7b",
    messages=[{"role": "user", "content": "Solve 2+2"}],
    think=True,
)
response = await primitive.execute(request, ctx)
print("Thinking:", response.thinking)
print("Answer:", response.content)

# Streaming
async for token in primitive.stream(request, ctx):
    print(token, end="", flush=True)

# Structured output
request = OllamaRequest(
    model="qwen3:1.7b",
    messages=[{"role": "user", "content": "List 3 colors as JSON"}],
    format="json",
)

# Vision
request = OllamaRequest(
    model="llava:latest",
    messages=[{"role": "user", "content": "Describe this", "images": ["base64..."]}],
)
```

### OllamaModelManagerPrimitive — lifecycle

```python
from ttadev.primitives.llm.ollama_primitive import OllamaModelManagerPrimitive, OllamaManagerRequest

manager = OllamaModelManagerPrimitive()

# Health check
r = await manager.execute(OllamaManagerRequest(action="health"), ctx)
print(r.healthy)  # True/False

# List models
r = await manager.execute(OllamaManagerRequest(action="list"), ctx)
for m in r.models:
    print(m.name, m.parameter_size, m.quantization)

# Running models
r = await manager.execute(OllamaManagerRequest(action="running"), ctx)
for m in r.running:
    print(m.name, "expires:", m.expires_at)

# Pull a model
r = await manager.execute(OllamaManagerRequest(action="pull", model="llama3.2:latest"), ctx)
print(r.status)            # "success"
print(r.progress_messages) # ["pulling manifest", "downloading...", "success"]

# Show model info
r = await manager.execute(OllamaManagerRequest(action="show", model="qwen3:1.7b"), ctx)
print(r.info.family, r.info.parameter_size, r.info.quantization)

# Delete a model
r = await manager.execute(OllamaManagerRequest(action="delete", model="qwen3:1.7b"), ctx)
print(r.status)  # "deleted"
```

### OllamaEmbeddingsPrimitive — RAG embeddings

```python
from ttadev.primitives.llm.ollama_primitive import OllamaEmbeddingsPrimitive, OllamaEmbeddingsRequest

embedder = OllamaEmbeddingsPrimitive()

# Convenience methods (recommended)
vector = await embedder.embed_one("Hello world", model="nomic-embed-text")
# → list[float] with 768 dimensions

vectors = await embedder.embed_batch(
    ["text one", "text two", "text three"],
    model="nomic-embed-text",
)
# → list[list[float]]

# Full request (for options/keep_alive)
request = OllamaEmbeddingsRequest(
    input=["sentence A", "sentence B"],
    model="mxbai-embed-large",
    options={"num_ctx": 512},
    keep_alive="30m",
)
result = await embedder.execute(request, ctx)
print(len(result.embeddings))       # 2
print(len(result.embeddings[0]))    # 1024 (mxbai-embed-large dims)
```

---

## Ollama CLI cheatsheet

```bash
ollama list                     # show downloaded models
ollama ps                       # show running models
ollama pull qwen3:1.7b          # download a model
ollama rm qwen3:1.7b            # delete a model
ollama run qwen3:1.7b           # interactive chat
ollama run qwen3:1.7b "Hello"   # single prompt
ollama show qwen3:1.7b          # show modelfile + metadata
ollama serve                    # start daemon (usually auto-started)
```

---

## Common issues and fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `message.content == ""` with Qwen3 | Implicit think mode | Send `"think": false` explicitly |
| `ConnectionRefusedError` | Daemon not running | `ollama serve` or systemctl start |
| `ollama.ResponseError: model not found` | Model not pulled | `ollama pull <model>` |
| Slow first response | Model loading into VRAM | Normal — subsequent requests are fast |
| `OOM` / CUDA out of memory | Model too large | Use smaller quant or `num_gpu: 0` for CPU |
| Embeddings wrong shape | Wrong model | Check model dims in table above |
| `stream=True` hangs | Not iterating async generator | Use `async for chunk in await client.chat(..., stream=True)` |

---

## Selecting a model

| Use case | Recommended model |
|----------|------------------|
| Fast chat (low VRAM) | `qwen3:1.7b` |
| Good reasoning | `qwen3:8b` |
| Long context | `qwen3:8b` with `num_ctx: 32768` |
| Code | `qwen2.5-coder:7b` |
| Vision | `llava:latest`, `llava-phi3` |
| Embeddings (fast) | `all-minilm` |
| Embeddings (quality) | `nomic-embed-text`, `mxbai-embed-large` |
| Thinking / CoT | `qwen3:any`, `deepseek-r1:latest` |

---

## References

- [Ollama API reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Python client](https://github.com/ollama/ollama-python)
- [Model library](https://ollama.com/search)
- [`ttadev/primitives/llm/ollama_primitive.py`](../../ttadev/primitives/llm/ollama_primitive.py)
