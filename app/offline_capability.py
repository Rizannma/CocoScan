"""Signed, scoped capability tokens for the farmer offline PWA session."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Optional

from flask import current_app, has_app_context

COOKIE_NAME = "cocoscan_offline_capability"
SCOPE = "offline_farmer"
MAX_AGE_SECONDS = 30 * 24 * 60 * 60


def _secret() -> bytes:
    secret = os.getenv("FLASK_SECRET_KEY", "").strip()
    if not secret and has_app_context():
        secret = str(current_app.secret_key or "").strip()
    if not secret:
        raise RuntimeError("FLASK_SECRET_KEY must be configured for offline capabilities.")
    return secret.encode("utf-8")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue(user_id: str, email: str, *, now: Optional[int] = None) -> str:
    if not user_id or not email:
        raise ValueError("Offline capability requires a user identifier and email.")
    issued_at = int(time.time() if now is None else now)
    payload = {
        "v": 1,
        "scope": SCOPE,
        "user_id": str(user_id),
        "email": str(email).strip().lower(),
        "iat": issued_at,
        "exp": issued_at + MAX_AGE_SECONDS,
        "nonce": secrets.token_urlsafe(16),
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(_secret(), encoded_payload.encode(), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def validate(token: str, *, now: Optional[int] = None) -> Optional[dict[str, Any]]:
    try:
        encoded_payload, encoded_signature = (token or "").split(".", 1)
        expected = hmac.new(_secret(), encoded_payload.encode(), hashlib.sha256).digest()
        supplied = _decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(_decode(encoded_payload))
        current = int(time.time() if now is None else now)
        if (
            payload.get("v") != 1
            or payload.get("scope") != SCOPE
            or not payload.get("user_id")
            or not payload.get("email")
            or current >= int(payload.get("exp", 0))
            or current < int(payload.get("iat", 0))
        ):
            return None
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, RuntimeError):
        return None
