#!/usr/bin/env python3
"""PTC (Programmatic Tool Calling) with Hypertool Integration Demo.

This example demonstrates the complete PTC flow:
1. Load a Hypertool persona with access control
2. Generate Python modules from MCP tool schemas
3. Create E2B sandbox files with the generated modules
4. Execute code in an E2B sandbox using the generated tool wrappers
5. Validate security boundaries (only allowed servers accessible)

Prerequisites:
- E2B_API_KEY environment variable set
- .hypertool directory with personas and mcp_servers.json

Usage:
    # Run the full demo (requires E2B API key)
    uv run python packages/tta-dev-primitives/examples/ptc_hypertool_demo.py

    # Run without E2B (just schema generation verification)
    uv run python packages/tta-dev-primitives/examples/ptc_hypertool_demo.py --no-sandbox

Author: TTA.dev Team
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import os
import sys
from pathlib import Path

# Add package to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tta_dev_primitives.integrations.e2b_template_config import (
    SandboxFile,
    create_mcp_sandbox_files,
)
from tta_dev_primitives.integrations.hypertool_bridge import (
    HypertoolLoader,
    HypertoolMCPConfig,
    HypertoolMCPExecutor,
    HypertoolPersona,
)
from tta_dev_primitives.integrations.mcp_schema_generator import (
    MCPToolParameter,
    MCPToolSchema,
    PythonModuleGenerator,
)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_step(step: int, description: str) -> None:
    """Print a step indicator."""
    print(f"\n[Step {step}] {description}")
    print("-" * 50)


def create_realistic_tool_schemas() -> dict[str, list[MCPToolSchema]]:
    """Create realistic MCP tool schemas based on actual MCP servers.

    These schemas mirror the actual tools available from:
    - context7: Library documentation search
    - github: GitHub operations
    - sequential-thinking: Reasoning tools
    """
    return {
        "context7": [
            MCPToolSchema(
                name="resolve_library_id",
                description="Resolve a library name to a Context7-compatible library ID",
                parameters=[
                    MCPToolParameter(
                        name="library_name",
                        type_hint="str",
                        description="Library name to search for (e.g., 'pandas', 'react')",
                        required=True,
                    ),
                ],
            ),
            MCPToolSchema(
                name="get_library_docs",
                description="Fetch documentation for a library from Context7",
                parameters=[
                    MCPToolParameter(
                        name="library_id",
                        type_hint="str",
                        description="Context7-compatible library ID (e.g., '/pydata/pandas')",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="topic",
                        type_hint="str",
                        description="Specific topic to focus on",
                        required=False,
                        default=None,
                    ),
                    MCPToolParameter(
                        name="max_tokens",
                        type_hint="int",
                        description="Maximum tokens for response",
                        required=False,
                        default=5000,
                    ),
                ],
            ),
        ],
        "github": [
            MCPToolSchema(
                name="github_get_file_contents",
                description="Get the contents of a file from a GitHub repository",
                parameters=[
                    MCPToolParameter(
                        name="owner",
                        type_hint="str",
                        description="Repository owner",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="repo",
                        type_hint="str",
                        description="Repository name",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="path",
                        type_hint="str",
                        description="Path to the file",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="ref",
                        type_hint="str",
                        description="Git ref (branch, tag, or commit)",
                        required=False,
                        default="main",
                    ),
                ],
            ),
            MCPToolSchema(
                name="github_search_code",
                description="Search for code across GitHub repositories",
                parameters=[
                    MCPToolParameter(
                        name="query",
                        type_hint="str",
                        description="Search query",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="per_page",
                        type_hint="int",
                        description="Results per page (max 100)",
                        required=False,
                        default=30,
                    ),
                ],
            ),
        ],
        "sequential-thinking": [
            MCPToolSchema(
                name="think",
                description="Process a thought step for complex reasoning",
                parameters=[
                    MCPToolParameter(
                        name="thought",
                        type_hint="str",
                        description="Current thinking step",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="thought_number",
                        type_hint="int",
                        description="Current thought number in sequence",
                        required=True,
                    ),
                ],
            ),
        ],
    }


def demo_step1_load_persona(
    hypertool_dir: Path,
) -> tuple[HypertoolPersona, dict[str, HypertoolMCPConfig]]:
    """Step 1: Load Hypertool persona and filter servers."""
    print_step(1, "Loading Hypertool Persona")

    loader = HypertoolLoader(hypertool_dir)

    # List available personas
    personas = loader.list_personas()
    print(f"Available personas: {personas}")

    # Load the backend engineer persona
    persona = loader.load_persona("tta-backend-engineer")
    print(f"\nLoaded persona: {persona.display_name}")
    print(f"  Description: {persona.description}")
    print(f"  Token budget: {persona.token_budget}")
    print(f"  Allowed servers: {persona.allowed_servers}")

    # Get filtered servers (only those allowed by persona)
    servers = loader.get_persona_servers(persona)
    print(f"\nFiltered servers ({len(servers)} of {len(loader.load_mcp_servers())}):")
    for name, config in servers.items():
        print(f"  - {name}: {config.description}")

    return persona, servers


def demo_step2_generate_modules(
    servers: dict[str, HypertoolMCPConfig],
    tool_schemas: dict[str, list[MCPToolSchema]],
) -> dict[str, str]:
    """Step 2: Generate Python modules from MCP schemas."""
    print_step(2, "Generating Python Modules from MCP Schemas")

    generator = PythonModuleGenerator()
    all_modules: dict[str, str] = {}

    for server_name, tools in tool_schemas.items():
        if server_name in servers:
            description = servers[server_name].description
            modules = generator.generate_server_modules(server_name, tools, description)
            all_modules.update(modules)
            print(f"\n{server_name} ({len(tools)} tools):")
            for path in modules.keys():
                print(f"  → {path}")

    # Also generate MCP client module
    server_configs = {
        name: {
            "command": cfg.command,
            "args": cfg.args,
            "env": cfg.env,
            "url": cfg.url,
            "transport": cfg.transport,
        }
        for name, cfg in servers.items()
    }
    mcp_client = generator.generate_mcp_client_module(server_configs)
    all_modules["mcp_client.py"] = mcp_client
    print("\n  → mcp_client.py (core MCP communication)")

    print(f"\nTotal modules generated: {len(all_modules)}")
    return all_modules


def demo_step3_validate_python(modules: dict[str, str]) -> bool:
    """Step 3: Validate generated Python is syntactically correct."""
    print_step(3, "Validating Generated Python Syntax")

    all_valid = True
    for path, content in modules.items():
        if path.endswith(".py"):
            try:
                ast.parse(content)
                print(f"  ✓ {path} - valid")
            except SyntaxError as e:
                print(f"  ✗ {path} - INVALID: {e}")
                all_valid = False

    if all_valid:
        print("\n✅ All generated Python modules are syntactically valid!")
    else:
        print("\n❌ Some modules have syntax errors!")

    return all_valid


def demo_step4_create_sandbox_files(
    persona: HypertoolPersona,
    servers: dict[str, HypertoolMCPConfig],
    tool_schemas: dict[str, list[MCPToolSchema]],
) -> list[SandboxFile]:
    """Step 4: Create E2B sandbox files."""
    print_step(4, "Creating E2B Sandbox Files")

    files = create_mcp_sandbox_files(
        persona=persona,
        servers=servers,
        tool_schemas=tool_schemas,
    )

    print(f"Created {len(files)} sandbox files:")
    for f in files:
        size = len(f.content)
        print(f"  {f.path} ({size} bytes)")

    return files


def demo_step5_show_generated_code(modules: dict[str, str]) -> None:
    """Step 5: Show examples of generated code."""
    print_step(5, "Sample Generated Code")

    # Show a tool wrapper example
    if "servers/context7/resolve_library_id.py" in modules:
        print("\n📄 servers/context7/resolve_library_id.py:")
        print("-" * 40)
        content = modules["servers/context7/resolve_library_id.py"]
        # Show first 30 lines
        lines = content.split("\n")[:30]
        for i, line in enumerate(lines, 1):
            print(f"{i:3}: {line}")
        if len(content.split("\n")) > 30:
            print("     ... (truncated)")

    # Show MCP client snippet
    if "mcp_client.py" in modules:
        print("\n📄 mcp_client.py (core function):")
        print("-" * 40)
        content = modules["mcp_client.py"]
        # Find and show call_mcp_tool function
        lines = content.split("\n")
        in_func = False
        func_lines = []
        for line in lines:
            if "async def call_mcp_tool" in line:
                in_func = True
            if in_func:
                func_lines.append(line)
                if len(func_lines) > 20:
                    break
        for i, line in enumerate(func_lines[:20], 1):
            print(f"{i:3}: {line}")
        print("     ... (truncated)")


def demo_step6_validate_access_control(
    persona: HypertoolPersona, servers: dict[str, HypertoolMCPConfig]
) -> None:
    """Step 6: Demonstrate access control validation."""
    print_step(6, "Access Control Validation")

    from unittest.mock import patch

    from tta_dev_primitives.integrations.hypertool_bridge import HypertoolLoader

    # Mock the loader with actual servers for validation
    with patch.object(HypertoolLoader, "load_mcp_servers") as mock:
        mock.return_value = servers
        executor = HypertoolMCPExecutor(
            persona=persona,
            hypertool_dir="/tmp/fake",
        )

    # Test valid imports
    valid_code = """
