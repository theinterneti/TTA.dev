# Acknowledgements

TTA.dev is built on the shoulders of giants. We're grateful to the following
open source projects, communities, and individuals that made this possible.

---

## Core Infrastructure

- **[Python](https://www.python.org/)** — The language TTA.dev is written in. We target Python
  3.11+ and rely on modern features like `match` statements, `asyncio`, and PEP 604 union types
  throughout the codebase.

- **[Astral](https://astral.sh/)** — Both `uv` (our blazing-fast package manager that replaced
  pip/poetry overnight) and `Ruff` (our linter and formatter). Astral tooling runs on every
  commit and keeps the codebase fast to install and consistent to read.

- **[Pydantic](https://docs.pydantic.dev/)** — Data validation and settings management. Pydantic
  `BaseModel` underpins every integration primitive, workflow config, and API schema in TTA.dev.

- **[OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)** — The
  `opentelemetry-api` and `opentelemetry-sdk` packages power TTA.dev's built-in observability.
  Every primitive execution emits spans, giving users traces without any extra setup.

- **[structlog](https://www.structlog.org/)** — Structured, context-aware logging that pairs
  naturally with our OpenTelemetry traces. Never a raw `print()` in the hot path.

- **[aiohttp](https://docs.aiohttp.org/)** — Async HTTP client/server used across our
  observability server and internal API surface.

- **[hatchling](https://hatch.pypa.io/)** — The build backend that produces TTA.dev's
  distributable wheel. Zero-config and spec-compliant.

---

## LLM Providers & AI Ecosystem

- **[Groq](https://console.groq.com/)** — Our recommended free-tier LLM provider. Groq's
  inference speed makes the default developer loop feel instant.

- **[OpenRouter](https://openrouter.ai/)** — Multi-provider LLM routing. TTA.dev supports
  OpenRouter as a first-class fallback when Groq isn't configured.

- **[Ollama](https://ollama.ai/)** — Local LLM serving for privacy-first, offline-capable AI.
  TTA.dev auto-detects whatever model you have pulled via `ollama list` — no config required.

- **[Anthropic](https://www.anthropic.com/)** — Claude models power many of the complex reasoning
  tasks in our agent layer. Anthropic's AI safety research has also shaped many of our design
  decisions around reliability and graceful degradation.

- **[Google Gemini](https://ai.google.dev/)** — Available via the `google-generativeai` optional
  extra and the `ModelRouterPrimitive` tier system.

- **[OpenAI](https://openai.com/)** — The `openai` SDK serves as the wire-protocol adapter for
  Groq, OpenRouter, and Ollama — all of which speak the OpenAI-compatible API. We use it without
  being locked to any single cloud.

- **[Together AI](https://www.together.ai/)** & **[Hugging Face](https://huggingface.co/)** —
  Additional LLM integration primitives for users who want open-weights models through managed
  APIs.

- **[E2B](https://e2b.dev/)** — Secure cloud sandboxes for safe code interpreter execution. The
  `e2b-code-interpreter` package lets agents run untrusted code without local risk.

---

## Developer Tooling

- **[pytest](https://pytest.org/)** & **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)**
  — Our entire test suite is built on pytest with async-first conventions. `pytest-cov` enforces
  our 80% coverage floor on every CI run.

- **[pyright](https://github.com/microsoft/pyright)** (Microsoft) — Static type analysis in
  `basic` mode catches real bugs before they ship. We run `uvx pyright ttadev/` as a required
  quality gate.

- **[pre-commit](https://pre-commit.com/)** — Git hook framework that wires together Semgrep,
  Bandit, Ruff, detect-secrets, and pytest into a single `git commit` check.

- **[Semgrep](https://semgrep.dev/)** — CodeQL-equivalent static analysis for Python security
  patterns. Runs in the pre-commit pipeline scanning for injection flaws, secret leaks, and
  common vulnerabilities.

- **[Bandit](https://bandit.readthedocs.io/)** (PyCQA) — Python-specific security linter.
  Catches hardcoded credentials, shell injection, and unsafe deserialization before they hit the
  repo.

- **[detect-secrets](https://github.com/Yelp/detect-secrets)** (Yelp) — Prevents credentials
  from ever being committed. Our `.secrets.baseline` is kept up to date on every push.

- **[pip-audit](https://github.com/pypa/pip-audit)** — Dependency vulnerability scanning
  integrated into our dev workflow to flag known CVEs in the dependency tree.

- **[Playwright](https://playwright.dev/)** — Browser automation for integration testing and the
  MCP browser tool used by agents during UI-facing tasks.

- **[fakeredis](https://github.com/cunla/fakeredis-py)** — In-memory Redis implementation that
  lets our coordination and cache primitives be tested without a running Redis instance.

- **[tdd-guard-pytest](https://github.com/tdd-guard/tdd-guard-pytest)** — Enforces TDD discipline
  by tracking test state across the development loop.

- **[cchooks](https://github.com/chriscarrollsmith/cchooks)** — Claude Code hook integration used
  in our agent quality gate automation.

---

## MCP Ecosystem

We're grateful to the growing [Model Context Protocol](https://modelcontextprotocol.io/)
ecosystem for giving AI agents a standard way to call tools.

- **[MCP SDK](https://github.com/modelcontextprotocol/python-sdk)** — The official Python MCP
  library (`mcp>=1.26.0`) that TTA.dev's built-in MCP server is built on.

- **[Context7](https://upstash.com/docs/context7/introduction)** (Upstash) — Documentation MCP
  server that gives our agents live, version-accurate library docs during development.

- **[Serena](https://github.com/oraios/serena)** — Code intelligence MCP server providing symbol
  search, rename, and semantic navigation across the TTA.dev repository.

- **[GitMCP](https://gitmcp.io/)** — Repository-level Git history and context as an MCP server,
  accessible directly from agent sessions.

- **[Langfuse](https://langfuse.com/)** — LLM observability and prompt management via MCP,
  helping us trace model calls end-to-end.

- **[CodeGraphContext](https://github.com/dhamidi/codegraphcontext)** — Code graph analysis MCP
  server that powers the CGC live view in TTA.dev's observability dashboard.

- **[E2B MCP Server](https://e2b.dev/)** — Secure sandbox execution available to agents via the
  MCP protocol for safe, isolated code runs.

---

## Hosting & CI/CD

- **[GitHub](https://github.com/)** — Repository hosting, issue tracking, and CI/CD via
  GitHub Actions. TTA.dev is open source at
  [github.com/theinterneti/TTA.dev](https://github.com/theinterneti/TTA.dev).

- **[GitHub Copilot](https://github.com/features/copilot)** — AI pair programming assistance
  used extensively during TTA.dev's development. The `.github/copilot-instructions.md` file
  encodes the conventions Copilot follows when contributing to this repo.

---

## Inspiration

TTA.dev's primitive-composition model was inspired by the layered design philosophy of tools like
[LangChain](https://langchain.com/) and [LlamaIndex](https://www.llamaindex.ai/), while
deliberately choosing simplicity over framework sprawl. The resilience patterns (Retry, Fallback,
CircuitBreaker, Timeout) draw from battle-tested ideas in distributed systems literature and
projects like [Polly](https://github.com/App-vNext/Polly) (.NET) and
[Resilience4j](https://resilience4j.readme.io/) (JVM).

---

*Built with gratitude by a solo developer. If we've missed a project that TTA.dev relies on,
please [open an issue](https://github.com/theinterneti/TTA.dev/issues) — we'd love to add it.*
