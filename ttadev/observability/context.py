"""Enhanced observability context with provider/model/agent tracking."""
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExecutionContext:
    """Tracks who/what is executing workflows."""
    
    # Infrastructure
    provider: str = "unknown"  # github-copilot, openrouter, ollama, direct
    model: str = "unknown"  # claude-sonnet-4.5, gpt-4, llama-3.1, etc.
    
    # TTA.dev layer
    agent: Optional[str] = None  # backend-engineer, architect, etc. (or None)
    user: str = "unknown"
    
    # Execution metadata
    workflow_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: Optional[str] = None
    
    start_time: datetime = field(default_factory=datetime.now)
    attributes: dict = field(default_factory=dict)
    
    @classmethod
    def detect_current(cls) -> "ExecutionContext":
        """Auto-detect current execution context from environment."""
        
        # Detect provider - GitHub Copilot sets GITHUB_ACTIONS when running in CLI
        provider = "github-copilot"  # Default assumption in TTA.dev context
        if os.getenv("OPENROUTER_API_KEY"):
            provider = "openrouter"
        elif os.getenv("OLLAMA_HOST"):
            provider = "ollama"
        elif os.getenv("ANTHROPIC_API_KEY") and not os.getenv("GITHUB_COPILOT"):
            provider = "anthropic-direct"
        
        # Detect model - for Copilot CLI, Claude Sonnet 4.5 is default
        model = os.getenv("MODEL_NAME", "claude-sonnet-4.5")
        
        # Detect user
        user = os.getenv("USER", os.getenv("USERNAME", "unknown"))
        
        # Detect TTA agent role from environment (set by agent wrappers)
        agent = os.getenv("TTA_AGENT_ROLE")
        
        return cls(
            provider=provider,
            model=model,
            user=user,
            agent=agent,
            attributes={
                "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
                "pid": os.getpid(),
                "detected_at": datetime.now().isoformat(),
            }
        )
    
    def to_dict(self) -> dict:
        """Serialize for logging/telemetry."""
        return {
            "provider": self.provider,
            "model": self.model,
            "agent": self.agent,
            "user": self.user,
            "workflow_id": self.workflow_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time.isoformat(),
            "attributes": self.attributes,
        }
