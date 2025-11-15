# Your Personal Cline Expert Guide

This guide provides a comprehensive overview of Cline's features, best practices, and advanced capabilities, synthesized from the official Cline documentation. Use this as your go-to reference for becoming a Cline power user.

## 1. Introduction to Cline: Core Concepts

Cline is an AI coding agent that operates on a client-server architecture. 
- **Cline Core:** A standalone service that manages tasks, AI model integration, and tool orchestration.
- **Frontends (CLI, VSCode):** Interfaces that connect to Cline Core to manage and interact with tasks.

This architecture allows for seamless task handoff between different environments (e.g., from the CLI to the VSCode extension).

## 2. The Command-Line Interface (CLI)

The `cline` CLI is a powerful tool for both interactive use and automation.

### Key Commands:

-   `cline "prompt"`: Instantly starts a new task.
    -   `-o, --oneshot`: Autonomous mode for a single task.
    -   `-y, --yolo`: Fully autonomous mode with no interactivity.
    -   `-m, --mode [act|plan]`: Sets the starting mode.
-   `cline instance`: Manage Cline Core instances.
    -   `new`: Spawns a new instance.
    -   `list`: Lists running instances.
    -   `kill`: Terminates an instance.
-   `cline task`: Manage individual tasks.
    -   `new "prompt"`: Creates a new task.
    -   `open [task-id]`: Resumes a previous task.
    -   `list`: Lists all tasks in history.
    -   `chat`: Enters interactive chat mode.
    -   `send "message"`: Sends a message to the current task.
-   `cline auth`: Configure authentication for AI providers.
-   `cline config`: Manage global configuration settings.

## 3. Core Features

### 3.1. Context Management with @-mentions

@-mentions are a powerful way to bring context into your conversation without copy-pasting.

-   `@/path/to/file`: Includes the full content of a file.
-   `@/path/to/folder/`: Includes the folder structure and all file contents.
-   `@problems`: Provides Cline with all errors and warnings in your workspace.
-   `@terminal`: Shares recent terminal output.
-   `@git-changes`: Shows all uncommitted changes.
-   `@[commit-hash]`: Provides the full diff and metadata for a specific commit.
-   `@https://...`: Fetches and includes the content of a URL.

### 3.2. Automation and Safety

-   **Auto-Approve:** Granular permissions for allowing Cline to perform actions without confirmation (e.g., read files, execute safe commands).
-   **YOLO Mode:** A dangerous, fully autonomous mode that auto-approves *all* actions, including destructive ones. Use with extreme caution, preferably in sandboxed environments.
-   **Checkpoints:** Automatic snapshots of your workspace after each tool use. This allows you to view changes and restore your workspace or task to any previous state, providing a safety net for experimentation.

### 3.3. Customization and Extensibility

-   **Cline Rules (`.clinerules`):** Project-specific or global markdown files that provide persistent, system-level guidance to Cline. You can define coding standards, architectural patterns, and required workflows. Cline also supports `AGENTS.md` as a fallback.
-   **Hooks:** Executable scripts that run at key moments in the Cline lifecycle (e.g., `PreToolUse`, `TaskStart`). They allow you to inject custom logic, validate operations, and enforce policies.
-   **Workflows (`/[workflow-name.md]`):** Reusable, multi-step templates for repetitive tasks. You can define a sequence of commands, tool uses, and prompts in a markdown file to automate complex processes like PR reviews or deployments.

### 3.4. IDE Integration

-   **Commands & Shortcuts:** Access Cline's capabilities directly from the VSCode interface.
-   **Code Commands:**
    -   **Right-Click -> "Add to Cline"**: Sends selected code to the chat.
    -   **Lightbulb Menu**:
        -   `Fix with Cline`: For errors and warnings.
        -   `Explain with Cline`: To understand complex code.
        -   `Improve with Cline`: For refactoring and optimizations.
-   **Terminal Integration:** Right-click in the terminal and select "Add to Cline" to send output directly to the chat.

## 4. Advanced Concepts

### 4.1. Plan & Act Mode

A structured workflow for development:
-   **Plan Mode:** Cline explores the codebase, asks questions, and collaborates with you to create a detailed implementation plan. No file modifications occur in this mode.
-   **Act Mode:** Cline executes the plan, modifying files, running commands, and using its tools to build the solution.

### 4.2. Task & Context Management

-   **Tasks:** Self-contained work sessions that store the entire conversation, code changes, and tool usage.
-   **`/newtask` Slash Command & `new_task` Tool:** When a context window fills up, this allows you to start a new task while intelligently carrying over essential context (e.g., project goals, completed work, next steps), leaving behind the noise of the previous session.
-   **Context Windows:** The "working memory" of the AI model. Larger context windows allow Cline to understand more of your project at once but can increase cost and latency. It's crucial to manage context efficiently by starting new tasks and using `@-mentions` strategically.

### 4.3. Extending Cline with MCP (Model Context Protocol)

-   **MCP Servers:** External services that provide additional tools and resources to Cline, allowing it to interact with any API or system.
-   **Configuration:** MCP servers are configured in `cline_mcp_settings.json`, supporting both local (`stdio`) and remote (`sse`) servers.
-   **Development Protocol:** A structured process, often enforced by a `.clinerules` file, for building robust and reliable MCP servers. The protocol emphasizes planning, comprehensive logging, strong typing, and thorough testing.

### 4.4. Persistent Knowledge with Memory Bank

The Memory Bank is a user-defined methodology for creating a structured documentation system that Cline can read to "remember" project details across sessions.
-   **Structure:** A set of markdown files (e.g., `projectbrief.md`, `techContext.md`, `progress.md`) that build a complete picture of the project.
-   **Workflow:** You instruct Cline to "follow custom instructions" or "update memory bank" to interact with this system.
-   **Benefit:** It transforms Cline from a stateless assistant into a persistent development partner with long-term project knowledge.

## 5. Best Practices and Pro-Tips

-   **Start in Plan Mode** for any non-trivial task to ensure a clear strategy before implementation.
-   **Use @-mentions liberally** to provide precise context instead of relying on large, unfocused context.
-   **Leverage Workflows** to automate any repetitive, multi-step process.
-   **Use Checkpoints** as a safety net, especially when experimenting or using `auto-approve`.
-   **Manage Your Context Window.** When the context meter gets high, use `/newtask` to start fresh without losing momentum.
-   **Create a `.clinerules` file** for your projects to enforce consistency and provide project-specific guidance.
-   **Build a Memory Bank** for long-running projects to give Cline a persistent source of truth.
-   **Extend Cline's capabilities** by building or installing MCP servers for the tools and APIs you use most.
