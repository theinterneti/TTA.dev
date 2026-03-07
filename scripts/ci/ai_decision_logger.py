#!/usr/bin/env python3
"""Immutable audit logging for AI agent decisions in CI."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def log_ai_decision(
    agent_name: str,
    proposed_action: str,
    confidence_score: float,
    rationale: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Log an AI agent decision with immutable audit trail.

    Args:
        agent_name: Name of the AI agent making the decision
        proposed_action: Description of the action being proposed
        confidence_score: Confidence score (0.0-1.0)
        rationale: Structured reasoning behind the decision
        metadata: Additional context (PR number, commit SHA, etc.)

    Returns:
        Path to the created audit log file
    """
    if not 0.0 <= confidence_score <= 1.0:
        raise ValueError(f"confidence_score must be 0.0-1.0, got {confidence_score}")

    trace_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Get CI context
    ci_context = {
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_number": os.getenv("GITHUB_RUN_NUMBER"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "github_ref": os.getenv("GITHUB_REF"),
        "github_actor": os.getenv("GITHUB_ACTOR"),
    }

    audit_log = {
        "trace_id": trace_id,
        "timestamp": timestamp,
        "agent_name": agent_name,
        "agent_version": os.getenv("AGENT_VERSION", "unknown"),
        "proposed_action": proposed_action,
        "confidence_score": confidence_score,
        "rationale": rationale,
        "ci_context": ci_context,
        "metadata": metadata or {},
        "otel_trace_parent": os.getenv("TRACEPARENT"),
    }

    # Create logs directory
    logs_dir = Path("ci-ai-decisions")
    logs_dir.mkdir(exist_ok=True)

    # Write immutable log file
    log_file = logs_dir / f"{timestamp.replace(':', '-')}_{trace_id[:8]}.json"
    with open(log_file, "w") as f:
        json.dump(audit_log, f, indent=2)

    print(f"✅ AI decision logged: {log_file}", file=sys.stderr)
    print(f"Trace ID: {trace_id}", file=sys.stderr)

    return log_file


def main():
    """CLI interface for logging AI decisions."""
    import argparse

    parser = argparse.ArgumentParser(description="Log AI agent decisions")
    parser.add_argument("--agent-name", required=True, help="Name of AI agent")
    parser.add_argument("--action", required=True, help="Proposed action")
    parser.add_argument(
        "--confidence", type=float, required=True, help="Confidence (0.0-1.0)"
    )
    parser.add_argument("--rationale", required=True, help="Decision rationale")
    parser.add_argument(
        "--metadata",
        type=json.loads,
        default={},
        help="Additional metadata as JSON",
    )

    args = parser.parse_args()

    log_file = log_ai_decision(
        agent_name=args.agent_name,
        proposed_action=args.action,
        confidence_score=args.confidence,
        rationale=args.rationale,
        metadata=args.metadata,
    )

    print(log_file)


if __name__ == "__main__":
    main()
