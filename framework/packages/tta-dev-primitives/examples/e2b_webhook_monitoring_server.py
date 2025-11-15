"""
E2B Webhook Monitoring Server Example

Demonstrates how to receive and process E2B sandbox lifecycle webhooks.

Use cases:
- Real-time cost tracking
- Budget enforcement
- Runaway sandbox detection
- Analytics and metrics
- Live dashboard updates
"""

import hashlib
import hmac
import os
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="E2B Webhook Monitor")

# Configuration
WEBHOOK_SECRET = os.getenv("E2B_WEBHOOK_SECRET", "your-secret-key")
DAILY_SANDBOX_LIMIT = int(os.getenv("DAILY_SANDBOX_LIMIT", "100"))
SANDBOX_TIMEOUT_MINUTES = int(os.getenv("SANDBOX_TIMEOUT_MINUTES", "10"))

# In-memory storage (use Redis/PostgreSQL in production)
sandbox_timers: dict[str, datetime] = {}
metrics = {
    "total_created": 0,
    "total_killed": 0,
    "current_concurrent": 0,
    "peak_concurrent": 0,
    "templates_used": defaultdict(int),
    "events_received": 0,
}


def verify_webhook_signature(secret: str, payload: bytes, signature: str) -> bool:
    """
    Verify E2B webhook signature.

    E2B uses SHA256 hash of (secret + payload) for verification.
    """
    expected_signature_raw = hashlib.sha256((secret + payload.decode()).encode()).digest()

    # E2B uses base64url encoding
    expected_signature = (
        expected_signature_raw.hex().replace("+", "-").replace("/", "_").rstrip("=")
    )

    return hmac.compare_digest(expected_signature, signature)


