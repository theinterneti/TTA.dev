#!/bin/bash
# .cline/hooks/task-start.sh

# This hook automatically syncs dependencies at the start of a task.
echo "TTA.dev: Syncing dependencies with 'uv sync --all-extras'..."
uv sync --all-extras
