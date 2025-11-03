"""Orchestration configuration for multi-model workflows.

Provides user-friendly YAML configuration for orchestration settings, enabling
customization of model selection, fallback strategies, and cost tracking.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator model (e.g., Claude Sonnet 4.5)."""

    model: str = Field(
        default="claude-sonnet-4.5",
        description="Model name for orchestrator (planning/validation)",
    )
    api_key_env: str = Field(
        default="ANTHROPIC_API_KEY",
        description="Environment variable name for API key",
    )


class ExecutorConfig(BaseModel):
    """Configuration for an executor model (e.g., Gemini Pro, Groq)."""

    model: str = Field(description="Model name for executor")
    provider: str = Field(description="Provider name (google-ai-studio, groq, etc.)")
    api_key_env: str = Field(description="Environment variable name for API key")
    use_cases: list[str] = Field(
        default_factory=list,
        description="Task complexities this executor handles (simple, moderate, complex, expert)",
    )

    @field_validator("use_cases")
    @classmethod
    def validate_use_cases(cls, v: list[str]) -> list[str]:
        """Validate use_cases are valid complexity levels."""
        valid_cases = {"simple", "moderate", "complex", "expert", "speed-critical", "reasoning"}
        invalid = set(v) - valid_cases
        if invalid:
            raise ValueError(f"Invalid use_cases: {invalid}. Must be one of: {valid_cases}")
        return v


