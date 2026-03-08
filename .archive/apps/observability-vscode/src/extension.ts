// Logseq: [[TTA.dev/Apps/Observability-vscode/Src/Extension]]
/**
 * TTA Observability VS Code Extension
 *
 * Provides a webview panel for viewing TTA.dev workflow traces in VS Code.
 * Reuses the existing web dashboard UI from tta-observability-ui package.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

/**
 * Extension activation entry point
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('TTA Observability extension is now active');

    // Create status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.command = 'tta.openDashboard';
    statusBarItem.text = '$(pulse) TTA: 0 traces';
    statusBarItem.tooltip = 'Click to open TTA Observability Dashboard';

    const config = vscode.workspace.getConfiguration('tta');
    if (config.get('showStatusBar', true)) {
        statusBarItem.show();
    }

    // Track active dashboard panel
    let dashboardPanel: vscode.WebviewPanel | undefined = undefined;

    // Command: Open Dashboard
    const openDashboard = vscode.commands.registerCommand('tta.openDashboard', () => {
        if (dashboardPanel) {
            // Panel already exists, just reveal it
            dashboardPanel.reveal(vscode.ViewColumn.Two);
        } else {
            // Create new panel
            dashboardPanel = vscode.window.createWebviewPanel(
                'ttaObservability',
                'TTA Observability',
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true,
                    localResourceRoots: [
                        vscode.Uri.file(path.join(context.extensionPath, 'resources'))
                    ]
                }
            );

            // Set webview content
            dashboardPanel.webview.html = getWebviewContent(context, dashboardPanel.webview);

            // Handle panel disposal
            dashboardPanel.onDidDispose(
                () => {
                    dashboardPanel = undefined;
                },
                null,
                context.subscriptions
            );

            // Handle messages from webview
            dashboardPanel.webview.onDidReceiveMessage(
                message => {
                    switch (message.type) {
                        case 'updateTraceCount':
                            statusBarItem.text = `$(pulse) TTA: ${message.count} traces`;
                            break;
                        case 'error':
                            vscode.window.showErrorMessage(`TTA Observability: ${message.message}`);
                            break;
                        case 'info':
                            vscode.window.showInformationMessage(`TTA Observability: ${message.message}`);
                            break;
                    }
                },
                undefined,
                context.subscriptions
            );
        }
    });

    // Command: Refresh Dashboard
    const refreshDashboard = vscode.commands.registerCommand('tta.refreshDashboard', () => {
        if (dashboardPanel) {
            dashboardPanel.webview.postMessage({ type: 'refresh' });
            vscode.window.showInformationMessage('TTA Dashboard refreshed');
        } else {
            vscode.window.showWarningMessage('TTA Dashboard is not open');
        }
    });

    // Command: Clear Traces
    const clearTraces = vscode.commands.registerCommand('tta.clearTraces', async () => {
        const choice = await vscode.window.showWarningMessage(
            'Are you sure you want to clear all traces?',
            'Yes',
            'No'
        );

        if (choice === 'Yes') {
            const config = vscode.workspace.getConfiguration('tta');
            const serviceUrl = config.get('serviceUrl', 'http://localhost:8765');

            try {
                const response = await fetch(`${serviceUrl}/api/cleanup`, {
                    method: 'POST'
                });

                if (response.ok) {
                    const result = await response.json();
                    vscode.window.showInformationMessage(
                        `Cleared ${result.deleted_count} traces`
                    );

                    if (dashboardPanel) {
                        dashboardPanel.webview.postMessage({ type: 'refresh' });
                    }
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(
                    `Failed to clear traces: ${error}`
                );
            }
        }
    });

    // Command: Start Service (placeholder - would need to spawn process)
    const startService = vscode.commands.registerCommand('tta.startService', () => {
        vscode.window.showInformationMessage(
            'To start the TTA Observability service, run: tta-observability-ui start'
        );

        // Open integrated terminal with command
        const terminal = vscode.window.createTerminal('TTA Observability');
        terminal.sendText('cd packages/tta-observability-ui && tta-observability-ui start');
        terminal.show();
    });

    // Command: Stop Service
    const stopService = vscode.commands.registerCommand('tta.stopService', () => {
        vscode.window.showInformationMessage(
            'To stop the service, press Ctrl+C in the terminal running it'
        );
    });

    // Register all commands
    context.subscriptions.push(
        openDashboard,
        refreshDashboard,
        clearTraces,
        startService,
        stopService,
        statusBarItem
    );

    // Check if service is running
    checkServiceHealth(statusBarItem);

    // Periodically check service health
    const healthCheckInterval = setInterval(() => {
        checkServiceHealth(statusBarItem);
    }, 30000); // Every 30 seconds

    context.subscriptions.push({
        dispose: () => clearInterval(healthCheckInterval)
    });
}

/**
 * Check if the TTA Observability service is running
 */
