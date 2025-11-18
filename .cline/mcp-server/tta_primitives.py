#!/usr/bin/env python3
"""
TTA.dev MCP Server - All Primitives as Tools

This MCP server exposes all TTA.dev primitives as direct MCP tools that Cline can use.
It provides programmatic access to the complete TTA.dev primitive ecosystem.

Tools Provided:
- All core workflow primitives (Sequential, Parallel, Router, etc.)
- Recovery primitives (Retry, Fallback, Timeout)
- Performance primitives (Cache)
- Context and memory management
- Orchestration and workflow coordination
"""

import asyncio
import json
import os
import sys
from typing import Any

# Add the packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../packages"))

try:
    # MCP server imports
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    # TTA.dev imports
    from tta_dev_primitives import (
        ParallelPrimitive,
        SequentialPrimitive,
        WorkflowContext,
    )
    from tta_dev_primitives.core.conditional import ConditionalPrimitive
    from tta_dev_primitives.core.routing import RouterPrimitive
    from tta_dev_primitives.performance import CachePrimitive
    from tta_dev_primitives.recovery import (
        CompensationPrimitive,
        FallbackPrimitive,
        RetryPrimitive,
        TimeoutPrimitive,
    )
    from tta_dev_primitives.testing import MockPrimitive

except ImportError as e:
    print(f"Import error: {e}")
    print("This MCP server requires TTA.dev primitives to be installed")
    sys.exit(1)


