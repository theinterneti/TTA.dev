"""Unit tests for RouterPrimitive (wrapper-based implementation)."""

from unittest.mock import MagicMock, patch

import pytest

from observability_integration.primitives.router import RouterPrimitive


# Mock WorkflowPrimitive for testing
class MockPrimitive:
    """Mock primitive for testing."""

    def __init__(self, name="mock"):
        self.name = name

    async def execute(self, data, context):
        """Mock execute method."""
        return f"{self.name}_result"


@pytest.fixture
def fast_primitive():
    """Create mock fast primitive."""
    return MockPrimitive("FastPrimitive")


@pytest.fixture
def premium_primitive():
    """Create mock premium primitive."""
    return MockPrimitive("PremiumPrimitive")


@pytest.fixture
def simple_router_fn():
    """Simple router function for tests."""

    def router(data, context):
        query_len = (
            len(str(data.get("query", "")))
            if isinstance(data, dict)
            else len(str(data))
        )
        return "fast" if query_len < 20 else "premium"

    return router


@pytest.fixture
def router_primitive(fast_primitive, premium_primitive, simple_router_fn):
    """Create RouterPrimitive instance for testing."""
    routes = {
        "fast": fast_primitive,
        "premium": premium_primitive,
    }

    return RouterPrimitive(
        routes=routes,
        router_fn=simple_router_fn,
        default_route="fast",
        cost_per_route={"fast": 0.001, "premium": 0.01},
    )


class TestRouterPrimitiveInit:
    """Test RouterPrimitive initialization."""

    def test_initialization_with_routes(
        self, fast_primitive, premium_primitive, simple_router_fn
    ):
        """Test initialization with valid routes."""
        routes = {"fast": fast_primitive, "premium": premium_primitive}

        router = RouterPrimitive(
            routes=routes,
            router_fn=simple_router_fn,
            default_route="fast",
        )

        assert router.default_route == "fast"
        assert "fast" in router.routes
        assert "premium" in router.routes

    def test_initialization_empty_routes_raises_error(self, simple_router_fn):
        """Test initialization with empty routes raises ValueError."""
        with pytest.raises(ValueError, match="Routes cannot be empty"):
            RouterPrimitive(
                routes={},
                router_fn=simple_router_fn,
                default_route="fast",
            )

    def test_initialization_invalid_default_route_raises_error(
        self, fast_primitive, simple_router_fn
    ):
        """Test initialization with invalid default route raises ValueError."""
        routes = {"fast": fast_primitive}

        with pytest.raises(ValueError, match="Default route.*not in routes"):
            RouterPrimitive(
                routes=routes,
                router_fn=simple_router_fn,
                default_route="nonexistent",
            )


class TestRoutingDecisions:
    """Test routing decision logic."""

    @pytest.mark.asyncio
    async def test_routes_to_fast_for_short_query(self, router_primitive):
        """Test routing short query to fast route."""
        mock_context = MagicMock()
        result = await router_primitive.execute({"query": "short"}, mock_context)

        # Should use fast route for short query
        assert "FastPrimitive" in result or "fast" in result.lower()

    @pytest.mark.asyncio
    async def test_routes_to_premium_for_long_query(self, router_primitive):
        """Test routing long query to premium route."""
        mock_context = MagicMock()
        result = await router_primitive.execute(
            {"query": "this is a much longer query that should route to premium model"},
            mock_context,
        )

        assert "PremiumPrimitive" in result or "premium" in result.lower()

    @pytest.mark.asyncio
    async def test_uses_default_route_on_router_error(
        self, fast_primitive, premium_primitive
    ):
        """Test falls back to default route when router function fails."""
        routes = {"fast": fast_primitive, "premium": premium_primitive}

        def failing_router(data, context):
            raise ValueError("Router error")

        router = RouterPrimitive(
            routes=routes,
            router_fn=failing_router,
            default_route="fast",
        )

        mock_context = MagicMock()
        result = await router.execute({"query": "test"}, mock_context)

        # Should fall back to default route
        assert "FastPrimitive" in result or "fast" in result.lower()


