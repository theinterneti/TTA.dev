# Context7 / Upstash MCP Server

This document provides an overview of the Context7/Upstash MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To provide AI coding assistants with up-to-date, version-specific documentation and code examples for any library or framework.
*   **Key Features:**
    *   **Real-time Documentation:** Fetches documentation directly from the source, ensuring it is always up-to-date.
    *   **Version-Specific:** Retrieves documentation for specific versions of a library.
    *   **Tool-Based Access:** Exposes two primary tools: `resolve-library-id` for finding libraries and `get-library-docs` for retrieving documentation.
    *   **Flexible Deployment:** Can be run as a local stdio server or a remote HTTP server.
    *   **Authentication and Rate Limiting:** Supports API key authentication and intelligent rate limiting.

## Usage by TTA.dev Agents

TTA.dev agents utilize the Context7 server to:

*   **Generate Accurate Code:** Generate accurate and working code by referencing the latest documentation.
*   **Avoid Hallucinated APIs:** Avoid using outdated or hallucinated APIs by fetching real-time information.
*   **Improve Problem-Solving:** Quickly understand how to use a library or framework to solve a specific problem.

## Developer Use Cases

As a developer, you can use the Context7 server to:

*   **Enhance Your AI Coding Assistant:** Integrate Context7 with your AI coding assistant to provide it with up-to-date documentation.
*   **Improve Your Development Workflow:** Use the "use context7" command in your prompts to get accurate and relevant code examples.
*   **Customize Documentation Indexing:** Use a `context7.json` file to customize how Context7 parses and indexes your library's documentation.

## Example

Here's an example of how an agent might use the `resolve-library-id` and `get-library-docs` tools to get documentation for Next.js routing:

1.  **Resolve Library ID:**
    ```json
    {
      "tool": "resolve-library-id",
      "arguments": {
        "libraryName": "next.js"
      }
    }
    ```

2.  **Get Library Documentation:**
    ```json
    {
      "tool": "get-library-docs",
      "arguments": {
        "context7CompatibleLibraryID": "/vercel/next.js",
        "topic": "routing",
        "tokens": 5000
      }
    }
