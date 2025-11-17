#!/bin/bash
# TTA.dev Multi-Agent Post-Commit Hook
# Logs commits for oversight and creates notifications

set -e

WORKTREE_PATH=$(git rev-parse --show-toplevel)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

# Identify agent
if [[ "$WORKTREE_PATH" == *"TTA.dev-augment"* ]]; then
    AGENT="augment"
elif [[ "$WORKTREE_PATH" == *"TTA.dev-cline"* ]]; then
    AGENT="cline"
elif [[ "$WORKTREE_PATH" == *"TTA.dev-copilot"* ]]; then
    AGENT="copilot"
else
    AGENT="unknown"
fi

# Create commit log directory if it doesn't exist
LOG_DIR="$WORKTREE_PATH/.agent-commits"
mkdir -p "$LOG_DIR"

# Log commit details
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="$LOG_DIR/commits-$AGENT.log"

cat >> "$LOG_FILE" << EOF
---
Timestamp: $TIMESTAMP
Agent: $AGENT
Branch: $BRANCH
Commit: $COMMIT_SHA
Message: $COMMIT_MSG
Files Changed:
$(git diff-tree --no-commit-id --name-status -r $COMMIT_SHA)

EOF

echo "✅ Commit logged to $LOG_FILE"

# If this is NOT copilot, notify copilot worktree
if [ "$AGENT" != "copilot" ]; then
    COPILOT_WORKTREE="/home/thein/repos/TTA.dev-copilot"
    if [ -d "$COPILOT_WORKTREE" ]; then
        NOTIFICATION_DIR="$COPILOT_WORKTREE/.agent-notifications"
        mkdir -p "$NOTIFICATION_DIR"
        
        NOTIFICATION_FILE="$NOTIFICATION_DIR/pending-$AGENT-$(date +%s).json"
        cat > "$NOTIFICATION_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "agent": "$AGENT",
  "branch": "$BRANCH",
  "commit": "$COMMIT_SHA",
  "message": "$(echo "$COMMIT_MSG" | head -1)",
  "worktree": "$WORKTREE_PATH",
  "reviewed": false
}
EOF
        echo "📬 Notification created for copilot agent: $NOTIFICATION_FILE"
    fi
fi
