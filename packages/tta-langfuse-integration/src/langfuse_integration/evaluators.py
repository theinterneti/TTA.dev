"""
Langfuse Custom Evaluators

This module provides custom evaluators for assessing LLM outputs across different domains:
- Code quality evaluation
- Documentation clarity
- Test coverage assessment
- General response quality

Evaluators can be used with Langfuse's scoring system to track quality metrics over time.
"""

from typing import Any

from langfuse import Langfuse

from .initialization import get_langfuse_client, is_langfuse_enabled


class BaseEvaluator:
    """Base class for custom evaluators."""

    def __init__(self, name: str, description: str, client: Langfuse | None = None):
        """
        Initialize evaluator.

        Args:
            name: Unique name for the evaluator
            description: Description of what this evaluator assesses
            client: Langfuse client instance
        """
        self.name = name
        self.description = description
        self.client = client or get_langfuse_client()

    def evaluate(self, output: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate an LLM output.

        Args:
            output: The LLM output to evaluate
            input_data: Optional input context

        Returns:
            Dict with score (0.0-1.0), reasoning, and details

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement evaluate()")

    def create_score(
        self,
        trace_id: str,
        observation_id: str | None = None,
        score: float = 0.0,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a score in Langfuse.

        Args:
            trace_id: Trace ID to score
            observation_id: Optional specific observation to score
            score: Score value (0.0-1.0)
            comment: Optional comment explaining the score
            metadata: Optional metadata

        Returns:
            Dict with score details
        """
        if not is_langfuse_enabled():
            return {
                "name": self.name,
                "value": score,
                "comment": comment,
                "disabled": True,
            }

        try:
            created = self.client.score(
                trace_id=trace_id,
                observation_id=observation_id,
                name=self.name,
                value=score,
                comment=comment,
                metadata=metadata or {},
            )

            return {
                "id": created.id if hasattr(created, "id") else None,
                "name": self.name,
                "value": score,
                "comment": comment,
                "trace_id": trace_id,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to create score: {e}") from e


class CodeQualityEvaluator(BaseEvaluator):
    """Evaluator for code quality."""

    def __init__(self, client: Langfuse | None = None):
        super().__init__(
            name="code-quality",
            description="Evaluates code for quality, style, and best practices",
            client=client,
        )

    def evaluate(self, output: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate code quality.

        Checks for:
        - Type hints
        - Docstrings
        - Error handling
        - Code structure
        - Best practices

        Args:
            output: Generated code
            input_data: Optional context (language, requirements, etc.)

        Returns:
            Dict with score (0.0-1.0) and detailed feedback
        """
        score = 1.0
        issues = []
        positive_aspects = []

        # Check for type hints
        if ":" in output and "->" in output:
            positive_aspects.append("Uses type hints")
        else:
            score -= 0.2
            issues.append("Missing type hints")

        # Check for docstrings
        if '"""' in output or "'''" in output:
            positive_aspects.append("Has docstrings")
        else:
            score -= 0.15
            issues.append("Missing docstrings")

        # Check for error handling
        if "try:" in output or "except" in output:
            positive_aspects.append("Includes error handling")
        elif "raise" in output:
            positive_aspects.append("Has error raising")
        else:
            score -= 0.2
            issues.append("No error handling")

        # Check for classes/functions
        if "class " in output or "def " in output or "async def " in output:
            positive_aspects.append("Well-structured code")
        else:
            score -= 0.1
            issues.append("Lacks clear structure")

        # Check for modern Python (3.10+) patterns
        if "match " in output or " | " in output:
            positive_aspects.append("Uses modern Python features")
            score += 0.05

        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))

        reasoning = []
        if positive_aspects:
            reasoning.append("Strengths: " + ", ".join(positive_aspects))
        if issues:
            reasoning.append("Issues: " + ", ".join(issues))

        return {
            "score": score,
            "reasoning": " | ".join(reasoning) if reasoning else "Basic code",
            "issues": issues,
            "strengths": positive_aspects,
        }


