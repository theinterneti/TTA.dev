"""Adaptive primitive for Cline CLI usage.

This primitive learns optimal Cline configurations and personas for different task types,
providing self-improving Cline CLI interactions with built-in safety mechanisms.

Key features:
- Automatic persona selection based on task analysis
- Learning optimal prompts and configurations
- Integration with E2B for code validation
- ACE integration for advanced analysis
- Logseq persistence of learned strategies
- Safety mechanisms and circuit breakers
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from tta_dev_primitives.adaptive.base import (
    AdaptivePrimitive,
    LearningMode,
    LearningStrategy,
)
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations import (
    ACEAnalysisPrimitive,
    E2BCodeExecutionPrimitive,
)

logger = logging.getLogger(__name__)


class ClineTaskClassifier:
    """Classifies tasks to determine optimal Cline configuration."""

    @staticmethod
    def classify_task(
        task_description: str, code_context: str | None = None
    ) -> dict[str, Any]:
        """Classify task type and recommend initial configuration."""

        task_lower = task_description.lower()

        # Code-related tasks
        if any(
            word in task_lower
            for word in [
                "code",
                "function",
                "class",
                "implement",
                "refactor",
                "debug",
                ".py",
                ".js",
                ".ts",
            ]
        ):
            base_persona = (
                "backend-developer"
                if "backend" in task_lower or ".py" in task_lower
                else "frontend-developer"
            )
            task_type = "coding"

        # Testing tasks
        elif any(
            word in task_lower
            for word in ["test", "pytest", "unit test", "integration test"]
        ):
            base_persona = "testing-specialist"
            task_type = "testing"

        # Observability/monitoring tasks
        elif any(
            word in task_lower
            for word in [
                "observability",
                "monitoring",
                "metrics",
                "tracing",
                "opentelemetry",
            ]
        ):
            base_persona = "observability-expert"
            task_type = "observability"

        # Infrastructure/deployment tasks
        elif any(
            word in task_lower
            for word in ["deploy", "infrastructure", "docker", "kubernetes", "ci/cd"]
        ):
            base_persona = "devops-engineer"
            task_type = "infrastructure"

        # Data/analysis tasks
        elif any(
            word in task_lower
            for word in [
                "data",
                "analytics",
                "ml",
                "machine learning",
                "pandas",
                "numpy",
            ]
        ):
            base_persona = "data-scientist"
            task_type = "data"

        # Default
        else:
            base_persona = "backend-developer"
            task_type = "general"

        return {
            "task_type": task_type,
            "recommended_persona": base_persona,
            "complexity": ClineTaskClassifier._estimate_complexity(task_description),
            "has_code_generation": "implement" in task_lower or "create" in task_lower,
            "needs_validation": task_type == "coding",
        }

    @staticmethod
    def _estimate_complexity(task_description: str) -> str:
        """Estimate task complexity based on keywords."""
        complex_keywords = [
            "complex",
            "advanced",
            "optimize",
            "refactor",
            "architecture",
            "system",
        ]
        medium_keywords = ["implement", "create", "build", "integrate"]
        simple_keywords = ["fix", "update", "add", "remove"]

        desc_lower = task_description.lower()
        if any(kw in desc_lower for kw in complex_keywords):
            return "complex"
        elif any(kw in desc_lower for kw in medium_keywords):
            return "medium"
        elif any(kw in desc_lower for kw in simple_keywords):
            return "simple"
        else:
            return "unknown"


class ClineExecutionStrategy:
    """Strategy for executing Cline CLI tasks."""

    def __init__(
        self,
        persona: str,
        prompt_template: str,
        validation_enabled: bool = True,
        ace_analysis: bool = False,
        max_retries: int = 2,
        timeout_seconds: int = 60,
    ):
        self.persona = persona
        self.prompt_template = prompt_template
        self.validation_enabled = validation_enabled
        self.ace_analysis = ace_analysis
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert strategy to dictionary for storage."""
        return {
            "persona": self.persona,
            "prompt_template": self.prompt_template,
            "validation_enabled": self.validation_enabled,
            "ace_analysis": self.ace_analysis,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClineExecutionStrategy":
        """Create strategy from dictionary."""
        return cls(
            persona=data.get("persona", "backend-developer"),
            prompt_template=data.get("prompt_template", "{task}"),
            validation_enabled=data.get("validation_enabled", True),
            ace_analysis=data.get("ace_analysis", False),
            max_retries=data.get("max_retries", 2),
            timeout_seconds=data.get("timeout_seconds", 60),
        )


class ClineCLISubAgentPrimitive(AdaptivePrimitive[str, dict[str, Any]]):
    """Adaptive sub-agent primitive for Cline CLI execution.

    An intelligent sub-agent that learns optimal Cline CLI configurations and personas
    for different task types, making the Cline CLI self-improving over time.

    Key features:
    - Automatic task classification and persona selection
    - Learning optimal prompts from execution patterns
    - E2B integration for code validation
    - ACE analysis for complex task evaluation
    - Logseq persistence of learned strategies
    - Safety mechanisms and circuit breakers for production use
    """

    def __init__(
        self,
        cline_binary: str = "cline",
        e2b_enabled: bool = True,
        ace_enabled: bool = True,
        logseq_integration_enabled: bool = True,
        learning_mode: LearningMode = LearningMode.VALIDATE,
        **kwargs,
    ):
        super().__init__(learning_mode=learning_mode, **kwargs)

        self.cline_binary = cline_binary
        self.e2b_enabled = e2b_enabled
        self.ace_enabled = ace_enabled
        self.logseq_integration_enabled = logseq_integration_enabled

        # Initialize integrations
        self.e2b_executor = E2BCodeExecutionPrimitive() if e2b_enabled else None
        self.ace_analyzer = ACEAnalysisPrimitive() if ace_enabled else None

        # Track executions
        self.execution_history: dict[str, dict[str, Any]] = {}

        # Set up baseline strategy
        self.baseline_strategy = self._create_baseline_strategy()

        # Strategy templates for learning
        self.strategy_templates = self._create_strategy_templates()

        logger.info(
            f"Initialized AdaptiveClinePrimitive with learning_mode={learning_mode.value}"
        )

    def _create_baseline_strategy(self) -> LearningStrategy:
        """Create the baseline strategy for safe fallbacks."""
        baseline_config = ClineExecutionStrategy(
            persona="backend-developer",
            prompt_template="Please {task}. Be thorough and follow best practices.",
            validation_enabled=False,
            ace_analysis=False,
        )

        return LearningStrategy(
            name="baseline",
            description="Conservative baseline strategy",
            parameters=baseline_config.to_dict(),
            context_pattern="general:simple",
        )

    def _create_strategy_templates(self) -> list[ClineExecutionStrategy]:
        """Create templates for strategy generation."""
        return [
            ClineExecutionStrategy(
                persona="backend-developer",
                prompt_template="Implement {task} with proper error handling and logging.",
                validation_enabled=True,
                ace_analysis=False,
            ),
            ClineExecutionStrategy(
                persona="frontend-developer",
                prompt_template="Create {task} with modern UI/UX best practices.",
                validation_enabled=True,
                ace_analysis=False,
            ),
            ClineExecutionStrategy(
                persona="testing-specialist",
                prompt_template="Write comprehensive tests for {task}, including edge cases.",
                validation_enabled=True,
                ace_analysis=False,
            ),
            ClineExecutionStrategy(
                persona="observability-expert",
                prompt_template="Add observability to {task} with proper instrumentation.",
                validation_enabled=False,
                ace_analysis=True,
            ),
            ClineExecutionStrategy(
                persona="data-scientist",
                prompt_template="Analyze and implement data processing for {task}.",
                validation_enabled=True,
                ace_analysis=True,
            ),
            ClineExecutionStrategy(
                persona="backend-developer",
                prompt_template="Implement {task} with TTA.dev primitives for reliability.",
                validation_enabled=True,
                ace_analysis=True,
            ),
        ]

    def _default_context_extractor(self, task: str, context: WorkflowContext) -> str:
        """Extract context key for strategy selection."""
        task_info = ClineTaskClassifier.classify_task(
            task, context.data.get("code_context")
        )
        environment = context.metadata.get("environment", "development")
        priority = context.metadata.get("priority", "normal")

        return f"{task_info['task_type']}:{task_info['complexity']}:{environment}:{priority}"

    async def _execute_with_strategy(
        self, task: str, context: WorkflowContext, strategy: LearningStrategy
    ) -> dict[str, Any]:
        """Execute Cline CLI with the selected strategy."""

        execution_id = str(uuid.uuid4())

        strategy_config = ClineExecutionStrategy.from_dict(strategy.parameters)
        task_info = ClineTaskClassifier.classify_task(task)

        # Prepare the actual prompt
        prompt = strategy_config.prompt_template.format(task=task)

        # Execute Cline CLI
        result = await self._execute_cline_cli(
            prompt,
            strategy_config.persona,
            strategy_config.timeout_seconds,
            execution_id,
        )

        # Validate results if enabled and applicable
        if strategy_config.validation_enabled and task_info["needs_validation"]:
            validation_result = await self._validate_results(
                result, context, strategy_config
            )
            result["validation"] = validation_result

        # Record execution
        self.execution_history[execution_id] = {
            "task": task,
            "strategy": strategy.name,
            "persona": strategy_config.persona,
            "success": result.get("success", False),
            "timestamp": time.time(),
        }

        return result

    async def _execute_cline_cli(
        self, prompt: str, persona: str, timeout: int, execution_id: str
    ) -> dict[str, Any]:
        """Execute the Cline CLI with specified parameters."""

        try:
            # Prepare command
            cmd = [self.cline_binary, "--persona", persona, "--execute", prompt]

            # Execute with timeout
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"EXECUTION_ID": execution_id, **{}},
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                execution_time = time.time() - start_time

                stdout_str = stdout.decode("utf-8", errors="replace")
                stderr_str = stderr.decode("utf-8", errors="replace")

                success = process.returncode == 0

                result = {
                    "success": success,
                    "execution_time": execution_time,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "return_code": process.returncode,
                    "persona": persona,
                }

                if not success:
                    logger.warning(f"Cline CLI execution failed: {stderr_str}")

                return result

            except TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": "timeout",
                    "execution_time": timeout,
                    "timeout_seconds": timeout,
                }

        except Exception as e:
            logger.error(f"Cline CLI execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - time.time(),  # Minimal time
            }

    async def _validate_results(
        self,
        result: dict[str, Any],
        context: WorkflowContext,
        strategy_config: ClineExecutionStrategy,
    ) -> dict[str, Any]:
        """Validate execution results using E2B and ACE."""

        validation_result = {
            "e2b_validation": None,
            "ace_analysis": None,
            "overall_valid": True,
            "issues": [],
        }

        # E2B validation for code-related results
        if self.e2b_executor and result.get("stdout", "").strip():
            try:
                e2b_context = WorkflowContext(
                    correlation_id=f"e2b-{uuid.uuid4()}",
                    data={"code": result["stdout"]},
                )

                e2b_result = await self.e2b_executor.execute(
                    {"code": result["stdout"], "timeout": 30}, e2b_context
                )

                validation_result["e2b_validation"] = {
                    "success": e2b_result.get("success", False),
                    "output": e2b_result.get("logs", ""),
                    "error": e2b_result.get("error"),
                }

                if not e2b_result.get("success", False):
                    validation_result["issues"].append("E2B validation failed")
                    validation_result["overall_valid"] = False

            except Exception as e:
                logger.warning(f"E2B validation failed: {e}")
                validation_result["e2b_validation"] = {"error": str(e)}

        # ACE analysis for complex tasks
        if self.ace_analyzer and strategy_config.ace_analysis:
            try:
                ace_context = WorkflowContext(
                    correlation_id=f"ace-{uuid.uuid4()}",
                    data={"task": context.data, "result": result},
                )

                ace_result = await self.ace_analyzer.execute(
                    {"analyze_target": result}, ace_context
                )

                validation_result["ace_analysis"] = ace_result

                # Use ACE analysis to determine validity
                if ace_result.get("quality_score", 0.5) < 0.7:
                    validation_result["issues"].append("ACE quality score too low")
                    validation_result["overall_valid"] = False

            except Exception as e:
                logger.warning(f"ACE analysis failed: {e}")
                validation_result["ace_analysis"] = {"error": str(e)}

        return validation_result

    def _get_default_strategy(self) -> LearningStrategy:
        """Get default strategy (baseline)."""
        return self.baseline_strategy

    async def _learn_from_execution(
        self,
        task: str,
        context: WorkflowContext,
        strategy: LearningStrategy,
        result: dict[str, Any],
        execution_time: float,
    ) -> None:
        """Learn from Cline CLI execution results."""

        # Call parent learning
        await super()._learn_from_execution(
            task, context, strategy, result, execution_time
        )

        # Additional Cline-specific learning
        task_info = ClineTaskClassifier.classify_task(task)
        execution_success = result.get("success", False) and result.get(
            "validation", {}
        ).get("overall_valid", True)

        # Learn Persona Effectiveness
        await self._learn_persona_effectiveness(
            strategy, task_info, execution_success, execution_time
        )

        # Learn Validation Patterns
        await self._learn_validation_patterns(strategy, result, execution_success)

        # Persist to Logseq if enabled
        if self.logseq_integration_enabled and execution_success:
            await self._persist_learning_to_logseq(strategy, task_info, result)

    async def _learn_persona_effectiveness(
        self,
        strategy: LearningStrategy,
        task_info: dict[str, Any],
        success: bool,
        execution_time: float,
    ) -> None:
        """Learn which personas perform best for different task types."""

        strategy_config = ClineExecutionStrategy.from_dict(strategy.parameters)
        task_type = task_info["task_type"]

        # Create or update persona effectiveness metric
        persona_key = f"{strategy_config.persona}_{task_type}"

        if persona_key not in self.strategies:
            # Create new strategy based on successful persona
            if success and strategy.metrics.success_rate > 0.7:
                new_strategy = LearningStrategy(
                    name=f"persona_{persona_key}",
                    description=f"Optimized for {persona_key}",
                    parameters=strategy.parameters.copy(),
                    context_pattern=f"{task_type}:*:*",
                )
                self.strategies[new_strategy.name] = new_strategy

    async def _learn_validation_patterns(
        self,
        strategy: LearningStrategy,
        result: dict[str, Any],
        execution_success: bool,
    ) -> None:
        """Learn when validation improves results vs overhead."""

        validation = result.get("validation", {})

        if validation and execution_success:
            # If validation found issues that would have been missed, favor validation
            if not validation.get("overall_valid", True):
                logger.info("Validation caught issues - learning to favor validation")
                # Could create a strategy that prioritizes validation

    async def _persist_learning_to_logseq(
        self,
        strategy: LearningStrategy,
        task_info: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Persist learned strategies to Logseq knowledge base."""

        try:
            # Import Logseq integration
            from tta_dev_primitives.adaptive.logseq_integration import (
                LogseqStrategyIntegration,
            )

            # Create session for this primitive
            logseq = LogseqStrategyIntegration("cline_cli_primitive")

            # Record successful strategy
            await logseq.record_strategy_success(
                strategy_name=strategy.name,
                context=f"{task_info['task_type']}:{task_info['complexity']}",
                metadata={
                    "persona": strategy.parameters.get("persona"),
                    "validation_used": strategy.parameters.get("validation_enabled"),
                    "ace_used": strategy.parameters.get("ace_analysis"),
                    "success_rate": strategy.metrics.success_rate,
                    "avg_latency": strategy.metrics.avg_latency,
                },
            )

        except ImportError:
            logger.debug("Logseq integration not available - skipping persistence")
        except Exception as e:
            logger.warning(f"Logseq persistence failed: {e}")

    async def _consider_strategy_adaptation(
        self,
        task: str,
        context: WorkflowContext,
        current_strategy: LearningStrategy,
        execution_time: float,
    ) -> None:
        """Consider creating new strategies based on performance patterns."""

        # Strategy adaptation for Cline CLI specific patterns
        task_info = ClineTaskClassifier.classify_task(task)

        # If current strategy performs well for this task type, create specialized version
        if (
            current_strategy.metrics.success_rate > 0.85
            and current_strategy.metrics.total_executions > 10
        ):
            specialized_name = (
                f"specialized_{task_info['task_type']}_{int(time.time())}"
            )

            if specialized_name not in self.strategies:
                new_strategy = LearningStrategy(
                    name=specialized_name,
                    description=f"Specialized for {task_info['task_type']} tasks",
                    parameters=current_strategy.parameters.copy(),
                    context_pattern=f"{task_info['task_type']}:*:*",
                )

                self.strategies[new_strategy.name] = new_strategy
                self.total_adaptations += 1

                logger.info(f"Created specialized strategy: {specialized_name}")

    def get_cline_specific_metrics(self) -> dict[str, Any]:
        """Get Cline CLI specific learning metrics."""

        persona_performance = {}
        task_type_performance = {}

        for strategy_name, strategy in self.strategies.items():
            if strategy.name.startswith("persona_"):
                # Extract persona and task type
                parts = strategy.name.split("_")
                if len(parts) >= 3:
                    persona = parts[1]
                    task_type = parts[2]

                    if persona not in persona_performance:
                        persona_performance[persona] = {}

                    persona_performance[persona][task_type] = {
                        "success_rate": strategy.metrics.success_rate,
                        "avg_latency": strategy.metrics.avg_latency,
                        "executions": strategy.metrics.total_executions,
                    }

        return {
            "persona_performance": persona_performance,
            "task_type_performance": task_type_performance,
            "total_executions": len(self.execution_history),
            "average_success_rate": (
                sum(1 for ex in self.execution_history.values() if ex["success"])
                / len(self.execution_history)
                if self.execution_history
                else 0
            ),
        }


# Integration helpers
def create_cline_cli_subagent(
    learning_mode: LearningMode = LearningMode.VALIDATE,
    enable_e2b: bool = True,
    enable_ace: bool = True,
) -> ClineCLISubAgentPrimitive:
    """Factory function to create a Cline CLI sub-agent primitive with recommended settings."""

    return ClineCLISubAgentPrimitive(
        learning_mode=learning_mode,
        e2b_enabled=enable_e2b,
        ace_enabled=enable_ace,
        max_strategies=15,  # Allow more strategies for Cline
        validation_window=25,  # Shorter validation for faster learning
        circuit_breaker_threshold=0.6,  # More tolerant circuit breaker
    )


# Export
__all__ = [
    "ClineCLISubAgentPrimitive",
    "ClineExecutionStrategy",
    "ClineTaskClassifier",
    "create_cline_cli_subagent",
]
