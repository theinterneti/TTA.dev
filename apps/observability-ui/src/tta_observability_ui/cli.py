"""CLI for TTA Observability UI service."""

from __future__ import annotations

import argparse
import logging
import sys

import uvicorn


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def start_service(
    host: str = "0.0.0.0",
    port: int = 8765,
    db_path: str | None = None,
    log_level: str = "info",
    reload: bool = False,
) -> None:
    """
    Start the TTA Observability UI service.

    Args:
        host: Host to bind to
        port: Port to bind to
        db_path: Path to SQLite database
        log_level: Logging level (debug, info, warning, error)
        reload: Enable auto-reload for development
    """
    # Set environment variables for configuration
    if db_path:
        import os

        os.environ["TTA_UI_DB_PATH"] = db_path

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            🔍 TTA Observability UI                          ║
║                                                              ║
║  Lightweight, LangSmith-inspired observability              ║
║  for TTA.dev workflows                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📍 Service URL:    http://{host}:{port}
📊 API Docs:       http://{host}:{port}/docs
🔌 OTLP Endpoint:  http://{host}:{port}/v1/traces
💬 WebSocket:      ws://{host}:{port}/ws/traces

📝 Database:       {db_path or "tta_traces.db"}
📈 Log Level:      {log_level.upper()}

Press Ctrl+C to stop the service
""")

    # Start uvicorn server
    uvicorn.run(
        "tta_observability_ui.api:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TTA Observability UI - Lightweight observability for TTA.dev",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with defaults
  tta-observability-ui start

  # Custom port and database
  tta-observability-ui start --port 9000 --db-path ./my_traces.db

  # Development mode with auto-reload
  tta-observability-ui start --reload --log-level debug

  # Bind to specific host
  tta-observability-ui start --host 127.0.0.1
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser(
        "start", help="Start the observability service"
    )
    start_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)",
    )
    start_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database (default: tta_traces.db)",
    )
    start_parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)",
    )
    start_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if args.command == "start":
        start_service(
            host=args.host,
            port=args.port,
            db_path=args.db_path,
            log_level=args.log_level,
            reload=args.reload,
        )
    elif args.command == "version":
        from . import __version__

        print(f"TTA Observability UI v{__version__}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
