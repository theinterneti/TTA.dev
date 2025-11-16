#!/bin/bash
# .cline/hooks/pre-tool-use.sh

# This hook prevents the use of 'pip' or 'poetry' in favor of 'uv'.
if [[ "$CLINE_TOOL_COMMAND" == pip* || "$CLINE_TOOL_COMMAND" == poetry* ]]; then
  echo "TTA.dev project policy: Use 'uv' for package management, not 'pip' or 'poetry'."
  exit 1
fi
