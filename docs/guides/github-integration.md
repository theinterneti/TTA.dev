# TTA.dev GitHub Integration - @cline Agent

This document describes how the autonomous Cline agent provides intelligent assistance for TTA.dev GitHub issues.

## Overview

TTA.dev now includes a GitHub Actions integration that enables an AI agent to analyze issues and provide actionable insights. Simply mention `@cline` in any issue comment to trigger autonomous analysis using the TTA.dev knowledge base and primitives.

## How It Works

1. **Trigger**: Comment `@cline [your question]` on any GitHub issue
2. **Analysis**: GitHub Actions starts a Cline CLI instance with access to the full TTA.dev codebase
3. **Response**: AI analyzes the issue and posts a response with TTA.dev-specific recommendations

## Example Usage

```
@cline What primitive should I use for this retry logic?
@cline Analyze this error and suggest a TTA.dev pattern
@cline Generate a WorkflowContext example for this use case
```

## What the Agent Knows

The @cline agent has complete access to TTA.dev's knowledge base and will analyze issues using:

- **AGENTS.md**: Primary rules and package-specific guidance
- **PRIMITIVES_CATALOG.md**: Complete list of available primitives
- **Package documentation**: Detailed usage patterns and examples
- **.clinerules**: Standards and anti-patterns to avoid
- **Examples directory**: Working code samples for common patterns

## Specialized for TTA.dev

Unlike generic AI analysis, the @cline agent specifically recommends:

### 🎯 Package Identification
- Determines which package (tta-dev-primitives, tta-observability-integration, universal-agent-context) relates to the issue
- References appropriate package AGENTS.md for context

### 🧱 Primitive Recommendations
- Suggests specific primitives: `RetryPrimitive`, `CachePrimitive`, `RouterPrimitive`, etc.
- References composition patterns with `>>` and `|` operators
- Points to relevant examples in the `examples/` directory

### 📏 Standards Enforcement
- Enforces TTA.dev best practices (uv instead of pip, modern type hints, etc.)
- References `.clinerules` for standards compliance
- Avoids anti-patterns like manual async orchestration

### 🔧 Code Generation
- Uses Iterative Code Refinement pattern with E2B validation when generating code
- Ensures examples are executable and correct
- Follows TTA.dev coding conventions

## Setup Requirements

To use the @cline agent, the repository must have:

1. **Cline responder workflow**: `.github/workflows/cline-responder.yml` (✓ already committed)
2. **Analysis script**: `git-scripts/analyze-issue.sh` (✓ already committed, executable)
3. **OpenRouter API key**: Secret `OPENROUTER_API_KEY` in GitHub repository secrets
4. **Environment**: "cline-actions" environment configured in GitHub Actions

### Environment Setup

In your GitHub repository settings:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name it: `cline-actions`
4. Add secret: `OPENROUTER_API_KEY` with your OpenRouter API key

## Security & Permissions

- **Environment-scoped**: Uses "cline-actions" environment for security isolation
- **Read-only access**: Only has access to issue content and GitHub Actions context
- **No code execution**: Analysis happens in GitHub Actions without external scripts
- **API authentication**: Uses secure secret storage for AI provider access

## Troubleshooting

### Agent Not Responding

If @cline doesn't respond to your comment:

1. Check that the comment contains "@cline" (case-insensitive)
2. Ensure it's an issue comment, not a pull request comment
3. Verify the GitHub Actions are enabled for your repository
4. Check the Actions tab for any workflow failures
5. Confirm the OPENROUTER_API_KEY secret is set

### Environment Error

If you see "cline-actions environment not found", follow the setup instructions above to create the required environment in GitHub repository settings.

## Integration with Development Workflow

The @cline agent enhances your development workflow by:

- **Reducing research time**: Instantly suggests relevant TTA.dev primitives
- **Standards compliance**: Ensures adherence to TTA.dev best practices
- **Pattern discovery**: Helps developers discover existing solutions
- **Code quality**: Generates examples following our conventions
- **Documentation bridge**: Connects issues directly to our knowledge base

## Technical Architecture

The integration uses:

- **Cline CLI**: Core AI agent runtime
- **GitHub Actions**: Workflow orchestration
- **OpenRouter**: AI model access
- **Environment isolation**: Secure secret management
- **Automated triggers**: Event-driven responses

This creates a seamless experience where developers get AI-powered assistance directly in their GitHub issues, specifically tailored to the TTA.dev ecosystem.


---
**Logseq:** [[TTA.dev/Docs/Guides/Github-integration]]
