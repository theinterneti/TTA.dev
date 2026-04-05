"""QAAgent stub — checks Python code for style and quality issues.

Checks for:
- Functions missing docstrings
- Missing type hints on function arguments and return values
- Lines exceeding 88 characters (Ruff default)
"""

from __future__ import annotations

import ast

from opentelemetry import trace

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

tracer = trace.get_tracer(__name__)


class QAAgent(WorkflowPrimitive[str, str]):
    """Analyse Python source for style and quality issues."""

    def __init__(self) -> None:
        """Initialise the QA agent."""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        """Run static quality checks on Python source.

        Args:
            input_data: Raw Python source code.
            context: Workflow context.

        Returns:
            A markdown quality report.
        """
        with tracer.start_as_current_span("showcase.qa_agent.execute") as span:
            span.set_attribute("code.length", len(input_data))
            span.set_attribute("agent.name", "QAAgent")
            span.set_attribute("workflow.id", context.workflow_id or "")

            findings: list[str] = []

            # Long lines
            for i, line in enumerate(input_data.splitlines(), start=1):
                if len(line) > 88:
                    findings.append(f"- Line {i}: Line too long ({len(line)} chars)")

            # AST-based checks
            try:
                tree = ast.parse(input_data)
            except SyntaxError as exc:
                span.set_attribute("findings.count", 1)
                return f"## Quality Review\n\n❌ Syntax error: {exc}"

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                lineno = node.lineno

                # Missing docstring
                if not (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    findings.append(f"- Line {lineno}: `{node.name}` is missing a docstring")

                # Missing return annotation
                if node.returns is None and node.name != "__init__":
                    findings.append(
                        f"- Line {lineno}: `{node.name}` is missing a return type annotation"
                    )

                # Missing argument annotations (skip self/cls)
                unannotated = [
                    a.arg
                    for a in node.args.args
                    if a.annotation is None and a.arg not in ("self", "cls")
                ]
                if unannotated:
                    findings.append(
                        f"- Line {lineno}: `{node.name}` has unannotated args: "
                        + ", ".join(f"`{a}`" for a in unannotated)
                    )

            span.set_attribute("findings.count", len(findings))

            if not findings:
                return "## Quality Review\n\n✅ No issues detected."

            return "## Quality Review\n\n" + "\n".join(findings)


__all__ = ["QAAgent"]
