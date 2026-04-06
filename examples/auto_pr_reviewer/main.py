#!/usr/bin/env python3
"""Auto PR Reviewer — example TTA.dev agentic application.

Demonstrates a complete agentic pattern using four TTA.dev primitives chained
with the ``>>`` operator::

    CachePrimitive[fetch_pr_diff]           ← avoids redundant gh CLI calls
      >> LambdaPrimitive[prepare_request]   ← builds LLMRequest from diff dict
      >> RetryPrimitive[LiteLLMPrimitive]   ← resilient LLM call with back-off
      >> LambdaPrimitive[format_review]     ← formats LLMResponse → human text

Usage::

    python examples/auto_pr_reviewer/main.py --pr https://github.com/owner/repo/pull/123
    python examples/auto_pr_reviewer/main.py --pr 123 --repo owner/repo
    python examples/auto_pr_reviewer/main.py --pr 123 --repo owner/repo --model ollama/qwen2.5:7b

Environment variables::

    GROQ_API_KEY       — Groq API key (fastest free tier; recommended)
    ANTHROPIC_API_KEY  — Anthropic API key
    OPENAI_API_KEY     — OpenAI API key
    OTEL_EXPORTER_OTLP_ENDPOINT — OTel collector endpoint for span export

When no provider API key is set the model falls back to ``ollama/qwen2.5:7b``
(requires a running Ollama instance).
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from collections.abc import Callable
from typing import Any

# ── OTel — optional, degrades gracefully ────────────────────────────────────
try:
    from opentelemetry import trace as otel_trace

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OTEL_AVAILABLE = False
    otel_trace = None  # type: ignore[assignment]

from ttadev.primitives import (
    CachePrimitive,
    LambdaPrimitive,
    LLMRequest,
    LLMResponse,
    RetryPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)
from ttadev.primitives.llm import LiteLLMPrimitive
from ttadev.primitives.recovery.retry import RetryStrategy

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"
_FALLBACK_MODEL = "ollama/qwen2.5:7b"

_REVIEW_SYSTEM_PROMPT = """\
You are an expert code reviewer. Review the following PR diff and provide:
1. A brief summary of what the PR does
2. Potential issues or bugs (if any)
3. Style/readability suggestions
4. An overall assessment (Approve / Request Changes / Comment)"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_pr_url(pr_url: str, repo: str | None = None) -> tuple[str, str, int]:
    """Parse a GitHub PR reference into ``(owner, repo, pr_number)``.

    Accepts:
    - Full URL: ``https://github.com/owner/repo/pull/123``
    - Short form: ``owner/repo#123``
    - Plain integer (requires *repo* kwarg): ``123``

    Args:
        pr_url: PR reference — full URL, short form, or plain integer string.
        repo: Fallback ``owner/repo`` string when *pr_url* is a plain integer.

    Returns:
        A ``(owner, repo_name, pr_number)`` tuple.

    Raises:
        ValueError: When *pr_url* cannot be parsed or is a plain integer
            without a *repo* fallback.
    """
    # Full GitHub URL
    url_match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        pr_url.strip(),
    )
    if url_match:
        return url_match.group(1), url_match.group(2), int(url_match.group(3))

    # Short form: owner/repo#number
    short_match = re.match(r"([^/]+)/([^#]+)#(\d+)", pr_url.strip())
    if short_match:
        return short_match.group(1), short_match.group(2), int(short_match.group(3))

    # Plain integer — needs repo from caller
    if pr_url.strip().isdigit():
        if not repo:
            raise ValueError(
                f"PR reference {pr_url!r} is a plain number. "
                "Pass --repo owner/repo so the reviewer knows which repository to query."
            )
        parts = repo.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"--repo must be in 'owner/repo' format, got: {repo!r}")
        return parts[0], parts[1], int(pr_url.strip())

    raise ValueError(
        f"Cannot parse PR reference: {pr_url!r}. "
        "Accepted formats: full GitHub URL, 'owner/repo#123', or a plain PR number with --repo."
    )


# ---------------------------------------------------------------------------
# Workflow step functions
# ---------------------------------------------------------------------------


