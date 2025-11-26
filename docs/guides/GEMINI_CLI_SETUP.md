# Gemini CLI Setup Guide

**Runtime**: Gemini CLI
**Role**: Primary Local Automation Runtime

## 1. Installation

The Gemini CLI is a standalone tool for executing agentic workflows.

### Prerequisites

- Node.js 18+ (recommended) or Python 3.11+
- Valid API Key (Google AI Studio or Vertex AI)

### Install via npm (Recommended)

```bash
npm install -g @google/generative-ai-cli
# OR if using a specific community wrapper (check internal docs)
```

*Note: If "gemini" refers to a specific internal tool or wrapper, ensure it is in your PATH.*

## 2. Configuration

TTA.dev includes a pre-configured settings file at `.gemini/settings.json`.

### Environment Variables

Create a `.env` file or export variables:

```bash
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-2.5-flash" # Recommended for speed/cost
```

### Settings File (`.gemini/settings.json`)

Key configurations enabled:

- **Session Retention**: Keeps context between runs (if supported).
- **Auto-Accept Tools**: Critical for `--yolo` mode.
- **Context Loading**: Loads memory from include directories.

## 3. Usage with APM

The Agent Package Manager (`apm.yml`) is configured to use Gemini by default.

```bash
# Run a workflow
apm run feature-implementation

# Equivalent raw command
gemini --yolo -p .github/prompts/feature-implementation.prompt.md
```

## 4. Troubleshooting

### Common Issues

#### "gemini not found"

- Verify installation: `npm list -g`

- Check PATH: `echo $PATH`
- If using a Python wrapper: `pip install gemini-cli-tool` (verify package name)