from servers.context7 import resolve_library_id, get_library_docs
from servers.github import github_get_file_contents

async def research_library(name: str):
    lib_id = await resolve_library_id(name)
    docs = await get_library_docs(lib_id, topic="quickstart")
    return docs
"""
    errors = executor.validate_code_imports(valid_code)
    print("Valid code (allowed servers):")
    print("  Code imports: context7, github")
    print(f"  Validation result: {'✅ ALLOWED' if not errors else '❌ BLOCKED'}")

    # Test blocked imports
    blocked_code = """
from servers.grafana import query_prometheus  # NOT in allowedServers!
from servers.playwright import browser_click   # NOT in allowedServers!
"""
    errors = executor.validate_code_imports(blocked_code)
    print("\nBlocked code (unauthorized servers):")
    print("  Code imports: grafana, playwright")
    print(f"  Validation result: {'✅ ALLOWED' if not errors else '❌ BLOCKED'}")
    if errors:
        for err in errors:
            print(f"    → {err}")


async def demo_step7_e2b_execution(sandbox_files: list[SandboxFile]) -> None:
    """Step 7: Execute in actual E2B sandbox."""
    print_step(7, "E2B Sandbox Execution")

    try:
        from e2b_code_interpreter import AsyncSandbox
    except ImportError:
        print("❌ e2b_code_interpreter not installed. Skipping sandbox execution.")
        return

    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        print("❌ E2B_API_KEY not set. Skipping sandbox execution.")
        return

    print("Creating E2B sandbox...")

    sandbox = await AsyncSandbox.create()
    try:
        print(f"✓ Sandbox created (ID: {sandbox.sandbox_id})")

        # Write all generated files to sandbox using run_code
        print("\nUploading generated files to sandbox:")
        for f in sandbox_files:
            # Create directory structure and write file via Python
            escaped_content = f.content.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
            write_code = f'''
import os
import pathlib

path = pathlib.Path("/home/user/{f.path}")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("""{escaped_content}""")
'''
            await sandbox.run_code(write_code)
            print(f"  ✓ {f.path}")

        # Execute test code that uses the generated modules
        test_code = """