async def fetch_pr_diff(pr_url: str, ctx: WorkflowContext) -> dict[str, Any]:
    """Fetch the PR diff via the ``gh`` CLI and return structured metadata.

    This function is wrapped by :class:`~ttadev.primitives.LambdaPrimitive`
    and cached by :class:`~ttadev.primitives.CachePrimitive`.  Caching avoids
    repeated ``gh`` CLI invocations for the same PR during a session.

    Args:
        pr_url: A GitHub PR URL, short reference (``owner/repo#N``), or plain
            PR number string.  Plain integers require ``ctx.metadata["repo"]``
            to be set.
        ctx: Workflow context.  ``ctx.metadata["repo"]`` is used as a fallback
            ``owner/repo`` string when *pr_url* is a plain integer.

    Returns:
        A dict with keys:
        - ``"diff"`` — the raw unified diff text
        - ``"pr_url"`` — the original *pr_url* argument
        - ``"pr_number"`` — integer PR number
        - ``"repo"`` — ``"owner/repo"`` string

    Raises:
        RuntimeError: When the ``gh`` CLI call returns a non-zero exit code.
        ValueError: When *pr_url* cannot be parsed (propagated from
            :func:`_parse_pr_url`).
    """
    tracer_name = __name__
    repo_hint: str | None = ctx.metadata.get("repo")
    owner, repo_name, pr_number = _parse_pr_url(pr_url, repo=repo_hint)
    full_repo = f"{owner}/{repo_name}"

    cmd = ["gh", "pr", "diff", str(pr_number), "--repo", full_repo]

    def _run_gh() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

    if _OTEL_AVAILABLE and otel_trace is not None:
        tracer = otel_trace.get_tracer(tracer_name)
        with tracer.start_as_current_span("auto_pr_reviewer.fetch_pr_diff") as span:
            span.set_attribute("pr.url", pr_url)
            span.set_attribute("pr.number", pr_number)
            span.set_attribute("pr.repo", full_repo)
            result = await asyncio.get_event_loop().run_in_executor(None, _run_gh)
            span.set_attribute("gh.exit_code", result.returncode)
    else:
        result = await asyncio.get_event_loop().run_in_executor(None, _run_gh)

    if result.returncode != 0:
        err = result.stderr.strip() or f"gh exited with code {result.returncode}"
        raise RuntimeError(f"Failed to fetch PR diff for {full_repo}#{pr_number}: {err}")

    return {
        "diff": result.stdout,
        "pr_url": pr_url,
        "pr_number": pr_number,
        "repo": full_repo,
    }


def _make_prepare_request(model: str) -> Callable[[dict[str, Any], WorkflowContext], Any]:
    """Return a coroutine function that builds an :class:`LLMRequest` from diff metadata.

    This factory captures *model* in a closure so the same string is embedded
    in every :class:`LLMRequest` without threading it through the context.

    Args:
        model: The litellm model string (e.g. ``"groq/llama-3.3-70b-versatile"``).

    Returns:
        An async function ``(diff_data, ctx) -> LLMRequest`` suitable for
        wrapping in a :class:`~ttadev.primitives.LambdaPrimitive`.
    """

    async def prepare_request(diff_data: dict[str, Any], ctx: WorkflowContext) -> LLMRequest:
        """Transform diff metadata dict into an LLMRequest for the reviewer."""
        diff_text = diff_data.get("diff", "").strip()
        if not diff_text:
            diff_text = "(no diff available — the PR may be empty or inaccessible)"

        pr_ref = diff_data.get("repo", "unknown") + "#" + str(diff_data.get("pr_number", "?"))

        return LLMRequest(
            model=model,
            messages=[
                {"role": "system", "content": _REVIEW_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Please review the following PR ({pr_ref}):\n\n```diff\n{diff_text}\n```",
                },
            ],
            temperature=0.2,
            max_tokens=2048,
        )

    return prepare_request


async def format_review(llm_response: LLMResponse, ctx: WorkflowContext) -> str:
    """Format an :class:`LLMResponse` into a human-readable review string.

    Args:
        llm_response: The LLM's review response.
        ctx: Workflow context (unused but required by the LambdaPrimitive interface).

    Returns:
        A formatted multi-line string ready for printing to stdout.
    """
    sep = "─" * 60
    lines: list[str] = [
        sep,
        "🔍  AUTO PR REVIEW  (powered by TTA.dev)",
        sep,
        "",
        llm_response.content,
        "",
        sep,
        f"Model    : {llm_response.provider}/{llm_response.model}",
    ]
    if llm_response.usage:
        total = llm_response.usage.get("total_tokens", "?")
        lines.append(f"Tokens   : {total}")
    if llm_response.finish_reason:
        lines.append(f"Finish   : {llm_response.finish_reason}")
    elapsed = f"{ctx.elapsed_ms():.0f} ms"
    lines.append(f"Elapsed  : {elapsed}")
    lines.append(sep)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------


