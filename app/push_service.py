"""
Web Push Notification Service for CocoScan.
Handles VAPID keys, browser push subscriptions, and push message dispatching.
"""

import os
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from py_vapid import Vapid, b64urlencode
from cryptography.hazmat.primitives import serialization

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

logger = logging.getLogger(__name__)

_VAPID_FILE_PATH = Path(__file__).parent / "vapid_private.pem"
_VAPID_CLAIM_EMAIL = os.environ.get("VAPID_CLAIM_EMAIL", "mailto:support@cocoscan.laguna.gov.ph")

_lock = threading.Lock()
_vapid_instance: Optional[Vapid] = None
_vapid_public_b64: Optional[str] = None
_vapid_private_pem: Optional[str] = None

# In-memory subscription store: endpoint -> dict
_subscriptions: Dict[str, Dict[str, Any]] = {}


def _init_vapid_keys():
    """Initializes or loads VAPID key pair."""
    global _vapid_instance, _vapid_public_b64, _vapid_private_pem
    with _lock:
        if _vapid_instance is not None and _vapid_public_b64 is not None:
            return

        env_priv = os.environ.get("VAPID_PRIVATE_KEY")
        if env_priv:
            try:
                vapid = Vapid()
                if "BEGIN PRIVATE KEY" in env_priv:
                    vapid = Vapid.from_pem(env_priv.encode("utf-8"))
                else:
                    vapid = Vapid.from_raw(env_priv.encode("utf-8"))
                _vapid_instance = vapid
                _vapid_private_pem = vapid.private_pem().decode("utf-8")
                raw_pub = vapid.public_key.public_bytes(
                    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
                )
                _vapid_public_b64 = b64urlencode(raw_pub)
                logger.info("VAPID keys initialized from environment variable.")
                return
            except Exception as e:
                logger.warning(f"Failed to load VAPID key from environment: {e}. Falling back to file/generation.")

        if _VAPID_FILE_PATH.exists():
            try:
                pem_data = _VAPID_FILE_PATH.read_bytes()
                vapid = Vapid.from_pem(pem_data)
                _vapid_instance = vapid
                _vapid_private_pem = vapid.private_pem().decode("utf-8")
                raw_pub = vapid.public_key.public_bytes(
                    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
                )
                _vapid_public_b64 = b64urlencode(raw_pub)
                logger.info("VAPID keys loaded from disk.")
                return
            except Exception as e:
                logger.warning(f"Failed to load VAPID key from {_VAPID_FILE_PATH}: {e}. Regenerating.")

        # Generate fresh VAPID keys and persist
        try:
            vapid = Vapid()
            vapid.generate_keys()
            _vapid_instance = vapid
            _vapid_private_pem = vapid.private_pem().decode("utf-8")
            raw_pub = vapid.public_key.public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )
            _vapid_public_b64 = b64urlencode(raw_pub)
            _VAPID_FILE_PATH.write_bytes(vapid.private_pem())
            logger.info(f"New VAPID key pair generated and saved to {_VAPID_FILE_PATH}.")
        except Exception as e:
            logger.error(f"Error generating VAPID keys: {e}")


def get_public_key() -> str:
    """Returns the URL-safe base64 VAPID public key string for browser client push subscriptions."""
    if _vapid_public_b64 is None:
        _init_vapid_keys()
    return _vapid_public_b64 or ""


def save_subscription(user_id: Any, subscription_data: Dict[str, Any]) -> bool:
    """
    Saves or updates a Web Push subscription for a user.
    `subscription_data` must contain 'endpoint' and 'keys' ({'p256dh', 'auth'}).
    """
    if not isinstance(subscription_data, dict):
        return False

    endpoint = subscription_data.get("endpoint")
    if not endpoint or not isinstance(endpoint, str):
        return False

    keys = subscription_data.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not p256dh or not auth:
        return False

    user_str = str(user_id) if user_id is not None else "anonymous"

    with _lock:
        _subscriptions[endpoint] = {
            "user_id": user_str,
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    logger.info(f"Saved push subscription for user={user_str}, total_subscriptions={len(_subscriptions)}")
    return True


def remove_subscription(endpoint: str) -> None:
    """Removes a push subscription by its endpoint."""
    with _lock:
        if endpoint in _subscriptions:
            del _subscriptions[endpoint]
            logger.info(f"Removed push subscription for endpoint: {endpoint[:30]}...")


def get_user_subscriptions(user_id: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Returns all subscriptions for a specific user, or all if user_id is None."""
    with _lock:
        if user_id is None:
            return list(_subscriptions.values())
        user_str = str(user_id)
        return [sub for sub in _subscriptions.values() if sub.get("user_id") == user_str]


def send_push_notification(
    user_id: Optional[Any] = None,
    title: str = "CocoScan Update",
    body: str = "",
    report_id: Optional[Any] = None,
    url: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Dispatches a Web Push notification to subscribers.
    If user_id is provided, sends only to that user's subscriptions.
    If user_id is None, broadcasts to all active subscriptions.
    """
    if _vapid_private_pem is None:
        _init_vapid_keys()

    if not _vapid_private_pem or webpush is None:
        logger.warning("WebPush is not available or VAPID private key is missing.")
        return {"sent": 0, "failed": 0, "status": "unavailable"}

    deep_link_url = url or (f"/farmer/reports?report_id={report_id}" if report_id else "/farmer/reports")

    payload_dict = {
        "title": title,
        "body": body,
        "icon": "/static/icons/icon-192x192.png",
        "badge": "/static/icons/icon-72x72.png",
        "data": {
            "report_id": report_id,
            "url": deep_link_url,
            **(data or {}),
        },
    }
    payload_json = json.dumps(payload_dict)

    target_subs = get_user_subscriptions(user_id)
    if not target_subs:
        logger.debug(f"No push subscriptions found for user_id={user_id}")
        return {"sent": 0, "failed": 0, "status": "no_subscribers"}

    sent_count = 0
    failed_count = 0
    endpoints_to_remove = []

    for sub in target_subs:
        endpoint = sub.get("endpoint")
        subscription_info = {
            "endpoint": endpoint,
            "keys": {
                "p256dh": sub.get("p256dh"),
                "auth": sub.get("auth"),
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload_json,
                vapid_private_key=_vapid_private_pem,
                vapid_claims={"sub": _VAPID_CLAIM_EMAIL},
                ttl=86400,
            )
            sent_count += 1
            logger.info(f"Push notification sent successfully to endpoint={endpoint[:30]}...")
        except WebPushException as ex:
            failed_count += 1
            logger.warning(f"WebPushException sending to {endpoint[:30]}...: {ex}")
            # If the subscription is no longer valid (e.g., 404 or 410 Gone), remove it
            if hasattr(ex, "response") and ex.response is not None:
                if ex.response.status_code in (404, 410):
                    endpoints_to_remove.append(endpoint)
        except Exception as e:
            failed_count += 1
            logger.error(f"Unexpected error sending web push: {e}")

    for ep in endpoints_to_remove:
        remove_subscription(ep)

    return {"sent": sent_count, "failed": failed_count, "status": "ok"}
