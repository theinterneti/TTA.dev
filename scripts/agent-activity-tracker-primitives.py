#!/usr/bin/env python3
"""
Agent Activity Tracker - Monitor VS Code and Copilot activity using TTA.dev primitives.

This script uses TTA.dev workflow primitives to monitor file system changes
and emit both OpenTelemetry traces AND Prometheus metrics.

This demonstrates dogfooding: using our own observability framework to monitor agent activity.

Usage:
    python scripts/agent-activity-tracker-primitives.py --workspace /path/to/workspace
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

from observability_integration import initialize_observability
from prometheus_client import Counter, Gauge, start_http_server
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics (still useful for scraping)
files_modified_total = Counter(
    "copilot_files_modified_total",
    "Total number of files modified during potential Copilot sessions",
    ["file_type", "operation"],
)

session_active = Gauge(
    "copilot_session_active",
    "Whether a Copilot session is currently active (1=active, 0=inactive)",
)


class FileEventValidationPrimitive(InstrumentedPrimitive[dict, dict]):
    """Validate and filter file system events."""

    def __init__(self):
        """Initialize primitive."""
        super().__init__(name="validate_file_event")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Validate if file should be tracked."""
        src_path = str(input_data["src_path"])

        # Ignore patterns
        ignore_patterns = [
            ".git/",
            ".venv/",
            "node_modules/",
            "__pycache__/",
            ".pytest_cache/",
            ".ruff_cache/",
            ".vscode/",
            "htmlcov/",
            "dist/",
            "build/",
        ]

        for pattern in ignore_patterns:
            if pattern in src_path:
                return {
                    **input_data,
                    "should_track": False,
                    "reason": f"matches {pattern}",
                }

        # Track extensions
        track_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".md",
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".txt",
            ".sh",
        }

        should_track = any(src_path.endswith(ext) for ext in track_extensions)

        return {
            **input_data,
            "should_track": should_track,
            "reason": "valid extension" if should_track else "not tracked extension",
        }


class FileTypeClassificationPrimitive(InstrumentedPrimitive[dict, dict]):
    """Classify file type from path."""

    def __init__(self):
        """Initialize primitive."""
        super().__init__(name="classify_file_type")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Classify file type."""
        src_path = str(input_data["src_path"])

        if src_path.endswith(".py"):
            file_type = "python"
        elif src_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            file_type = "javascript"
        elif src_path.endswith(".md"):
            file_type = "markdown"
        elif src_path.endswith((".yml", ".yaml")):
            file_type = "yaml"
        elif src_path.endswith(".json"):
            file_type = "json"
        elif src_path.endswith(".toml"):
            file_type = "toml"
        elif src_path.endswith(".sh"):
            file_type = "shell"
        else:
            file_type = "other"

        return {**input_data, "file_type": file_type}


class MetricsEmissionPrimitive(InstrumentedPrimitive[dict, dict]):
    """Emit Prometheus metrics for file event."""

    def __init__(self):
        """Initialize primitive."""
        super().__init__(name="emit_metrics")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Emit metrics to Prometheus."""
        if input_data.get("should_track"):
            file_type = input_data["file_type"]
            operation = input_data["operation"]

            # Increment Prometheus counter
            files_modified_total.labels(file_type=file_type, operation=operation).inc()

            logger.info(
                f"📊 Metrics emitted: {operation} {file_type} file",
                extra={
                    "correlation_id": context.correlation_id,
                    "file_type": file_type,
                    "operation": operation,
                },
            )

        return input_data


