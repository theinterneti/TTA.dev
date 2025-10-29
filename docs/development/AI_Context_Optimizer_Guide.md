# AI Context Optimizer Developer Guide

## 1. Introduction

This guide provides instructions for installing, configuring, and using the `ai-context-optimizer` VSCode extension. This tool is intended to help developers reduce AI token usage and improve the quality of AI interactions during the development of the TTA.dev project.

## 2. Why Use the AI Context Optimizer?

*   **Reduce Costs:** Less tokens means lower API bills.
*   **Improve AI Quality:** More focused context helps the AI generate better responses.
*   **Increase Productivity:** Automates context management, saving you time.

## 3. Installation

1.  **Download the Extension:** Download the latest version of the `ai-context-optimizer` from the [releases page](https://github.com/web-werkstatt/ai-context-optimizer/releases) of the official repository. It is recommended to use the `universal-ai-platform` version.
2.  **Install in VSCode:**
    *   Open VSCode.
    *   Go to the Extensions view (Ctrl+Shift+X).
    *   Click on the "..." menu in the top-right corner and select "Install from VSIX...".
    *   Select the downloaded `.vsix` file.
    *   Restart VSCode when prompted.

## 4. Configuration

The extension works well with its default configuration. However, you can customize its behavior in the VSCode settings (`settings.json`).

```json
{
    "clineTokenManager.autoOptimize": true,
    "clineTokenManager.showStatusBar": true,
    "clineTokenManager.optimizeThreshold": 10000,
    "clineTokenManager.compressionLevel": "smart"
}
```

*   `autoOptimize`: Set to `true` to automatically optimize the context for every AI interaction.
*   `showStatusBar`: Set to `true` to display token usage information in the status bar.
*   `optimizeThreshold`: The token limit above which the optimizer will trigger.
*   `compressionLevel`: The optimization strategy to use. `smart` is recommended.

## 5. How to Use

### 5.1. Dashboard

The main interface for the `ai-context-optimizer` is its dashboard, which can be accessed by clicking on the Token Manager icon in the VSCode sidebar.

The dashboard provides:

*   Real-time token usage statistics.
*   Cost monitoring.
*   Optimization metrics.
*   Quick access to all the extension's features.

### 5.2. Key Features

*   **Cache-Explosion Prevention:** This feature is enabled by default and works in the background to prevent the AI context from becoming bloated.
*   **Smart File Selection:** To use this feature, open the command palette (Ctrl+Shift+P) and run the "Cline Token Manager: Smart File Selection" command. This will open a dialog where you can select the most relevant files for your current task.
*   **Auto-Fix Token Limits:** If you are using Anthropic models, you can use the "Cline Token Manager: Auto-Fix Token Limits" command to remove the artificial token limits imposed by some tools.

## 6. Best Practices for TTA.dev

*   **Always have the extension enabled** when working on features that involve AI interaction.
*   **Use the Smart File Selection feature** to provide the AI with only the most relevant parts of the codebase.
*   **Monitor the dashboard** to keep an eye on token usage and costs.
*   **Report any issues or bugs** you encounter on the project's Slack channel, so we can track them and report them to the extension's developers if necessary.

## 7. Feedback

This is a new tool for our team, and we welcome your feedback. Please share your experiences, both positive and negative, in the #dev-tools channel on Slack.
