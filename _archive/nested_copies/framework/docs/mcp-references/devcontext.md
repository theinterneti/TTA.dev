# DevContext MCP Server

This document provides an overview of the DevContext MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To provide developers with continuous, project-centric context awareness. DevContext continuously learns from and adapts to your development patterns to deliver highly relevant context.
*   **Key Features:**
    *   **Autonomous Context Management:** Continuously learns from and adapts to your development patterns.
    *   **Non-Vector Retrieval:** Uses keyword analysis, relationship graphs, and structured metadata for context retrieval.
    *   **Project-Centric Design:** Each server instance is dedicated to a single project.
    *   **Task Management Integration:** Integrates with a task management workflow.
    *   **External Documentation Context:** Can incorporate external documentation into its context.

## Usage by TTA.dev Agents

TTA.dev agents use the DevContext server to:

*   **Maintain Project Scope Alignment:** Ensure that their work is aligned with the overall goals of the project.
*   **Incorporate Up-to-Date Documentation:** Use the latest documentation to ensure that their work is accurate and up-to-date.
*   **Implement Advanced Task Workflows:** Use the task workflow system to manage their work and track their progress.

## Developer Use Cases

As a developer, you can use the DevContext server to:

*   **Empower Your Development Workflow:** Empower your development workflow with intelligent context awareness.
*   **Gain a Deeper Understanding of Your Codebase:** Gain a deeper understanding of your codebase by leveraging the server's context retrieval capabilities.
*   **Automate Your Development Environment:** Automate your development environment by implementing the provided Cursor Rules system.

## Example

Here's an example of the tool execution sequence defined by the core Cursor Rule:

1.  **`initialize_conversation_context`**: Called once at the start of a conversation.
2.  **`update_conversation_context`**: Called as needed for code changes or new messages.
3.  **`retrieve_relevant_context`**: Called when specific context is required.
4.  **`record_milestone_context`**: Called occasionally for significant achievements.
5.  **`finalize_conversation_context`**: Called once at the end of a conversation.
