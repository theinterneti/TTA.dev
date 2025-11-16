import hashlib
import hmac
import time

from fastapi import Depends, FastAPI, HTTPException, Request

from .config import get_webhook_config
from .redis_queue import enqueue_webhook

app = FastAPI()

MAX_TIMESTAMP_SKEW_SECONDS = 300  # 5 minutes


async def verify_signature(request: Request, webhook_id: str):
    """
    FastAPI dependency to verify a TTA.dev (Stripe-style) webhook signature.
    This protects against spoofing and replay attacks.
    """
    try:
        # 1. Get the raw request body. DO NOT PARSE JSON FIRST.
        payload_body = await request.body()

        # 2. Get the signature header
        sig_header = request.headers.get("TTA-Signature")
        if not sig_header:
            raise HTTPException(status_code=403, detail="TTA-Signature header missing.")

        # 3. Parse the timestamp and signature(s)
        timestamp_str = None
        signature_v1_str = None

        for part in sig_header.split(","):
            key, value = part.split("=", 1)
            if key == "t":
                timestamp_str = value
            elif key == "v1":
                signature_v1_str = value

        if not timestamp_str or not signature_v1_str:
            raise HTTPException(
                status_code=403, detail="Malformed TTA-Signature header."
            )

        # 4. (Replay Attack Defense) Verify the timestamp
        timestamp = int(timestamp_str)
        if abs(time.time() - timestamp) > MAX_TIMESTAMP_SKEW_SECONDS:
            raise HTTPException(
                status_code=403,
                detail="Webhook timestamp expired. Possible replay attack.",
            )

        # 5. Get the webhook secret from config
        config = await get_webhook_config(webhook_id)
        if not config or "secret" not in config:
            raise HTTPException(
                status_code=404, detail=f"Webhook ID not found: {webhook_id}"
            )
        webhook_secret = config["secret"]

        # 6. Prepare the signed payload string
        signed_payload = f"{timestamp_str}.{payload_body.decode('utf-8')}"

        # 7. Compute the expected signature
        hash_object = hmac.new(
            webhook_secret.encode("utf-8"),
            msg=signed_payload.encode("utf-8"),
            digestmod=hashlib.sha256,
        )
        expected_signature = hash_object.hexdigest()
        expected_signature = hash_object.hexdigest()

        # 8. (Timing Attack Defense) Compare signatures
        if not hmac.compare_digest(signature_v1_str, expected_signature):
            raise HTTPException(
                status_code=403, detail="Request signatures didn't match."
            )

        # 9. Store the validated raw body for the async worker
        request.state.raw_body = payload_body

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid payload or signature. Error: {e}"
        )


@app.post("/hooks/catch/{webhook_id}", dependencies=[Depends(verify_signature)])
async def webhook_receiver(request: Request, webhook_id: str):
    """
    Receives, authenticates, and enqueues incoming webhooks.
    """
    raw_body = request.state.raw_body

    # Enqueue the webhook for asynchronous processing.
    await enqueue_webhook(webhook_id, raw_body)

    # Immediately return 202 Accepted to the sender.
    return {"status": "accepted"}