class SessionManagementPrimitive(InstrumentedPrimitive[dict, dict]):
    """Manage session state (start/update/end)."""

    def __init__(self, session_tracker: dict):
        """Initialize primitive."""
        super().__init__(name="manage_session")
        self.session_tracker = session_tracker

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Manage session state."""
        current_time = time.time()

        if input_data.get("should_track"):
            # Start or update session
            if self.session_tracker.get("start_time") is None:
                self.session_tracker["start_time"] = current_time
                session_active.set(1)
                logger.info("🎯 Agent session started")

            self.session_tracker["last_activity"] = current_time

        return {
            **input_data,
            "session_duration": (
                current_time - self.session_tracker.get("start_time", current_time)
            ),
        }


class AgentActivityHandler(FileSystemEventHandler):
    """Handler that processes file events through TTA.dev workflow."""

    def __init__(self, workspace_path: Path, workflow: SequentialPrimitive):
        """Initialize handler."""
        self.workspace_path = workspace_path
        self.workflow = workflow
        self.session_tracker: dict[str, Any] = {}
        self.event_loop = asyncio.new_event_loop()

    def _process_event(self, event: FileSystemEvent, operation: str) -> None:
        """Process file system event through workflow."""
        if event.is_directory:
            return

        # Convert event to workflow input
        src_path_str = str(event.src_path)
        rel_path = Path(src_path_str).relative_to(self.workspace_path)

        input_data = {
            "src_path": src_path_str,
            "rel_path": str(rel_path),
            "operation": operation,
        }

        # Create workflow context with correlation ID
        context = WorkflowContext(
            correlation_id=f"file-{operation}-{int(time.time() * 1000)}",
            workflow_id="agent-activity-tracker",
        )

        # Execute workflow asynchronously
        try:
            result = self.event_loop.run_until_complete(
                self.workflow.execute(input_data, context)
            )

            if result.get("should_track"):
                logger.info(
                    f"✏️  {operation.title()}: {rel_path} ({result['file_type']})"
                )
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}", exc_info=True)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        self._process_event(event, "modified")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation."""
        self._process_event(event, "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion."""
        self._process_event(event, "deleted")


def build_workflow(session_tracker: dict) -> SequentialPrimitive:
    """Build file event processing workflow using primitives."""
    # Sequential workflow: validate -> classify -> emit metrics -> manage session
    return (
        FileEventValidationPrimitive()
        >> FileTypeClassificationPrimitive()
        >> MetricsEmissionPrimitive()
        >> SessionManagementPrimitive(session_tracker)
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track agent activity using TTA.dev primitives"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace directory to monitor (default: current directory)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Prometheus metrics port (default: 8001)",
    )
    args = parser.parse_args()

    # Validate workspace
    if not args.workspace.exists():
        logger.error(f"❌ Workspace not found: {args.workspace}")
        sys.exit(1)

    logger.info("🚀 Initializing TTA.dev observability...")

    # Initialize observability (OpenTelemetry + Prometheus)
    success = initialize_observability(
        service_name="agent-activity-tracker",
        enable_prometheus=True,
        prometheus_port=args.port,
    )

    if success:
        logger.info("✅ OpenTelemetry and Prometheus initialized")
    else:
        logger.warning("⚠️  OpenTelemetry unavailable, continuing with Prometheus only")

    # Start additional Prometheus metrics server for custom metrics
    try:
        start_http_server(args.port)
        logger.info(f"✅ Metrics server started on port {args.port}")
    except OSError as e:
        logger.error(f"❌ Failed to start metrics server: {e}")
        sys.exit(1)

    logger.info(f"🔍 Monitoring workspace: {args.workspace}")
    logger.info(f"📊 Metrics: http://localhost:{args.port}/metrics")
    logger.info("🔗 Traces: http://localhost:16686 (Jaeger)")

    # Build workflow
    session_tracker: dict[str, Any] = {}
    workflow = build_workflow(session_tracker)

    # Set up file system observer
    event_handler = AgentActivityHandler(args.workspace, workflow)
    observer = Observer()
    observer.schedule(event_handler, str(args.workspace), recursive=True)
    observer.start()

    logger.info("🚀 Agent activity tracker running with TTA.dev primitives...")
    logger.info("   Each file change creates OpenTelemetry traces!")
    logger.info("   Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping agent activity tracker...")
        observer.stop()
        observer.join()
        logger.info("✅ Tracker stopped")


if __name__ == "__main__":
    main()
