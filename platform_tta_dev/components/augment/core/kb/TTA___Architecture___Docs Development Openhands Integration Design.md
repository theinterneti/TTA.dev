---
title: OpenHands Integration Design
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/openhands-integration-design.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/OpenHands Integration Design]]

**Status:** Phase 2 - Design
**Date:** 2025-10-24
**Author:** The Augster

## Overview

This document outlines the design for integrating OpenHands Python SDK into TTA's multi-agent architecture. OpenHands will serve as a development sub-agent, handling code generation, debugging, and development tasks delegated by the TTA orchestrator.

## Architecture

### Component Overview

```
TTA Orchestrator
    ↓
OpenHandsAgentProxy (Agent)
    ↓
OpenHandsAdapter (Communication Layer)
    ↓
OpenHandsClient (SDK Wrapper)
    ↓
OpenHands SDK → OpenRouter API → Free Models
```

### Integration Points

1. **Agent Registry:** Register OpenHands as `AgentType.OPENHANDS`
2. **Message Coordinator:** Use Redis-based message coordination
3. **Circuit Breaker:** Protect against OpenHands SDK failures
4. **Error Recovery:** Retry with exponential backoff
5. **Event Publisher:** Real-time progress updates

## Design Details

### 1. OpenHandsClient (SDK Wrapper)

**Purpose:** Low-level wrapper around OpenHands Python SDK with error handling and logging.

**Class Definition:**

```python
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from openhands.sdk import LLM, Conversation
from openhands.tools.preset.default import get_default_agent
from pydantic import BaseModel, Field, SecretStr

logger = logging.getLogger(__name__)


class OpenHandsConfig(BaseModel):
    """Configuration for OpenHands SDK client."""

    api_key: SecretStr = Field(
        description="OpenRouter API key (from environment or secrets manager)"
    )
    model: str = Field(
        default="deepseek/deepseek-v3:free",
        description="OpenRouter model to use (free models recommended)"
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    workspace_path: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Workspace directory for OpenHands execution"
    )
    cli_mode: bool = Field(
        default=True,
        description="Enable CLI mode for agent"
    )
    usage_id: str = Field(
        default="tta-openhands",
        description="Usage identifier for tracking"
    )
    timeout_seconds: float = Field(
        default=300.0,
        ge=10.0,
        le=3600.0,
        description="Task execution timeout in seconds"
    )


class OpenHandsTaskResult(BaseModel):
    """Result from OpenHands task execution."""

    success: bool = Field(description="Whether task completed successfully")
    output: str = Field(description="Task output/result")
    error: str | None = Field(default=None, description="Error message if failed")
    execution_time: float = Field(description="Execution time in seconds")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (files created, actions taken, etc.)"
    )


class OpenHandsClient:
    """
    Low-level wrapper around OpenHands Python SDK.

    Provides:
    - SDK initialization with OpenRouter configuration
    - Task execution with timeout handling
    - Conversation management
    - Result parsing and error handling
    - Logging and metrics

    Example:
        config = OpenHandsConfig(
            api_key=SecretStr(os.getenv("OPENROUTER_API_KEY")),
            model="deepseek/deepseek-v3:free"
        )
        client = OpenHandsClient(config)
        result = await client.execute_task("Write a Python function to calculate fibonacci")
    """

    def __init__(self, config: OpenHandsConfig) -> None:
        """
        Initialize OpenHands client with configuration.

        Args:
            config: OpenHands configuration
        """
        self.config = config
        self._llm: LLM | None = None
        self._agent: Any | None = None
        self._conversation: Conversation | None = None

        logger.info(
            f"Initialized OpenHandsClient with model={config.model}, "
            f"workspace={config.workspace_path}"
        )

    def _initialize_sdk(self) -> None:
        """Initialize OpenHands SDK components (LLM, Agent)."""
        if self._llm is None:
            self._llm = LLM(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                usage_id=self.config.usage_id,
            )
            logger.debug(f"Initialized LLM with model={self.config.model}")

        if self._agent is None:
            self._agent = get_default_agent(
                llm=self._llm,
                cli_mode=self.config.cli_mode
            )
            logger.debug("Initialized OpenHands agent")

    async def execute_task(
        self,
        task_description: str,
        workspace_path: Path | None = None,
        timeout: float | None = None,
    ) -> OpenHandsTaskResult:
        """
        Execute a development task using OpenHands SDK.

        Args:
            task_description: Natural language task description
            workspace_path: Optional workspace override
            timeout: Optional timeout override (seconds)

        Returns:
            OpenHandsTaskResult with execution details

        Raises:
            TimeoutError: If task execution exceeds timeout
            RuntimeError: If SDK initialization or execution fails
        """
        import time

        start_time = time.time()
        timeout = timeout or self.config.timeout_seconds
        workspace = workspace_path or self.config.workspace_path

        try:
            # Initialize SDK components
            self._initialize_sdk()

            # Create conversation
            self._conversation = Conversation(
                agent=self._agent,
                workspace=str(workspace)
            )

            # Send task message
            self._conversation.send_message(task_description)

            # Execute with timeout
            # TODO: Implement actual timeout mechanism
            self._conversation.run()

            execution_time = time.time() - start_time

            # Parse results
            # TODO: Extract actual output from conversation
            output = "Task completed"  # Placeholder

            return OpenHandsTaskResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={"workspace": str(workspace)}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"OpenHands task execution failed: {e}")

            return OpenHandsTaskResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time
            )

    async def cleanup(self) -> None:
        """Clean up SDK resources."""
        self._conversation = None
        self._agent = None
        self._llm = None
        logger.debug("Cleaned up OpenHands client resources")
```

