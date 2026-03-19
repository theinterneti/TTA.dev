"""AgentRegistry — global registry with contextvar override for test isolation."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class AgentRegistry:
    """Maps agent names to agent classes.

    The global instance is populated automatically when agent modules are
    imported. Tests can inject a scoped override via :func:`override_registry`
    without touching the global state.
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[Any]] = {}

    def register(self, name: str, agent_class: type[Any]) -> None:
        """Register an agent class under ``name``."""
        self._agents[name] = agent_class

    def get(self, name: str) -> type[Any]:
        """Return the agent class registered under ``name``.

        Raises:
            KeyError: if no agent with that name is registered.
        """
        if name not in self._agents:
            registered = list(self._agents.keys())
            raise KeyError(f"No agent named {name!r} in registry. Registered agents: {registered}")
        return self._agents[name]

    def all(self) -> list[type[Any]]:
        """Return all registered agent classes."""
        return list(self._agents.values())


# Global instance — populated by agent module imports.
_global_registry = AgentRegistry()

# Contextvar allows tests to inject a scoped registry without mutating global state.
_registry_var: ContextVar[AgentRegistry | None] = ContextVar("agent_registry", default=None)


def get_registry() -> AgentRegistry:
    """Return the active registry.

    Returns the contextvar override if one is set (e.g. inside a test),
    otherwise returns the module-level global registry.
    """
    return _registry_var.get() or _global_registry


@contextmanager
def override_registry(registry: AgentRegistry) -> Generator[AgentRegistry, None, None]:
    """Temporarily replace the active registry within this context.

    Safe to use in concurrent async tasks — each task's contextvar is
    independent.

    Example::

        test_reg = AgentRegistry()
        test_reg.register("developer", MockDeveloperAgent)
        with override_registry(test_reg):
            assert get_registry() is test_reg
        # global registry is restored here
    """
    token = _registry_var.set(registry)
    try:
        yield registry
    finally:
        _registry_var.reset(token)