import sys
sys.path.insert(0, '/home/user')

# Test 1: Import generated modules
print("Test 1: Importing generated modules...")
from servers.context7 import resolve_library_id, get_library_docs
from servers.github import github_get_file_contents
print("  ✓ All imports successful!")

# Test 2: Check function signatures
print("\\nTest 2: Checking function signatures...")
import inspect
sig = inspect.signature(resolve_library_id)
print(f"  resolve_library_id{sig}")
sig = inspect.signature(get_library_docs)
print(f"  get_library_docs{sig}")
sig = inspect.signature(github_get_file_contents)
print(f"  github_get_file_contents{sig}")

# Test 3: Verify MCP client
print("\\nTest 3: Verifying MCP client...")
from mcp_client import call_mcp_tool, SERVER_CONFIGS
print(f"  Configured servers: {list(SERVER_CONFIGS.keys())}")
print(f"  call_mcp_tool is async: {inspect.iscoroutinefunction(call_mcp_tool)}")

# Test 4: Check persona info
print("\\nTest 4: Checking persona info...")
from persona_info import PERSONA_NAME, ALLOWED_SERVERS
print(f"  Persona: {PERSONA_NAME}")
print(f"  Allowed servers: {ALLOWED_SERVERS}")

print("\\n✅ All sandbox tests passed!")
"""

        print("\nExecuting test code in sandbox:")
        print("-" * 40)

        result = await sandbox.run_code(test_code)

        if result.logs.stdout:
            for line in result.logs.stdout:
                print(line)

        if result.logs.stderr:
            print("\nStderr:")
            for line in result.logs.stderr:
                print(f"  {line}")

        if result.error:
            print(f"\n❌ Execution error: {result.error}")
        else:
            print("\n✅ E2B sandbox execution completed successfully!")
    finally:
        await sandbox.kill()


def main():
    """Run the complete PTC + Hypertool demo."""
    parser = argparse.ArgumentParser(description="PTC + Hypertool Integration Demo")
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Skip E2B sandbox execution (useful without API key)",
    )
    # Calculate default path: examples/ -> tta-dev-primitives/ -> packages/ -> repo root
    default_hypertool_dir = Path(__file__).resolve().parent.parent.parent.parent / ".hypertool"
    parser.add_argument(
        "--hypertool-dir",
        type=Path,
        default=default_hypertool_dir,
        help="Path to .hypertool directory",
    )
    args = parser.parse_args()

    print_header("PTC (Programmatic Tool Calling) + Hypertool Integration Demo")

    print("This demo shows how TTA.dev enables secure, token-efficient tool calling")
    print("by combining Hypertool's persona-based access control with E2B code execution.")
    print(f"\nHypertool directory: {args.hypertool_dir}")

    # Check if hypertool dir exists
    if not args.hypertool_dir.exists():
        print(f"\n❌ Hypertool directory not found: {args.hypertool_dir}")
        print("Please ensure .hypertool directory exists with personas and mcp_servers.json")
        sys.exit(1)

    # Step 1: Load persona
    persona, servers = demo_step1_load_persona(args.hypertool_dir)

    # Create realistic tool schemas
    tool_schemas = create_realistic_tool_schemas()

    # Step 2: Generate Python modules
    modules = demo_step2_generate_modules(servers, tool_schemas)

    # Step 3: Validate Python syntax
    if not demo_step3_validate_python(modules):
        sys.exit(1)

    # Step 4: Create sandbox files
    sandbox_files = demo_step4_create_sandbox_files(persona, servers, tool_schemas)

    # Step 5: Show generated code examples
    demo_step5_show_generated_code(modules)

    # Step 6: Validate access control
    demo_step6_validate_access_control(persona, servers)

    # Step 7: E2B sandbox execution (optional)
    if not args.no_sandbox:
        asyncio.run(demo_step7_e2b_execution(sandbox_files))
    else:
        print_step(7, "E2B Sandbox Execution (SKIPPED)")
        print("  Use --no-sandbox flag was provided, skipping sandbox execution.")

    print_header("Demo Complete!")
    print("Key takeaways:")
    print("  1. Hypertool personas provide security boundaries")
    print("  2. MCP schemas are converted to callable Python modules")
    print("  3. Generated code is syntactically valid and importable")
    print("  4. Access control is enforced at the code level")
    print("  5. E2B sandbox provides isolated execution environment")
    print("\nThis enables ~98% token reduction vs. traditional tool calling!")


if __name__ == "__main__":
    main()
