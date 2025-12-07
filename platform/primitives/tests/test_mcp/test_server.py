"""Tests for the TTA.dev MCP Server."""

import pytest

from tta_dev_primitives.mcp_server.server import MCP_AVAILABLE, create_server

# Skip all tests if MCP is not available
pytestmark = pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP package not installed")


class TestMCPServerCreation:
    """Tests for MCP server creation."""

    def test_create_server(self) -> None:
        """Verify server can be created."""
        server = create_server()
        assert server is not None

    def test_server_has_name(self) -> None:
        """Verify server has a name."""
        server = create_server()
        assert server.name == "TTA.dev Primitives"

    def test_server_has_tools(self) -> None:
        """Verify server has tools registered."""
        server = create_server()
        tools = server._tool_manager._tools
        assert len(tools) > 0

    def test_server_has_required_tools(self) -> None:
        """Verify server has all required tools."""
        server = create_server()
        tools = server._tool_manager._tools
        required_tools = [
            "analyze_code",
            "get_primitive_info",
            "list_primitives",
            "search_templates",
            "get_composition_example",
        ]
        for tool_name in required_tools:
            assert tool_name in tools, f"Missing tool: {tool_name}"


class TestAnalyzeCodeTool:
    """Tests for the analyze_code MCP tool."""

    @pytest.fixture
    def analyze_tool(self):
        """Get the analyze_code tool."""
        server = create_server()
        return server._tool_manager._tools["analyze_code"]

    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self, analyze_tool) -> None:
        """Verify analyze_code returns a dict."""
        result = await analyze_tool.fn(code="def test(): pass")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_has_analysis_key(self, analyze_tool) -> None:
        """Verify result has analysis key."""
        result = await analyze_tool.fn(code="def test(): pass")
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_has_recommendations_key(self, analyze_tool) -> None:
        """Verify result has recommendations key."""
        result = await analyze_tool.fn(code="def test(): pass")
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_analyze_detects_async_patterns(self, analyze_tool) -> None:
        """Verify async patterns are detected."""
        code = """
async def fetch():
    return await client.get('/api')
"""
        result = await analyze_tool.fn(code=code)
        assert "async_operations" in result["analysis"]["detected_patterns"]

    @pytest.mark.asyncio
    async def test_analyze_detects_error_handling(self, analyze_tool) -> None:
        """Verify error handling patterns are detected."""
        code = """
def risky():
    try:
        return do_something()
    except Exception:
        return None
"""
        result = await analyze_tool.fn(code=code)
        assert "error_handling" in result["analysis"]["detected_patterns"]

    @pytest.mark.asyncio
    async def test_analyze_with_file_path(self, analyze_tool) -> None:
        """Verify file_path parameter works."""
        result = await analyze_tool.fn(
            code="def test(): pass", file_path="api_client.py"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_project_type(self, analyze_tool) -> None:
        """Verify project_type parameter works."""
        result = await analyze_tool.fn(code="def test(): pass", project_type="web")
        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_min_confidence(self, analyze_tool) -> None:
        """Verify min_confidence parameter works."""
        code = """
async def fetch():
    try:
        return await api.call()
    except:
        pass
"""
        low_result = await analyze_tool.fn(code=code, min_confidence=0.1)
        high_result = await analyze_tool.fn(code=code, min_confidence=0.9)
        assert len(low_result["recommendations"]) >= len(high_result["recommendations"])


class TestGetPrimitiveInfoTool:
    """Tests for the get_primitive_info MCP tool."""

    @pytest.fixture
    def info_tool(self):
        """Get the get_primitive_info tool."""
        server = create_server()
        return server._tool_manager._tools["get_primitive_info"]

    @pytest.mark.asyncio
    async def test_get_info_returns_dict(self, info_tool) -> None:
        """Verify get_primitive_info returns a dict."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_info_has_name(self, info_tool) -> None:
        """Verify result has name."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert "name" in result
        assert result["name"] == "RetryPrimitive"

    @pytest.mark.asyncio
    async def test_get_info_has_description(self, info_tool) -> None:
        """Verify result has description."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert "description" in result
        assert len(result["description"]) > 0

    @pytest.mark.asyncio
    async def test_get_info_has_import_path(self, info_tool) -> None:
        """Verify result has import_path."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert "import_path" in result
        assert "from tta_dev_primitives" in result["import_path"]

    @pytest.mark.asyncio
    async def test_get_info_has_use_cases(self, info_tool) -> None:
        """Verify result has use_cases."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert "use_cases" in result
        assert isinstance(result["use_cases"], list)

    @pytest.mark.asyncio
    async def test_get_info_retry_primitive(self, info_tool) -> None:
        """Verify RetryPrimitive info."""
        result = await info_tool.fn(primitive_name="RetryPrimitive")
        assert "retry" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_get_info_timeout_primitive(self, info_tool) -> None:
        """Verify TimeoutPrimitive info."""
        result = await info_tool.fn(primitive_name="TimeoutPrimitive")
        assert "timeout" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_get_info_cache_primitive(self, info_tool) -> None:
        """Verify CachePrimitive info."""
        result = await info_tool.fn(primitive_name="CachePrimitive")
        assert "cache" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_get_info_unknown_primitive(self, info_tool) -> None:
        """Verify unknown primitive returns error."""
        result = await info_tool.fn(primitive_name="UnknownPrimitive")
        assert "error" in result or result.get("name") == "UnknownPrimitive"


class TestListPrimitivesTool:
    """Tests for the list_primitives MCP tool."""

    @pytest.fixture
    def list_tool(self):
        """Get the list_primitives tool."""
        server = create_server()
        return server._tool_manager._tools["list_primitives"]

    @pytest.mark.asyncio
    async def test_list_returns_list(self, list_tool) -> None:
        """Verify list_primitives returns a list."""
        result = await list_tool.fn()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_has_primitives(self, list_tool) -> None:
        """Verify list has primitives."""
        result = await list_tool.fn()
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_list_includes_retry(self, list_tool) -> None:
        """Verify list includes RetryPrimitive."""
        result = await list_tool.fn()
        names = [p["name"] for p in result]
        assert "RetryPrimitive" in names

    @pytest.mark.asyncio
    async def test_list_includes_timeout(self, list_tool) -> None:
        """Verify list includes TimeoutPrimitive."""
        result = await list_tool.fn()
        names = [p["name"] for p in result]
        assert "TimeoutPrimitive" in names

    @pytest.mark.asyncio
    async def test_list_includes_cache(self, list_tool) -> None:
        """Verify list includes CachePrimitive."""
        result = await list_tool.fn()
        names = [p["name"] for p in result]
        assert "CachePrimitive" in names

    @pytest.mark.asyncio
    async def test_list_items_have_required_fields(self, list_tool) -> None:
        """Verify list items have required fields."""
        result = await list_tool.fn()
        for item in result:
            assert "name" in item
            assert "description" in item


class TestSearchTemplatesTool:
    """Tests for the search_templates MCP tool."""

    @pytest.fixture
    def search_tool(self):
        """Get the search_templates tool."""
        server = create_server()
        return server._tool_manager._tools["search_templates"]

    @pytest.mark.asyncio
    async def test_search_returns_list(self, search_tool) -> None:
        """Verify search_templates returns a list."""
        result = await search_tool.fn(query="retry")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_finds_retry(self, search_tool) -> None:
        """Verify search finds retry-related templates."""
        result = await search_tool.fn(query="retry")
        # Should find at least RetryPrimitive
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_finds_timeout(self, search_tool) -> None:
        """Verify search finds timeout-related templates."""
        result = await search_tool.fn(query="timeout")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_finds_cache(self, search_tool) -> None:
        """Verify search finds cache-related templates."""
        result = await search_tool.fn(query="cache")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_tool) -> None:
        """Verify search handles empty query."""
        result = await search_tool.fn(query="")
        assert isinstance(result, list)


class TestGetCompositionExampleTool:
    """Tests for the get_composition_example MCP tool."""

    @pytest.fixture
    def compose_tool(self):
        """Get the get_composition_example tool."""
        server = create_server()
        return server._tool_manager._tools["get_composition_example"]

    @pytest.mark.asyncio
    async def test_compose_returns_dict(self, compose_tool) -> None:
        """Verify get_composition_example returns a dict."""
        result = await compose_tool.fn(
            primitives=["RetryPrimitive", "TimeoutPrimitive"]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_compose_has_code(self, compose_tool) -> None:
        """Verify result has code."""
        result = await compose_tool.fn(
            primitives=["RetryPrimitive", "TimeoutPrimitive"]
        )
        assert "code" in result
        assert len(result["code"]) > 0

    @pytest.mark.asyncio
    async def test_compose_has_explanation(self, compose_tool) -> None:
        """Verify result has explanation."""
        result = await compose_tool.fn(
            primitives=["RetryPrimitive", "TimeoutPrimitive"]
        )
        assert "explanation" in result

    @pytest.mark.asyncio
    async def test_compose_code_has_imports(self, compose_tool) -> None:
        """Verify generated code has imports."""
        result = await compose_tool.fn(primitives=["RetryPrimitive", "CachePrimitive"])
        assert "from tta_dev_primitives" in result["code"]

    @pytest.mark.asyncio
    async def test_compose_single_primitive(self, compose_tool) -> None:
        """Verify composition works with single primitive."""
        result = await compose_tool.fn(primitives=["RetryPrimitive"])
        assert "code" in result

    @pytest.mark.asyncio
    async def test_compose_three_primitives(self, compose_tool) -> None:
        """Verify composition works with three primitives."""
        result = await compose_tool.fn(
            primitives=["CachePrimitive", "RetryPrimitive", "TimeoutPrimitive"]
        )
        assert "code" in result


class TestMCPToolIntegration:
    """Integration tests for MCP tools working together."""

    @pytest.mark.asyncio
    async def test_analyze_then_get_info(self) -> None:
        """Verify workflow: analyze -> get_info."""
        server = create_server()
        tools = server._tool_manager._tools

        # Analyze code
        code = """
async def fetch():
    for i in range(3):
        try:
            return await api.call()
        except:
            await asyncio.sleep(i)
"""
        analyze_result = await tools["analyze_code"].fn(code=code)
        assert len(analyze_result["recommendations"]) > 0

        # Get info for top recommendation
        top_primitive = analyze_result["recommendations"][0]["primitive_name"]
        info_result = await tools["get_primitive_info"].fn(primitive_name=top_primitive)
        assert info_result["name"] == top_primitive

    @pytest.mark.asyncio
    async def test_list_then_get_info(self) -> None:
        """Verify workflow: list -> get_info."""
        server = create_server()
        tools = server._tool_manager._tools

        # List primitives
        list_result = await tools["list_primitives"].fn()
        assert len(list_result) > 0

        # Get info for first primitive
        first_primitive = list_result[0]["name"]
        info_result = await tools["get_primitive_info"].fn(
            primitive_name=first_primitive
        )
        assert info_result["name"] == first_primitive

    @pytest.mark.asyncio
    async def test_analyze_then_compose(self) -> None:
        """Verify workflow: analyze -> compose."""
        server = create_server()
        tools = server._tool_manager._tools

        # Analyze code
        code = """
async def fetch():
    try:
        return await asyncio.wait_for(api.call(), timeout=30)
    except:
        return await fallback()
"""
        analyze_result = await tools["analyze_code"].fn(code=code)

        # Get top 2 recommendations
        primitives = [
            r["primitive_name"] for r in analyze_result["recommendations"][:2]
        ]
        if len(primitives) >= 2:
            # Compose them
            compose_result = await tools["get_composition_example"].fn(
                primitives=primitives
            )
            assert "code" in compose_result


class TestTransformCodeTool:
    """Tests for the transform_code MCP tool."""

    @pytest.fixture
    def transform_tool(self):
        """Get the transform_code tool."""
        server = create_server()
        return server._tool_manager._tools["transform_code"]

    @pytest.mark.asyncio
    async def test_transform_returns_dict(self, transform_tool) -> None:
        """Verify transform_code returns a dict."""
        code = """
import httpx

async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
"""
        result = await transform_tool.fn(code=code, primitive="RetryPrimitive")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_transform_has_transformed_code(self, transform_tool) -> None:
        """Verify transform result has transformed code."""
        code = """
import httpx

async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
"""
        result = await transform_tool.fn(code=code, primitive="RetryPrimitive")
        assert "transformed_code" in result
        assert "RetryPrimitive" in result["transformed_code"]

    @pytest.mark.asyncio
    async def test_transform_has_diff(self, transform_tool) -> None:
        """Verify transform result has diff."""
        code = """
import httpx

async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
"""
        result = await transform_tool.fn(code=code, primitive="RetryPrimitive")
        assert "diff" in result
        assert "+" in result["diff"]  # Diff should show additions

    @pytest.mark.asyncio
    async def test_transform_unknown_primitive(self, transform_tool) -> None:
        """Verify transform handles unknown primitive."""
        result = await transform_tool.fn(
            code="def test(): pass", primitive="UnknownPrimitive"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_transform_specific_function(self, transform_tool) -> None:
        """Verify transform can target specific function."""
        code = """
async def fetch_user(): pass
async def fetch_orders(): pass
"""
        result = await transform_tool.fn(
            code=code, primitive="TimeoutPrimitive", function_name="fetch_user"
        )
        assert "wrapped_functions" in result
        # Should only wrap specified function
        assert "fetch_user" in result.get("wrapped_functions", [])


class TestAnalyzeAndFixTool:
    """Tests for the analyze_and_fix MCP tool."""

    @pytest.fixture
    def analyze_fix_tool(self):
        """Get the analyze_and_fix tool."""
        server = create_server()
        return server._tool_manager._tools["analyze_and_fix"]

    @pytest.mark.asyncio
    async def test_analyze_fix_returns_dict(self, analyze_fix_tool) -> None:
        """Verify analyze_and_fix returns a dict."""
        code = """
import httpx

async def fetch_api(url: str):
    return await httpx.get(url)
"""
        result = await analyze_fix_tool.fn(code=code)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_fix_has_analysis(self, analyze_fix_tool) -> None:
        """Verify result has analysis."""
        code = """
async def fetch_api(): pass
"""
        result = await analyze_fix_tool.fn(code=code)
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_fix_applies_specific_primitive(
        self, analyze_fix_tool
    ) -> None:
        """Verify can apply specific primitive."""
        code = """
import httpx

async def fetch_data(url: str):
    return await httpx.get(url)
"""
        result = await analyze_fix_tool.fn(code=code, primitive="CachePrimitive")
        if result.get("transformation"):
            assert "CachePrimitive" in result["transformation"]["code"]


class TestSuggestFixesTool:
    """Tests for the suggest_fixes MCP tool."""

    @pytest.fixture
    def suggest_tool(self):
        """Get the suggest_fixes tool."""
        server = create_server()
        return server._tool_manager._tools["suggest_fixes"]

    @pytest.mark.asyncio
    async def test_suggest_returns_dict(self, suggest_tool) -> None:
        """Verify suggest_fixes returns a dict."""
        code = """
import httpx

async def fetch_api():
    return await httpx.get("https://api.example.com")
"""
        result = await suggest_tool.fn(code=code)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_suggest_has_issues(self, suggest_tool) -> None:
        """Verify result has issues list."""
        code = """
async def test(): pass
"""
        result = await suggest_tool.fn(code=code)
        assert "issues" in result
        assert isinstance(result["issues"], list)

    @pytest.mark.asyncio
    async def test_suggest_has_opportunities(self, suggest_tool) -> None:
        """Verify result has opportunities list."""
        code = """
async def test(): pass
"""
        result = await suggest_tool.fn(code=code)
        assert "opportunities" in result
        assert isinstance(result["opportunities"], list)

    @pytest.mark.asyncio
    async def test_suggest_has_top_fixes(self, suggest_tool) -> None:
        """Verify result has top_fixes list."""
        code = """
import httpx

async def fetch():
    return await httpx.get("url")
"""
        result = await suggest_tool.fn(code=code)
        assert "top_fixes" in result
        assert isinstance(result["top_fixes"], list)

    @pytest.mark.asyncio
    async def test_suggest_respects_max_suggestions(self, suggest_tool) -> None:
        """Verify max_suggestions is respected."""
        code = """
import httpx

async def fetch():
    try:
        return await httpx.get("url")
    except:
        pass
"""
        result = await suggest_tool.fn(code=code, max_suggestions=2)
        assert len(result["top_fixes"]) <= 2


class TestDetectAntiPatternsTool:
    """Tests for the detect_anti_patterns MCP tool."""

    @pytest.fixture
    def detect_tool(self):
        """Get the detect_anti_patterns tool."""
        server = create_server()
        return server._tool_manager._tools["detect_anti_patterns"]

    @pytest.mark.asyncio
    async def test_detect_returns_dict(self, detect_tool) -> None:
        """Verify detect_anti_patterns returns a dict."""
        code = """
async def fetch_data():
    for attempt in range(3):
        try:
            return await httpx.get("url")
        except:
            pass
"""
        result = await detect_tool.fn(code=code)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_detect_has_total_issues(self, detect_tool) -> None:
        """Verify result has total_issues count."""
        code = """
async def fetch_data():
    for attempt in range(3):
        try:
            return await httpx.get("url")
        except:
            pass
"""
        result = await detect_tool.fn(code=code)
        assert "total_issues" in result
        assert isinstance(result["total_issues"], int)

    @pytest.mark.asyncio
    async def test_detect_has_primitives_needed(self, detect_tool) -> None:
        """Verify result has primitives_needed list."""
        code = """
async def fetch_data():
    for attempt in range(3):
        try:
            return await httpx.get("url")
        except:
            pass
"""
        result = await detect_tool.fn(code=code)
        assert "primitives_needed" in result
        assert isinstance(result["primitives_needed"], list)

    @pytest.mark.asyncio
    async def test_detect_finds_manual_retry(self, detect_tool) -> None:
        """Verify detects manual retry pattern."""
        code = """
async def fetch_data():
    for attempt in range(3):
        try:
            return await httpx.get("url")
        except:
            if attempt == 2:
                raise
"""
        result = await detect_tool.fn(code=code)
        assert result["total_issues"] > 0
        assert "RetryPrimitive" in result["primitives_needed"]

    @pytest.mark.asyncio
    async def test_detect_finds_manual_timeout(self, detect_tool) -> None:
        """Verify detects manual timeout pattern."""
        code = """
import asyncio

async def fetch_with_timeout():
    result = await asyncio.wait_for(api_call(), timeout=30)
    return result
"""
        result = await detect_tool.fn(code=code)
        assert result["total_issues"] > 0
        assert "TimeoutPrimitive" in result["primitives_needed"]

    @pytest.mark.asyncio
    async def test_detect_finds_manual_fallback(self, detect_tool) -> None:
        """Verify detects manual fallback pattern."""
        code = """
async def get_value():
    result = maybe_none() or default_value
    if result is None:
        result = fallback_value
    return result
"""
        result = await detect_tool.fn(code=code)
        assert result["total_issues"] > 0
        assert "FallbackPrimitive" in result["primitives_needed"]

    @pytest.mark.asyncio
    async def test_detect_clean_code_returns_no_issues(self, detect_tool) -> None:
        """Verify clean code returns no issues."""
        code = """
def simple_function():
    return 42
"""
        result = await detect_tool.fn(code=code)
        assert result["total_issues"] == 0
        assert len(result["primitives_needed"]) == 0


class TestMCPResources:
    """Tests for MCP resources."""

    def test_catalog_resource_exists(self) -> None:
        """Verify catalog resource is registered."""
        server = create_server()
        resources = server._resource_manager._resources
        assert "tta://catalog" in resources

    def test_patterns_resource_exists(self) -> None:
        """Verify patterns resource is registered."""
        server = create_server()
        resources = server._resource_manager._resources
        assert "tta://patterns" in resources

    @pytest.mark.asyncio
    async def test_catalog_resource_content(self) -> None:
        """Verify catalog resource returns valid content."""
        server = create_server()
        resources = server._resource_manager._resources
        catalog_fn = resources["tta://catalog"].fn
        content = catalog_fn()
        assert "# TTA.dev Primitives Catalog" in content
        assert "RetryPrimitive" in content
        assert "Import:" in content

    @pytest.mark.asyncio
    async def test_patterns_resource_content(self) -> None:
        """Verify patterns resource returns valid content."""
        server = create_server()
        resources = server._resource_manager._resources
        patterns_fn = resources["tta://patterns"].fn
        content = patterns_fn()
        assert "# Detectable Code Patterns" in content
        assert "Total patterns:" in content


class TestMCPPrompts:
    """Tests for MCP prompts."""

    def test_analyze_prompt_exists(self) -> None:
        """Verify analyze_and_improve prompt is registered."""
        server = create_server()
        prompts = server._prompt_manager._prompts
        assert "analyze_and_improve" in prompts

    def test_analyze_prompt_content(self) -> None:
        """Verify analyze_and_improve prompt generates correct content."""
        server = create_server()
        prompts = server._prompt_manager._prompts
        prompt_fn = prompts["analyze_and_improve"].fn

        code = "async def test(): pass"
        result = prompt_fn(code=code, goal="performance")

        assert "Goal: performance" in result
        assert "async def test(): pass" in result
        assert "TTA.dev primitive improvements" in result

    def test_analyze_prompt_default_goal(self) -> None:
        """Verify analyze_and_improve prompt has default goal."""
        server = create_server()
        prompts = server._prompt_manager._prompts
        prompt_fn = prompts["analyze_and_improve"].fn

        code = "def test(): pass"
        result = prompt_fn(code=code)

        assert "Goal: reliability" in result


class TestRunServer:
    """Tests for server run functions."""

    def test_run_server_without_mcp(self, monkeypatch) -> None:
        """Verify run_server handles missing MCP package."""
        import sys
        from io import StringIO

        from tta_dev_primitives.mcp_server import server as server_module

        # Temporarily set MCP_AVAILABLE to False
        monkeypatch.setattr(server_module, "MCP_AVAILABLE", False)

        # Capture stderr and expect SystemExit
        captured = StringIO()
        monkeypatch.setattr(sys, "stderr", captured)

        with pytest.raises(SystemExit) as exc_info:
            server_module.run_server()

        assert exc_info.value.code == 1
        assert "MCP package not installed" in captured.getvalue()

    def test_run_server_unknown_transport(self, monkeypatch) -> None:
        """Verify run_server handles unknown transport."""
        import sys
        from io import StringIO

        from tta_dev_primitives.mcp_server import server as server_module

        # Ensure MCP is available
        monkeypatch.setattr(server_module, "MCP_AVAILABLE", True)

        # Mock create_server to avoid actually running
        mock_server = type("MockServer", (), {"run": lambda self, **kwargs: None})()
        monkeypatch.setattr(server_module, "create_server", lambda: mock_server)

        # Capture stderr
        captured = StringIO()
        monkeypatch.setattr(sys, "stderr", captured)

        with pytest.raises(SystemExit) as exc_info:
            server_module.run_server(transport="invalid")

        assert exc_info.value.code == 1
        assert "Unknown transport: invalid" in captured.getvalue()

    def test_main_parses_args(self, monkeypatch) -> None:
        """Verify main() parses command line arguments."""
        import sys

        from tta_dev_primitives.mcp_server import server as server_module

        # Track what run_server was called with
        called_with = {}

        def mock_run_server(transport="stdio", port=8000):
            called_with["transport"] = transport
            called_with["port"] = port

        monkeypatch.setattr(server_module, "run_server", mock_run_server)
        monkeypatch.setattr(
            sys, "argv", ["tta-dev-mcp", "--transport", "sse", "--port", "9000"]
        )

        server_module.main()

        assert called_with["transport"] == "sse"
        assert called_with["port"] == 9000

    def test_main_default_args(self, monkeypatch) -> None:
        """Verify main() uses default arguments."""
        import sys

        from tta_dev_primitives.mcp_server import server as server_module

        called_with = {}

        def mock_run_server(transport="stdio", port=8000):
            called_with["transport"] = transport
            called_with["port"] = port

        monkeypatch.setattr(server_module, "run_server", mock_run_server)
        monkeypatch.setattr(sys, "argv", ["tta-dev-mcp"])

        server_module.main()

        assert called_with["transport"] == "stdio"
        assert called_with["port"] == 8000