def build_reviewer(
    model: str = _DEFAULT_MODEL,
    *,
    llm_primitive: WorkflowPrimitive | None = None,
    cache_ttl_seconds: float = 3600.0,
    max_retries: int = 3,
) -> WorkflowPrimitive:
    """Compose the PR reviewer workflow from TTA.dev primitives.

    The resulting pipeline::

        CachePrimitive[LambdaPrimitive[fetch_pr_diff]]
          >> LambdaPrimitive[prepare_request]
          >> RetryPrimitive[LiteLLMPrimitive]
          >> LambdaPrimitive[format_review]

    **Why each primitive?**

    - :class:`~ttadev.primitives.LambdaPrimitive` — wraps any async function
      as a typed workflow step without boilerplate.
    - :class:`~ttadev.primitives.CachePrimitive` — caches the ``gh pr diff``
      result keyed on the PR URL so repeated runs in the same session skip
      the network round-trip.
    - :class:`~ttadev.primitives.RetryPrimitive` — transparently retries the
      LLM call on transient ``429 Rate-Limit`` errors with exponential back-off.
    - :class:`~ttadev.primitives.llm.LiteLLMPrimitive` — single entrypoint
      for 100+ LLM providers; no provider-specific code needed.

    Args:
        model: litellm model string, e.g. ``"groq/llama-3.3-70b-versatile"``.
            Falls back to ``"ollama/qwen2.5:7b"`` automatically in :func:`main`
            when no cloud API key is present.
        llm_primitive: Override the :class:`~ttadev.primitives.llm.LiteLLMPrimitive`
            with any :class:`~ttadev.primitives.WorkflowPrimitive`.  Intended
            for testing — pass a :class:`~ttadev.primitives.MockPrimitive`.
        cache_ttl_seconds: TTL for the PR diff cache (default: 1 hour).
        max_retries: Maximum LLM retry attempts on transient failures.

    Returns:
        A :class:`~ttadev.primitives.WorkflowPrimitive` that accepts a PR URL
        string and produces a formatted review string.
    """
    # ── Step 1: fetch PR diff (wrapped in cache) ─────────────────────────────
    fetch: WorkflowPrimitive = LambdaPrimitive(fetch_pr_diff)
    cached_fetch: WorkflowPrimitive = CachePrimitive(
        fetch,
        cache_key_fn=lambda url, _ctx: f"pr-diff:{url}",
        ttl_seconds=cache_ttl_seconds,
    )

    # ── Step 2: transform diff dict → LLMRequest ────────────────────────────
    prepare: WorkflowPrimitive = LambdaPrimitive(_make_prepare_request(model))

    # ── Step 3: call LLM with retry for transient rate limits ───────────────
    _llm: WorkflowPrimitive = llm_primitive if llm_primitive is not None else LiteLLMPrimitive()
    retry_llm: WorkflowPrimitive = RetryPrimitive(
        _llm,
        strategy=RetryStrategy(max_retries=max_retries, backoff_base=2.0),
    )

    # ── Step 4: format LLMResponse → printable string ───────────────────────
    format_output: WorkflowPrimitive = LambdaPrimitive(format_review)

    return cached_fetch >> prepare >> retry_llm >> format_output


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


async def main() -> None:
    """CLI entrypoint for the Auto PR Reviewer.

    Parses arguments, resolves the model (with local Ollama fallback when no
    cloud key is present), builds the reviewer workflow, and prints the review.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto PR Reviewer — TTA.dev agentic example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/auto_pr_reviewer/main.py --pr https://github.com/owner/repo/pull/42
  python examples/auto_pr_reviewer/main.py --pr 42 --repo owner/repo
  python examples/auto_pr_reviewer/main.py --pr 42 --repo owner/repo --model ollama/qwen2.5:7b
        """.strip(),
    )
    parser.add_argument("--pr", required=True, help="PR URL, 'owner/repo#N', or plain PR number")
    parser.add_argument(
        "--repo",
        default=None,
        help="Repository in 'owner/repo' format (required when --pr is a plain number)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"litellm model string (default: {_DEFAULT_MODEL!r} or "
            f"{_FALLBACK_MODEL!r} when no cloud key is set)"
        ),
    )
    args = parser.parse_args()

    # Resolve model: explicit > cloud default > local fallback
    if args.model:
        model = args.model
    elif any(
        os.environ.get(k)
        for k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY")
    ):
        model = _DEFAULT_MODEL
    else:
        model = _FALLBACK_MODEL
        print(
            f"⚠️  No cloud API key found — falling back to local Ollama model: {model!r}\n"
            "   Set GROQ_API_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY) for cloud providers.",
            file=sys.stderr,
        )

    print(f"🔍 Reviewing PR: {args.pr}  |  Model: {model}", file=sys.stderr)

    ctx = WorkflowContext.root("auto-pr-review")
    if args.repo:
        ctx.metadata["repo"] = args.repo

    workflow = build_reviewer(model=model)
    review = await workflow.execute(args.pr, ctx)
    print(review)


if __name__ == "__main__":
    asyncio.run(main())
