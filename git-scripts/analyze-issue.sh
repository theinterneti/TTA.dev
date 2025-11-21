#!/bin/bash
# Analyze a GitHub issue using Cline CLI - TTA.dev specialized version

if [ -z "$1" ]; then
    echo "Usage: $0 <github-issue-url> [prompt] [address]"
    echo "Example: $0 https://github.com/theinterneti/TTA.dev/issues/123"
    echo "Example: $0 https://github.com/theinterneti/TTA.dev/issues/123 'What primitive would solve this?'"
    echo "Example: $0 https://github.com/theinterneti/TTA.dev/issues/123 'What primitive would solve this?' 127.0.0.1:46529"
    exit 1
fi

# Gather the args
ISSUE_URL="$1"
PROMPT="${2:-Analyze this issue and suggest TTA.dev primitives/patterns to solve it.}"
if [ -n "$3" ]; then
    ADDRESS="--address $3"
fi

# TTA.dev specific context for Cline
# Use act mode with yolo for autonomous analysis of TTA.dev issues
cline -y "
You are analyzing a TTA.dev issue. TTA.dev is a Python monorepo with agentic primitives for workflow orchestration.

CRITICAL INSTRUCTIONS:
- Read AGENTS.md, PRIMITIVES_CATALOG.md, and relevant package documentation first
- Identify which TTA.dev package this issue relates to (tta-dev-primitives, tta-observability-integration, universal-agent-context)
- Suggest specific primitives or patterns that solve the problem
- Point to examples/ directory for working code samples
- Follow TTA.dev standards: use uv (not pip), type hints with str | None (not Optional), primitives for workflow patterns
- If generating code, use the Iterative Code Refinement pattern with E2B for validation
- Reference the .clinerules file for standards and anti-patterns

${PROMPT}: ${ISSUE_URL}
" --mode act $ADDRESS -F json | \
    sed -n '/^{/,$p' | \
    jq -r 'select(.say == "completion_result") | .text' | \
    sed 's/\\n/\n/g'