async function checkServiceHealth(statusBarItem: vscode.StatusBarItem) {
    const config = vscode.workspace.getConfiguration('tta');
    const serviceUrl = config.get('serviceUrl', 'http://localhost:8765');

    try {
        const response = await fetch(`${serviceUrl}/health`);
        if (response.ok) {
            statusBarItem.tooltip = `TTA Observability: Service running at ${serviceUrl}`;
            vscode.commands.executeCommand('setContext', 'tta.serviceRunning', true);
        } else {
            throw new Error('Service not healthy');
        }
    } catch (error) {
        statusBarItem.tooltip = `TTA Observability: Service not running. Click to view instructions.`;
        vscode.commands.executeCommand('setContext', 'tta.serviceRunning', false);
    }
}

/**
 * Generate HTML content for the webview
 *
 * This loads the existing dashboard UI from tta-observability-ui package
 * and embeds it in the VS Code webview.
 */
function getWebviewContent(context: vscode.ExtensionContext, webview: vscode.Webview): string {
    const config = vscode.workspace.getConfiguration('tta');
    const serviceUrl = config.get('serviceUrl', 'http://localhost:8765');

    // Try to find the UI files from the sibling package
    const uiPackagePath = path.join(
        context.extensionPath,
        '..',
        'tta-observability-ui',
        'ui'
    );

    let dashboardHtml = '';

    // Check if UI files exist
    const indexPath = path.join(uiPackagePath, 'index.html');
    if (fs.existsSync(indexPath)) {
        // Load the actual dashboard HTML
        dashboardHtml = fs.readFileSync(indexPath, 'utf8');

        // Update paths to work with webview
        const cssPath = webview.asWebviewUri(
            vscode.Uri.file(path.join(uiPackagePath, 'app.css'))
        );
        const jsPath = webview.asWebviewUri(
            vscode.Uri.file(path.join(uiPackagePath, 'app.js'))
        );

        // Replace relative paths with webview URIs
        dashboardHtml = dashboardHtml
            .replace('href="app.css"', `href="${cssPath}"`)
            .replace('src="app.js"', `src="${jsPath}"`);

        // Inject service URL configuration
        dashboardHtml = dashboardHtml.replace(
            '<script src="app.js"',
            `<script>
                window.TTA_SERVICE_URL = '${serviceUrl}';
                window.TTA_IN_VSCODE = true;

                // Send trace count updates to extension
                window.addEventListener('tta:traceCountUpdate', (e) => {
                    const vscode = acquireVsCodeApi();
                    vscode.postMessage({
                        type: 'updateTraceCount',
                        count: e.detail.count
                    });
                });
            </script>
            <script src="app.js"`
        );
    } else {
        // Fallback: Show instructions if UI files not found
        dashboardHtml = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>TTA Observability</title>
                <style>
                    body {
                        font-family: var(--vscode-font-family);
                        color: var(--vscode-foreground);
                        background: var(--vscode-editor-background);
                        padding: 20px;
                        line-height: 1.6;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    h1 {
                        color: var(--vscode-textLink-foreground);
                    }
                    .status {
                        background: var(--vscode-editor-selectionBackground);
                        padding: 15px;
                        border-radius: 4px;
                        margin: 20px 0;
                    }
                    code {
                        background: var(--vscode-textCodeBlock-background);
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: var(--vscode-editor-font-family);
                    }
                    .command {
                        background: var(--vscode-terminal-background);
                        padding: 12px;
                        border-radius: 4px;
                        margin: 10px 0;
                        font-family: var(--vscode-editor-font-family);
                    }
                    a {
                        color: var(--vscode-textLink-foreground);
                        text-decoration: none;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔍 TTA Observability Dashboard</h1>

                    <div class="status">
                        <h2>⚙️ Setup Required</h2>
                        <p>The TTA Observability service needs to be running to view traces.</p>
                    </div>

                    <h3>📋 Steps to Get Started:</h3>

                    <p><strong>1. Start the TTA Observability Service:</strong></p>
                    <div class="command">
                        <code>cd packages/tta-observability-ui</code><br>
                        <code>tta-observability-ui start</code>
                    </div>

                    <p><strong>2. Verify Service is Running:</strong></p>
                    <p>Open <a href="${serviceUrl}">${serviceUrl}</a> in your browser</p>

                    <p><strong>3. Run a TTA Workflow:</strong></p>
                    <div class="command">
                        <code>uv run examples/ui_test.py</code>
                    </div>

                    <p><strong>4. Refresh this Dashboard:</strong></p>
                    <p>Use the command palette: <code>TTA: Refresh Dashboard</code></p>

                    <h3>📚 Documentation:</h3>
                    <ul>
                        <li><a href="command:workbench.action.openSettings?%5B%22tta%22%5D">Extension Settings</a></li>
                        <li><a href="${serviceUrl}/docs">API Documentation</a></li>
                        <li>Quick Start: <code>packages/tta-observability-ui/QUICKSTART.md</code></li>
                    </ul>

                    <h3>💡 Tip:</h3>
                    <p>Enable <strong>Auto-start Service</strong> in settings to automatically start the service when VS Code opens.</p>
                </div>
            </body>
            </html>
        `;
    }

    return dashboardHtml;
}

/**
 * Extension deactivation
 */
export function deactivate() {
    console.log('TTA Observability extension deactivated');
}
