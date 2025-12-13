# TTA Observability VS Code Extension

Real-time observability dashboard for TTA.dev workflows, integrated directly into VS Code.

## Features

- **🔍 Webview Dashboard**: View traces, metrics, and primitive statistics without leaving VS Code
- **⚡ Real-Time Updates**: WebSocket connection for live trace updates
- **📊 Status Bar Integration**: Quick glance at trace count
- **🎯 Commands**: Open dashboard, refresh, clear traces, manage service
- **🎨 VS Code Theme**: Matches your editor theme automatically

## Installation

### Development Setup

1. Navigate to the extension directory:
   ```bash
   cd apps/vscode-extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Compile TypeScript:
   ```bash
   npm run compile
   ```

4. Open in VS Code and press `F5` to launch Extension Development Host

### From VSIX

```bash
code --install-extension tta-observability-vscode-0.1.0.vsix
```

## Usage

### Quick Start

1. **Start the TTA Observability Service:**
   ```bash
   tta-observability-ui start
   ```
   Or use command: `TTA: Start Observability Service`

2. **Open Dashboard:**
   - Click status bar item: `$(pulse) TTA: 0 traces`
   - Or use command: `TTA: Open Observability Dashboard`
   - Or press `Ctrl+Shift+P` → `TTA: Open Observability Dashboard`

3. **Run TTA Workflows:**
   ```python
   from observability_integration import initialize_observability

   initialize_observability(
       service_name="my-app",
       enable_tta_ui=True
   )
   ```

4. **Watch Traces Appear!**
   - Dashboard updates in real-time
   - Status bar shows trace count
   - Click any trace for details

### Commands

All commands available via `Ctrl+Shift+P`:

| Command | Description |
|---------|-------------|
| `TTA: Open Observability Dashboard` | Open webview panel with dashboard |
| `TTA: Refresh Dashboard` | Reload dashboard data |
| `TTA: Clear All Traces` | Delete all traces from storage |
| `TTA: Start Observability Service` | Open terminal to start service |
| `TTA: Stop Observability Service` | Instructions to stop service |

### Status Bar

The status bar item shows:
- `$(pulse) TTA: 0 traces` - Number of traces collected
- Click to open dashboard
- Tooltip shows service status

### Configuration

Configure via `Settings` → `Extensions` → `TTA Observability`:

```json
{
  "tta.serviceUrl": "http://localhost:8765",
  "tta.autoStartService": false,
  "tta.showStatusBar": true,
  "tta.refreshInterval": 5000
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `serviceUrl` | `http://localhost:8765` | URL of TTA Observability service |
| `autoStartService` | `false` | Auto-start service on VS Code launch |
| `showStatusBar` | `true` | Show trace count in status bar |
| `refreshInterval` | `5000` | Refresh interval (ms), 0 for WebSocket only |

## Requirements

- **TTA Observability Service** must be running
- Install: `pip install tta-observability-ui`
- Start: `tta-observability-ui start`

## Architecture

This extension is a **minimal wrapper** around the existing web dashboard:

```
VS Code Extension (TypeScript)
    ↓
Webview Panel (loads Phase 2 UI)
    ↓
FastAPI Service (localhost:8765)
    ↓
SQLite Storage
```

**Benefits:**
- ✅ Reuses 100% of Phase 2 dashboard code
- ✅ Single source of truth for UI
- ✅ Consistent experience in browser & VS Code
- ✅ Minimal maintenance overhead

## Development

### Compile TypeScript

```bash
npm run compile
```

### Watch Mode

```bash
npm run watch
```

### Package Extension

```bash
npm run package
```

Creates `tta-observability-vscode-0.1.0.vsix`

### Debug

1. Open `packages/tta-observability-vscode` in VS Code
2. Press `F5` to launch Extension Development Host
3. Use `Ctrl+Shift+P` → `TTA: Open Observability Dashboard`

## Troubleshooting

### Dashboard Shows "Setup Required"

**Problem:** UI files not found

**Solution:** Ensure `tta-observability-ui` package is installed:
```bash
cd packages/tta-observability-ui
ls ui/  # Should show index.html, app.css, app.js
```

### "Service Not Running"

**Problem:** TTA Observability service not started

**Solution:**
```bash
tta-observability-ui start
```

Or use command: `TTA: Start Observability Service`

### Status Bar Not Showing

**Problem:** Disabled in settings

**Solution:**
```json
{
  "tta.showStatusBar": true
}
```

### WebSocket Connection Failed

**Problem:** Service URL misconfigured

**Solution:** Check settings:
```json
{
  "tta.serviceUrl": "http://localhost:8765"
}
```

## Contributing

See main TTA.dev repository: [github.com/theinterneti/TTA.dev](https://github.com/theinterneti/TTA.dev)

## License

MIT

## Related Packages

- **tta-observability-ui** - FastAPI service and web dashboard
- **tta-observability-integration** - OpenTelemetry integration
- **tta-dev-primitives** - Core workflow primitives

## Resources

- **Documentation**: `packages/tta-observability-ui/README.md`
- **Quick Start**: `packages/tta-observability-ui/QUICKSTART.md`
- **API Docs**: `http://localhost:8765/docs` (when service running)
- **TTA.dev**: `AGENTS.md`


---
**Logseq:** [[TTA.dev/Apps/Observability-vscode/Readme]]
