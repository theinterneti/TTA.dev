#!/bin/bash

# Get the directory of the script itself to ensure the log path is correct
SCRIPT_DIR=$(dirname "$0")
LOG_FILE="$SCRIPT_DIR/post-message.log"

# Redirect all output to a log file for debugging
exec >> "$LOG_FILE" 2>&1
echo "--- New Hook Execution ---"
date

# Log all available environment variables to see what's available
echo "Available environment variables:"
printenv
echo "-----------------------------"

# The user's message is likely in an environment variable.
# Let's assume it's CLINE_USER_MESSAGE for now.
message="$CLINE_USER_MESSAGE"

echo "Received message from environment: $message"

# Regex to find GitHub URIs (handles various formats)
github_uri_regex="(https?://)?(www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)"

if [[ $message =~ $github_uri_regex ]]; then
    owner=${BASH_REMATCH[3]}
    repo=${BASH_REMATCH[4]}
    uri="github.com/$owner/$repo"
    
    echo "Detected potential MCP URI: $uri"
    
    # Use the GitHub CLI (gh) to inspect the repository contents
    echo "Inspecting repository contents for $owner/$repo..."
    repo_files=$(gh api repos/$owner/$repo/contents/ | jq -r '.[].name')
    echo "Repository files found: $repo_files"

    if echo "$repo_files" | grep -q "package.json"; then
        echo "Detected npm-based MCP. Adding with default npx command."
        uv run python scripts/add_mcp_server.py --uri "$uri"
    elif echo "$repo_files" | grep -q "pyproject.toml"; then
        echo "Detected Python-based MCP. Adding with uvx command."
        uv run python scripts/add_mcp_server.py --manual --name "$owner/$repo" -- uvx --from "git+https://github.com/$owner/$repo" "$repo" start-mcp-server
    else
        echo "Could not determine MCP type for repo '$repo'. Please add manually."
    fi
else
    echo "No GitHub URI found in message."
fi
echo "--- Hook Execution Finished ---"
