#!/usr/bin/env python3
"""
Copilot CLI → Langfuse hook

Traces Copilot CLI sessions in Langfuse Cloud.
Captures: session lifecycle, user prompts, tool calls (bash/edit/view/etc).

Hook event is passed via LF_EVENT env var.
Langfuse credentials read from env or .env file in cwd.
State persisted in ~/.copilot/langfuse_sessions/ between hook invocations.

Uses Langfuse v4 SDK API (create_trace_id, TraceContext, create_event, etc.)
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: load .env if needed
# ---------------------------------------------------------------------------


def _load_dotenv(cwd: str) -> None:
    """Manually parse a .env file and inject into os.environ (no pip required)."""
    env_path = Path(cwd) / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# ---------------------------------------------------------------------------
# State: persist session info between hook invocations
# ---------------------------------------------------------------------------

STATE_DIR = Path.home() / ".copilot" / "langfuse_sessions"
LOG_FILE = STATE_DIR / "hook.log"


def _log(msg: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _state_key(cwd: str) -> str:
    return hashlib.sha256(cwd.encode()).hexdigest()[:16]


def _load_state(cwd: str) -> dict:
    path = STATE_DIR / f"{_state_key(cwd)}.json"
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_state(cwd: str, state: dict) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        path = STATE_DIR / f"{_state_key(cwd)}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception as exc:
        _log(f"save_state failed: {exc}")


def _clear_state(cwd: str) -> None:
    path = STATE_DIR / f"{_state_key(cwd)}.json"
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Langfuse helpers
# ---------------------------------------------------------------------------


def _get_langfuse_client():
    """Return a Langfuse client or None if unavailable."""
    try:
        from langfuse import Langfuse  # type: ignore[import-untyped]

        return Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )
    except Exception as exc:
        _log(f"langfuse client failed: {exc}")
        return None


def _get_trace_context(trace_id: str, session_id: str, user_id: str):
    """Build a Langfuse v4 TraceContext dict."""
    return {"trace_id": trace_id, "session_id": session_id, "user_id": user_id}


def _user_id() -> str:
    """Best-effort agent identity."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return os.environ.get("USER", "copilot-cli")


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------


def handle_session_start(payload: dict, cwd: str) -> None:
    import uuid

    session_id = str(uuid.uuid4())
    started_at = payload.get("timestamp", int(time.time() * 1000))
    initial_prompt = payload.get("initialPrompt", "")

    lf = _get_langfuse_client()
    if not lf:
        # Save state without trace_id so other handlers no-op gracefully
        _save_state(
            cwd,
            {"session_id": session_id, "trace_id": None, "started_at": started_at, "tool_count": 0},
        )
        return

    try:
        uid = _user_id()
        # v4: create_trace_id to get deterministic or random trace ID
        trace_id = lf.create_trace_id()

        ctx = {"trace_id": trace_id, "session_id": session_id, "user_id": uid}

        # Create top-level agent observation for this session
        obs = lf.start_observation(
            trace_context=ctx,  # type: ignore[arg-type]
            name="copilot-cli-session",
            as_type="agent",
            input=initial_prompt or None,
            metadata={
                "cwd": cwd,
                "source": payload.get("source", "new"),
                "agent": "github-copilot-cli",
            },
        )
        obs_id = obs.id

        state = {
            "session_id": session_id,
            "trace_id": trace_id,
            "obs_id": obs_id,
            "user_id": uid,
            "started_at": started_at,
            "tool_count": 0,
        }
        _save_state(cwd, state)

        _log(f"session_start trace={trace_id} session={session_id}")
        url = lf.get_trace_url(trace_id=trace_id)
        _log(f"Langfuse trace: {url}")
    except Exception as exc:
        _log(f"session_start error: {exc}")
    finally:
        try:
            lf.flush()
        except Exception:
            pass


