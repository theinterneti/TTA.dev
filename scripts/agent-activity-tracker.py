#!/usr/bin/env python3
"""
Agent Activity Tracker - Monitor VS Code and Copilot activity indirectly.

This script monitors file system changes and emits Prometheus metrics.
It provides indirect observability into AI agent workflows by tracking:
- Files modified
- Session duration
- Edit patterns
- Most active files

Usage:
    python scripts/agent-activity-tracker.py --workspace /path/to/workspace
"""

import argparse
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, start_http_server
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

lines_changed = Histogram(
    "copilot_lines_changed",
    "Histogram of line changes per file edit",
    ["file_type"],
    buckets=[1, 5, 10, 20, 50, 100, 200, 500, 1000],
)

session_active = Gauge(
    "copilot_session_active",
    "Whether a Copilot session is currently active (1=active, 0=inactive)",
)


class AgentActivityHandler(FileSystemEventHandler):
    """Handler for file system events to track agent activity."""

    def __init__(self, workspace_path: Path):
        """Initialize handler."""
        self.workspace_path = workspace_path
        self.session_start = None
        self.last_activity = None
        self.file_stats: dict[str, Any] = defaultdict(
            lambda: {"count": 0, "last_modified": None}
        )
        self.session_timeout = 300  # 5 minutes of inactivity ends session

    def _should_track(self, path: str) -> bool:
        """Determine if file should be tracked."""
        # Ignore certain directories and file types
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

        # Only track code and documentation files
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

    def _start_session(self) -> None:
        """Start a new tracking session."""
        if self.session_start is None:
            self.session_start = time.time()
            session_active.set(1)
            logger.info("🎯 Agent session started")

    def _update_session(self) -> None:
        """Update session activity timestamp."""
        self.last_activity = time.time()

        # Update session duration metric
        if self.session_start:
            duration = time.time() - self.session_start
            session_duration_seconds.set(duration)

    def _end_session(self) -> None:
        """End current tracking session."""
        if self.session_start:
            duration = time.time() - self.session_start
            logger.info(f"✅ Agent session ended. Duration: {duration:.1f}s")
            self.session_start = None
            self.last_activity = None
            session_duration_seconds.set(0)
            session_active.set(0)

    def _check_session_timeout(self) -> None:
        """Check if session has timed out due to inactivity."""
        if (
            self.last_activity
            and (time.time() - self.last_activity) > self.session_timeout
        ):
            self._end_session()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Convert to string explicitly to handle bytes | str union
        src_path_str = str(event.src_path)

        if not self._should_track(src_path_str):
            return

        self._start_session()
        self._update_session()

        rel_path = Path(src_path_str).relative_to(self.workspace_path)
        file_type = self._get_file_type(src_path_str)

        files_modified_total.labels(file_type=file_type, operation="modified").inc()
        file_edit_frequency.labels(filename=str(rel_path)).inc()

        # Track in session stats
        self.file_stats[str(rel_path)]["count"] += 1
        self.file_stats[str(rel_path)]["last_modified"] = time.time()

        logger.info(f"✏️  Modified: {rel_path} ({file_type})")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event."""
        # Convert to string explicitly to handle bytes | str union
        src_path_str = str(event.src_path)

        if event.is_directory or not self._should_track(src_path_str):
            return

        self._start_session()
        self._update_session()

        rel_path = Path(src_path_str).relative_to(self.workspace_path)
        file_type = self._get_file_type(src_path_str)

        files_modified_total.labels(file_type=file_type, operation="created").inc()

        logger.info(f"✨ Created: {rel_path} ({file_type})")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event."""
        # Convert to string explicitly to handle bytes | str union
        src_path_str = str(event.src_path)

        if event.is_directory or not self._should_track(src_path_str):
            return

        self._start_session()
        self._update_session()

        rel_path = Path(src_path_str).relative_to(self.workspace_path)
        file_type = self._get_file_type(src_path_str)

        files_modified_total.labels(file_type=file_type, operation="deleted").inc()

        logger.info(f"🗑️  Deleted: {rel_path} ({file_type})")

    def get_stats(self) -> dict[str, Any]:
        """Get current session statistics."""
        return {
            "session_active": self.session_start is not None,
            "session_duration": (
                time.time() - self.session_start if self.session_start else 0
            ),
            "files_tracked": len(self.file_stats),
            "most_edited": sorted(
                self.file_stats.items(), key=lambda x: x[1]["count"], reverse=True
            )[:10],
        }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track agent activity via file system monitoring"
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
        default=8000,
        help="Prometheus metrics port (default: 8000)",
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

    logger.info(f"🔍 Monitoring workspace: {args.workspace}")
    logger.info(f"📊 Metrics available at: http://localhost:{args.port}/metrics")
    logger.info(f"⏱️  Session timeout: {args.session_timeout}s")

    # Start Prometheus metrics server
    try:
        start_http_server(args.port)
        logger.info(f"✅ Metrics server started on port {args.port}")
    except OSError as e:
        logger.error(f"❌ Failed to start metrics server: {e}")
        sys.exit(1)

    # Set up file system observer
    event_handler = AgentActivityHandler(args.workspace)
    event_handler.session_timeout = args.session_timeout
    observer = Observer()
    observer.schedule(event_handler, str(args.workspace), recursive=True)
    observer.start()

    logger.info("🚀 Agent activity tracker running...")
    logger.info("   Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
            event_handler._check_session_timeout()
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping agent activity tracker...")
        observer.stop()
        observer.join()

        # Print final statistics
        stats = event_handler.get_stats()
        logger.info("\n=== Final Statistics ===")
        logger.info(f"Session duration: {stats['session_duration']:.1f}s")
        logger.info(f"Files tracked: {stats['files_tracked']}")

        if stats["most_edited"]:
            logger.info("\nMost edited files:")
            for filename, data in stats["most_edited"]:
                logger.info(f"  {filename}: {data['count']} edits")

        logger.info("\n✅ Tracker stopped")


if __name__ == "__main__":
    main()
