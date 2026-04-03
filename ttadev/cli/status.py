"""TTA.dev CLI: `tta status` — quick system health check.

No external dependencies beyond stdlib (json, os, pathlib, socket, time) and
internal TTA.dev modules.
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

# Re-export setup helpers so tests can patch them at this module's namespace.
from ttadev.cli.setup import SETUP_PROVIDERS, _get_key, _read_env, validate_provider

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DASHBOARD_PORT = 8000
_MCP_SERVER_PORT = 9999
_VALIDATE_TIMEOUT_S = 3
_RULE = "═" * 46

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _provider_slug(provider: object) -> str:
    """Return a short lowercase display slug for a provider.

    Args:
        provider: A SetupProvider instance.

    Returns:
        e.g. "google", "groq", "openrouter", "ollama".
    """
    env_var: str = getattr(provider, "env_var", "")
    is_local: bool = getattr(provider, "is_local", False)
    name: str = getattr(provider, "name", "")

    if is_local:
        return name.lower()
    if env_var.endswith("_API_KEY"):
        return env_var[: -len("_API_KEY")].lower()
    return name.lower()


def _check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if a TCP connection succeeds on (host, port).

    Args:
        host: Hostname or IP address.
        port: TCP port number.
        timeout: Connection timeout in seconds.

    Returns:
        True if port is open/listening, False otherwise.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def _count_control_plane(data_dir: Path) -> tuple[int, int]:
    """Return (active_tasks, active_runs) from the control plane store.

    Active tasks: status PENDING or IN_PROGRESS.
    Active runs: status ACTIVE.

    Args:
        data_dir: TTA state directory (contains control/ sub-directory).

    Returns:
        Tuple of (active_task_count, active_run_count). Returns (0, 0) on
        any error (e.g. store not initialised yet).
    """
    try:
        from ttadev.control_plane.models import RunStatus, TaskStatus
        from ttadev.control_plane.store import ControlPlaneStore

        store = ControlPlaneStore(data_dir)
        active_tasks = sum(
            1
            for t in store.list_tasks()
            if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        )
        active_runs = sum(1 for r in store.list_runs() if r.status == RunStatus.ACTIVE)
        return active_tasks, active_runs
    except Exception:  # noqa: BLE001
        return 0, 0


# ---------------------------------------------------------------------------
# Public command
# ---------------------------------------------------------------------------


def cmd_status(
    args: object,
    *,
    project_root: Path = Path("."),
    data_dir: Path | None = None,
) -> int:
    """Implement `tta status`.

    Checks provider connectivity (with latency), service ports, and control
    plane counters, then prints a human-readable summary (or JSON when
    --json is passed).

    Args:
        args: Parsed CLI args (expects ``.json_output`` and ``.data_dir``).
        project_root: Directory containing .env.
        data_dir: Override for TTA state directory (defaults to .data_dir
            on args, falling back to ``.tta``).

    Returns:
        0 if ≥1 provider is healthy; 1 if all providers are missing/failing.
    """
    json_output: bool = getattr(args, "json_output", False)

    # Resolve data directory
    if data_dir is None:
        raw_data_dir: str = getattr(args, "data_dir", ".tta")
        data_dir = Path(raw_data_dir)

    env_path = project_root / ".env"
    env = _read_env(env_path)

    # ------------------------------------------------------------------ #
    # 1. Provider checks                                                   #
    # ------------------------------------------------------------------ #
    provider_results: list[dict] = []
    healthy_count = 0
    configured_count = 0  # non-local providers that have a key set

    for provider in SETUP_PROVIDERS:
        key = _get_key(provider, env)
        slug = _provider_slug(provider)
        is_local: bool = getattr(provider, "is_local", False)

        if not is_local and key:
            configured_count += 1

        t0 = time.monotonic()
        result = validate_provider(provider, key)
        latency_ms = round((time.monotonic() - t0) * 1000)

        if result.connected:
            healthy_count += 1
            status = "healthy"
        elif is_local:
            status = "not_detected"
        elif not key:
            status = "missing_key"
        else:
            status = "error"

        provider_results.append(
            {
                "name": slug,
                "status": status,
                "latency_ms": latency_ms if result.connected else None,
                "model": result.models[0] if result.models else None,
                "error": result.error,
                "is_local": is_local,
                "validate_url": getattr(provider, "validate_url", ""),
            }
        )

    # ------------------------------------------------------------------ #
    # 2. Service port checks                                               #
    # ------------------------------------------------------------------ #
    dashboard_up = _check_port("localhost", _DASHBOARD_PORT)
    mcp_up = _check_port("localhost", _MCP_SERVER_PORT)

    services = [
        {
            "name": "dashboard",
            "url": f"http://localhost:{_DASHBOARD_PORT}",
            "port": _DASHBOARD_PORT,
            "running": dashboard_up,
        },
        {
            "name": "mcp-server",
            "url": f"http://localhost:{_MCP_SERVER_PORT}",
            "port": _MCP_SERVER_PORT,
            "running": mcp_up,
        },
    ]

    # ------------------------------------------------------------------ #
    # 3. Control plane counts                                              #
    # ------------------------------------------------------------------ #
    active_tasks, active_runs = _count_control_plane(data_dir)

    # ------------------------------------------------------------------ #
    # 4. Config summary                                                    #
    # ------------------------------------------------------------------ #
    config_source = ".env" if env_path.exists() else "environment"
    config_info = {
        "source": config_source,
        "configured_providers": configured_count,
    }

    # ------------------------------------------------------------------ #
    # 5. Output                                                            #
    # ------------------------------------------------------------------ #
    exit_code = 0 if healthy_count >= 1 else 1

    if json_output:
        payload = {
            "providers": [
                {k: v for k, v in r.items() if k != "validate_url"} for r in provider_results
            ],
            "services": services,
            "control_plane": {
                "active_tasks": active_tasks,
                "active_runs": active_runs,
            },
            "config": config_info,
            "healthy": healthy_count >= 1,
        }
        print(json.dumps(payload))
        return exit_code

    # Human-readable output
    print()
    print("TTA.dev status")
    print(_RULE)

    # --- Providers ---
    print("Providers")
    for r in provider_results:
        name = r["name"]
        if r["status"] == "healthy":
            latency = r["latency_ms"]
            model = r["model"] or ""
            model_str = f"  ({model})" if model else ""
            lat_str = f"latency {latency} ms"
            print(f"  \u2713 {name:<12} {lat_str:<18}{model_str}")
        elif r["status"] == "missing_key":
            print(f"  \u2717 {name:<12} MISSING key \u2014 run `tta setup`")
        elif r["status"] == "not_detected":
            # Extract host from validate_url for display
            validate_url: str = r.get("validate_url", "localhost:11434")
            host_hint = validate_url.removeprefix("http://").removeprefix("https://")
            host_hint = host_hint.split("/")[0]
            print(f"  - {name:<12} not detected at {host_hint}")
        else:
            err = r["error"] or "connection failed"
            print(f"  \u2717 {name:<12} {err}")

    # --- Observability ---
    print()
    print("Observability")
    for svc in services:
        mark = "\u2713" if svc["running"] else "\u2717"
        url = svc["url"]
        name = svc["name"]
        if svc["running"]:
            print(f"  {mark} {name:<12} {url}  (running)")
        else:
            print(f"  {mark} {name:<12} not running on port {svc['port']}")

    # --- Control plane ---
    print()
    print("Control plane")
    print(f"  Active tasks   {active_tasks}")
    print(f"  Active runs    {active_runs}")

    # --- Config ---
    print()
    provider_word = "provider" if configured_count == 1 else "providers"
    print(f"Config          {config_source}  ({configured_count} {provider_word} configured)")
    print()

    return exit_code
