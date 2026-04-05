"""Smart Code Reviewer — entry point.

Run::

    python -m examples.showcase.main path/to/file.py
    python -m examples.showcase.main path/to/file.py --mock
    python -m examples.showcase.main path/to/file.py --json

Implements #323 (showcase scaffold) and #326 (multi-provider routing).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from examples.showcase.agents.qa_agent import QAAgent
from examples.showcase.agents.security_agent import SecurityAgent
from examples.showcase.router import build_router
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.parallel import ParallelPrimitive


async def review(file_path: Path, *, mock_mode: bool = False) -> dict[str, str]:
    """Run the Smart Code Reviewer on a Python file.

    Args:
        file_path: Path to the Python source file to review.
        mock_mode: When True, skip real LLM calls.

    Returns:
        A dict with keys ``security``, ``quality``, and ``llm`` review strings.
    """
    code = file_path.read_text(encoding="utf-8")
    ctx = WorkflowContext(workflow_id=f"showcase-{file_path.stem}")

    # Static agents run in parallel — no LLM call, always fast
    static_pipeline = ParallelPrimitive([SecurityAgent(), QAAgent()])
    static_results: list[str] = await static_pipeline.execute(code, ctx)

    # LLM-backed review: Groq -> Google Gemini -> Ollama -> MockLLM
    llm_router = build_router(
        mock_mode=mock_mode,
        prompt_prefix=(
            "You are a senior Python developer doing a code review. "
            "Identify bugs, design issues, and improvements. Be concise."
        ),
    )
    llm_review: str = await llm_router.execute(code, ctx)

    return {
        "security": static_results[0],
        "quality": static_results[1],
        "llm": llm_review,
    }


def _render_markdown(results: dict[str, str], file_path: Path) -> str:
    """Format review results as a markdown document.

    Args:
        results: Dict with security, quality, and llm keys.
        file_path: The reviewed file path (used in the heading).

    Returns:
        A markdown string.
    """
    return (
        f"# Code Review: `{file_path.name}`\n\n"
        f"{results['security']}\n\n"
        f"{results['quality']}\n\n"
        f"## LLM Review\n\n{results['llm']}\n"
    )


async def _main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list (uses sys.argv when None).

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Smart Code Reviewer — TTA.dev showcase",
    )
    parser.add_argument("file", type=Path, help="Python file to review")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic MockLLM (no API key needed)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"error: {args.file} does not exist", file=sys.stderr)
        return 1

    results = await review(args.file, mock_mode=args.mock)

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        print(_render_markdown(results, args.file))

    return 0


def main() -> None:
    """Synchronous entry point for console_scripts."""
    sys.exit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