class DocumentationEvaluator(BaseEvaluator):
    """Evaluator for documentation quality."""

    def __init__(self, client: Langfuse | None = None):
        super().__init__(
            name="documentation-quality",
            description="Evaluates documentation for clarity, completeness, and examples",
            client=client,
        )

    def evaluate(self, output: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate documentation quality.

        Checks for:
        - Clear structure
        - Code examples
        - Proper formatting
        - Completeness

        Args:
            output: Generated documentation
            input_data: Optional context

        Returns:
            Dict with score and feedback
        """
        score = 1.0
        issues = []
        positive_aspects = []

        # Check for headers
        if "#" in output:
            positive_aspects.append("Has structured sections")
        else:
            score -= 0.15
            issues.append("Missing section headers")

        # Check for code examples
        if "```" in output:
            positive_aspects.append("Includes code examples")
        else:
            score -= 0.25
            issues.append("No code examples")

        # Check for lists/bullets
        if "-" in output or "*" in output or "1." in output:
            positive_aspects.append("Uses lists for clarity")
        else:
            score -= 0.1
            issues.append("Could use more lists")

        # Check for emphasis
        if "**" in output or "__" in output:
            positive_aspects.append("Uses formatting for emphasis")

        # Check for parameters/returns documentation
        if ("Args:" in output or "Parameters:" in output) and ("Returns:" in output):
            positive_aspects.append("Documents parameters and returns")
        elif "Args:" in output or "Parameters:" in output or "Returns:" in output:
            score -= 0.1
            issues.append("Incomplete API documentation")
        else:
            score -= 0.15
            issues.append("Missing API documentation")

        # Check for examples section
        if "Example:" in output or "Examples:" in output or "Usage:" in output:
            positive_aspects.append("Has usage examples")
        else:
            score -= 0.1
            issues.append("Missing usage examples")

        score = max(0.0, min(1.0, score))

        reasoning = []
        if positive_aspects:
            reasoning.append("Strengths: " + ", ".join(positive_aspects))
        if issues:
            reasoning.append("Improvements: " + ", ".join(issues))

        return {
            "score": score,
            "reasoning": " | ".join(reasoning) if reasoning else "Basic documentation",
            "issues": issues,
            "strengths": positive_aspects,
        }


class TestCoverageEvaluator(BaseEvaluator):
    """Evaluator for test quality and coverage."""

    def __init__(self, client: Langfuse | None = None):
        super().__init__(
            name="test-coverage",
            description="Evaluates test completeness and quality",
            client=client,
        )

    def evaluate(self, output: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate test coverage and quality.

        Checks for:
        - Multiple test cases
        - Async test support
        - Mocking
        - Edge cases
        - Test structure

        Args:
            output: Generated test code
            input_data: Optional context

        Returns:
            Dict with score and feedback
        """
        score = 1.0
        issues = []
        positive_aspects = []

        # Count test functions
        import re

        test_count = len(re.findall(r"def test_\w+|async def test_\w+", output))

        if test_count >= 5:
            positive_aspects.append(f"Comprehensive coverage ({test_count} tests)")
        elif test_count >= 3:
            positive_aspects.append(f"Good coverage ({test_count} tests)")
        elif test_count >= 1:
            score -= 0.15
            issues.append(f"Limited coverage ({test_count} tests)")
        else:
            score -= 0.3
            issues.append("No tests found")

        # Check for async tests
        if "@pytest.mark.asyncio" in output or "async def test_" in output:
            positive_aspects.append("Supports async testing")

        # Check for mocking
        if "Mock" in output or "patch" in output or "AsyncMock" in output:
            positive_aspects.append("Uses mocks for isolation")
        else:
            score -= 0.15
            issues.append("No mocking (may have dependencies)")

        # Check for fixtures
        if "@pytest.fixture" in output:
            positive_aspects.append("Uses fixtures for reusability")

        # Check for assertions
        assert_count = output.count("assert ")
        if assert_count >= test_count * 2:
            positive_aspects.append("Multiple assertions per test")
        elif assert_count < test_count:
            score -= 0.15
            issues.append("Insufficient assertions")

        # Check for edge cases
        edge_case_keywords = ["empty", "none", "null", "invalid", "error", "exception"]
        if any(keyword in output.lower() for keyword in edge_case_keywords):
            positive_aspects.append("Tests edge cases")
        else:
            score -= 0.1
            issues.append("Missing edge case tests")

        # Check for AAA pattern (Arrange, Act, Assert)
        if "# Arrange" in output or "# Act" in output or "# Assert" in output:
            positive_aspects.append("Follows AAA pattern")

        score = max(0.0, min(1.0, score))

        reasoning = []
        if positive_aspects:
            reasoning.append("Strengths: " + ", ".join(positive_aspects))
        if issues:
            reasoning.append("Improvements: " + ", ".join(issues))

        return {
            "score": score,
            "reasoning": " | ".join(reasoning) if reasoning else "Basic tests",
            "issues": issues,
            "strengths": positive_aspects,
            "test_count": test_count,
            "assertion_count": assert_count,
        }


class ResponseQualityEvaluator(BaseEvaluator):
    """General-purpose response quality evaluator."""

    def __init__(self, client: Langfuse | None = None):
        super().__init__(
            name="response-quality",
            description="Evaluates general LLM response quality",
            client=client,
        )

    def evaluate(self, output: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate general response quality.

        Checks for:
        - Length and completeness
        - Structure
        - Relevance
        - Clarity

        Args:
            output: LLM response
            input_data: Optional input context with 'prompt' or 'question'

        Returns:
            Dict with score and feedback
        """
        score = 1.0
        issues = []
        positive_aspects = []

        # Check length
        word_count = len(output.split())

        if word_count < 10:
            score -= 0.3
            issues.append(f"Too short ({word_count} words)")
        elif word_count < 30:
            score -= 0.1
            issues.append(f"Brief response ({word_count} words)")
        elif word_count > 500:
            score -= 0.05
            issues.append(f"Very long ({word_count} words)")
        else:
            positive_aspects.append(f"Good length ({word_count} words)")

        # Check for structure
        if "\n\n" in output:
            positive_aspects.append("Well-paragraphed")

        # Check for lists or examples
        if "-" in output or "*" in output or "```" in output:
            positive_aspects.append("Includes examples or lists")

        # Check for keywords from input (relevance)
        if input_data and ("prompt" in input_data or "question" in input_data):
            query = input_data.get("prompt") or input_data.get("question", "")
            query_words = set(query.lower().split())
            output_words = set(output.lower().split())

            # Check for keyword overlap
            overlap = query_words & output_words
            relevance_ratio = len(overlap) / len(query_words) if query_words else 0

            if relevance_ratio > 0.3:
                positive_aspects.append("Highly relevant to query")
            elif relevance_ratio > 0.1:
                positive_aspects.append("Relevant to query")
            else:
                score -= 0.2
                issues.append("Low relevance to query")

        # Check for hedge words (uncertainty)
        hedge_words = ["maybe", "perhaps", "possibly", "might", "could be"]
        hedge_count = sum(1 for word in hedge_words if word in output.lower())
        if hedge_count > 3:
            score -= 0.1
            issues.append("High uncertainty (many hedge words)")

        score = max(0.0, min(1.0, score))

        reasoning = []
        if positive_aspects:
            reasoning.append(" | ".join(positive_aspects))
        if issues:
            reasoning.append("Issues: " + ", ".join(issues))

        return {
            "score": score,
            "reasoning": " | ".join(reasoning) if reasoning else "Adequate response",
            "issues": issues,
            "strengths": positive_aspects,
            "word_count": word_count,
        }


def get_evaluator(evaluator_type: str, client: Langfuse | None = None) -> BaseEvaluator:
    """
    Get an evaluator by type.

    Args:
        evaluator_type: Type of evaluator ('code', 'docs', 'tests', 'response')
        client: Optional Langfuse client

    Returns:
        Evaluator instance

    Raises:
        ValueError: If evaluator type is unknown

    Example:
        >>> evaluator = get_evaluator('code')
        >>> result = evaluator.evaluate('def foo(): pass')
        >>> print(result['score'])  # 0.55 (missing docstrings, type hints, etc.)
    """
    evaluators = {
        "code": CodeQualityEvaluator,
        "docs": DocumentationEvaluator,
        "documentation": DocumentationEvaluator,
        "tests": TestCoverageEvaluator,
        "test": TestCoverageEvaluator,
        "response": ResponseQualityEvaluator,
        "quality": ResponseQualityEvaluator,
    }

    evaluator_class = evaluators.get(evaluator_type.lower())
    if not evaluator_class:
        raise ValueError(
            f"Unknown evaluator type: {evaluator_type}. "
            f"Available: {', '.join(evaluators.keys())}"
        )

    return evaluator_class(client=client)
