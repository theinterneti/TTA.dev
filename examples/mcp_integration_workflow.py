"""Example: Using MCP Integration Primitives

This example demonstrates:
1. Auto-detecting MCP configuration across AI agents (Copilot, Cline)
2. Validating MCP server setup
3. Using GitHub MCP primitive for repository operations
4. Using Context7 MCP primitive for library documentation
5. Adaptive setup guidance when configuration is missing

Run this to:
- Check your MCP configuration health
- Get step-by-step setup instructions
- See how to use MCP primitives in workflows
"""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import (
    Context7MCPConfigValidator,
    Context7MCPPrimitive,
    GitHubMCPConfigValidator,
    GitHubMCPPrimitive,
    MCPConfigurationPrimitive,
    MCPSetupGuidePrimitive,
    detect_all_mcp_servers,
)


async def check_mcp_health():
    """Check health of all MCP server configurations."""
    print("=" * 70)
    print("🔍 MCP Configuration Health Check")
    print("=" * 70)

    # Detect all configured servers
    servers = detect_all_mcp_servers()
    print(f"\n📡 Detected {len(servers)} MCP server(s)")

    if servers:
        for server in servers:
            print(f"\n  • {server.name}")
            print(f"    Agent: {server.agent_type}")
            print(f"    Config: {server.config_path}")
            if server.requires_auth:
                print(
                    f"    Auth: {server.auth_env_var} {'✅' if server.auth_env_var else '❌'}"
                )
    else:
        print("\n⚠️  No MCP servers detected")
        print("    Run setup guide below for instructions")

    # Comprehensive validation
    print("\n" + "=" * 70)
    print("✅ Running Comprehensive Validation")
    print("=" * 70)

    validator = MCPConfigurationPrimitive()
    context = WorkflowContext(trace_id="mcp-health-check")
    result = await validator.execute(None, context)

    print(f"\nStatus: {'✅ All Valid' if result['all_valid'] else '❌ Issues Found'}")
    print(f"Total: {result['total_servers']} servers")
    print(f"Valid: {result['valid_servers']}")
    print(f"Invalid: {result['invalid_servers']}")

    if result["issues"]:
        print("\n🔧 Issues Found:")
        for server, issues in result["issues"].items():
            print(f"\n  {server}:")
            for issue in issues:
                print(f"    • {issue}")

    if result["suggestions"]:
        print("\n💡 Suggestions:")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")

    return result


async def validate_github_mcp():
    """Validate GitHub MCP configuration specifically."""
    print("\n" + "=" * 70)
    print("🐙 GitHub MCP Validation")
    print("=" * 70)

    validator = GitHubMCPConfigValidator()
    context = WorkflowContext(trace_id="github-validation")
    result = await validator.execute(None, context)

    print(f"\nStatus: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    print(f"Agent Type: {result['agent_type']}")
    print(f"Config Path: {result['config_path']}")
    print(f"Has Token: {'✅' if result['has_token'] else '❌'}")

    if result["errors"]:
        print("\n❌ Errors:")
        for error in result["errors"]:
            print(f"  • {error}")

    if result["suggestions"]:
        print("\n💡 Suggestions:")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")

    return result


async def validate_context7_mcp():
    """Validate Context7 MCP configuration specifically."""
    print("\n" + "=" * 70)
    print("📚 Context7 MCP Validation")
    print("=" * 70)

    validator = Context7MCPConfigValidator()
    context = WorkflowContext(trace_id="context7-validation")
    result = await validator.execute(None, context)

    print(f"\nStatus: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    print(f"Agent Type: {result['agent_type']}")
    print(f"Config Path: {result['config_path']}")

    if result["errors"]:
        print("\n❌ Errors:")
        for error in result["errors"]:
            print(f"  • {error}")

    if result["suggestions"]:
        print("\n💡 Suggestions:")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")

    return result


async def show_setup_guide(server: str = "github", agent: str = "copilot"):
    """Show adaptive setup guide for MCP server."""
    print("\n" + "=" * 70)
    print(f"📖 Setup Guide: {server.upper()} on {agent.capitalize()}")
    print("=" * 70)

    guide_primitive = MCPSetupGuidePrimitive()
    context = WorkflowContext(trace_id="setup-guide")
    result = await guide_primitive.execute({"server": server, "agent": agent}, context)

    print(f"\n{result['guide']}")

    return result


async def example_github_workflow():
    """Example workflow using GitHub MCP primitive."""
    print("\n" + "=" * 70)
    print("🔄 GitHub MCP Workflow Example")
    print("=" * 70)

    try:
        github = GitHubMCPPrimitive()
        context = WorkflowContext(trace_id="github-workflow")

        # Example: Search for code
        print("\n📝 Searching for 'CachePrimitive' in TTA.dev...")
        result = await github.search_code(
            query="CachePrimitive repo:theinterneti/TTA.dev language:python",
            context=context,
        )
        print(f"Result: {result['status']}")
        print(f"Found {result.get('total_count', 0)} matches")

        # Example: List issues
        print("\n📋 Listing open issues...")
        result = await github.list_issues(
            repo="theinterneti/TTA.dev", state="open", context=context
        )
        print(f"Result: {result['status']}")
        print(f"Found {result.get('total_count', 0)} open issues")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Run: python examples/mcp_integration_workflow.py --setup github")


async def example_context7_workflow():
    """Example workflow using Context7 MCP primitive."""
    print("\n" + "=" * 70)
    print("🔄 Context7 MCP Workflow Example")
    print("=" * 70)

    try:
        context7 = Context7MCPPrimitive()
        context = WorkflowContext(trace_id="context7-workflow")

        # Example: Resolve library
        print("\n🔍 Resolving 'httpx' library...")
        result = await context7.resolve_library(library_name="httpx", context=context)
        print(f"Result: {result['status']}")
        print(f"Library ID: {result.get('library_id', 'unknown')}")

        # Example: Get documentation
        print("\n📚 Getting httpx async client docs...")
        result = await context7.get_docs(
            library="httpx", topic="async client usage", tokens=5000, context=context
        )
        print(f"Result: {result['status']}")
        print(f"Tokens used: {result.get('tokens_used', 0)}")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Run: python examples/mcp_integration_workflow.py --setup context7")


async def main():
    """Run all examples."""
    import sys

    # Check for setup guide request
    if "--setup" in sys.argv:
        try:
            server = sys.argv[sys.argv.index("--setup") + 1]
        except IndexError:
            server = "github"

        agent = "copilot"
        if "--agent" in sys.argv:
            try:
                agent = sys.argv[sys.argv.index("--agent") + 1]
            except IndexError:
                pass

        await show_setup_guide(server=server, agent=agent)
        return

    # Run health checks
    await check_mcp_health()
    await validate_github_mcp()
    await validate_context7_mcp()

    # Show example workflows
    await example_github_workflow()
    await example_context7_workflow()

    print("\n" + "=" * 70)
    print("✅ MCP Integration Examples Complete")
    print("=" * 70)
    print("\nUsage:")
    print("  python examples/mcp_integration_workflow.py")
    print("  python examples/mcp_integration_workflow.py --setup github")
    print(
        "  python examples/mcp_integration_workflow.py --setup context7 --agent cline"
    )


if __name__ == "__main__":
    asyncio.run(main())
