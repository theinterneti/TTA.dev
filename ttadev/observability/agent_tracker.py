"""Agent activity tracking for observability dashboard."""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class AgentActivityTracker:
    """Track agent activities for the observability dashboard."""
    
    def __init__(self, log_dir: Path | None = None):
        """Initialize agent activity tracker.
        
        Args:
            log_dir: Directory to store agent activity logs
        """
        self.log_dir = log_dir or Path(".ttadev/observability")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "agent_activity.jsonl"
    
    async def track_agent_action(
        self,
        agent_name: str,
        action: str,
        context: dict[str, Any] | None = None
    ) -> None:
        """Track an agent action.
        
        Args:
            agent_name: Name of the agent performing the action
            action: Description of the action
            context: Additional context about the action
        """
        with tracer.start_as_current_span(f"agent.{agent_name}.{action}") as span:
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("agent.action", action)
            
            activity = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "action": action,
                "context": context or {},
                "trace_id": format(span.get_span_context().trace_id, "032x"),
                "span_id": format(span.get_span_context().span_id, "016x")
            }
            
            # Append to JSONL file
            with open(self.log_file, "a") as f:
                f.write(json.dumps(activity) + "\n")
    
    def get_recent_activity(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent agent activities.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        if not self.log_file.exists():
            return []
        
        activities = []
        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    activities.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Return most recent first
        return activities[-limit:][::-1]
    
    def get_agent_summary(self) -> dict[str, Any]:
        """Get summary of agent activities.
        
        Returns:
            Summary statistics by agent
        """
        activities = self.get_recent_activity(limit=1000)
        
        summary = {}
        for activity in activities:
            agent_name = activity["agent_name"]
            if agent_name not in summary:
                summary[agent_name] = {
                    "total_actions": 0,
                    "recent_actions": [],
                    "last_seen": None
                }
            
            summary[agent_name]["total_actions"] += 1
            summary[agent_name]["last_seen"] = activity["timestamp"]
            
            if len(summary[agent_name]["recent_actions"]) < 10:
                summary[agent_name]["recent_actions"].append({
                    "action": activity["action"],
                    "timestamp": activity["timestamp"],
                    "context": activity["context"]
                })
        
        return summary