**Key Design Decisions:**

1. **Pydantic Models:** Use Pydantic for configuration validation and result serialization
2. **SecretStr:** Protect API key in memory and logs
3. **Lazy Initialization:** Initialize SDK components on first use
4. **Timeout Handling:** Configurable timeout with override capability
5. **Error Handling:** Return structured results instead of raising exceptions
6. **Logging:** Comprehensive logging at DEBUG and INFO levels

### 2. OpenHandsAdapter (Communication Layer)

**Purpose:** Bridge between TTA orchestration and OpenHands client, following TTA's adapter pattern.

**Class Definition:**

```python
from __future__ import annotations

import logging
from typing import Any

from ..adapters import AgentCommunicationError, RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


class OpenHandsAdapter:
    """
    Adapter for OpenHands SDK communication following TTA patterns.

    Provides:
    - Retry logic with exponential backoff
    - Error classification and handling
    - Fallback to mock responses (optional)
    - Integration with TTA's error recovery system

    Example:
        adapter = OpenHandsAdapter(
            client=openhands_client,
            retry_config=RetryConfig(max_retries=3),
            fallback_to_mock=True
        )
        result = await adapter.execute_development_task("Fix bug in auth.py")
    """

    def __init__(
        self,
        client: OpenHandsClient,
        retry_config: RetryConfig | None = None,
        fallback_to_mock: bool = False,
    ) -> None:
        """
        Initialize OpenHands adapter.

        Args:
            client: OpenHandsClient instance
            retry_config: Retry configuration (defaults to 3 retries)
            fallback_to_mock: Whether to fall back to mock responses on failure
        """
        self.client = client
        self.retry_config = retry_config or RetryConfig(max_retries=3, base_delay=1.0)
        self.fallback_to_mock = fallback_to_mock

        logger.info(
            f"Initialized OpenHandsAdapter with retry_config={self.retry_config}, "
            f"fallback_to_mock={fallback_to_mock}"
        )

    async def execute_development_task(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a development task with retry logic.

        Args:
            task_description: Natural language task description
            context: Optional context (workspace path, files, etc.)

        Returns:
            Task result dictionary

        Raises:
            AgentCommunicationError: If all retries fail and no fallback
        """
        context = context or {}

        try:
            # Execute with retry
            result = await retry_with_backoff(
                self.client.execute_task,
                self.retry_config,
                task_description=task_description,
                workspace_path=context.get("workspace_path"),
                timeout=context.get("timeout"),
            )

            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error(f"OpenHands adapter execution failed: {e}")

            if self.fallback_to_mock:
                return self._mock_response(task_description)

            raise AgentCommunicationError(f"OpenHands execution failed: {e}") from e

    def _mock_response(self, task_description: str) -> dict[str, Any]:
        """Generate mock response for fallback."""
        return {
            "success": True,
            "output": f"[MOCK] Task '{task_description}' completed",
            "error": None,
            "execution_time": 0.1,
            "metadata": {"mock": True},
        }
```

**Key Design Decisions:**

1. **Retry Integration:** Use TTA's `retry_with_backoff` utility
2. **Fallback Support:** Optional mock responses for testing/degradation
3. **Context Passing:** Flexible context dictionary for workspace, timeout, etc.
4. **Error Classification:** Raise `AgentCommunicationError` for consistency with TTA
5. **Logging:** Track adapter-level operations

### 3. OpenHandsAgentProxy (Agent Integration)

**Purpose:** TTA Agent proxy following the established proxy pattern for OpenHands integration.

**Class Definition:**

