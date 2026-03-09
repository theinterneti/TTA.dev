"""
Auto-tracking for GitHub Copilot CLI agent actions.

This module automatically detects and tracks actions by GitHub Copilot CLI.
"""

import os
import inspect
from functools import wraps
from typing import Any, Callable
from .agent_tracker import track_action

def is_copilot_session() -> bool:
    """Detect if we're running in a GitHub Copilot CLI session."""
    # Check environment variables that indicate Copilot CLI
    copilot_indicators = [
        "GITHUB_COPILOT",
        "COPILOT_SESSION_ID",
        "GH_COPILOT",
    ]
    return any(os.getenv(var) for var in copilot_indicators)

def get_copilot_context() -> dict[str, Any]:
    """Get context about the current Copilot session."""
    return {
        "provider": "github-copilot",
        "model": os.getenv("COPILOT_MODEL", "claude-sonnet-4.5"),
        "user": os.getenv("USER", "unknown"),
        "session_id": os.getenv("COPILOT_SESSION_ID", "unknown"),
    }

def track_primitive_execution(func: Callable) -> Callable:
    """Decorator to auto-track primitive executions."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if is_copilot_session():
            ctx = get_copilot_context()
            
            # Determine TTA agent if any
            tta_agent = None
            frame = inspect.currentframe()
            if frame and frame.f_back:
                # Check call stack for agent markers
                local_vars = frame.f_back.f_locals
                if "agent_name" in local_vars:
                    tta_agent = local_vars["agent_name"]
            
            # Track execution start
            track_action(
                provider=ctx["provider"],
                model=ctx["model"],
                action_type="primitive_execution",
                action_data={
                    "primitive": self.__class__.__name__,
                    "method": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
                tta_agent=tta_agent,
                user=ctx["user"],
            )
        
        result = await func(self, *args, **kwargs)
        return result
    
    return wrapper

def track_workflow_execution(workflow_name: str, primitives: list[str]) -> None:
    """Track a complete workflow execution."""
    if is_copilot_session():
        ctx = get_copilot_context()
        track_action(
            provider=ctx["provider"],
            model=ctx["model"],
            action_type="workflow_execution",
            action_data={
                "workflow_name": workflow_name,
                "primitives": primitives,
                "primitive_count": len(primitives),
            },
            user=ctx["user"],
        )

def track_agent_activation(agent_name: str, task: str) -> None:
    """Track when a TTA agent is activated."""
    if is_copilot_session():
        ctx = get_copilot_context()
        track_action(
            provider=ctx["provider"],
            model=ctx["model"],
            action_type="agent_activation",
            action_data={
                "task": task,
            },
            tta_agent=agent_name,
            user=ctx["user"],
        )
