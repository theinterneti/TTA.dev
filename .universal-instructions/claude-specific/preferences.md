# Claude-Specific Preferences

## Response Format

- **Progress Updates**: After 3-5 tool calls or file edits, provide a brief progress summary
- **Code Changes**: Use edit tools, not full file dumps in chat
- **Error Handling**: Explain root cause first, then provide specific fix

## Tone & Communication

- **Concise but Complete**: Respect user's time while providing full context
- **Specific Examples**: Use actual file names, line numbers, function names
- **Proactive Suggestions**: Anticipate follow-up questions and address them

## Context Management

- **File References**: Use backticks for filenames: `packages/tta-dev-primitives/src/core/base.py`
- **Code References**: Reference specific functions/classes: `WorkflowPrimitive.execute()`
- **Documentation Links**: Point to relevant files: See `docs/architecture/Overview.md`

## Chat Modes

Claude offers different chat modes for different tasks:

- **Normal Mode**: General conversation and code assistance
- **Extended Thinking**: Deep reasoning for complex problems, architecture decisions
- **Code Mode**: Optimized for code generation and editing

Choose the appropriate mode based on task complexity and user needs.


---
**Logseq:** [[TTA.dev/.universal-instructions/Claude-specific/Preferences]]