class TTAPrimitivesMCPServer:
    """MCP server providing all TTA.dev primitives as tools"""

    def __init__(self):
        self.active_contexts: dict[str, WorkflowContext] = {}
        self.active_workflows: dict[str, Any] = {}
        self.primitive_instances: dict[str, Any] = {}

    def _create_tool_definition(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> types.Tool:
        """Create a standardized tool definition"""
        return types.Tool(name=name, description=description, inputSchema=input_schema)

    def _get_workflow_context(self, workflow_id: str) -> WorkflowContext:
        """Get or create a workflow context"""
        if workflow_id not in self.active_contexts:
            self.active_contexts[workflow_id] = WorkflowContext(
                correlation_id=workflow_id,
                data={"created_by": "cline_mcp", "mcp_session": True},
            )
        return self.active_contexts[workflow_id]

    async def _execute_primitive_async(
        self, primitive: Any, input_data: Any, context: WorkflowContext
    ) -> Any:
        """Execute a primitive asynchronously"""
        try:
            if hasattr(primitive, "execute"):
                return await primitive.execute(context, input_data)
            else:
                # Synchronous execution in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, primitive.execute, context, input_data
                )
        except Exception as e:
            return {"error": str(e), "error_type": type(e).__name__}

    def get_available_tools(self) -> list[types.Tool]:
        """Get all available TTA.dev primitive tools"""

        core_tools = [
            # Context Management Tools
            self._create_tool_definition(
                "create_workflow_context",
                "Create a new workflow context for tracking execution",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Unique workflow identifier",
                        },
                        "initial_data": {
                            "type": "object",
                            "description": "Initial context data",
                        },
                    },
                    "required": ["workflow_id"],
                },
            ),
            # Core Workflow Primitives
            self._create_tool_definition(
                "sequential_execute",
                "Execute multiple steps in sequence using SequentialPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "steps": {
                            "type": "array",
                            "description": "Array of functions/primitives to execute sequentially",
                            "items": {"type": "object"},
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for the workflow",
                        },
                    },
                    "required": ["workflow_id", "steps"],
                },
            ),
            self._create_tool_definition(
                "parallel_execute",
                "Execute multiple steps in parallel using ParallelPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "parallel_steps": {
                            "type": "array",
                            "description": "Array of functions to execute in parallel",
                            "items": {"type": "object"},
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for parallel execution",
                        },
                    },
                    "required": ["workflow_id", "parallel_steps"],
                },
            ),
            self._create_tool_definition(
                "conditional_execute",
                "Execute conditionally based on input data using ConditionalPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "condition": {
                            "type": "object",
                            "description": "Condition function to evaluate",
                        },
                        "true_branch": {
                            "type": "object",
                            "description": "Function to execute if condition is true",
                        },
                        "false_branch": {
                            "type": "object",
                            "description": "Function to execute if condition is false",
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for conditional execution",
                        },
                    },
                    "required": [
                        "workflow_id",
                        "condition",
                        "true_branch",
                        "false_branch",
                    ],
                },
            ),
            self._create_tool_definition(
                "router_execute",
                "Route execution to different primitives based on conditions",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "routes": {
                            "type": "object",
                            "description": "Route mapping: route_name -> primitive/function",
                            "pattern": ".*",
                        },
                        "routing_function": {
                            "type": "string",
                            "description": "JavaScript-like routing function (eval'd)",
                            "example": "data => data.priority > 5 ? 'high_priority' : 'normal'",
                        },
                        "default_route": {
                            "type": "string",
                            "description": "Default route if no match",
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for routing",
                        },
                    },
                    "required": ["workflow_id", "routes", "routing_function"],
                },
            ),
            # Recovery Primitives
            self._create_tool_definition(
                "retry_execute",
                "Execute with automatic retry using RetryPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "target_function": {
                            "type": "object",
                            "description": "Function/primitive to retry",
                        },
                        "max_retries": {
                            "type": "integer",
                            "default": 3,
                            "description": "Maximum retry attempts",
                        },
                        "backoff_strategy": {
                            "type": "string",
                            "enum": ["fixed", "linear", "exponential"],
                            "default": "exponential",
                            "description": "Backoff strategy between retries",
                        },
                        "initial_delay": {
                            "type": "number",
                            "default": 1.0,
                            "description": "Initial delay in seconds",
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for the retried function",
                        },
                    },
                    "required": ["workflow_id", "target_function"],
                },
            ),
            self._create_tool_definition(
                "fallback_execute",
                "Execute with fallback strategy using FallbackPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "primary_function": {
                            "type": "object",
                            "description": "Primary function to try",
                        },
                        "fallback_functions": {
                            "type": "array",
                            "description": "Array of fallback functions",
                            "items": {"type": "object"},
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for execution",
                        },
                    },
                    "required": [
                        "workflow_id",
                        "primary_function",
                        "fallback_functions",
                    ],
                },
            ),
            self._create_tool_definition(
                "timeout_execute",
                "Execute with timeout protection using TimeoutPrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "target_function": {
                            "type": "object",
                            "description": "Function with timeout protection",
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "default": 30.0,
                            "description": "Timeout in seconds",
                        },
                        "fallback_function": {
                            "type": "object",
                            "description": "Fallback if timeout occurs",
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for execution",
                        },
                    },
                    "required": ["workflow_id", "target_function"],
                },
            ),
            # Performance Primitives
            self._create_tool_definition(
                "cache_execute",
                "Execute with caching using CachePrimitive",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "target_function": {
                            "type": "object",
                            "description": "Function to cache",
                        },
                        "ttl_seconds": {
                            "type": "integer",
                            "default": 3600,
                            "description": "Cache TTL in seconds",
                        },
                        "max_size": {
                            "type": "integer",
                            "default": 1000,
                            "description": "Maximum cache size",
                        },
                        "cache_key_function": {
                            "type": "object",
                            "description": "Function to generate cache keys",
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input data for cached execution",
                        },
                    },
                    "required": ["workflow_id", "target_function"],
                },
            ),
            # Testing Primitives
            self._create_tool_definition(
                "mock_create",
                "Create a mock primitive for testing",
                {
                    "type": "object",
                    "properties": {
                        "mock_id": {
                            "type": "string",
                            "description": "Unique ID for the mock",
                        },
                        "return_value": {
                            "type": "any",
                            "description": "Value to return",
                        },
                        "side_effect": {
                            "type": "any",
                            "description": "Exception or callable to raise",
                        },
                        "call_count": {
                            "type": "integer",
                            "default": 0,
                            "description": "Track call count",
                        },
                    },
                    "required": ["mock_id"],
                },
            ),
            # Context and Memory Tools
            self._create_tool_definition(
                "context_get",
                "Get current workflow context data",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        }
                    },
                    "required": ["workflow_id"],
                },
            ),
            self._create_tool_definition(
                "context_update",
                "Update workflow context data",
                {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow context ID",
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to add/update in context",
                        },
                    },
                    "required": ["workflow_id", "data"],
                },
            ),
            # Memory and Pattern Tools
            self._create_tool_definition(
                "memory_find_patterns",
                "Find similar patterns in memory for current task",
                {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "Description of current task",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 5,
                            "description": "Maximum patterns to return",
                        },
                    },
                    "required": ["task_description"],
                },
            ),
            self._create_tool_definition(
                "memory_record_usage",
                "Record usage of a pattern for learning",
                {
                    "type": "object",
                    "properties": {
                        "pattern_id": {
                            "type": "string",
                            "description": "Pattern that was used",
                        },
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow session ID",
                        },
                        "success": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether usage succeeded",
                        },
                        "feedback": {
                            "type": "string",
                            "description": "User feedback on the pattern",
                        },
                    },
                    "required": ["pattern_id", "workflow_id"],
                },
            ),
            # Orchestration Tools
            self._create_tool_definition(
                "orchestrate_workflow",
                "Execute a complex orchestrated workflow with multiple primitives",
                {
                    "type": "object",
                    "properties": {
                        "workflow_spec": {
                            "type": "object",
                            "description": "Complete workflow specification",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "stages": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": [
                                                    "sequential",
                                                    "parallel",
                                                    "retry",
                                                    "cache",
                                                ],
                                            },
                                            "steps": {"type": "array"},
                                        },
                                    },
                                },
                            },
                        },
                        "input_data": {
                            "type": "any",
                            "description": "Input for the workflow",
                        },
                    },
                    "required": ["workflow_spec"],
                },
            ),
            # Analysis and Diagnostics
            self._create_tool_definition(
                "diagnostics_context",
                "Get context analysis for current state",
                {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "Current task context",
                        },
                        "max_files": {
                            "type": "integer",
                            "default": 5,
                            "description": "Max files to analyze",
                        },
                    },
                    "required": ["task_description"],
                },
            ),
            self._create_tool_definition(
                "diagnostics_architecture",
                "Analyze system architecture relationships",
                {"type": "object", "properties": {}, "required": []},
            ),
            self._create_tool_definition(
                "diagnostics_performance",
                "Get performance metrics for primitives",
                {"type": "object", "properties": {}, "required": []},
            ),
        ]

        return core_tools