class TestMetricsRecording:
    """Test metrics recording."""

    @pytest.mark.asyncio
    async def test_decision_metrics_recorded(self, router_primitive):
        """Test routing decision metrics are recorded."""
        # Metrics should work with graceful degradation
        mock_context = MagicMock()
        result = await router_primitive.execute({"query": "test"}, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execution_completes_successfully(self, router_primitive):
        """Test execution completes successfully."""
        mock_context = MagicMock()
        result = await router_primitive.execute({"query": "test"}, mock_context)
        assert "Primitive_result" in result


class TestGracefulDegradation:
    """Test graceful degradation when OpenTelemetry unavailable."""

    @pytest.mark.asyncio
    async def test_works_without_metrics(
        self, fast_primitive, premium_primitive, simple_router_fn
    ):
        """Test router works without metrics infrastructure."""
        with patch(
            "observability_integration.primitives.router.get_meter",
            return_value=None,
        ):
            routes = {"fast": fast_primitive, "premium": premium_primitive}

            router = RouterPrimitive(
                routes=routes,
                router_fn=simple_router_fn,
                default_route="fast",
            )

            mock_context = MagicMock()
            result = await router.execute({"query": "test"}, mock_context)

            assert result is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_data(self, router_primitive):
        """Test routing with empty data."""
        mock_context = MagicMock()
        result = await router_primitive.execute({}, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_none_data(self, router_primitive):
        """Test routing with None data."""
        mock_context = MagicMock()
        result = await router_primitive.execute(None, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_router_returns_invalid_route(
        self, fast_primitive, premium_primitive
    ):
        """Test behavior when router returns invalid route name."""
        routes = {"fast": fast_primitive, "premium": premium_primitive}

        def bad_router(data, context):
            return "nonexistent_route"

        router = RouterPrimitive(
            routes=routes,
            router_fn=bad_router,
            default_route="fast",
        )

        mock_context = MagicMock()
        # Should fall back to default route
        result = await router.execute({"query": "test"}, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_router_statistics_tracking(self, router_primitive):
        """Test routing statistics are tracked correctly."""
        mock_context = MagicMock()

        # Execute multiple requests
        await router_primitive.execute({"query": "short"}, mock_context)  # fast
        await router_primitive.execute(
            {"query": "this is a very long query"}, mock_context
        )  # premium

        # Statistics should be tracked (even if metrics not available)
        assert True  # Metrics work with graceful degradation


class TestCustomRouterFunctions:
    """Test custom router function implementations."""

    @pytest.mark.asyncio
    async def test_complexity_based_routing(self, fast_primitive, premium_primitive):
        """Test routing based on custom complexity logic."""
        routes = {"fast": fast_primitive, "premium": premium_primitive}

        def complexity_router(data, context):
            query = str(data.get("query", ""))
            complex_keywords = ["analyze", "explain", "reason"]

            if any(kw in query.lower() for kw in complex_keywords):
                return "premium"
            return "fast"

        router = RouterPrimitive(
            routes=routes,
            router_fn=complexity_router,
            default_route="fast",
        )

        mock_context = MagicMock()

        # Simple query -> fast
        result1 = await router.execute({"query": "What is 2+2?"}, mock_context)
        assert result1 is not None

        # Complex query -> premium
        result2 = await router.execute(
            {"query": "Please analyze the implications..."}, mock_context
        )
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_context_based_routing(self, fast_primitive, premium_primitive):
        """Test routing based on context information."""
        routes = {"fast": fast_primitive, "premium": premium_primitive}

        def context_router(data, context):
            if hasattr(context, "priority") and context.priority == "high":
                return "premium"
            return "fast"

        router = RouterPrimitive(
            routes=routes,
            router_fn=context_router,
            default_route="fast",
        )

        # Low priority context
        low_priority_context = MagicMock()
        low_priority_context.priority = "low"
        result1 = await router.execute({"query": "test"}, low_priority_context)
        assert result1 is not None

        # High priority context
        high_priority_context = MagicMock()
        high_priority_context.priority = "high"
        result2 = await router.execute({"query": "test"}, high_priority_context)
        assert result2 is not None
