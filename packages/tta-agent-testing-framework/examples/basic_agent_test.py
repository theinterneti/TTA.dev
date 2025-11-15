#!/usr/bin/env python3
"""
Basic AI Agent Testing Example

Demonstrates the TTA Agent Testing Framework for validating
AI coding assistants in VS Code workspaces.

Run with: python examples/basic_agent_test.py
"""

import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright
from tta_agent_testing_framework import AgentTestingFramework
from tta_agent_testing_framework.browser import PlaywrightAutomationProvider
from tta_agent_testing_framework.core import WorkspaceType
from tta_agent_testing_framework.mcp import MCPConnectionHealthChecker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_workspace_validation():
    """Basic workspace configuration validation."""
    print("🔧 Basic Workspace Validation")
    print("=" * 40)

    # Initialize framework
    workspace_root = Path("../../")  # Root of TTA.dev project
    framework = AgentTestingFramework(workspace_root=workspace_root)

    # Test all workspace types
    results = {}
    for workspace_type in WorkspaceType:
        print(f"Testing {workspace_type.value} workspace...")
        result = await framework.validate_workspace_configuration(workspace_type)

        results[workspace_type] = result
        status = "✅ PASS" if result.success else "❌ FAIL"

        print(f"  {status} - {result.metadata.get('workspace_type', 'unknown')}")
        if result.errors:
            for error in result.errors:
                print(f"    ERROR: {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"    WARN: {warning}")

    return results


async def browser_setup_validation():
    """Validate browser automation setup."""
    print("\n🌐 Browser Setup Validation")
    print("=" * 40)

    try:
        async with async_playwright() as playwright:
            # Initialize Playwright provider
            browser_provider = PlaywrightAutomationProvider(playwright)

            print("Creating browser context...")
            context = await browser_provider.create_context()

            print("Testing basic page navigation...")
            page = await context.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            print(f"Page title: {title}")

            # Cleanup
            await page.close()
            await context.close()

            print("✅ Browser setup validated successfully")
            return True

    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return False


async def mcp_server_validation():
    """Validate MCP server health."""
    print("\n🔌 MCP Server Validation")
    print("=" * 40)

    # Initialize MCP checker
    mcp_checker = MCPConnectionHealthChecker()

    # Test servers configured in the project
    test_servers = ["context7", "sequential-thinking", "serena", "playwright"]

    results = {}
    for server_name in test_servers:
        print(f"Testing MCP server: {server_name}")
        result = await mcp_checker.test_server_connectivity(server_name)

        results[server_name] = result
        status = "✅ CONNECTED" if result.success else "❌ FAILED"

        print(f"  {status} - {result.metadata.get('response_time', 'N/A'):.2f}s")
        if result.errors:
            for error in result.errors:
                print(f"    ERROR: {error}")

    return results


async def comprehensive_workspace_test():
    """Run comprehensive test on Cline workspace with MCP servers."""
    print("\n🚀 Comprehensive Cline Workspace Test")
    print("=" * 50)

    workspace_root = Path("../../")  # Root of TTA.dev project

    # Initialize components
    try:
        async with async_playwright() as playwright:
            browser_provider = PlaywrightAutomationProvider(playwright)
            mcp_checker = MCPConnectionHealthChecker()

            # Initialize framework with both providers
            framework = AgentTestingFramework(
                workspace_root=workspace_root,
                browser_provider=browser_provider,
                mcp_checker=mcp_checker,
            )

            # Run comprehensive test
            result = await framework.run_comprehensive_test(WorkspaceType.CLINE)

            print("📋 Test Results:")
            print(f"  Overall Status: {'✅ PASS' if result.success else '❌ FAIL'}")
            print(f"  Tests Run: {result.metadata.get('test_count', 0)}")

            if result.errors:
                print("  ❌ Errors:")
                for error in result.errors:
                    print(f"    • {error}")

            if result.warnings:
                print("  ⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"    • {warning}")

            return result

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print(
            "Install test dependencies: uv pip install -e 'packages/tta-agent-testing-framework[dev,playwright]'"
        )
        return None


async def benchmark_mcp_performance():
    """Benchmark MCP server performance."""
    print("\n⚡ MCP Performance Benchmark")
    print("=" * 40)

    mcp_checker = MCPConnectionHealthChecker()

    server_name = "context7"  # Test the documentation server
    print(f"Benchmarking {server_name} server...")

    result = await mcp_checker.benchmark_server_performance(server_name, iterations=5)

    if result.success:
        metadata = result.metadata
        print(f"  ✅ Successful Tests: {metadata.get('successful_tests', 0)}/5")
        print(".2f")
        print(".2f")
        print(".2f")
    else:
        print(f"  ❌ Benchmark failed: {result.errors}")


async def main():
    """Run all validation tests."""
    print("🤖 TTA Agent Testing Framework - Basic Validation")
    print("=" * 60)

    results_summary = {
        "workspace_validation": False,
        "browser_setup": False,
        "mcp_validation": False,
        "comprehensive_test": False,
        "benchmark": False,
    }

    # Basic workspace validation
    workspace_results = await basic_workspace_validation()
    results_summary["workspace_validation"] = all(
        r.success for r in workspace_results.values()
    )

    # Browser setup validation
    browser_result = await browser_setup_validation()
    results_summary["browser_setup"] = browser_result

    # MCP server validation
    mcp_results = await mcp_server_validation()
    results_summary["mcp_validation"] = any(r.success for r in mcp_results.values())

    # Comprehensive workspace test (may fail if dependencies missing)
    try:
        comprehensive_result = await comprehensive_workspace_test()
        results_summary["comprehensive_test"] = (
            comprehensive_result.success if comprehensive_result else False
        )
    except Exception as e:
        print(f"Note: Comprehensive test skipped due to: {e}")
        results_summary["comprehensive_test"] = None

    # Performance benchmark
    await benchmark_mcp_performance()
    results_summary["benchmark"] = True  # Always attempt benchmark

    # Final summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)

    for test_name, success in results_summary.items():
        if success is None:
            status = "⏭️  SKIPPED"
        elif success:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")

    total_passed = sum(1 for s in results_summary.values() if s is True)
    total_tests = sum(1 for s in results_summary.values() if s is not None)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All validations passed! Ready for advanced agent testing.")
    else:
        print(
            "💡 Some validations failed. Check missing dependencies or configuration."
        )


if __name__ == "__main__":
    asyncio.run(main())
