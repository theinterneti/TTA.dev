"""Entry point: python -m ttadev.observability

Idempotent — if port 8000 is already in use, opens the browser and exits cleanly.
"""

import asyncio
import socket
import sys
import webbrowser

PORT = 8000


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


async def _run() -> None:
    from ttadev.observability.server import ObservabilityServer

    server = ObservabilityServer(port=PORT)
    await server.start()
    print(f"TTA.dev Observability Dashboard → http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutting down...")
        await server.stop()


def main() -> None:
    if _port_in_use(PORT):
        print(f"Dashboard already running → http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        sys.exit(0)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
