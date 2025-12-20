"""Tests for routing primitive."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_router_basic() -> None:
    """Test basic routing."""
    route_a = MockPrimitive("a", return_value={"result": "A"})
    route_b = MockPrimitive("b", return_value={"result": "B"})

    router = RouterPrimitive(
        routes={"a": route_a, "b": route_b}, router_fn=lambda data, ctx: data["route"]
    )

    context = WorkflowContext()
    result = await router.execute({"route": "a"}, context)

    assert result == {"result": "A"}
    assert route_a.call_count == 1
    assert route_b.call_count == 0


@pytest.mark.asyncio
async def test_router_context_based() -> None:
    """Test routing based on context metadata."""
    openai = MockPrimitive("openai", return_value={"provider": "openai"})
    local = MockPrimitive("local", return_value={"provider": "local"})

    router = RouterPrimitive(
        routes={"openai": openai, "local": local},
        router_fn=lambda data, ctx: ctx.metadata.get("provider", "openai"),
    )

    # Route to local via context
    context = WorkflowContext(metadata={"provider": "local"})
    result = await router.execute({}, context)

    assert result == {"provider": "local"}
    assert local.call_count == 1
    assert openai.call_count == 0


@pytest.mark.asyncio
async def test_router_default() -> None:
    """Test default route fallback."""
    default = MockPrimitive("default", return_value={"result": "DEFAULT"})

    router = RouterPrimitive(
        routes={"a": default}, router_fn=lambda data, ctx: data.get("route", "unknown"), default="a"
    )

    context = WorkflowContext()
    result = await router.execute({"route": "unknown"}, context)

    assert result == {"result": "DEFAULT"}
    assert default.call_count == 1


@pytest.mark.asyncio
async def test_router_no_route_error() -> None:
    """Test error when no route found."""
    router = RouterPrimitive(
        routes={"a": MockPrimitive("a", return_value={})}, router_fn=lambda data, ctx: "nonexistent"
    )

    with pytest.raises(ValueError, match="No route found"):
        await router.execute({}, WorkflowContext())


@pytest.mark.asyncio
async def test_router_tracks_history() -> None:
    """Test routing history is tracked in context."""
    route_a = MockPrimitive("a", return_value={"result": "A"})
    route_b = MockPrimitive("b", return_value={"result": "B"})

    router = RouterPrimitive(
        routes={"a": route_a, "b": route_b}, router_fn=lambda data, ctx: data["route"]
    )

    context = WorkflowContext()

    # First routing
    await router.execute({"route": "a"}, context)
    assert context.state["routing_history"] == ["a"]

    # Second routing
    await router.execute({"route": "b"}, context)
    assert context.state["routing_history"] == ["a", "b"]


@pytest.mark.asyncio
async def test_router_cost_optimization() -> None:
    """Test routing for cost optimization."""
    expensive = MockPrimitive("expensive", return_value={"cost": 10})
    cheap = MockPrimitive("cheap", return_value={"cost": 1})

    def cost_router(data, ctx) -> str:
        """Route simple queries to cheap model."""
        prompt_length = len(data.get("prompt", ""))
        return "cheap" if prompt_length < 100 else "expensive"

    router = RouterPrimitive(routes={"expensive": expensive, "cheap": cheap}, router_fn=cost_router)

    context = WorkflowContext()

    # Short prompt -> cheap route
    result = await router.execute({"prompt": "Hello"}, context)
    assert result == {"cost": 1}
    assert cheap.call_count == 1
    assert expensive.call_count == 0

    # Long prompt -> expensive route
    result = await router.execute({"prompt": "x" * 150}, context)
    assert result == {"cost": 10}
    assert expensive.call_count == 1


@pytest.mark.asyncio
async def test_router_tier_based() -> None:
    """Test routing based on user tier."""
    premium = MockPrimitive("premium", return_value={"tier": "premium"})
    free = MockPrimitive("free", return_value={"tier": "free"})

    router = RouterPrimitive(
        routes={"premium": premium, "free": free},
        router_fn=lambda data, ctx: ctx.metadata.get("tier", "free"),
        default="free",
    )

    # Premium user
    context = WorkflowContext(metadata={"tier": "premium"})
    result = await router.execute({}, context)
    assert result == {"tier": "premium"}

    # Free user (default)
    context = WorkflowContext()
    result = await router.execute({}, context)
    assert result == {"tier": "free"}