@app.post("/webhooks/e2b")
async def handle_e2b_webhook(request: Request):
    """
    Main webhook endpoint for E2B sandbox events.

    Events received:
    - sandbox.lifecycle.created
    - sandbox.lifecycle.killed
    - sandbox.lifecycle.updated
    - sandbox.lifecycle.paused
    - sandbox.lifecycle.resumed
    """
    # Get signature from header
    signature = request.headers.get("e2b-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    # Get raw body for verification
    body = await request.body()

    # Verify signature
    if not verify_webhook_signature(WEBHOOK_SECRET, body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = await request.json()

    # Update metrics
    metrics["events_received"] += 1

    # Process based on event type
    event_type = event.get("type")
    sandbox_id = event.get("sandboxId")

    if event_type == "sandbox.lifecycle.created":
        await handle_sandbox_created(event, sandbox_id)

    elif event_type == "sandbox.lifecycle.killed":
        await handle_sandbox_killed(event, sandbox_id)

    elif event_type == "sandbox.lifecycle.updated":
        await handle_sandbox_updated(event, sandbox_id)

    elif event_type == "sandbox.lifecycle.paused":
        await handle_sandbox_paused(event, sandbox_id)

    elif event_type == "sandbox.lifecycle.resumed":
        await handle_sandbox_resumed(event, sandbox_id)

    # Log event
    print(f"✅ Processed {event_type} for sandbox {sandbox_id}")

    return JSONResponse({"status": "ok", "event_id": event.get("id")})


async def handle_sandbox_created(event: dict, sandbox_id: str):
    """Handle sandbox creation event."""
    # Track creation time
    sandbox_timers[sandbox_id] = datetime.now()

    # Update metrics
    metrics["total_created"] += 1
    metrics["current_concurrent"] += 1

    if metrics["current_concurrent"] > metrics["peak_concurrent"]:
        metrics["peak_concurrent"] = metrics["current_concurrent"]

    # Track template usage
    template_id = event.get("sandboxTemplateId", "default")
    metrics["templates_used"][template_id] += 1

    # Check daily limit
    today_count = sum(
        1 for created_at in sandbox_timers.values() if created_at.date() == datetime.now().date()
    )

    if today_count > DAILY_SANDBOX_LIMIT:
        print(f"⚠️  WARNING: Daily sandbox limit exceeded! {today_count}/{DAILY_SANDBOX_LIMIT}")
        # In production: send alert, potentially pause new creations

    print(
        f"🟢 Sandbox created: {sandbox_id[:12]}... "
        f"(concurrent: {metrics['current_concurrent']}, "
        f"template: {template_id})"
    )


async def handle_sandbox_killed(event: dict, sandbox_id: str):
    """Handle sandbox termination event."""
    # Calculate lifetime
    created_at = sandbox_timers.pop(sandbox_id, None)
    if created_at:
        lifetime = datetime.now() - created_at
        print(f"🔴 Sandbox killed: {sandbox_id[:12]}... (lifetime: {lifetime})")
    else:
        print(f"🔴 Sandbox killed: {sandbox_id[:12]}... (no creation record)")

    # Update metrics
    metrics["total_killed"] += 1
    metrics["current_concurrent"] = max(0, metrics["current_concurrent"] - 1)


async def handle_sandbox_updated(event: dict, sandbox_id: str):
    """Handle sandbox configuration update."""
    print(f"⚪ Sandbox updated: {sandbox_id[:12]}...")


async def handle_sandbox_paused(event: dict, sandbox_id: str):
    """Handle sandbox pause event."""
    print(f"🟡 Sandbox paused: {sandbox_id[:12]}...")


async def handle_sandbox_resumed(event: dict, sandbox_id: str):
    """Handle sandbox resume event."""
    print(f"🟢 Sandbox resumed: {sandbox_id[:12]}...")


@app.get("/metrics")
async def get_metrics():
    """
    Expose metrics endpoint.

    Returns current sandbox usage statistics.
    """
    return {
        "metrics": metrics,
        "active_sandboxes": len(sandbox_timers),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "events_processed": metrics["events_received"]}


@app.get("/sandboxes/active")
async def list_active_sandboxes():
    """List all currently active sandboxes."""
    active = []
    now = datetime.now()

    for sandbox_id, created_at in sandbox_timers.items():
        lifetime = now - created_at
        active.append(
            {
                "sandbox_id": sandbox_id,
                "created_at": created_at.isoformat(),
                "lifetime_seconds": lifetime.total_seconds(),
                "lifetime_minutes": lifetime.total_seconds() / 60,
            }
        )

    # Sort by lifetime (longest running first)
    active.sort(key=lambda x: x["lifetime_seconds"], reverse=True)

    return {"active_sandboxes": active, "count": len(active)}


@app.get("/sandboxes/runaway")
async def list_runaway_sandboxes():
    """Identify sandboxes exceeding timeout threshold."""
    runaways = []
    now = datetime.now()
    timeout = timedelta(minutes=SANDBOX_TIMEOUT_MINUTES)

    for sandbox_id, created_at in sandbox_timers.items():
        lifetime = now - created_at
        if lifetime > timeout:
            runaways.append(
                {
                    "sandbox_id": sandbox_id,
                    "created_at": created_at.isoformat(),
                    "lifetime_seconds": lifetime.total_seconds(),
                    "exceeded_by_seconds": (lifetime - timeout).total_seconds(),
                }
            )

    return {
        "runaway_sandboxes": runaways,
        "count": len(runaways),
        "timeout_minutes": SANDBOX_TIMEOUT_MINUTES,
    }


def main():
    """
    Run the webhook server.

    Usage:
        python webhook_monitoring_server.py

    Then register with E2B:
        curl -X POST https://api.e2b.app/events/webhooks \
          -H "X-API-Key: $E2B_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "name": "Production Webhook",
            "url": "https://your-server.com/webhooks/e2b",
            "enabled": true,
            "events": [
              "sandbox.lifecycle.created",
              "sandbox.lifecycle.killed"
            ],
            "signatureSecret": "your-secret-key"
          }'
    """
    print("🚀 Starting E2B Webhook Monitor")
    print(f"📊 Daily limit: {DAILY_SANDBOX_LIMIT} sandboxes")
    print(f"⏱️  Timeout threshold: {SANDBOX_TIMEOUT_MINUTES} minutes")
    print(f"🔑 Using webhook secret: {WEBHOOK_SECRET[:4]}...{WEBHOOK_SECRET[-4:] if len(WEBHOOK_SECRET) > 8 else '****'}")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
