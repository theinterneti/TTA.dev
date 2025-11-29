# Hypertool MCP Server

This document provides an overview of the Hypertool MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To dynamically expose tools from proxied MCP servers based on an Agent Persona, allowing for the creation of task-specific toolsets.
*   **Key Features:**
    *   **Unlimited MCP Servers:** Connect to an unlimited number of MCP servers without hitting tool limits.
    *   **Task-Specific Toolsets:** Create focused toolsets for specific tasks, such as "git-essentials" or "coding."
    *   **Smart Tool Descriptions:** Enhance tools with examples and context to improve the AI's ability to select the right tool.
    *   **Personas:** Use pre-configured MCP server bundles with pre-built toolsets for specific workflows.
    *   **Context Measurement:** See exactly how much context each tool consumes to optimize your toolsets.

## Usage by TTA.dev Agents

TTA.dev agents use the Hypertool server to:

*   **Focus on the Task at Hand:** Switch between different toolsets to focus on the specific tools needed for the current task.
*   **Improve Tool Selection:** Use the enhanced tool descriptions and context measurement to make better decisions about which tools to use.
*   **Streamline Workflows:** Use personas to quickly set up their environment with the tools needed for a specific workflow.

## Developer Use Cases

As a developer, you can use the Hypertool server to:

*   **Give your AI the best tools from all your MCPs:** Create a more focused and effective AI assistant by providing it with task-specific toolsets.
*   **Break free from tool limits:** Connect to as many MCP servers as you need without worrying about hitting tool limits.
*   **Optimize your context usage:** Use the context measurement feature to identify and optimize heavyweight tools.

## Example

Here's an example of how you might create and switch to a "coding" toolset:

```
You: "Create a toolset called 'coding' with git and docker tools"
AI: "Created 'coding' toolset with 15 focused tools"

You: "Switch to coding toolset"
AI: "Equipped! I now have just the tools needed for development"
