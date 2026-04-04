#!/usr/bin/env python3
"""OpenHands automated PR code review script for TTA.dev local CI.

Selects the best available free model (Ollama-first, cloud fallback),
runs an OpenHands review against the PR diff, and posts results as a
GitHub PR comment. Always exits 0 — review failures must not block CI.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent
SKILL_PATH = REPO_ROOT / ".agents" / "skills" / "code-review.md"

# Ordered list of Ollama model tags to try (best quality first).
#
# qwen3/qwen3.5 are thinking models. The OpenAI-compatible endpoint
# (/v1/chat/completions) uses ``reasoning_effort`` (not ``think``) to control
# thinking. We pass ``reasoning_effort: "none"`` via ``extra_body`` so that
# thinking is disabled and ``message.content`` is populated with the actual
# answer. Without this, the model auto-enables thinking, all tokens go to the
# reasoning trace, and content is empty (silent failure).
_OLLAMA_CANDIDATES = [
    "qwen3.5:2b",  # 2.7 GB — best quality on this GPU
    "qwen3:1.7b",  # 1.4 GB — fallback
    "qwen3.5:0.8b",  # 1.0 GB — last local resort
]

# Max diff chars to send — small local models can't handle huge diffs
_MAX_DIFF_CHARS = 24_000


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------


def _ollama_available_tags() -> set[str]:
    """Return the set of model tags currently present in Ollama."""
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        tags: set[str] = set()
        for line in result.stdout.splitlines()[1:]:  # skip header
            parts = line.split()
            if parts:
                tags.add(parts[0])
        logger.debug("ollama tags available", extra={"tags": tags, "url": ollama_url})
        return tags
    except Exception:
        return set()


def _select_model() -> tuple[str, str | None, str | None, dict]:
    """Return (model_id, base_url, api_key, extra_body) for the best available model.

    Priority:
      1. Local Ollama qwen3.5:2b (GPU, thinking-capable, no quota)
      2. Local Ollama qwen3:1.7b
      3. Local Ollama qwen3.5:0.8b
      4. OpenRouter free model (cloud)
      5. Google Gemini free model (cloud)

    For Ollama thinking models (qwen3/qwen3.5), we pass
    ``extra_body={"reasoning_effort": "none"}`` through LiteLLM to the
    OpenAI-compatible endpoint so that thinking is disabled and
    ``message.content`` is populated with the actual answer.

    See https://docs.ollama.com/capabilities/thinking — the OpenAI-compat
    endpoint uses ``reasoning_effort`` (not ``think``) to control reasoning.
    """
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    available = _ollama_available_tags()

    for candidate in _OLLAMA_CANDIDATES:
        if candidate in available:
            logger.info("selected local ollama model", extra={"model": candidate})
            # Disable thinking so content is populated; qwen3/qwen3.5 default
            # to auto-thinking which leaves content empty on the OpenAI endpoint.
            extra_body = {"reasoning_effort": "none"}
            return f"ollama/{candidate}", ollama_base, "ollama", extra_body

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        model = "openrouter/qwen/qwen3.6-plus:free"
        logger.info("selected openrouter model", extra={"model": model})
        return model, None, openrouter_key, {}

    google_key = os.environ.get("GOOGLE_API_KEY")
    if google_key:
        model = "gemini/gemini-flash-lite-latest"
        logger.info("selected google model", extra={"model": model})
        return model, None, google_key, {}

    # Last resort — anonymous OpenRouter (heavily rate-limited but won't crash)
    fallback = "openrouter/qwen/qwen3.6-plus:free"
    logger.warning(
        "no preferred model available, using anonymous fallback", extra={"model": fallback}
    )
    return fallback, None, None, {}


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------


def _get_pr_diff(pr_number: str, base_ref: str, head_sha: str) -> str:
    """Get the unified diff for this PR, truncated to _MAX_DIFF_CHARS."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", pr_number],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
        )
        diff = result.stdout
    except Exception:
        # Fallback: git diff
        try:
            result = subprocess.run(
                ["git", "diff", f"origin/{base_ref}...{head_sha}"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(REPO_ROOT),
            )
            diff = result.stdout
        except Exception as exc:
            logger.warning("could not retrieve diff", extra={"error": str(exc)})
            diff = f"(diff unavailable: {exc})"

    if len(diff) > _MAX_DIFF_CHARS:
        diff = diff[:_MAX_DIFF_CHARS] + "\n\n... [diff truncated — too large for local model]"

    return diff


# ---------------------------------------------------------------------------
# OpenHands invocation
# ---------------------------------------------------------------------------


async def _run_review(
    pr_number: str,
    diff: str,
    model_id: str,
    base_url: str | None,
    api_key: str | None,
    extra_body: dict,
) -> str:
    """Run OpenHands review and return the review text."""
    skill_content = ""
    if SKILL_PATH.exists():
        skill_content = SKILL_PATH.read_text()

    task = f"""You are performing a code review for TTA.dev pull request #{pr_number}.

## Review Guidelines
{skill_content}

## Diff to Review
```diff
{diff}
```

Review the diff against the guidelines above. Be concise.
For each issue found, state:
- File and line (if identifiable)
- Severity (🔴 Critical / 🟡 Suggestion)
- What's wrong
- A corrected snippet

If no issues are found, say "✅ No issues found." and APPROVE.
"""

    try:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.primitives.integrations.openhands_primitive import OpenHandsPrimitive

        primitive = OpenHandsPrimitive(
            model=model_id,
            base_url=base_url,
            api_key=api_key,
            raise_on_stuck=False,
            extra_body=extra_body if extra_body else None,
        )
        context = WorkflowContext(workflow_id=f"pr-review-{pr_number}")

        result = await asyncio.wait_for(
            primitive.execute(task, context),
            timeout=14 * 60,  # 14 min — inside the 20-min job timeout
        )

        if isinstance(result, dict):
            return str(result.get("output", result))
        return str(result)

    except ImportError:
        logger.warning("openhands_primitive not available, using litellm direct")
        return await _run_review_litellm_direct(task, model_id, base_url, api_key, extra_body)
    except TimeoutError:
        return "⚠️ Review timed out (14 min). No feedback posted."
    except Exception as exc:
        logger.exception("openhands review failed")
        return f"⚠️ Review failed: {exc}"


async def _run_review_litellm_direct(
    task: str,
    model_id: str,
    base_url: str | None,
    api_key: str | None,
    extra_body: dict,
) -> str:
    """Fallback: call the model directly via LiteLLM with extra_body support.

    Passes ``extra_body`` (e.g. ``{"reasoning_effort": "none"}``) so that
    Ollama thinking models return populated ``content`` rather than an empty
    field with all tokens consumed by the reasoning trace.
    """
    try:
        import litellm

        kwargs: dict = {
            "model": model_id,
            "messages": [{"role": "user", "content": task}],
            "max_tokens": 2048,
        }
        if base_url:
            kwargs["api_base"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        if extra_body:
            kwargs["extra_body"] = extra_body

        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content or ""
        return content or "⚠️ Model returned empty content."
    except Exception as exc:
        return f"⚠️ LiteLLM fallback failed: {exc}"


# ---------------------------------------------------------------------------
# GitHub comment posting
# ---------------------------------------------------------------------------


def _post_review_comment(pr_number: str, body: str) -> bool:
    """Post review text as a PR comment via gh CLI. Returns True on success."""
    header = (
        "## 🤖 OpenHands Automated Code Review\n\n"
        "_This review was generated by the local CI pipeline using a free model._\n\n"
        "---\n\n"
    )
    full_body = header + body

    try:
        result = subprocess.run(
            ["gh", "pr", "comment", pr_number, "--body", full_body],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
        )
        if result.returncode == 0:
            logger.info("review comment posted", extra={"pr": pr_number})
            return True
        logger.warning("gh comment failed", extra={"stderr": result.stderr})
        return False
    except Exception as exc:
        logger.warning("could not post comment", extra={"error": str(exc)})
        return False


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenHands PR review for TTA.dev CI")
    parser.add_argument("--pr", required=True, help="PR number")
    parser.add_argument("--base", required=True, help="Base branch ref")
    parser.add_argument("--head", required=True, help="Head commit SHA")
    return parser.parse_args()


async def main() -> None:
    """Run the PR review pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    args = _parse_args()

    try:
        model_id, base_url, api_key, extra_body = _select_model()
        logger.info(
            "starting pr review",
            extra={"pr": args.pr, "model": model_id},
        )

        diff = _get_pr_diff(args.pr, args.base, args.head)
        if not diff.strip():
            logger.info("empty diff — skipping review")
            return

        review_text = await _run_review(
            pr_number=args.pr,
            diff=diff,
            model_id=model_id,
            base_url=base_url,
            api_key=api_key,
            extra_body=extra_body,
        )

        posted = _post_review_comment(args.pr, review_text)
        if not posted:
            # Print to stdout so it at least appears in CI logs
            print("\n=== OpenHands Review (not posted to GitHub) ===")
            print(review_text)
            print("================================================\n")

    except Exception:
        logger.exception("pr review pipeline failed — exiting 0 to avoid blocking CI")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logger.exception("unhandled error in review script")
    sys.exit(0)  # Always exit 0 — never block CI
