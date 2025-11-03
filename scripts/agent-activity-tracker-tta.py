#!/usr/bin/env python3
"""
Agent Activity Tracker (TTA Primitives Version)

This version properly uses TTA.dev primitives and observability integration.
Monitors file system changes and emits metrics using the TTA observability framework.

Key improvements over standalone version:
- Uses InstrumentedPrimitive for automatic tracing
- Leverages WorkflowContext for correlation
- Integrates with OpenTelemetry spans
- Composes with other TTA primitives via operators

Usage:
    python scripts/agent-activity-tracker-tta.py --workspace /path/to/workspace
"""

import argparse
import asyncio
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# TTA.dev imports
from observability_integration import initialize_observability, is_observability_enabled
from prometheus_client import Counter, Gauge, start_http_server
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics
files_modified_total = Counter(
    "copilot_files_modified_total",
    "Total number of files modified during potential Copilot sessions",
    ["file_type", "operation"],
)

session_duration_seconds = Gauge(
    "copilot_session_duration_seconds",
    "Duration of current Copilot session in seconds",
)

file_edit_frequency = Counter(
    "copilot_file_edit_frequency_total",
    "Frequency of edits to specific files",
    ["filename"],
)

session_active = Gauge(
    "copilot_session_active",
    "Whether a Copilot session is currently active (1=active, 0=inactive)",
)


class FileChangeEvent:
    """Input type for file change processing."""

    def __init__(
        self,
        path: str,
        file_type: str,
        operation: str,
        relative_path: str,
    ):
        self.path = path
        self.file_type = file_type
        self.operation = operation
        self.relative_path = relative_path
        self.timestamp = time.time()


class MetricsUpdate:
    """Output type for metrics update."""

    def __init__(
        self,
        success: bool,
        session_active: bool,
        session_duration: float,
        message: str,
    ):
        self.success = success
        self.session_active = session_active
        self.session_duration = session_duration
        self.message = message


class FileChangeProcessor(InstrumentedPrimitive[FileChangeEvent, MetricsUpdate]):
    """Process file changes using TTA primitives with automatic observability."""

    def __init__(self):
        super().__init__(name="file_change_processor")
        self.session_start: float | None = None
        self.last_activity: float | None = None
        self.file_stats: dict[str, Any] = defaultdict(
            lambda: {"count": 0, "last_modified": None}
        )
        self.session_timeout = 300  # 5 minutes

    async def _execute_impl(
        self,
        input_data: FileChangeEvent,
        context: WorkflowContext,
    ) -> MetricsUpdate:
        """Process file change event with automatic tracing."""
        # Start session if needed
        if self.session_start is None:
            self.session_start = time.time()
            session_active.set(1)
            logger.info(
                "🎯 Agent session started",
                extra={
                    "correlation_id": context.correlation_id,
                    "event": "session_start",
                },
            )

        # Update session activity
        self.last_activity = time.time()
        duration = time.time() - self.session_start
        session_duration_seconds.set(duration)

        # Update metrics (automatically traced)
        files_modified_total.labels(
            file_type=input_data.file_type,
            operation=input_data.operation,
        ).inc()

        file_edit_frequency.labels(filename=input_data.relative_path).inc()

        # Track in session stats
        self.file_stats[input_data.relative_path]["count"] += 1
        self.file_stats[input_data.relative_path]["last_modified"] = (
            input_data.timestamp
        )

        message = f"{input_data.operation.title()}: {input_data.relative_path} ({input_data.file_type})"
        logger.info(
            message,
            extra={
                "correlation_id": context.correlation_id,
                "file_path": input_data.relative_path,
                "file_type": input_data.file_type,
                "operation": input_data.operation,
                "session_duration": duration,
            },
        )

        return MetricsUpdate(
            success=True,
            session_active=True,
            session_duration=duration,
            message=message,
        )

    def check_session_timeout(self) -> None:
        """Check if session has timed out due to inactivity."""
        if (
            self.last_activity
            and (time.time() - self.last_activity) > self.session_timeout
        ):
            self._end_session()

    def _end_session(self) -> None:
        """End current tracking session."""
        if self.session_start:
            duration = time.time() - self.session_start
            logger.info(
                f"✅ Agent session ended. Duration: {duration:.1f}s",
                extra={"event": "session_end", "duration": duration},
            )
            self.session_start = None
            self.last_activity = None
            session_duration_seconds.set(0)
            session_active.set(0)