def handle_user_prompt(payload: dict, cwd: str) -> None:
    state = _load_state(cwd)
    if not state or not state.get("trace_id"):
        return

    lf = _get_langfuse_client()
    if not lf:
        return

    try:
        ctx = {
            "trace_id": state["trace_id"],
            "session_id": state["session_id"],
            "user_id": state.get("user_id", "copilot-cli"),
        }
        prompt = payload.get("prompt", "")
        lf.create_event(
            trace_context=ctx,  # type: ignore[arg-type]
            name="user-prompt",
            input=prompt,
            metadata={"cwd": cwd},
        )
        _log(f"user_prompt trace={state['trace_id']} len={len(prompt)}")
    except Exception as exc:
        _log(f"user_prompt error: {exc}")
    finally:
        try:
            lf.flush()
        except Exception:
            pass


def handle_post_tool_use(payload: dict, cwd: str) -> None:
    state = _load_state(cwd)
    if not state or not state.get("trace_id"):
        return

    lf = _get_langfuse_client()
    if not lf:
        return

    try:
        ctx = {
            "trace_id": state["trace_id"],
            "session_id": state["session_id"],
            "user_id": state.get("user_id", "copilot-cli"),
        }
        tool_name = payload.get("toolName", "unknown")
        tool_result = payload.get("toolResult", {})
        result_type = tool_result.get("resultType", "unknown")
        result_text = tool_result.get("textResultForLlm", "")

        try:
            tool_args = json.loads(payload.get("toolArgs", "{}"))
        except Exception:
            tool_args = {"raw": payload.get("toolArgs", "")}

        obs = lf.start_observation(
            trace_context=ctx,  # type: ignore[arg-type]
            name=f"tool:{tool_name}",
            as_type="tool",
            input=tool_args,
            output=result_text[:2000] if result_text else None,
            level="ERROR" if result_type == "failure" else "DEFAULT",
            metadata={
                "tool": tool_name,
                "result_type": result_type,
                "cwd": cwd,
            },
        )
        obs.end()

        state["tool_count"] = state.get("tool_count", 0) + 1
        _save_state(cwd, state)
        _log(f"post_tool_use tool={tool_name} result={result_type} trace={state['trace_id']}")
    except Exception as exc:
        _log(f"post_tool_use error: {exc}")
    finally:
        try:
            lf.flush()
        except Exception:
            pass


def handle_session_end(payload: dict, cwd: str) -> None:
    state = _load_state(cwd)
    if not state or not state.get("trace_id"):
        _clear_state(cwd)
        return

    lf = _get_langfuse_client()
    if not lf:
        _clear_state(cwd)
        return

    try:
        ctx = {
            "trace_id": state["trace_id"],
            "session_id": state["session_id"],
            "user_id": state.get("user_id", "copilot-cli"),
        }
        started_at = state.get("started_at", 0)
        ended_at = payload.get("timestamp", int(time.time() * 1000))
        duration_s = round((ended_at - started_at) / 1000, 1)

        # Update the top-level session observation with final output
        lf.create_event(
            trace_context=ctx,  # type: ignore[arg-type]
            name="session-end",
            output={
                "reason": payload.get("reason", "complete"),
                "tool_calls": state.get("tool_count", 0),
                "duration_seconds": duration_s,
            },
            metadata={"cwd": cwd},
        )
        _log(
            f"session_end trace={state['trace_id']} reason={payload.get('reason')} "
            f"tools={state.get('tool_count', 0)} duration={duration_s}s"
        )
    except Exception as exc:
        _log(f"session_end error: {exc}")
    finally:
        try:
            lf.flush()
        except Exception:
            pass
        _clear_state(cwd)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    event = os.environ.get("LF_EVENT", "")
    if not event:
        sys.exit(0)

    # Read payload from stdin
    try:
        raw = sys.stdin.read().strip()
        payload = json.loads(raw) if raw else {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd", os.getcwd())

    # Load credentials from .env if not in env
    _load_dotenv(cwd)

    # Bail out silently if no credentials
    if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
        sys.exit(0)

    dispatch = {
        "sessionStart": handle_session_start,
        "sessionEnd": handle_session_end,
        "userPromptSubmitted": handle_user_prompt,
        "postToolUse": handle_post_tool_use,
    }

    handler = dispatch.get(event)
    if handler:
        handler(payload, cwd)

    sys.exit(0)


if __name__ == "__main__":
    main()
