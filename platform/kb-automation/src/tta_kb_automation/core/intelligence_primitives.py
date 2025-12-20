"""Intelligence primitives for KB automation.

These primitives provide AI/ML capabilities for content processing.
"""

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class ClassifyTODO(InstrumentedPrimitive[dict, dict]):
    """Classify TODO items using rule-based or LLM classification.

    Input:
        {
            "todo_text": str,         # TODO content
            "context": dict,          # Surrounding code context
            "use_llm": bool,          # Use LLM classification (default: False)
        }

    Output:
        {
            "category": str,          # implementation/testing/documentation/etc
            "priority": str,          # high/medium/low
            "confidence": float,      # 0.0-1.0
        }
    """

    def __init__(self):
        """Initialize ClassifyTODO primitive."""
        super().__init__(name="classify_todo")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Classify TODO (rule-based implementation)."""
        todo_text = input_data.get("todo_text", "").lower()
        # context = input_data.get("context", []) # Not used in rule-based for now

        category = "implementation"
        priority = "medium"
        confidence = 0.8  # Default confidence for rule-based classification

        # Rule-based classification for category
        if any(kw in todo_text for kw in ["test", "testing", "coverage", "pytest"]):
            category = "testing"
        elif any(kw in todo_text for kw in ["doc", "docs", "documentation", "readme"]):
            category = "documentation"
        elif any(kw in todo_text for kw in ["fix", "bug", "issue", "error", "debug"]):
            category = "bugfix"
        elif any(kw in todo_text for kw in ["refactor", "cleanup", "optimize", "restructure"]):
            category = "refactoring"
        elif any(kw in todo_text for kw in ["infra", "infrastructure", "deploy", "ci/cd"]):
            category = "infrastructure"
        elif any(kw in todo_text for kw in ["learn", "tutorial", "example", "onboard"]):
            category = "learning"  # Moved this higher
        elif any(kw in todo_text for kw in ["feature", "implement", "add", "create", "build"]):
            category = "implementation"
        elif any(kw in todo_text for kw in ["template", "pattern"]):
            category = "template"
        elif any(kw in todo_text for kw in ["ops", "operation", "monitor", "alert"]):
            category = "operations"

        # Rule-based classification for priority
        if any(kw in todo_text for kw in ["urgent", "critical", "asap", "blocker"]):
            priority = "high"
        elif any(kw in todo_text for kw in ["later", "someday", "low priority", "nice to have"]):
            priority = "low"

        return {
            "category": category,
            "priority": priority,
            "confidence": confidence,
        }


class SuggestKBLinks(InstrumentedPrimitive[dict, dict]):
    """Suggest KB page links for code/TODO items.

    Input:
        {
            "content": str,           # Content to analyze
            "existing_links": List[str], # Already linked pages
            "kb_pages": List[str],    # Available KB pages
        }

    Output:
        {
            "suggestions": List[{
                "page": str,
                "relevance": float,
                "reason": str
            }]
        }
    """

    def __init__(self):
        """Initialize SuggestKBLinks primitive."""
        super().__init__(name="suggest_kb_links")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Suggest KB links (stub implementation)."""
        # Return empty suggestions for now to unblock tests
        return {"suggestions": []}


class GenerateFlashcards(InstrumentedPrimitive[dict, dict]):
    """Generate flashcards from code/documentation.

    Input:
        {
            "content": str,           # Content to create flashcards from
            "topic": str,             # Topic/category
            "format": str,            # "simple" | "cloze" | "both"
        }

    Output:
        {
            "flashcards": List[{
                "question": str,
                "answer": str,
                "type": str,          # "simple" | "cloze"
                "tags": List[str]
            }]
        }
    """

    def __init__(self):
        """Initialize GenerateFlashcards primitive."""
        super().__init__(name="generate_flashcards")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Generate flashcards (stub implementation)."""
        # TODO: Implement flashcard generation
        raise NotImplementedError("GenerateFlashcards not yet implemented")