```python
from __future__ import annotations

import logging
from typing import Any

from ..agents import Agent
from ..interfaces import MessageCoordinator
from ..models import AgentId, AgentType
from ..realtime.agent_event_integration import get_agent_event_integrator
from ..realtime.event_publisher import EventPublisher
from .openhands_adapter import OpenHandsAdapter
from .openhands_client import OpenHandsClient, OpenHandsConfig

logger = logging.getLogger(__name__)


class OpenHandsAgentProxy(Agent):
    """
    Agent proxy for OpenHands development sub-agent.

    Follows TTA's agent proxy pattern (similar to WorldBuilderAgentProxy).

    Provides:
    - Agent registration and lifecycle management
    - Message coordination for task delegation
    - Real-time event integration
    - Circuit breaker protection
    - Capability advertisement

    Example:
        proxy = OpenHandsAgentProxy(
            coordinator=message_coordinator,
            instance="dev-1",
            openhands_config=config,
            agent_registry=registry,
            event_publisher=publisher
        )
        await proxy.start()
    """

    def __init__(
        self,
        *,
        coordinator: MessageCoordinator | None = None,
        instance: str | None = None,
        default_timeout_s: float = 300.0,
        enable_real_agent: bool = True,
        fallback_to_mock: bool = False,
        openhands_config: OpenHandsConfig | None = None,
        agent_registry=None,
        event_publisher: EventPublisher | None = None,
        circuit_breaker=None,
    ) -> None:
        """
        Initialize OpenHands agent proxy.

        Args:
            coordinator: Message coordinator for agent communication
            instance: Agent instance identifier
            default_timeout_s: Default timeout for operations (300s for dev tasks)
            enable_real_agent: Whether to use real OpenHands SDK
            fallback_to_mock: Whether to fall back to mock responses
            openhands_config: OpenHands configuration (auto-loaded if None)
            agent_registry: Agent registry for registration
            event_publisher: Event publisher for real-time updates
            circuit_breaker: Circuit breaker for fault tolerance
        """
        super().__init__(
            agent_id=AgentId(type=AgentType.OPENHANDS, instance=instance),
            name=f"openhands:{instance or 'default'}",
            coordinator=coordinator,
            default_timeout_s=default_timeout_s,
        )

        # Configuration
        self.enable_real_agent = enable_real_agent
        self.fallback_to_mock = fallback_to_mock
        self.openhands_config = openhands_config or self._load_config()

        # Real-time event integration
        self.event_integrator = get_agent_event_integrator(
            agent_id=str(self.agent_id),
            event_publisher=event_publisher,
            enabled=event_publisher is not None,
        )

        # Circuit breaker for fault tolerance
        self.circuit_breaker = circuit_breaker

        # Initialize adapter and client
        if self.enable_real_agent:
            from ..adapters import RetryConfig

            client = OpenHandsClient(self.openhands_config)
            retry_config = RetryConfig(max_retries=3, base_delay=1.0)
            self.adapter = OpenHandsAdapter(
                client=client,
                retry_config=retry_config,
                fallback_to_mock=fallback_to_mock,
            )
        else:
            self.adapter = None

        # Register with agent registry
        if agent_registry:
            try:
                agent_registry.register(self)
                logger.info(f"Registered OpenHands proxy {self.name} with agent registry")
            except Exception as e:
                logger.warning(f"Failed to register with agent registry: {e}")

    def _load_config(self) -> OpenHandsConfig:
        """Load OpenHands configuration from environment."""
        import os
        from pydantic import SecretStr

        return OpenHandsConfig(
            api_key=SecretStr(os.getenv("OPENROUTER_API_KEY", "")),
            model=os.getenv("OPENHANDS_MODEL", "deepseek/deepseek-v3:free"),
            base_url=os.getenv("OPENHANDS_BASE_URL", "https://openrouter.ai/api/v1"),
        )

    async def execute_development_task(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a development task via OpenHands.

        Args:
            task_description: Natural language task description
            context: Optional context (workspace, files, etc.)

        Returns:
            Task result dictionary
        """
        if not self.enable_real_agent or self.adapter is None:
            return self._mock_development_task(task_description)

        # Publish start event
        await self.event_integrator.publish_agent_event(
            event_type="task_started",
            data={"task": task_description, "context": context},
        )

        try:
            # Execute with circuit breaker if available
            if self.circuit_breaker:
                result = await self.circuit_breaker.execute(
                    self.adapter.execute_development_task,
                    task_description=task_description,
                    context=context,
                )
            else:
                result = await self.adapter.execute_development_task(
                    task_description=task_description,
                    context=context,
                )

            # Publish completion event
            await self.event_integrator.publish_agent_event(
                event_type="task_completed",
                data={"task": task_description, "result": result},
            )

            return result

        except Exception as e:
            # Publish error event
            await self.event_integrator.publish_agent_event(
                event_type="task_failed",
                data={"task": task_description, "error": str(e)},
            )
            raise

    def _mock_development_task(self, task_description: str) -> dict[str, Any]:
        """Generate mock response for development task."""
        return {
            "success": True,
            "output": f"[MOCK] Development task completed: {task_description}",
            "error": None,
            "execution_time": 0.1,
            "metadata": {"mock": True},
        }

    async def get_capabilities(self) -> dict[str, Any]:
        """
        Advertise OpenHands capabilities for discovery.

        Returns:
            Capability dictionary
        """
        return {
            "agent_type": "OPENHANDS",
            "capabilities": [
                "code_generation",
                "code_debugging",
                "code_refactoring",
                "file_editing",
                "bash_execution",
                "web_browsing",
            ],
            "supported_languages": [
                "python",
                "javascript",
                "typescript",
                "java",
                "go",
                "rust",
            ],
            "max_context_tokens": 190_000_000,  # Llama 4 Scout context
            "timeout_seconds": self.default_timeout_s,
        }
```

