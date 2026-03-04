# NotebookLM MCP Server

This document provides an overview of the NotebookLM MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To let your AI agents (Claude Code, Codex) research documentation directly with grounded, citation-backed answers from Gemini.
*   **Key Features:**
    *   **Zero Hallucinations:** NotebookLM refuses to answer if information isn't in your docs.
    *   **Autonomous Research:** Claude asks follow-up questions automatically, building complete understanding before coding.
    *   **Smart Library Management:** Save NotebookLM links with tags and descriptions. Claude auto-selects the right notebook for your task.
    *   **Cross-Tool Sharing:** Set up once, use everywhere. Claude Code, Codex, Cursor—all share the same library.

## Usage by TTA.dev Agents

TTA.dev agents use the NotebookLM MCP server to:

*   **Get Zero-Hallucination Answers:** Get answers based on your own notebooks, with no invented APIs.
*   **Build Deep Understanding:** Build deep understanding through automatic follow-ups, getting specific implementation details, edge cases, and best practices.
*   **Write Correct Code:** Write correct code the first time, without debugging hallucinated APIs.

## Developer Use Cases

As a developer, you can use the NotebookLM MCP server to:

*   **Let your local agents chat directly with NotebookLM:** Let your local agents chat directly with NotebookLM for zero-hallucination answers based on your own notebooks.
*   **Stop debugging hallucinations. Start shipping accurate code:** Stop debugging hallucinations and start shipping accurate code by using NotebookLM to provide your agents with a reliable source of information.
*   **Create your own knowledge base:** Create your own knowledge base by uploading your docs to NotebookLM.

## Example

Here's an example of how you might add a notebook to your library:

```
"Add [link] to library tagged 'frontend, react, components'"


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Notebooklm]]
