"""Auto-instrumentation that logs agent activity."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from .context import ExecutionContext


class ActivityLogger:
    """Logs agent/workflow activity to filesystem."""
    
    def __init__(self):
        self.traces_dir = Path.home() / ".tta" / "traces"
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect current context
        self.context = ExecutionContext.detect_current()
        self.context.provider = "github-copilot"  # We know we're Copilot
        self.context.model = "claude-sonnet-4.5"  # We know the model
    
    def log_activity(
        self,
        activity_type: str,
        details: dict,
        agent: Optional[str] = None
    ):
        """Log a single activity."""
        
        trace_id = str(uuid.uuid4())
        
        activity = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "provider": self.context.provider,
            "model": self.context.model,
            "agent": agent,  # TTA agent if any
            "user": self.context.user,
            "details": details,
        }
        
        # Write to file
        trace_file = self.traces_dir / f"{trace_id}.json"
        with open(trace_file, "w") as f:
            json.dump(activity, f, indent=2)
        
        return trace_id


# Global singleton
_logger: Optional[ActivityLogger] = None


def get_logger() -> ActivityLogger:
    """Get global activity logger."""
    global _logger
    if _logger is None:
        _logger = ActivityLogger()
    return _logger


def log_tool_use(tool_name: str, parameters: dict, agent: Optional[str] = None):
    """Log that a tool was used."""
    logger = get_logger()
    return logger.log_activity(
        "tool_use",
        {
            "tool": tool_name,
            "parameters": parameters,
        },
        agent=agent
    )


def log_workflow_start(workflow_name: str, agent: Optional[str] = None):
    """Log workflow started."""
    logger = get_logger()
    return logger.log_activity(
        "workflow_start",
        {
            "workflow": workflow_name,
        },
        agent=agent
    )


def log_workflow_end(workflow_name: str, status: str, agent: Optional[str] = None):
    """Log workflow completed."""
    logger = get_logger()
    return logger.log_activity(
        "workflow_end",
        {
            "workflow": workflow_name,
            "status": status,
        },
        agent=agent
    )


def auto_initialize():
    """Initialize observability (create logger singleton)."""
    get_logger()
    print("✓ TTA.dev observability initialized")
