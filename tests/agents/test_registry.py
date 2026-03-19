"""Tests for ttadev.agents.registry — Task B1."""

import asyncio

import pytest

from ttadev.agents.registry import AgentRegistry, get_registry, override_registry


class _FakeAgent:
    _spec_name = "fake"


class _OtherAgent:
    _spec_name = "other"


class TestAgentRegistry:
    def test_register_and_get(self):
        reg = AgentRegistry()
        reg.register("fake", _FakeAgent)
        assert reg.get("fake") is _FakeAgent

    def test_get_unknown_raises_keyerror(self):
        reg = AgentRegistry()
        with pytest.raises(KeyError, match="fake"):
            reg.get("fake")

    def test_all_returns_registered(self):
        reg = AgentRegistry()
        reg.register("fake", _FakeAgent)
        reg.register("other", _OtherAgent)
        all_agents = reg.all()
        assert _FakeAgent in all_agents
        assert _OtherAgent in all_agents

    def test_all_empty_registry(self):
        reg = AgentRegistry()
        assert reg.all() == []

    def test_register_overwrites(self):
        reg = AgentRegistry()
        reg.register("fake", _FakeAgent)
        reg.register("fake", _OtherAgent)
        assert reg.get("fake") is _OtherAgent


class TestOverrideRegistry:
    def test_override_is_visible_inside_context(self):
        test_reg = AgentRegistry()
        test_reg.register("fake", _FakeAgent)
        with override_registry(test_reg):
            assert get_registry() is test_reg

    def test_global_restored_after_context(self):
        global_reg = get_registry()
        test_reg = AgentRegistry()
        with override_registry(test_reg):
            pass
        assert get_registry() is global_reg

    def test_override_restored_on_exception(self):
        global_reg = get_registry()
        test_reg = AgentRegistry()
        with pytest.raises(ValueError):
            with override_registry(test_reg):
                raise ValueError("oops")
        assert get_registry() is global_reg

    def test_contextvar_isolation_across_async_tasks(self):
        """Two concurrent tasks with different overrides must not bleed."""

        async def _run():
            reg_a = AgentRegistry()
            reg_b = AgentRegistry()
            reg_a.register("fake", _FakeAgent)
            reg_b.register("other", _OtherAgent)

            results = {}

            async def task_a():
                with override_registry(reg_a):
                    await asyncio.sleep(0)  # yield to task_b
                    results["a"] = get_registry()

            async def task_b():
                with override_registry(reg_b):
                    await asyncio.sleep(0)
                    results["b"] = get_registry()

            await asyncio.gather(task_a(), task_b())
            return results

        results = asyncio.run(_run())
        assert results["a"] is not results["b"]
