"""
Web Push Notification Service for CocoScan.
Handles VAPID keys, persistent database push subscriptions (Supabase + local SQLite fallback),
and role-based push message dispatching.
"""

import os
import json
import sqlite3
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from py_vapid import Vapid, b64urlencode
except ImportError:
    Vapid = None
    b64urlencode = None

try:
    from cryptography.hazmat.primitives import serialization
except ImportError:
    serialization = None

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

logger = logging.getLogger(__name__)

_VAPID_FILE_PATH = Path(__file__).parent / "vapid_private.pem"
_SQLITE_PATH = Path(__file__).parent / "cocoscan_push.db"
_VAPID_CLAIM_EMAIL = os.environ.get("VAPID_CLAIM_EMAIL", "mailto:support@cocoscan.laguna.gov.ph")

_lock = threading.Lock()
_vapid_instance: Any = None
_vapid_public_b64: Optional[str] = None
_vapid_private_pem: Optional[str] = None
_sqlite_initialized = False


def _get_sqlite_conn():
    conn = sqlite3.connect(str(_SQLITE_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def _init_sqlite_db():
    global _sqlite_initialized
    if _sqlite_initialized:
        return
    try:
        with _get_sqlite_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    endpoint TEXT PRIMARY KEY,
                    user_id TEXT,
                    role TEXT,
                    p256dh TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_push_user_id ON push_subscriptions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_push_role ON push_subscriptions(role)")
            conn.commit()
        _sqlite_initialized = True
    except Exception as e:
        logger.warning(f"Error initializing SQLite push database: {e}")


def _get_supabase_client():
    try:
        from main import supabase
        return supabase
    except Exception:
        return None


def _init_vapid_keys():
    """Initializes or loads VAPID key pair."""
    global _vapid_instance, _vapid_public_b64, _vapid_private_pem
    if Vapid is None or b64urlencode is None or serialization is None:
        logger.warning("py_vapid or cryptography is not installed. Push notifications are disabled.")
        return

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
                pub_key = vapid.public_key
                if pub_key is not None and serialization is not None and b64urlencode is not None:
                    raw_pub = pub_key.public_bytes(
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
                pub_key = vapid.public_key
                if pub_key is not None and serialization is not None and b64urlencode is not None:
                    raw_pub = pub_key.public_bytes(
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
            pub_key = vapid.public_key
            if pub_key is not None and serialization is not None and b64urlencode is not None:
                raw_pub = pub_key.public_bytes(
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


def save_subscription(user_id: Any, subscription_data: Dict[str, Any], role: Optional[str] = None) -> bool:
    """
    Saves or updates a Web Push subscription persistently in SQLite and Supabase.
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
    role_str = role.strip().lower() if role else None
    now_iso = datetime.now(timezone.utc).isoformat()

    _init_sqlite_db()

    # 1. Persist to local SQLite
    with _lock:
        try:
            with _get_sqlite_conn() as conn:
                conn.execute("""
                    INSERT INTO push_subscriptions (endpoint, user_id, role, p256dh, auth, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(endpoint) DO UPDATE SET
                        user_id = excluded.user_id,
                        role = COALESCE(excluded.role, push_subscriptions.role),
                        p256dh = excluded.p256dh,
                        auth = excluded.auth,
                        updated_at = excluded.updated_at
                """, (endpoint, user_str, role_str, p256dh, auth, now_iso, now_iso))
                conn.commit()
        except Exception as sq_err:
            logger.error(f"SQLite save subscription error: {sq_err}")

    # 2. Persist to Supabase if connected
    sb = _get_supabase_client()
    if sb and hasattr(sb, "table"):
        try:
            sb.table("push_subscriptions").upsert({
                "endpoint": endpoint,
                "user_id": user_str,
                "role": role_str,
                "p256dh": p256dh,
                "auth": auth,
                "created_at": now_iso,
                "updated_at": now_iso
            }).execute()
        except Exception as sb_err:
            logger.debug(f"Supabase push_subscriptions upsert note: {sb_err}")

    logger.info(f"Saved persistent push subscription for user={user_str}, role={role_str}")
    return True


def remove_subscription(endpoint: str) -> None:
    """Removes a push subscription by its endpoint from SQLite and Supabase."""
    _init_sqlite_db()
    with _lock:
        try:
            with _get_sqlite_conn() as conn:
                conn.execute("DELETE FROM push_subscriptions WHERE endpoint = ?", (endpoint,))
                conn.commit()
        except Exception as sq_err:
            logger.error(f"SQLite remove subscription error: {sq_err}")

    sb = _get_supabase_client()
    if sb and hasattr(sb, "table"):
        try:
            sb.table("push_subscriptions").delete().eq("endpoint", endpoint).execute()
        except Exception as sb_err:
            logger.debug(f"Supabase push_subscriptions delete note: {sb_err}")

    logger.info(f"Removed push subscription for endpoint: {endpoint[:30]}...")


def get_user_subscriptions(user_id: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Returns all subscriptions for a specific user, or all if user_id is None."""
    _init_sqlite_db()
    
    # Try Supabase if available
    sb = _get_supabase_client()
    if sb and hasattr(sb, "table"):
        try:
            query = sb.table("push_subscriptions").select("*")
            if user_id is not None:
                query = query.eq("user_id", str(user_id))
            resp = query.execute()
            rows = getattr(resp, "data", None)
            if rows is not None and len(rows) > 0:
                return rows
        except Exception as sb_err:
            logger.debug(f"Supabase get_user_subscriptions query note: {sb_err}")

    # Fallback to local SQLite
    with _get_sqlite_conn() as conn:
        if user_id is None:
            cur = conn.execute("SELECT * FROM push_subscriptions")
        else:
            cur = conn.execute("SELECT * FROM push_subscriptions WHERE user_id = ?", (str(user_id),))
        return [dict(row) for row in cur.fetchall()]


def get_role_subscriptions(role: str) -> List[Dict[str, Any]]:
    """Returns all subscriptions for a specific role (e.g., 'lgu', 'agri_expert', 'farmer')."""
    _init_sqlite_db()
    norm_role = (role or "").strip().lower()
    if norm_role in ["agri_expert", "agriculturist", "expert"]:
        target_roles = ["agri_expert", "agriculturist", "expert"]
    elif norm_role in ["lgu", "lgu_officer"]:
        target_roles = ["lgu", "lgu_officer"]
    elif norm_role in ["admin", "administrator"]:
        target_roles = ["admin", "administrator"]
    else:
        target_roles = [norm_role]

    # Try Supabase if available
    sb = _get_supabase_client()
    if sb and hasattr(sb, "table"):
        try:
            resp = sb.table("push_subscriptions").select("*").in_("role", target_roles).execute()
            rows = getattr(resp, "data", None)
            if rows is not None and len(rows) > 0:
                return rows
        except Exception as sb_err:
            logger.debug(f"Supabase get_role_subscriptions query note: {sb_err}")

    # Fallback to local SQLite
    with _get_sqlite_conn() as conn:
        placeholders = ",".join("?" for _ in target_roles)
        cur = conn.execute(
            f"SELECT * FROM push_subscriptions WHERE LOWER(role) IN ({placeholders})",
            target_roles
        )
        return [dict(row) for row in cur.fetchall()]


def _dispatch_payload_to_subscriptions(
    subscriptions: List[Dict[str, Any]],
    title: str,
    body: str,
    report_id: Optional[Any] = None,
    url: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Helper that dispatches webpush to a list of subscription records."""
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(data or {}),
        },
    }
    payload_json = json.dumps(payload_dict)

    sent_count = 0
    failed_count = 0
    endpoints_to_remove = []

    for sub in subscriptions:
        endpoint = sub.get("endpoint")
        if not endpoint or not isinstance(endpoint, str):
            continue

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
            # If the subscription is no longer valid (e.g., 404 or 410 Gone), mark for deletion
            if hasattr(ex, "response") and ex.response is not None:
                if ex.response.status_code in (404, 410):
                    endpoints_to_remove.append(endpoint)
        except Exception as e:
            failed_count += 1
            logger.error(f"Unexpected error sending web push: {e}")

    for ep in endpoints_to_remove:
        remove_subscription(ep)

    return {"sent": sent_count, "failed": failed_count, "status": "ok"}


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
    target_subs = get_user_subscriptions(user_id)
    if not target_subs:
        logger.debug(f"No push subscriptions found for user_id={user_id}")
        return {"sent": 0, "failed": 0, "status": "no_subscribers"}

    return _dispatch_payload_to_subscriptions(
        target_subs, title=title, body=body, report_id=report_id, url=url, data=data
    )


def send_push_to_role(
    role: str,
    title: str = "CocoScan Alert",
    body: str = "",
    report_id: Optional[Any] = None,
    url: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Dispatches a Web Push notification to all subscribers belonging to a specific role.
    E.g., role='lgu', role='agri_expert', role='farmer'.
    """
    target_subs = get_role_subscriptions(role)
    if not target_subs:
        logger.debug(f"No push subscriptions found for role={role}")
        return {"sent": 0, "failed": 0, "status": "no_subscribers"}

    return _dispatch_payload_to_subscriptions(
        target_subs, title=title, body=body, report_id=report_id, url=url, data=data
    )
