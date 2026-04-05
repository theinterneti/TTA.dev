"""SecurityAgent stub — reviews Python code for common vulnerabilities.

Checks for:
- Hardcoded secrets / API keys
- Unsafe use of eval / exec
- SQL string concatenation (injection risk)
- subprocess calls without shell=False
"""

from __future__ import annotations

import re

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(api_key|secret|password|token)\s*=\s*['\"][^'\"]{4,}['\"]"),
    re.compile(r"(?i)aws_access_key_id\s*="),
]

_UNSAFE_CALLS: list[re.Pattern[str]] = [
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"subprocess\.call\([^)]*shell\s*=\s*True"),
]

_SQL_CONCAT: re.Pattern[str] = re.compile(
    r'(SELECT|INSERT|UPDATE|DELETE).+["\'].*\+', re.IGNORECASE
)


class SecurityAgent(WorkflowPrimitive[str, str]):
    """Scan Python source code for common security anti-patterns."""

    def __init__(self) -> None:
        """Initialise the security agent."""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        """Run static security checks on Python source.

        Args:
            input_data: Raw Python source code.
            context: Workflow context.

        Returns:
            A markdown security report.
        """
        findings: list[str] = []

        for i, line in enumerate(input_data.splitlines(), start=1):
            for pat in _SECRET_PATTERNS:
                if pat.search(line):
                    findings.append(f"- Line {i}: Possible hardcoded secret — `{line.strip()}`")

            for pat in _UNSAFE_CALLS:
                if pat.search(line):
                    findings.append(f"- Line {i}: Unsafe call — `{line.strip()}`")

            if _SQL_CONCAT.search(line):
                findings.append(f"- Line {i}: Possible SQL injection — `{line.strip()}`")

        if not findings:
            return "## Security Review\n\n✅ No issues detected."

        return "## Security Review\n\n" + "\n".join(findings)


__all__ = ["SecurityAgent"]
