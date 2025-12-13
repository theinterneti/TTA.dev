# E2B MCP Server

This document provides an overview of the E2B MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To provide a secure and isolated environment for executing code and running commands.
*   **Key Features:**
    *   **Code Interpreting:** Adds code interpreting capabilities to your Claude Desktop app via the E2B Sandbox.
    *   **Secure Sandbox:** Runs code in a secure sandbox, preventing it from affecting your local system.
    *   **Multiple Editions:** Available in both JavaScript and Python editions.

## Usage by TTA.dev Agents

TTA.dev agents use the E2B server to:

*   **Execute Code Safely:** Execute code in a secure and isolated environment.
*   **Test Code Snippets:** Test code snippets and small programs without affecting the host system.
*   **Run External Tools:** Run external tools and commands that are not available on the host system.

## Developer Use Cases

As a developer, you can use the E2B server to:

*   **Add Code Interpreting Capabilities to Your Applications:** Add code interpreting capabilities to your applications by integrating the E2B MCP server.
*   **Create Secure Code Execution Environments:** Create secure environments for running untrusted code in your own applications.
*   **Test and Debug Code:** Test and debug code in a clean and isolated environment.

## Example

Here's an example of how you might configure the E2B MCP server in your Claude Desktop app:

```json
{
  "mcpServers": {
    "e2b-server": {
      "command": "npx",
      "args": ["-y", "@e2b/mcp-server"],
      "env": { "E2B_API_KEY": "${e2bApiKey}" }
    }
  }
}


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp-references/E2b]]
