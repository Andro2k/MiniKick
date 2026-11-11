# backend\services\webhooks\webhook_signer.py

import hashlib
import hmac

EVENT_ID_HEADER = "X-MiniKick-Event-Id"
TIMESTAMP_HEADER = "X-MiniKick-Timestamp"
SIGNATURE_HEADER = "X-MiniKick-Signature-256"


def sign_payload(body: bytes, secret: str, timestamp_ms: int) -> str:
    message = f"{timestamp_ms}.".encode("utf-8") + body
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def build_headers(event_id: str, body: bytes, secret: str, timestamp_ms: int) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MiniKick-Webhooks/1",
        EVENT_ID_HEADER: event_id,
        TIMESTAMP_HEADER: str(timestamp_ms),
    }
    if secret:
        headers[SIGNATURE_HEADER] = sign_payload(body, secret, timestamp_ms)
    return headers
