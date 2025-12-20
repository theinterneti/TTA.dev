"""Task classification primitive for intelligent model routing.

Classifies tasks by complexity, requirements, and characteristics to determine
the most appropriate model for execution.

# See: [[TTA.dev/Primitives/TaskClassifierPrimitive]]
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class TaskComplexity(str, Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # Simple queries, factual questions
    MODERATE = "moderate"  # Analysis, summarization, basic reasoning
    COMPLEX = "complex"  # Multi-step reasoning, planning, creative tasks
    EXPERT = "expert"  # Advanced reasoning, code generation, research


class TaskCharacteristics(BaseModel):
    """Characteristics of a task that influence model selection."""

    requires_reasoning: bool = Field(
        default=False, description="Task requires multi-step reasoning"
    )
    requires_creativity: bool = Field(default=False, description="Task requires creative output")
    requires_code: bool = Field(default=False, description="Task involves code generation")
    requires_speed: bool = Field(default=False, description="Task requires ultra-fast response")
    requires_long_context: bool = Field(
        default=False, description="Task requires >100K context window"
    )
    requires_accuracy: bool = Field(default=True, description="Task requires high accuracy")


class TaskClassification(BaseModel):
    """Result of task classification."""

    complexity: TaskComplexity = Field(description="Task complexity level")
    characteristics: TaskCharacteristics = Field(description="Task characteristics")
    recommended_model: str = Field(description="Recommended model for this task")
    reasoning: str = Field(description="Explanation for model recommendation")
    estimated_cost: float = Field(description="Estimated cost in USD (0.0 for free models)")
    fallback_models: list[str] = Field(
        default_factory=list, description="Alternative models if primary fails"
    )


class TaskClassifierRequest(BaseModel):
    """Request for task classification."""

    task_description: str = Field(description="Description of the task to classify")
    user_preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences (e.g., prefer_free=True)"
    )


class TaskClassifierPrimitive(WorkflowPrimitive[TaskClassifierRequest, TaskClassification]):
    """Classifies tasks to determine the best model for execution.

    This primitive analyzes task characteristics and recommends the most appropriate
    model based on complexity, requirements, and cost optimization goals.

    **Classification Logic:**
    - Simple tasks → Groq (ultra-fast, free)
    - Moderate tasks → Gemini Pro (flagship quality, free)
    - Complex reasoning → DeepSeek R1 (on par with o1, free)
    - Expert tasks → Claude Sonnet 4.5 (paid, highest quality)

    Example:
        ```python
        from tta_dev_primitives.orchestration import TaskClassifierPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create classifier
        classifier = TaskClassifierPrimitive()

        # Classify task
        context = WorkflowContext(workflow_id="classify-demo")
        request = TaskClassifierRequest(
            task_description="Summarize this article in 3 bullet points",
            user_preferences={"prefer_free": True}
        )
        classification = await classifier.execute(request, context)

        print(f"Recommended: {classification.recommended_model}")
        print(f"Reasoning: {classification.reasoning}")
        print(f"Cost: ${classification.estimated_cost}")
        ```

    Attributes:
        prefer_free: If True, prefer free models when quality is sufficient
    """

    def __init__(self, prefer_free: bool = True) -> None:
        """Initialize task classifier.

        Args:
            prefer_free: If True, prefer free models when quality is sufficient
        """
        super().__init__()
        self.prefer_free = prefer_free

    async def execute(
        self, input_data: TaskClassifierRequest, context: WorkflowContext
    ) -> TaskClassification:
        """Classify task and recommend model.

        Args:
            input_data: Task description and preferences
            context: Workflow context for observability

        Returns:
            Classification with recommended model and reasoning
        """
        # Extract task description
        task = input_data.task_description.lower()

        # Determine task characteristics
        characteristics = self._analyze_characteristics(task)

        # Determine complexity
        complexity = self._determine_complexity(task, characteristics)

        # Recommend model based on classification
        recommendation = self._recommend_model(
            complexity, characteristics, input_data.user_preferences
        )

        return recommendation

    def _analyze_characteristics(self, task: str) -> TaskCharacteristics:
        """Analyze task characteristics.

        Args:
            task: Task description (lowercase)

        Returns:
            Task characteristics
        """
        # Keywords for different characteristics
        reasoning_keywords = [
            "analyze",
            "compare",
            "evaluate",
            "reason",
            "explain why",
            "multi-step",
        ]
        creativity_keywords = ["create", "write", "generate", "design", "brainstorm"]
        code_keywords = ["code", "function", "class", "debug", "implement", "refactor"]
        speed_keywords = ["quick", "fast", "immediately", "urgent", "real-time"]
        long_context_keywords = ["document", "article", "book", "long", "entire"]

        return TaskCharacteristics(
            requires_reasoning=any(kw in task for kw in reasoning_keywords),
            requires_creativity=any(kw in task for kw in creativity_keywords),
            requires_code=any(kw in task for kw in code_keywords),
            requires_speed=any(kw in task for kw in speed_keywords),
            requires_long_context=any(kw in task for kw in long_context_keywords),
            requires_accuracy=True,  # Default to high accuracy
        )

    def _determine_complexity(
        self, task: str, characteristics: TaskCharacteristics
    ) -> TaskComplexity:
        """Determine task complexity.

        Args:
            task: Task description (lowercase)
            characteristics: Task characteristics

        Returns:
            Task complexity level
        """
        # Expert-level tasks
        if characteristics.requires_code and characteristics.requires_reasoning:
            return TaskComplexity.EXPERT
        if "research" in task or "comprehensive" in task:
            return TaskComplexity.EXPERT

        # Complex tasks
        if characteristics.requires_reasoning and characteristics.requires_creativity:
            return TaskComplexity.COMPLEX
        if "plan" in task or "strategy" in task:
            return TaskComplexity.COMPLEX

        # Moderate tasks
        if characteristics.requires_reasoning or characteristics.requires_creativity:
            return TaskComplexity.MODERATE
        if any(kw in task for kw in ["summarize", "translate", "rewrite"]):
            return TaskComplexity.MODERATE

        # Simple tasks
        return TaskComplexity.SIMPLE

    def _recommend_model(
        self,
        complexity: TaskComplexity,
        characteristics: TaskCharacteristics,
        preferences: dict[str, Any],
    ) -> TaskClassification:
        """Recommend model based on classification.

        Args:
            complexity: Task complexity level
            characteristics: Task characteristics
            preferences: User preferences

        Returns:
            Task classification with model recommendation
        """
        prefer_free = preferences.get("prefer_free", self.prefer_free)

        # Expert tasks → Claude Sonnet 4.5 (paid)
        if complexity == TaskComplexity.EXPERT and not prefer_free:
            return TaskClassification(
                complexity=complexity,
                characteristics=characteristics,
                recommended_model="claude-sonnet-4.5",
                reasoning="Expert-level task requiring highest quality reasoning and code generation",
                estimated_cost=0.015,  # ~$15 per 1M tokens
                fallback_models=["gemini-2.5-pro", "deepseek/deepseek-r1:free"],
            )

        # Complex reasoning → DeepSeek R1 (free, on par with o1)
        if complexity == TaskComplexity.COMPLEX or characteristics.requires_reasoning:
            return TaskClassification(
                complexity=complexity,
                characteristics=characteristics,
                recommended_model="deepseek/deepseek-r1:free",
                reasoning="Complex reasoning task, DeepSeek R1 provides o1-level quality for free",
                estimated_cost=0.0,
                fallback_models=["gemini-2.5-pro", "llama-3.3-70b-versatile"],
            )

        # Speed-critical → Groq (ultra-fast, free)
        if characteristics.requires_speed:
            return TaskClassification(
                complexity=complexity,
                characteristics=characteristics,
                recommended_model="llama-3.3-70b-versatile",
                reasoning="Speed-critical task, Groq provides 300+ tokens/sec for free",
                estimated_cost=0.0,
                fallback_models=["gemini-2.5-flash", "llama-3.1-8b-instant"],
            )

        # Default → Gemini Pro (flagship quality, free)
        return TaskClassification(
            complexity=complexity,
            characteristics=characteristics,
            recommended_model="gemini-2.5-pro",
            reasoning="General-purpose task, Gemini Pro provides flagship quality for free",
            estimated_cost=0.0,
            fallback_models=["llama-3.3-70b-versatile", "deepseek/deepseek-r1:free"],
        )