**Key Design Decisions:**

1. **Agent Base Class:** Inherit from `Agent` for consistency
2. **Event Integration:** Use `AgentEventIntegrator` for real-time updates
3. **Circuit Breaker:** Optional circuit breaker for fault tolerance
4. **Configuration Loading:** Auto-load from environment variables
5. **Capability Advertisement:** Expose capabilities for discovery
6. **Mock Support:** Fallback for testing without OpenRouter API key

### 4. Configuration Management

**Purpose:** Centralized configuration with validation, environment variable loading, and model selection.

**Configuration Schema:**

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator


class OpenHandsModelConfig(BaseModel):
    """Configuration for a specific OpenRouter model."""

    model_id: str = Field(description="OpenRouter model identifier")
    display_name: str = Field(description="Human-readable model name")
    context_tokens: int = Field(description="Maximum context tokens")
    is_free: bool = Field(description="Whether model is free tier")
    recommended: bool = Field(default=False, description="Recommended for TTA")


# Free model catalog
FREE_MODELS = {
    "deepseek-v3": OpenHandsModelConfig(
        model_id="deepseek/deepseek-v3:free",
        display_name="DeepSeek V3 (685B MoE)",
        context_tokens=64_000,
        is_free=True,
        recommended=True,  # Default choice
    ),
    "gemini-flash": OpenHandsModelConfig(
        model_id="google/gemini-2.0-flash-exp:free",
        display_name="Google Gemini 2.0 Flash",
        context_tokens=1_000_000,
        is_free=True,
        recommended=True,
    ),
    "llama-scout": OpenHandsModelConfig(
        model_id="meta-llama/llama-4-scout:free",
        display_name="Meta Llama 4 Scout (17B)",
        context_tokens=190_000_000,
        is_free=True,
        recommended=False,  # Experimental
    ),
    "deepseek-r1": OpenHandsModelConfig(
        model_id="deepseek/deepseek-r1-0528-qwen3-8b:free",
        display_name="DeepSeek R1 Qwen3 (8B)",
        context_tokens=32_000,
        is_free=True,
        recommended=False,
    ),
}