class AgentActivityHandler(FileSystemEventHandler):
    """Handler for file system events that uses TTA primitives."""

    def __init__(self, workspace_path: Path, processor: FileChangeProcessor):
        """Initialize handler."""
        self.workspace_path = workspace_path
        self.processor = processor
        self.session_timeout = 300

    def _should_track(self, path: str) -> bool:
        """Determine if file should be tracked."""
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
            if pattern in path:
                return False

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

        return any(path.endswith(ext) for ext in track_extensions)

    def _get_file_type(self, path: str) -> str:
        """Get file type from path."""
        if path.endswith(".py"):
            return "python"
        elif path.endswith((".js", ".ts", ".jsx", ".tsx")):
            return "javascript"
        elif path.endswith(".md"):
            return "markdown"
        elif path.endswith((".yml", ".yaml")):
            return "yaml"
        elif path.endswith(".json"):
            return "json"
        elif path.endswith(".toml"):
            return "toml"
        elif path.endswith(".sh"):
            return "shell"
        else:
            return "other"

    def _process_event(
        self,
        src_path: str,
        operation: str,
    ) -> None:
        """Process file event using TTA primitives."""
        if not self._should_track(src_path):
            return

        rel_path = Path(src_path).relative_to(self.workspace_path)
        file_type = self._get_file_type(src_path)

        # Create event
        event = FileChangeEvent(
            path=src_path,
            file_type=file_type,
            operation=operation,
            relative_path=str(rel_path),
        )

        # Create workflow context with correlation ID
        context = WorkflowContext(
            correlation_id=f"fs-event-{int(time.time() * 1000)}",
            data={
                "workspace": str(self.workspace_path),
                "file_type": file_type,
                "operation": operation,
            },
        )

        # Execute primitive (automatically traced)
        try:
            result = asyncio.run(self.processor.execute(event, context))
            if not result.success:
                logger.error(f"Failed to process event: {result.message}")
        except Exception as e:
            logger.error(
                f"Error processing file event: {e}",
                exc_info=True,
                extra={
                    "correlation_id": context.correlation_id,
                    "file_path": src_path,
                },
            )

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            self._process_event(str(event.src_path), "modified")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            self._process_event(str(event.src_path), "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            self._process_event(str(event.src_path), "deleted")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track agent activity via file system monitoring (TTA Primitives version)"
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
    parser.add_argument(
        "--session-timeout",
        type=int,
        default=300,
        help="Session timeout in seconds (default: 300)",
    )
    args = parser.parse_args()

    # Validate workspace
    if not args.workspace.exists():
        logger.error(f"❌ Workspace not found: {args.workspace}")
        sys.exit(1)

    # Initialize TTA observability
    logger.info("🔧 Initializing TTA observability integration...")
    success = initialize_observability(
        service_name="agent-activity-tracker",
        enable_prometheus=True,
        prometheus_port=args.port,
    )

    if success:
        logger.info("✅ TTA observability initialized")
        logger.info(f"   OpenTelemetry: {is_observability_enabled()}")
        logger.info(f"   Prometheus: http://localhost:{args.port}/metrics")
    else:
        logger.warning("⚠️  Observability initialization failed, metrics only mode")

    logger.info(f"🔍 Monitoring workspace: {args.workspace}")
    logger.info(f"⏱️  Session timeout: {args.session_timeout}s")

    # Start additional Prometheus metrics server (for custom metrics)
    try:
        start_http_server(args.port)
        logger.info(f"✅ Metrics server started on port {args.port}")
    except OSError as e:
        logger.error(f"❌ Failed to start metrics server: {e}")
        sys.exit(1)

    # Set up file change processor using TTA primitives
    processor = FileChangeProcessor()
    processor.session_timeout = args.session_timeout

    # Set up file system observer
    event_handler = AgentActivityHandler(args.workspace, processor)
    observer = Observer()
    observer.schedule(event_handler, str(args.workspace), recursive=True)
    observer.start()

    logger.info("🚀 Agent activity tracker running (TTA Primitives version)...")
    logger.info("   Using InstrumentedPrimitive for automatic tracing")
    logger.info("   Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
            processor.check_session_timeout()
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping agent activity tracker...")
        observer.stop()
        observer.join()

        # Print final statistics
        logger.info("\n=== Final Statistics ===")
        logger.info(f"Files tracked: {len(processor.file_stats)}")

        most_edited = sorted(
            processor.file_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:10]

        if most_edited:
            logger.info("\nMost edited files:")
            for filename, data in most_edited:
                logger.info(f"  {filename}: {data['count']} edits")

        logger.info("\n✅ Tracker stopped")


if __name__ == "__main__":
    main()
