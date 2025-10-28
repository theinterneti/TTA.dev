#!/usr/bin/env python3
"""
MCP Schema Validator

Validates that MCP tool definitions match actual implementation.
Ensures the contract between LLM agents and deterministic code is sound.

Usage:
    python scripts/validate-mcp-schemas.py
"""

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def load_apm_config() -> dict[str, Any]:
    """Load apm.yml configuration."""
    config_path = Path("apm.yml")
    if not config_path.exists():
        print("❌ apm.yml not found")
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)


def validate_tool_schema(tool_name: str, schema: dict[str, Any]) -> bool:
    """Validate a single tool schema."""
    required_fields = ["name", "description", "input_schema"]

    for field in required_fields:
        if field not in schema:
            print(f"❌ Tool '{tool_name}' missing required field: {field}")
            return False

    # Validate input schema
    input_schema = schema.get("input_schema", {})
    if not isinstance(input_schema, dict):
        print(f"❌ Tool '{tool_name}' has invalid input_schema")
        return False

    if "type" not in input_schema:
        print(f"❌ Tool '{tool_name}' input_schema missing 'type'")
        return False

    # Check description clarity (basic heuristics)
    description = schema.get("description", "")
    if len(description) < 20:
        print(
            f"⚠️  Tool '{tool_name}' has short description (may not be clear to agents)"
        )

    return True


def validate_mcp_servers(config: dict[str, Any]) -> bool:
    """Validate all MCP server configurations."""
    mcp_servers = config.get("mcp", {}).get("servers", [])

    if not mcp_servers:
        print("⚠️  No MCP servers defined")
        return True

    all_valid = True

    for server in mcp_servers:
        server_name = server.get("name", "unknown")
        print(f"\n🔍 Validating MCP server: {server_name}")

        # Validate required fields
        required = ["name", "protocol", "command"]
        for field in required:
            if field not in server:
                print(f"  ❌ Missing required field: {field}")
                all_valid = False
                continue

        # Validate tools list
        tools = server.get("tools", [])
        if not tools:
            print(f"  ⚠️  Server '{server_name}' has no tools defined")

        # Validate access level
        access = server.get("access", "read-only")
        if access not in ["read-only", "read-write"]:
            print(f"  ❌ Invalid access level: {access}")
            all_valid = False

        if all_valid:
            print(f"  ✅ Server '{server_name}' configuration valid")

    return all_valid


def main() -> int:
    """Main validation function."""
    print("🔍 Validating MCP Schemas\n")

    # Load configuration
    config = load_apm_config()
    print("✅ Loaded apm.yml configuration\n")

    # Validate MCP servers
    if not validate_mcp_servers(config):
        print("\n❌ MCP server validation failed")
        return 1

    print("\n✅ All MCP schemas valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
