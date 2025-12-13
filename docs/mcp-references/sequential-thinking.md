# Sequential Thinking MCP Server

This document provides an overview of the Sequential Thinking MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To facilitate structured, progressive thinking through defined stages.
*   **Key Features:**
    *   **Structured Thinking Framework:** Organizes thoughts through standard cognitive stages (Problem Definition, Research, Analysis, Synthesis, Conclusion).
    *   **Thought Tracking:** Records and manages sequential thoughts with metadata.
    *   **Related Thought Analysis:** Identifies connections between similar thoughts.
    *   **Progress Monitoring:** Tracks your position in the overall thinking sequence.
    *   **Summary Generation:** Creates concise overviews of the entire thought process.

## Usage by TTA.dev Agents

TTA.dev agents use the Sequential Thinking server to:

*   **Break Down Complex Problems:** Break down complex problems into a sequence of manageable thoughts.
*   **Track Their Thinking Process:** Track the progression of their thinking process and generate summaries.
*   **Ensure a Methodical Approach:** Ensure a methodical approach to problem-solving by following a structured thinking framework.

## Developer Use Cases

As a developer, you can use the Sequential Thinking server to:

*   **Work Through Important Decisions Methodically:** Work through important decisions methodically by breaking them down into a series of sequential thoughts.
*   **Structure Your Research Approach:** Structure your research approach with clear stages.
*   **Develop Ideas Progressively Before Writing:** Develop ideas progressively before writing by organizing your thoughts in a structured way.

## Example

Here's an example of how you might use the `process_thought` tool to begin a thinking process:

```python
# First thought in a 5-thought sequence
process_thought(
    thought="The problem of climate change requires analysis of multiple factors including emissions, policy, and technology adoption.",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True,
    stage="Problem Definition",
    tags=["climate", "global policy", "systems thinking"],
    axioms_used=["Complex problems require multifaceted solutions"],
    assumptions_challenged=["Technology alone can solve climate change"]
)


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Sequential-thinking]]
