# Claude-Specific Capabilities

## Artifacts

Claude can generate content in artifacts (separate, editable documents). When generating substantial code files or documentation:

- Use artifacts for complete, standalone files (>50 lines)
- Use inline code blocks for small snippets or examples
- Create separate artifacts for different file types (Python, config, docs)

## Extended Context

Claude has extended context windows (200K+ tokens). Leverage this:

- Reference multiple files when needed without concern for token limits
- Provide comprehensive context from the workspace
- Don't hesitate to include full file contents for analysis

## Reasoning Style

Claude excels at step-by-step reasoning:

- **Think through complex problems** using the `<thinking>` pattern
- **Break down multi-step tasks** into clear phases
- **Explain the "why"** behind architectural decisions

## Structured Output

Claude works well with XML and structured formats:

- Use XML tags for structured thinking: `<analysis>`, `<implementation>`, `<verification>`
- Prefer clear hierarchical structures over flat lists
- Use markdown tables for comparative information

## Extended Thinking Mode

Claude supports Extended Thinking mode for complex reasoning:

- Available for deep problem analysis and planning
- Useful for architecture decisions, debugging complex issues
- Access via chat mode selection in supported tools


---
**Logseq:** [[TTA.dev/.universal-instructions/Claude-specific/Capabilities]]
