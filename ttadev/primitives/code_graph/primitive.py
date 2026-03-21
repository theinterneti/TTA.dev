"""CodeGraphPrimitive — typed, instrumented Orient step for the DevelopmentCycle loop.

Queries CGC's FalkorDB graph to understand what a target function/class touches
and what touches it. Degrades gracefully when FalkorDB is unreachable.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from typing import Any

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability import InstrumentedPrimitive

from .client import FalkorDBClient
from .types import CGCOp, CodeGraphQuery, ImpactReport

logger = logging.getLogger(__name__)

_MAX_DEPTH = 5


# ── Helpers ───────────────────────────────────────────────────────────────────


def _derive_risk(complexity: float, callers: list[str]) -> str:
    if complexity >= 10:
        return "high"
    if complexity >= 5 or len(callers) >= 5:
        return "medium"
    return "low"


def _format_location(name: str, path: str | None, line: int | None) -> str:
    if path and line:
        return f"{name} ({path}:{line})"
    if path:
        return f"{name} ({path})"
    return name


def _is_test_path(path: str | None) -> bool:
    if not path:
        return False
    return "/test" in path or path.split("/")[-1].startswith("test_")


def _build_summary(
    target: str,
    callers: list[str],
    deps: list[str],
    tests: list[str],
    complexity: float,
    risk: str,
) -> str:
    parts = [f"`{target}`: risk={risk}, complexity={complexity:.1f}."]
    if callers:
        preview = ", ".join(callers[:3])
        suffix = "..." if len(callers) > 3 else ""
        parts.append(f"Called by {len(callers)} function(s): {preview}{suffix}.")
    if deps:
        parts.append(f"Calls {len(deps)} function(s).")
    if tests:
        names = ", ".join(t.split("/")[-1] for t in tests[:2])
        parts.append(f"Covered by {len(tests)} test file(s): {names}.")
    else:
        parts.append("No test coverage found.")
    return " ".join(parts)


def _empty_report(target: str, reason: str) -> ImpactReport:
    return ImpactReport(
        target=target,
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary=reason,
        cgc_available=False,
    )


# ── Primitive ─────────────────────────────────────────────────────────────────


class CodeGraphPrimitive(InstrumentedPrimitive[CodeGraphQuery, ImpactReport]):
    """Orient step: query CGC to understand what code exists and what will change.

    Queries FalkorDB directly via Unix socket using the ``falkordb`` Python package.
    Degrades gracefully if FalkorDB is unreachable — returns an empty ImpactReport,
    never raises.

    Example::

        graph = CodeGraphPrimitive()
        report = await graph.execute(
            CodeGraphQuery(
                target="RetryPrimitive._execute_impl",
                operations=[CGCOp.get_relationships, CGCOp.find_tests, CGCOp.get_complexity],
            ),
            WorkflowContext(),
        )
        # report["risk"] in ("low", "medium", "high")
        # report["related_tests"] — list of test file paths
    """

    def __init__(
        self,
        cgc_client: FalkorDBClient | None = None,
        repo_path: str | None = None,
    ) -> None:
        super().__init__(name="CodeGraphPrimitive")
        self._client = cgc_client or FalkorDBClient()
        self._repo_path = repo_path
        # Separate tracer for the cgc.orient span so tests can mock it
        # without corrupting the base-class primitive.CodeGraphPrimitive span.
        self._cgc_tracer = self._tracer

    async def _execute_impl(
        self, input_data: CodeGraphQuery, context: WorkflowContext
    ) -> ImpactReport:
        target: str = input_data.get("target", "")
        operations: list[CGCOp] = input_data.get("operations", [])
        requested_depth: int = input_data.get("depth", 2)
        cypher: str = input_data.get("cypher", "")
        repo_path: str | None = input_data.get("repo_path") or self._repo_path

        if requested_depth > _MAX_DEPTH:
            logger.warning("depth clamped to %d (requested %d)", _MAX_DEPTH, requested_depth)

        # ── Span wraps ALL execution paths (including unavailable / validation) ─
        span_cm: Any = (
            self._cgc_tracer.start_as_current_span("cgc.orient")
            if self._cgc_tracer
            else nullcontext()
        )
        with span_cm as span:
            try:
                # ── Validation ────────────────────────────────────────────────
                if not operations:
                    if span is not None:
                        span.set_attribute("target", target)
                        span.set_attribute("operations", [])
                        span.set_attribute("risk", "low")
                        span.set_attribute("cgc_available", False)
                    return _empty_report(target, f"No operations requested for `{target}`")
                if not target and CGCOp.raw_cypher not in operations:
                    raise ValueError("target is required for non-cypher operations")
                if CGCOp.raw_cypher in operations and not cypher:
                    raise ValueError("cypher query string is required for CGCOp.raw_cypher")

                # ── Availability check ─────────────────────────────────────────
                if not self._client.is_reachable():
                    if span is not None:
                        span.set_attribute("target", target)
                        span.set_attribute("operations", [op.value for op in operations])
                        span.set_attribute("risk", "low")
                        span.set_attribute("cgc_available", False)
                    return _empty_report(target, "CGC unavailable — orient step skipped")

                # ── Execute operations ─────────────────────────────────────────
                callers: list[str] = []
                deps: list[str] = []
                tests: list[str] = []
                complexity: float = 0.0
                raw_result: str = ""

                for op in operations:
                    if op == CGCOp.find_code:
                        await self._client.find_code(target, repo_path)

                    elif op == CGCOp.get_relationships:
                        caller_rows = await self._client.get_callers(target, repo_path)
                        callers = [
                            _format_location(r["name"], r.get("path"), r.get("line_number"))
                            for r in caller_rows
                        ]
                        dep_rows = await self._client.get_callees(target, repo_path)
                        deps = [
                            _format_location(r["name"], r.get("path"), r.get("line_number"))
                            for r in dep_rows
                        ]

                    elif op == CGCOp.get_complexity:
                        complexity = await self._client.get_complexity(target, repo_path)

                    elif op == CGCOp.find_tests:
                        code_results = await self._client.find_code(target, None)
                        seen: set[str] = set()
                        for r in code_results:
                            p = r.get("path", "")
                            if _is_test_path(p) and p not in seen:
                                tests.append(p)
                                seen.add(p)

                    elif op == CGCOp.raw_cypher:
                        rows = await self._client.execute_cypher(cypher)
                        raw_result = "\n".join(str(r["values"]) for r in rows[:50])

                risk = _derive_risk(complexity, callers)

                only_raw = operations == [CGCOp.raw_cypher]
                summary = (
                    (raw_result or "Cypher query returned no results.")
                    if only_raw
                    else _build_summary(target, callers, deps, tests, complexity, risk)
                )

                if span is not None:
                    span.set_attribute("target", target)
                    span.set_attribute("operations", [op.value for op in operations])
                    span.set_attribute("risk", risk)
                    span.set_attribute("cgc_available", True)

                return ImpactReport(
                    target=target,
                    callers=callers,
                    dependencies=deps,
                    related_tests=tests,
                    complexity=complexity,
                    risk=risk,
                    summary=summary,
                    cgc_available=True,
                )

            except (ValueError, TypeError):
                raise  # validation errors bubble up
            except Exception as exc:
                logger.warning("CGC query failed for target=%r: %s", target, exc)
                return _empty_report(target, f"CGC unavailable: {exc}")
