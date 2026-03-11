"""
Agent Activity Tracker - Real-time tracking of AI agent actions.

Tracks:
- Provider (GitHub Copilot, OpenRouter, Ollama)
- Model (Claude Sonnet 4.5, GPT-4, etc.)
- TTA Agent (backend-engineer, architect, or none)
- User (session owner)
- Actions (tool calls, code changes, etc.)
"""

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AgentContext:
    """Context for tracking agent execution."""

    provider: str  # "github_copilot", "openrouter", "ollama"
    model: str  # "claude-sonnet-4.5", "gpt-4", etc.
    agent_role: str | None  # "backend-engineer", "architect", or None
    user: str  # "thein", etc.


class AgentTracker:
    """Tracks AI agent activity in real-time."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(".observability/agents")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_file = self.data_dir / "current_session.jsonl"
        self.agents_registry = self.data_dir / "agents_registry.json"
        self._lock = threading.Lock()

    def track_agent_action(
        self,
        provider: str,
        model: str,
        action_type: str,
        action_data: dict[str, Any],
        tta_agent: str | None = None,
        user: str | None = None,
    ) -> None:
        """Track a single agent action."""
        with self._lock:
            action_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider,
                "model": model,
                "tta_agent": tta_agent,
                "user": user or "unknown",
                "action_type": action_type,
                "action_data": action_data,
            }

            # Append to session log
            with open(self.current_session_file, "a") as f:
                f.write(json.dumps(action_record) + "\n")

            # Update agent registry
            self._update_registry(provider, model, tta_agent)

    def log_activity(
        self, activity_type: str, context: AgentContext, details: dict[str, Any]
    ) -> None:
        """Log an activity with full agent context."""
        self.track_agent_action(
            provider=context.provider,
            model=context.model,
            action_type=activity_type,
            action_data=details,
            tta_agent=context.agent_role,
            user=context.user,
        )

    def _update_registry(self, provider: str, model: str, tta_agent: str | None) -> None:
        """Update the agents registry with active agents."""
        registry = {}
        if self.agents_registry.exists():
            with open(self.agents_registry) as f:
                registry = json.load(f)

        agent_key = f"{provider}:{model}"
        if agent_key not in registry:
            registry[agent_key] = {
                "provider": provider,
                "model": model,
                "first_seen": datetime.utcnow().isoformat(),
                "tta_agents_used": [],
                "action_count": 0,
            }

        registry[agent_key]["last_seen"] = datetime.utcnow().isoformat()
        registry[agent_key]["action_count"] += 1

        if tta_agent and tta_agent not in registry[agent_key]["tta_agents_used"]:
            registry[agent_key]["tta_agents_used"].append(tta_agent)

        with open(self.agents_registry, "w") as f:
            json.dump(registry, f, indent=2)

    def get_active_agents(self, since_minutes: int = 5) -> list[dict[str, Any]]:
        """Get agents active in the last N minutes."""
        cutoff = time.time() - (since_minutes * 60)

        if not self.agents_registry.exists():
            return []

        with open(self.agents_registry) as f:
            registry = json.load(f)

        active = []
        for agent_key, agent_data in registry.items():
            last_seen = datetime.fromisoformat(agent_data["last_seen"]).timestamp()
            if last_seen >= cutoff:
                active.append(agent_data)

        return active

    def get_recent_actions(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent agent actions."""
        if not self.current_session_file.exists():
            return []

        with open(self.current_session_file) as f:
            lines = f.readlines()

        # Get last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        return [json.loads(line) for line in recent_lines]


# Global tracker instance
_tracker: AgentTracker | None = None


def get_tracker() -> AgentTracker:
    """Get the global agent tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = AgentTracker()
    return _tracker


def track_action(
    provider: str,
    model: str,
    action_type: str,
    action_data: dict[str, Any],
    tta_agent: str | None = None,
    user: str | None = None,
) -> None:
    """Convenience function to track an agent action."""
    get_tracker().track_agent_action(
        provider=provider,
        model=model,
        action_type=action_type,
        action_data=action_data,
        tta_agent=tta_agent,
        user=user,
    )
