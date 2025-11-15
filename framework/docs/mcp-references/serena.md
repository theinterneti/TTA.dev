# Serena

Serena is a powerful, project-based AI coding assistant designed to streamline your development workflow. It provides a comprehensive set of tools for symbolic operations, code analysis, and project management, all accessible through a flexible MCP server. This document provides a comprehensive guide to installing, configuring, and using Serena effectively.

## Getting Started

This section covers the various ways you can install and run Serena.

### Using uvx

The recommended way to run Serena is with `uvx`, which allows you to run the latest version directly from the repository without a local installation.

```bash
uvx --from git+https://github.com/oraios/serena serena
```

### Local Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/oraios/serena
    cd serena
    ```
2.  Run Serena using `uv`:
    ```bash
    uv run serena
    ```

### Using Docker (Experimental)

You can run the Serena MCP server in a Docker container for better security and environment consistency.

```bash
docker run --rm -i --network host -v /path/to/your/projects:/workspaces/projects ghcr.io/oraios/serena:latest serena
```

### Using Nix

If you are a Nix user, you can run Serena with the following command:

```bash
nix run github:oraios/serena -- <command> [options]
```

## Running the MCP Server

The core of Serena is its MCP server, which can be run in two modes:

### Standard I/O Mode

This is the default mode, where the MCP client runs the server as a subprocess and communicates with it over stdin/stdout.

```bash
<serena> start-mcp-server
```

### Streamable HTTP Mode

In this mode, you start the server manually and configure the client to connect to it via a URL.

```bash
<serena> start-mcp-server --transport streamable-http --port <port>
```

## Configuring MCP Clients

Serena can be integrated with a variety of MCP-enabled clients.

### Cline

To add Serena to Cline, use the following command:

```bash
cline mcp add serena -- <serena> start-mcp-server --context ide-assistant --project "$(pwd)"
```

### Other Clients

Serena can also be used with other popular clients like Codex, Claude Desktop, and various terminal-based assistants. Refer to the official Serena documentation for detailed configuration instructions for each client.

## Project Workflow

Serena uses a project-based workflow that involves the following steps:

1.  **Project Creation**: Create a `.serena/project.yml` file in your project directory to configure project-specific settings.
2.  **Project Activation**: Make Serena aware of the project you want to work on, either by activating it in a conversation or by passing the project path as a command-line argument.
3.  **Onboarding**: Serena will perform an onboarding process to get familiar with your project and create memories.
4.  **Coding Tasks**: Use Serena's powerful tools to assist you with your coding tasks.

## Configuration

Serena can be configured at four levels:

1.  **`serena_config.yml`**: Global settings in your user directory.
2.  **Command-Line Arguments**: Overrides global settings for a specific session.
3.  **`.serena/project.yml`**: Project-level configuration.
4.  **Contexts and Modes**: Dynamic adjustments to Serena's behavior.

## Modes and Contexts

### Contexts

A context defines the general environment in which Serena is operating. Pre-defined contexts include `desktop-app`, `agent`, and `ide-assistant`.

### Modes

Modes further refine Serena's behavior for specific tasks. Examples include `planning`, `editing`, `interactive`, and `one-shot`.

## Dashboard and GUI Tool

Serena includes a web-based dashboard for monitoring and managing your session, which is enabled by default. A native GUI tool is also available but is disabled by default.

## Security Considerations

Since Serena can execute shell commands and modify files, it is important to follow these security best practices:

*   Use a version control system like Git.
*   Monitor tool executions carefully.
*   Use a sandboxed environment like Docker.

## Advanced Usage

### Prompting Strategies

For complex tasks, it is often helpful to spend time planning and conceptualizing the task before implementation.

### Running Out of Context

If you run out of context tokens, you can create a summary of the current progress and continue in a new conversation.

### Git Worktrees

Serena works well with Git worktrees, allowing you to parallelize your work.

## Custom Agents

Serena can be integrated with custom agent frameworks like Agno. The official documentation provides a reference implementation and guidance on how to create your own integrations.