# MCP Server Implementation
app = Server("tta-dev-primitives")
tta_server = TTAPrimitivesMCPServer()


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available TTA.dev primitive tools"""
    return tta_server.get_available_tools()


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool execution calls"""

    try:
        # Context Management Tools
        if name == "create_workflow_context":
            workflow_id = arguments["workflow_id"]
            initial_data = arguments.get("initial_data", {})

            context = tta_server._get_workflow_context(workflow_id)
            if initial_data:
                context.data.update(initial_data)

            result = {
                "workflow_id": workflow_id,
                "context_created": True,
                "correlation_id": context.correlation_id,
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "context_get":
            workflow_id = arguments["workflow_id"]
            context = tta_server._get_workflow_context(workflow_id)

            result = {
                "workflow_id": workflow_id,
                "correlation_id": context.correlation_id,
                "data": context.data,
                "created_at": context.created_at.isoformat()
                if hasattr(context, "created_at")
                else None,
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "context_update":
            workflow_id = arguments["workflow_id"]
            new_data = arguments["data"]

            context = tta_server._get_workflow_context(workflow_id)
            context.data.update(new_data)

            result = {"workflow_id": workflow_id, "updated": True, "new_data": new_data}
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Core Workflow Primitives
        elif name == "sequential_execute":
            workflow_id = arguments["workflow_id"]
            steps = arguments["steps"]
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            # Create SequentialPrimitive with the steps
            sequential = SequentialPrimitive(steps)
            result = await tta_server._execute_primitive_async(
                sequential, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "SequentialPrimitive",
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "parallel_execute":
            workflow_id = arguments["workflow_id"]
            parallel_steps = arguments["parallel_steps"]
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            parallel = ParallelPrimitive(parallel_steps)
            result = await tta_server._execute_primitive_async(
                parallel, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "ParallelPrimitive",
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "conditional_execute":
            workflow_id = arguments["workflow_id"]
            condition = arguments["condition"]
            true_branch = arguments["true_branch"]
            false_branch = arguments["false_branch"]
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            conditional = ConditionalPrimitive(
                condition=condition,
                true_branch=true_branch,
                false_branch=false_branch,
            )
            result = await tta_server._execute_primitive_async(
                conditional, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "ConditionalPrimitive",
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "router_execute":
            workflow_id = arguments["workflow_id"]
            routes = arguments["routes"]
            routing_function = arguments["routing_function"]
            default_route = arguments.get("default_route")
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            # Note: Simplified routing - in practice would need to safely eval routing function
            router = RouterPrimitive(routes=routes, default_route=default_route)
            result = await tta_server._execute_primitive_async(
                router, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "RouterPrimitive",
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        # Recovery Primitives
        elif name == "retry_execute":
            workflow_id = arguments["workflow_id"]
            target_function = arguments["target_function"]
            max_retries = arguments.get("max_retries", 3)
            backoff_strategy = arguments.get("backoff_strategy", "exponential")
            initial_delay = arguments.get("initial_delay", 1.0)
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            retry = RetryPrimitive(
                primitive=target_function,
                max_retries=max_retries,
                backoff_strategy=backoff_strategy,
                initial_delay=initial_delay,
            )
            result = await tta_server._execute_primitive_async(
                retry, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "RetryPrimitive",
                            "max_retries": max_retries,
                            "backoff_strategy": backoff_strategy,
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "fallback_execute":
            workflow_id = arguments["workflow_id"]
            primary_function = arguments["primary_function"]
            fallback_functions = arguments["fallback_functions"]
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            fallback = FallbackPrimitive(
                primary=primary_function, fallbacks=fallback_functions
            )
            result = await tta_server._execute_primitive_async(
                fallback, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "FallbackPrimitive",
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "timeout_execute":
            workflow_id = arguments["workflow_id"]
            target_function = arguments["target_function"]
            timeout_seconds = arguments.get("timeout_seconds", 30.0)
            fallback_function = arguments.get("fallback_function")
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            timeout = TimeoutPrimitive(
                primitive=target_function,
                timeout_seconds=timeout_seconds,
                fallback=fallback_function,
            )
            result = await tta_server._execute_primitive_async(
                timeout, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "TimeoutPrimitive",
                            "timeout_seconds": timeout_seconds,
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        # Performance Primitives
        elif name == "cache_execute":
            workflow_id = arguments["workflow_id"]
            target_function = arguments["target_function"]
            ttl_seconds = arguments.get("ttl_seconds", 3600)
            max_size = arguments.get("max_size", 1000)
            cache_key_function = arguments.get("cache_key_function")
            input_data = arguments.get("input_data")

            context = tta_server._get_workflow_context(workflow_id)

            cache = CachePrimitive(
                primitive=target_function,
                ttl_seconds=ttl_seconds,
                max_size=max_size,
                key_fn=cache_key_function,
            )
            result = await tta_server._execute_primitive_async(
                cache, input_data, context
            )

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "primitive": "CachePrimitive",
                            "ttl_seconds": ttl_seconds,
                            "max_size": max_size,
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        # Testing Tools
        elif name == "mock_create":
            mock_id = arguments["mock_id"]
            return_value = arguments.get("return_value")
            side_effect = arguments.get("side_effect")
            call_count = arguments.get("call_count", 0)

            # Create and store mock
            mock = MockPrimitive(return_value=return_value, side_effect=side_effect)
            mock.call_count = call_count

            tta_server.primitive_instances[mock_id] = mock

            result = {
                "mock_id": mock_id,
                "mock_created": True,
                "return_value": return_value,
                "has_side_effect": side_effect is not None,
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Memory and Pattern Tools
        elif name == "memory_find_patterns":
            try:
                # Import memory manager for pattern search
                from ..memory.memory_manager import memory_manager as mem_man

                task_description = arguments["task_description"]
                limit = arguments.get("limit", 5)

                patterns = mem_man.find_similar_patterns(task_description, limit)

                result = {
                    "task_description": task_description,
                    "patterns_found": len(patterns),
                    "patterns": patterns,
                }
            except ImportError as e:
                result = {
                    "error": "Memory manager not available",
                    "import_error": str(e),
                    "task_description": arguments["task_description"],
                    "note": "Memory pattern search temporarily unavailable",
                }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "memory_record_usage":
            try:
                from ..memory.memory_manager import memory_manager as mem_man

                pattern_id = arguments["pattern_id"]
                workflow_id = arguments["workflow_id"]
                success = arguments.get("success", False)
                feedback = arguments.get("feedback")

                mem_man.record_pattern_usage(pattern_id, workflow_id, success, feedback)

                result = {
                    "pattern_id": pattern_id,
                    "workflow_id": workflow_id,
                    "recorded": True,
                    "success": success,
                }
            except ImportError as e:
                result = {
                    "error": "Memory manager not available",
                    "import_error": str(e),
                    "pattern_id": arguments["pattern_id"],
                    "note": "Pattern usage recording temporarily unavailable",
                }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Context Analysis Tools
        elif name == "diagnostics_context":
            try:
                from ..context.context_engine import context_engine as ctx_eng

                task_description = arguments["task_description"]
                max_files = arguments.get("max_files", 5)

                context_analysis = ctx_eng.get_context_for_task(
                    task_description, max_files
                )
            except ImportError as e:
                context_analysis = {
                    "error": "Context engine not available",
                    "import_error": str(e),
                    "task_description": arguments["task_description"],
                    "note": "Context analysis temporarily unavailable",
                }

            return [
                types.TextContent(
                    type="text", text=json.dumps(context_analysis, indent=2)
                )
            ]

        elif name == "diagnostics_architecture":
            try:
                from ..context.context_engine import context_engine as ctx_eng

                architecture = ctx_eng.analyze_architecture()
            except ImportError as e:
                architecture = {
                    "error": "Context engine not available",
                    "import_error": str(e),
                    "note": "Architecture analysis temporarily unavailable",
                }

            return [
                types.TextContent(type="text", text=json.dumps(architecture, indent=2))
            ]

        elif name == "diagnostics_performance":
            # Placeholder - would integrate with observability
            result = {
                "message": "Performance diagnostics available through observability integration",
                "available_metrics": [
                    "response_times",
                    "error_rates",
                    "primitive_usage",
                ],
                "integration_points": ["tta-observability-integration"],
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Orchestration (Complex workflow execution)
        elif name == "orchestrate_workflow":
            workflow_spec = arguments["workflow_spec"]
            input_data = arguments.get("input_data")

            # This would implement complex multi-stage orchestration
            result = {
                "workflow_name": workflow_spec.get("name", "unnamed"),
                "stages_count": len(workflow_spec.get("stages", [])),
                "status": "orchestration_started",
                "note": "Full orchestration implementation would process each stage",
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()

        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": error_details,
                    },
                    indent=2,
                ),
            )
        ]


async def main():
    """Main entry point for MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tta-dev-primitives",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    # Run as MCP server
    asyncio.run(main())