class CostTrackingConfig(BaseModel):
    """Configuration for cost tracking and budgeting."""

    enabled: bool = Field(default=True, description="Enable cost tracking")
    budget_limit_usd: float = Field(default=100.0, description="Monthly budget limit in USD")
    alert_threshold: float = Field(
        default=0.8,
        description="Alert when budget reaches this percentage (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )


class FallbackStrategy(BaseModel):
    """Configuration for fallback model selection."""

    models: list[str] = Field(
        default_factory=lambda: [
            "gemini-2.5-pro",
            "llama-3.3-70b-versatile",
            "claude-sonnet-4.5",
        ],
        description="Ordered list of models to try (free first, paid last)",
    )


class OrchestrationConfig(BaseModel):
    """Complete orchestration configuration."""

    enabled: bool = Field(default=True, description="Enable orchestration")
    prefer_free_models: bool = Field(
        default=True, description="Prefer free models when quality is sufficient"
    )
    quality_threshold: float = Field(
        default=0.85,
        description="Minimum quality score (0-1) to use free models",
        ge=0.0,
        le=1.0,
    )

    orchestrator: OrchestratorConfig = Field(
        default_factory=OrchestratorConfig,
        description="Orchestrator model configuration",
    )
    executors: list[ExecutorConfig] = Field(
        default_factory=list, description="List of executor model configurations"
    )
    fallback_strategy: FallbackStrategy = Field(
        default_factory=FallbackStrategy, description="Fallback model selection"
    )
    cost_tracking: CostTrackingConfig = Field(
        default_factory=CostTrackingConfig, description="Cost tracking configuration"
    )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "OrchestrationConfig":
        """Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Loaded configuration

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "orchestration" not in data:
            raise ValueError(
                f"Invalid configuration file: {yaml_path}. Must contain 'orchestration' key."
            )

        return cls(**data["orchestration"])

    @classmethod
    def from_env(cls) -> "OrchestrationConfig":
        """Load configuration from environment variables.

        Environment variables override YAML configuration:
        - TTA_ORCHESTRATION_ENABLED: Enable/disable orchestration
        - TTA_PREFER_FREE_MODELS: Prefer free models
        - TTA_QUALITY_THRESHOLD: Minimum quality threshold
        - TTA_ORCHESTRATOR_MODEL: Orchestrator model name
        - TTA_BUDGET_LIMIT_USD: Monthly budget limit

        Returns:
            Configuration with environment variable overrides
        """
        config = cls()

        # Override from environment variables
        if os.getenv("TTA_ORCHESTRATION_ENABLED"):
            config.enabled = os.getenv("TTA_ORCHESTRATION_ENABLED", "true").lower() == "true"

        if os.getenv("TTA_PREFER_FREE_MODELS"):
            config.prefer_free_models = (
                os.getenv("TTA_PREFER_FREE_MODELS", "true").lower() == "true"
            )

        if os.getenv("TTA_QUALITY_THRESHOLD"):
            config.quality_threshold = float(os.getenv("TTA_QUALITY_THRESHOLD", "0.85"))

        if os.getenv("TTA_ORCHESTRATOR_MODEL"):
            config.orchestrator.model = os.getenv("TTA_ORCHESTRATOR_MODEL", "claude-sonnet-4.5")

        if os.getenv("TTA_BUDGET_LIMIT_USD"):
            config.cost_tracking.budget_limit_usd = float(
                os.getenv("TTA_BUDGET_LIMIT_USD", "100.0")
            )

        return config

    def get_executor_for_use_case(self, use_case: str) -> ExecutorConfig | None:
        """Get the first executor that handles the given use case.

        Args:
            use_case: Task complexity or use case (simple, moderate, complex, etc.)

        Returns:
            Executor configuration or None if no executor handles this use case
        """
        for executor in self.executors:
            if use_case in executor.use_cases:
                return executor
        return None

    def get_api_key(self, api_key_env: str) -> str | None:
        """Get API key from environment variable.

        Args:
            api_key_env: Environment variable name

        Returns:
            API key value or None if not set
        """
        return os.getenv(api_key_env)


def load_orchestration_config(
    config_path: str | Path | None = None,
    use_env_overrides: bool = True,
) -> OrchestrationConfig:
    """Load orchestration configuration from file or environment.

    Args:
        config_path: Path to YAML configuration file (optional)
        use_env_overrides: Apply environment variable overrides

    Returns:
        Loaded configuration

    Example:
        >>> # Load from default location
        >>> config = load_orchestration_config()
        >>>
        >>> # Load from specific file
        >>> config = load_orchestration_config(".tta/orchestration-config.yaml")
        >>>
        >>> # Load from environment only
        >>> config = load_orchestration_config(config_path=None, use_env_overrides=True)
    """
    # Try to load from file
    if config_path:
        config = OrchestrationConfig.from_yaml(config_path)
        logger.info(f"✅ Loaded orchestration config from {config_path}")
    else:
        # Try default locations
        default_paths = [
            Path(".tta/orchestration-config.yaml"),
            Path("orchestration-config.yaml"),
            Path.home() / ".tta" / "orchestration-config.yaml",
        ]

        config = None
        for path in default_paths:
            if path.exists():
                config = OrchestrationConfig.from_yaml(path)
                logger.info(f"✅ Loaded orchestration config from {path}")
                break

        if config is None:
            # No config file found, use defaults
            config = OrchestrationConfig()
            logger.info("⚠️  No config file found, using defaults")

    # Apply environment variable overrides
    if use_env_overrides:
        env_config = OrchestrationConfig.from_env()
        config.enabled = env_config.enabled
        config.prefer_free_models = env_config.prefer_free_models
        config.quality_threshold = env_config.quality_threshold
        config.orchestrator.model = env_config.orchestrator.model
        config.cost_tracking.budget_limit_usd = env_config.cost_tracking.budget_limit_usd
        logger.info("✅ Applied environment variable overrides")

    return config


def create_default_config(output_path: str | Path = ".tta/orchestration-config.yaml") -> None:
    """Create a default orchestration configuration file.

    Args:
        output_path: Path where to save the configuration file

    Example:
        >>> from tta_dev_primitives.config import create_default_config
        >>> create_default_config(".tta/orchestration-config.yaml")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "orchestration": {
            "enabled": True,
            "prefer_free_models": True,
            "quality_threshold": 0.85,
            "orchestrator": {
                "model": "claude-sonnet-4.5",
                "api_key_env": "ANTHROPIC_API_KEY",
            },
            "executors": [
                {
                    "model": "gemini-2.5-pro",
                    "provider": "google-ai-studio",
                    "api_key_env": "GOOGLE_API_KEY",
                    "use_cases": ["moderate", "complex"],
                },
                {
                    "model": "llama-3.3-70b-versatile",
                    "provider": "groq",
                    "api_key_env": "GROQ_API_KEY",
                    "use_cases": ["simple", "speed-critical"],
                },
                {
                    "model": "deepseek/deepseek-r1:free",
                    "provider": "openrouter",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "use_cases": ["complex", "reasoning"],
                },
            ],
            "fallback_strategy": {
                "models": [
                    "gemini-2.5-pro",
                    "llama-3.3-70b-versatile",
                    "claude-sonnet-4.5",
                ]
            },
            "cost_tracking": {
                "enabled": True,
                "budget_limit_usd": 100.0,
                "alert_threshold": 0.8,
            },
        }
    }

    with open(output_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"✅ Created default configuration at {output_path}")