class OpenHandsIntegrationConfig(BaseModel):
    """
    Complete configuration for OpenHands integration.

    Supports:
    - Environment variable loading
    - Model selection and validation
    - Workspace configuration
    - Timeout and retry settings
    - Circuit breaker configuration
    """

    # API Configuration
    api_key: SecretStr = Field(
        description="OpenRouter API key (from OPENROUTER_API_KEY env var)"
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )

    # Model Selection
    model_preset: Literal["deepseek-v3", "gemini-flash", "llama-scout", "deepseek-r1"] = Field(
        default="deepseek-v3",
        description="Model preset to use (free models only)"
    )
    custom_model_id: str | None = Field(
        default=None,
        description="Custom model ID (overrides preset)"
    )

    # Workspace Configuration
    workspace_root: Path = Field(
        default_factory=lambda: Path.cwd() / "openhands_workspace",
        description="Root directory for OpenHands workspaces"
    )
    workspace_isolation: bool = Field(
        default=True,
        description="Create isolated workspace per task"
    )

    # Execution Settings
    default_timeout_seconds: float = Field(
        default=300.0,
        ge=10.0,
        le=3600.0,
        description="Default task execution timeout"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    retry_base_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base delay for exponential backoff (seconds)"
    )

    # Circuit Breaker Settings
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker for fault tolerance"
    )
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Failures before opening circuit"
    )
    circuit_breaker_timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Timeout before attempting recovery"
    )

    # Feature Flags
    enable_real_agent: bool = Field(
        default=True,
        description="Use real OpenHands SDK (false for testing)"
    )
    fallback_to_mock: bool = Field(
        default=False,
        description="Fall back to mock responses on failure"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate API key is not empty."""
        if not v.get_secret_value():
            raise ValueError("OpenRouter API key is required")
        return v

    @field_validator("workspace_root")
    @classmethod
    def ensure_workspace_exists(cls, v: Path) -> Path:
        """Ensure workspace directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def get_model_config(self) -> OpenHandsModelConfig:
        """Get model configuration based on preset or custom ID."""
        if self.custom_model_id:
            # Custom model (assume free tier)
            return OpenHandsModelConfig(
                model_id=self.custom_model_id,
                display_name=self.custom_model_id,
                context_tokens=64_000,  # Conservative default
                is_free=True,
                recommended=False,
            )

        return FREE_MODELS[self.model_preset]

    @classmethod
    def from_env(cls) -> OpenHandsIntegrationConfig:
        """
        Load configuration from environment variables.

        Environment Variables:
            OPENROUTER_API_KEY: Required API key
            OPENHANDS_MODEL: Model preset (default: deepseek-v3)
            OPENHANDS_BASE_URL: API base URL (default: https://openrouter.ai/api/v1)
            OPENHANDS_WORKSPACE_ROOT: Workspace root directory
            OPENHANDS_TIMEOUT: Default timeout in seconds
            OPENHANDS_ENABLE_CIRCUIT_BREAKER: Enable circuit breaker (true/false)

        Returns:
            OpenHandsIntegrationConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Get your API key from https://openrouter.ai/keys"
            )

        return cls(
            api_key=SecretStr(api_key),
            base_url=os.getenv("OPENHANDS_BASE_URL", "https://openrouter.ai/api/v1"),
            model_preset=os.getenv("OPENHANDS_MODEL", "deepseek-v3"),
            workspace_root=Path(os.getenv("OPENHANDS_WORKSPACE_ROOT", "./openhands_workspace")),
            default_timeout_seconds=float(os.getenv("OPENHANDS_TIMEOUT", "300.0")),
            circuit_breaker_enabled=os.getenv("OPENHANDS_ENABLE_CIRCUIT_BREAKER", "true").lower() == "true",
        )
```

**Key Design Decisions:**

1. **Pydantic Validation:** Comprehensive validation with field validators
2. **Free Model Catalog:** Predefined catalog of free models with metadata
3. **Environment Loading:** Convenient `from_env()` class method
4. **Workspace Isolation:** Optional per-task workspace isolation
5. **Circuit Breaker Config:** Integrated circuit breaker settings
6. **Feature Flags:** Enable/disable features for testing and gradual rollout

### 5. Error Recovery Strategy

**Purpose:** Comprehensive error handling with retry, circuit breaker, and fallback mechanisms.

**Error Classification:**

```python
from enum import Enum


class OpenHandsErrorType(str, Enum):
    """Classification of OpenHands errors for recovery strategy selection."""

    CONNECTION_ERROR = "connection_error"  # Network/API connectivity issues
    TIMEOUT_ERROR = "timeout_error"  # Task execution timeout
    AUTHENTICATION_ERROR = "authentication_error"  # Invalid API key
    RATE_LIMIT_ERROR = "rate_limit_error"  # OpenRouter rate limit
    VALIDATION_ERROR = "validation_error"  # Invalid task/configuration
    SDK_ERROR = "sdk_error"  # OpenHands SDK internal error
    UNKNOWN_ERROR = "unknown_error"  # Unclassified error


class OpenHandsRecoveryStrategy(str, Enum):
    """Recovery strategies for different error types."""

    RETRY = "retry"  # Retry with exponential backoff
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with longer backoff
    FALLBACK_MODEL = "fallback_model"  # Try different free model
    FALLBACK_MOCK = "fallback_mock"  # Return mock response
    CIRCUIT_BREAK = "circuit_break"  # Open circuit breaker
    ESCALATE = "escalate"  # Escalate to human intervention
```

**Recovery Strategy Mapping:**

```python
# Error type → Recovery strategies (in order of preference)
RECOVERY_STRATEGIES = {
    OpenHandsErrorType.CONNECTION_ERROR: [
        OpenHandsRecoveryStrategy.RETRY_WITH_BACKOFF,
        OpenHandsRecoveryStrategy.CIRCUIT_BREAK,
        OpenHandsRecoveryStrategy.FALLBACK_MOCK,
    ],
    OpenHandsErrorType.TIMEOUT_ERROR: [
        OpenHandsRecoveryStrategy.RETRY,
        OpenHandsRecoveryStrategy.FALLBACK_MOCK,
    ],
    OpenHandsErrorType.AUTHENTICATION_ERROR: [
        OpenHandsRecoveryStrategy.ESCALATE,  # Cannot auto-recover
    ],
    OpenHandsErrorType.RATE_LIMIT_ERROR: [
        OpenHandsRecoveryStrategy.RETRY_WITH_BACKOFF,
        OpenHandsRecoveryStrategy.FALLBACK_MODEL,
        OpenHandsRecoveryStrategy.CIRCUIT_BREAK,
    ],
    OpenHandsErrorType.VALIDATION_ERROR: [
        OpenHandsRecoveryStrategy.FALLBACK_MOCK,
        OpenHandsRecoveryStrategy.ESCALATE,
    ],
    OpenHandsErrorType.SDK_ERROR: [
        OpenHandsRecoveryStrategy.RETRY,
        OpenHandsRecoveryStrategy.CIRCUIT_BREAK,
        OpenHandsRecoveryStrategy.FALLBACK_MOCK,
    ],
    OpenHandsErrorType.UNKNOWN_ERROR: [
        OpenHandsRecoveryStrategy.RETRY,
        OpenHandsRecoveryStrategy.FALLBACK_MOCK,
    ],
}
```

**Error Recovery Implementation:**

```python
from __future__ import annotations

import logging
from typing import Any

from scripts.primitives.error_recovery import (
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    classify_error,
    with_retry_async,
)
from src.agent_orchestration.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class OpenHandsErrorRecovery:
    """
    Error recovery manager for OpenHands integration.

    Provides:
    - Error classification
    - Recovery strategy selection
    - Retry with exponential backoff
    - Circuit breaker integration
    - Fallback mechanisms
    - Error reporting
    """

    def __init__(
        self,
        config: OpenHandsIntegrationConfig,
        circuit_breaker: CircuitBreaker | None = None,
        error_reporter=None,
    ) -> None:
        """
        Initialize error recovery manager.

        Args:
            config: OpenHands integration configuration
            circuit_breaker: Circuit breaker instance
            error_reporter: Error reporting service
        """
        self.config = config
        self.circuit_breaker = circuit_breaker
        self.error_reporter = error_reporter

        # Retry configuration
        self.retry_config = RetryConfig(
            max_retries=config.max_retries,
            base_delay=config.retry_base_delay,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True,
        )

    def classify_openhands_error(self, error: Exception) -> OpenHandsErrorType:
        """
        Classify error into OpenHands error type.

        Args:
            error: Exception to classify

        Returns:
            OpenHandsErrorType classification
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Connection errors
        if "connection" in error_str or "network" in error_str:
            return OpenHandsErrorType.CONNECTION_ERROR

        # Timeout errors
        if "timeout" in error_str or isinstance(error, TimeoutError):
            return OpenHandsErrorType.TIMEOUT_ERROR

        # Authentication errors
        if "auth" in error_str or "api key" in error_str or "401" in error_str:
            return OpenHandsErrorType.AUTHENTICATION_ERROR

        # Rate limit errors
        if "rate limit" in error_str or "429" in error_str:
            return OpenHandsErrorType.RATE_LIMIT_ERROR

        # Validation errors
        if "validation" in error_str or isinstance(error, ValueError):
            return OpenHandsErrorType.VALIDATION_ERROR

        # SDK errors
        if "openhands" in error_str or "sdk" in error_str:
            return OpenHandsErrorType.SDK_ERROR

        return OpenHandsErrorType.UNKNOWN_ERROR

    async def execute_with_recovery(
        self,
        func: callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with comprehensive error recovery.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all recovery strategies fail
        """
        # Wrap with retry decorator
        @with_retry_async(self.retry_config)
        async def execute_with_retry():
            try:
                # Execute with circuit breaker if available
                if self.circuit_breaker:
                    return await self.circuit_breaker.execute(func, *args, **kwargs)
                else:
                    return await func(*args, **kwargs)

            except Exception as e:
                # Classify error
                error_type = self.classify_openhands_error(e)
                logger.error(f"OpenHands error: {error_type.value} - {e}")

                # Report error
                if self.error_reporter:
                    await self.error_reporter.report_error(
                        error_type=error_type.value,
                        error_message=str(e),
                        context={"function": func.__name__},
                    )

                # Apply recovery strategy
                recovery_strategies = RECOVERY_STRATEGIES.get(
                    error_type,
                    [OpenHandsRecoveryStrategy.RETRY, OpenHandsRecoveryStrategy.FALLBACK_MOCK],
                )

                for strategy in recovery_strategies:
                    if strategy == OpenHandsRecoveryStrategy.RETRY:
                        # Let retry decorator handle this
                        raise

                    elif strategy == OpenHandsRecoveryStrategy.RETRY_WITH_BACKOFF:
                        # Increase backoff delay
                        self.retry_config.base_delay *= 2
                        raise

                    elif strategy == OpenHandsRecoveryStrategy.CIRCUIT_BREAK:
                        # Circuit breaker will handle this
                        raise

                    elif strategy == OpenHandsRecoveryStrategy.FALLBACK_MOCK:
                        if self.config.fallback_to_mock:
                            logger.warning("Falling back to mock response")
                            return self._generate_mock_response()
                        raise

                    elif strategy == OpenHandsRecoveryStrategy.ESCALATE:
                        logger.error(f"Escalating error: {error_type.value}")
                        raise

                # No recovery strategy succeeded
                raise

        return await execute_with_retry()

    def _generate_mock_response(self) -> dict[str, Any]:
        """Generate mock response for fallback."""
        return {
            "success": True,
            "output": "[MOCK] Task completed (fallback response)",
            "error": None,
            "execution_time": 0.1,
            "metadata": {"mock": True, "fallback": True},
        }
```

**Key Design Decisions:**

1. **Error Classification:** Classify errors into specific types for targeted recovery
2. **Strategy Hierarchy:** Multiple recovery strategies per error type
3. **Retry Integration:** Use TTA's `@with_retry_async` decorator
4. **Circuit Breaker:** Integrate with TTA's circuit breaker pattern
5. **Fallback Support:** Optional mock responses for graceful degradation
6. **Error Reporting:** Integration with TTA's error reporting service

## Implementation Plan

### File Structure

```
src/agent_orchestration/openhands_integration/
├── __init__.py                 # Public API exports
├── client.py                   # OpenHandsClient (SDK wrapper)
├── adapter.py                  # OpenHandsAdapter (communication layer)
├── proxy.py                    # OpenHandsAgentProxy (agent integration)
├── config.py                   # Configuration models and loading
├── error_recovery.py           # Error recovery manager
└── models.py                   # Pydantic models (config, results, etc.)

tests/integration/openhands_integration/
├── __init__.py
├── test_client.py              # OpenHandsClient tests
├── test_adapter.py             # OpenHandsAdapter tests
├── test_proxy.py               # OpenHandsAgentProxy tests
├── test_config.py              # Configuration tests
├── test_error_recovery.py      # Error recovery tests
└── conftest.py                 # Pytest fixtures
```

### Integration with Existing TTA Components

**1. Add OPENHANDS to AgentType Enum:**

```python
# src/agent_orchestration/models.py

class AgentType(str, Enum):
    """Agent types in the orchestration system."""

    IPA = "ipa"  # Input Processor Agent
    WBA = "wba"  # World Builder Agent
    NGA = "nga"  # Narrative Generator Agent
    OPENHANDS = "openhands"  # OpenHands Development Agent (NEW)
```

**2. Register OpenHands Proxy in Service:**

```python
# src/agent_orchestration/service.py

from .openhands_integration import OpenHandsAgentProxy, OpenHandsIntegrationConfig

class OrchestrationService:
    async def _initialize_agents(self) -> None:
        """Initialize all agent proxies."""
        # ... existing agent initialization ...

        # Initialize OpenHands proxy
        if self.config.agents.openhands.enabled:
            openhands_config = OpenHandsIntegrationConfig.from_env()
            self.openhands_proxy = OpenHandsAgentProxy(
                coordinator=self.coordinator,
                instance="default",
                openhands_config=openhands_config,
                agent_registry=self.agent_registry,
                event_publisher=self.event_publisher,
                circuit_breaker=self._create_circuit_breaker("openhands"),
            )
            await self.openhands_proxy.start()
```

**3. Add Configuration Schema:**

```python
# src/agent_orchestration/config_schema.py

class OpenHandsAgentConfig(AgentConfig):
    """Configuration for OpenHands agent."""

    model_preset: str = Field(
        default="deepseek-v3",
        description="Free model preset to use"
    )
    workspace_root: str = Field(
        default="./openhands_workspace",
        description="Workspace root directory"
    )
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker"
    )


class AgentsConfig(BaseModel):
    """Configuration for all agent orchestration settings."""

    # ... existing agent configs ...

    openhands: OpenHandsAgentConfig = Field(
        default_factory=OpenHandsAgentConfig,
        description="OpenHands development agent configuration"
    )
```

### Dependencies

**New Dependencies to Add:**

```toml
# pyproject.toml

[project]
dependencies = [
    # ... existing dependencies ...
    "openhands-sdk>=0.1.0",  # OpenHands Python SDK
]
```

### Environment Variables

**Required:**
- `OPENROUTER_API_KEY`: OpenRouter API key (get from https://openrouter.ai/keys)

**Optional:**
- `OPENHANDS_MODEL`: Model preset (default: `deepseek-v3`)
- `OPENHANDS_BASE_URL`: API base URL (default: `https://openrouter.ai/api/v1`)
- `OPENHANDS_WORKSPACE_ROOT`: Workspace directory (default: `./openhands_workspace`)
- `OPENHANDS_TIMEOUT`: Default timeout in seconds (default: `300.0`)
- `OPENHANDS_ENABLE_CIRCUIT_BREAKER`: Enable circuit breaker (default: `true`)

### Testing Strategy

**Unit Tests:**
- Test configuration loading and validation
- Test error classification and recovery strategy selection
- Test mock responses and fallback mechanisms
- Test Pydantic model validation

**Integration Tests:**
- Test OpenHandsClient with real OpenRouter API (requires API key)
- Test adapter retry logic with simulated failures
- Test proxy registration and lifecycle
- Test circuit breaker behavior
- Test end-to-end task execution

**Test Fixtures:**
```python
# tests/integration/openhands_integration/conftest.py

import pytest
from pydantic import SecretStr

from src.agent_orchestration.openhands_integration import (
    OpenHandsClient,
    OpenHandsConfig,
    OpenHandsIntegrationConfig,
)


@pytest.fixture
def openhands_config():
    """OpenHands configuration for testing."""
    return OpenHandsConfig(
        api_key=SecretStr("test-api-key"),
        model="deepseek/deepseek-v3:free",
    )


@pytest.fixture
def openhands_client(openhands_config):
    """OpenHands client for testing."""
    return OpenHandsClient(openhands_config)


@pytest.fixture
def integration_config():
    """Integration configuration for testing."""
    return OpenHandsIntegrationConfig(
        api_key=SecretStr("test-api-key"),
        model_preset="deepseek-v3",
        enable_real_agent=False,  # Use mock for tests
        fallback_to_mock=True,
    )
```

## Next Steps (Phase 3: Implementation)

1. **Create Package Structure:**
   - Create `src/agent_orchestration/openhands_integration/` directory
   - Create `__init__.py` with public API exports

2. **Implement Core Components:**
   - Implement `OpenHandsClient` (client.py)
   - Implement `OpenHandsAdapter` (adapter.py)
   - Implement `OpenHandsAgentProxy` (proxy.py)
   - Implement configuration models (config.py)
   - Implement error recovery (error_recovery.py)

3. **Update Existing Components:**
   - Add `OPENHANDS` to `AgentType` enum
   - Add `OpenHandsAgentConfig` to configuration schema
   - Register OpenHands proxy in `OrchestrationService`

4. **Write Tests:**
   - Unit tests for each component
   - Integration tests with mock and real API
   - Error recovery tests

5. **Documentation:**
   - Update architecture documentation
   - Create integration guide
   - Document configuration options
   - Add troubleshooting guide

6. **Deployment:**
   - Add to component maturity tracking
   - Create deployment checklist
   - Plan gradual rollout strategy

## Success Criteria

**Phase 2 (Design) - COMPLETE:**
- ✅ OpenHandsClient design documented
- ✅ OpenHandsAdapter design documented
- ✅ OpenHandsAgentProxy design documented
- ✅ Configuration management design documented
- ✅ Error recovery strategy design documented
- ✅ Integration points identified
- ✅ File structure defined
- ✅ Testing strategy outlined

**Phase 3 (Implementation) - TODO:**
- [ ] All components implemented
- [ ] Unit tests passing (>70% coverage)
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Code review complete
- [ ] Component maturity: Development stage

**Phase 4 (Deployment) - TODO:**
- [ ] Staging deployment successful
- [ ] Integration tests passing in staging
- [ ] Performance benchmarks met
- [ ] Security review complete
- [ ] Production deployment approved

---

**Design Status:** ✅ COMPLETE
**Next Phase:** Implementation (Phase 3)
**Estimated Effort:** 2-3 days for implementation, 1 day for testing


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs development openhands integration design]]
