from datetime import datetime, UTC, timedelta, timezone
import json
import logging
import os
from urllib.parse import quote, unquote, urlparse
from typing import Any, Mapping


logger = logging.getLogger(__name__)

MANILA_TIMEZONE = timezone(timedelta(hours=8))


def resolve_farmer_notes(form_data: Mapping[str, Any]) -> str:
    """Return the farmer notes from the submitted form data."""
    for key in ("farmer_notes", "field_notes", "location_notes", "notes"):
        value = form_data.get(key, "") if hasattr(form_data, "get") else ""
        if isinstance(value, str):
            value = value.strip()
            if value:
                return value
    return ""


# Backward-compatible alias so existing imports keep working during migration.
resolve_field_notes = resolve_farmer_notes


def normalize_report_status(value: Any, *, default: str = "Under Review") -> str:
    """Normalize report status values to the simple workflow used across the app."""
    if value is None:
        return default

    normalized = str(value).strip()
    if not normalized:
        return default

    key = normalized.lower().replace("_", " ").replace("-", " ")
    status_map = {
        "pending assessment": "Under Review",
        "pending review": "Under Review",
        "under review": "Under Review",
        "reviewed": "Under Review",
        "submitted": "Under Review",
        "awaiting confirmed schedule": "Waiting for Agriculturist Confirmation",
        "in progress": "In Progress",
        "in_progress": "In Progress",
        "assessment issued": "Assessment Issued",
        "assessment": "Assessment Issued",
        "on site visit requested": "Waiting for Agriculturist Confirmation",
        "visit requested": "Waiting for Agriculturist Confirmation",
        "waiting for agriculturist confirmation": "Waiting for Agriculturist Confirmation",
        "waiting for schedule": "Waiting for Agriculturist Confirmation",
        "visit scheduled": "Visit Scheduled",
        "visit completed": "Visit Completed",
        "resolved": "Resolved",
        "complete": "Resolved",
        "completed": "Resolved",
        "closed": "Resolved",
        "final remarks issued": "Resolved",
        "final remarks": "Resolved",
        "recommendation issued": "Resolved",
    }

    return status_map.get(key, normalized)


def is_under_review_report_status(value: Any) -> bool:
    """Return True if the status represents an initial report awaiting review."""
    return normalize_report_status(value, default="Under Review") == "Under Review"


def is_in_progress_report_status(value: Any) -> bool:
    """Return True if the status represents an active report that has been reviewed or is in progress."""
    normalized = normalize_report_status(value, default="Under Review")
    return normalized not in ("Under Review", "Resolved")


def is_pending_report_status(value: Any) -> bool:
    return not is_resolved_report_status(value)


def is_active_report_status(value: Any) -> bool:
    return is_pending_report_status(value)


def is_reviewed_report_status(value: Any) -> bool:
    return is_resolved_report_status(value)


def is_resolved_report_status(value: Any) -> bool:
    return normalize_report_status(value, default="Under Review") == "Resolved"


def _storage_object_path(image_url: str) -> str:
    """Extract a bucket-relative path from a stored Supabase image reference."""
    parsed = urlparse(image_url)
    path = parsed.path
    marker = "/storage/v1/object/"
    if marker in path:
        object_path = path.split(marker, 1)[1].lstrip("/")
        for prefix in ("public/", "sign/"):
            if object_path.startswith(prefix):
                object_path = object_path[len(prefix):]
        bucket = (os.getenv("SUPABASE_STORAGE_BUCKET", "reports") or "reports").strip()
        if object_path.startswith(f"{bucket}/"):
            return unquote(object_path[len(bucket) + 1:])
        return ""
    if parsed.scheme and parsed.netloc:
        return ""
    return unquote(path.lstrip("/"))


def resolve_report_image_url(image_url: Any, storage_client: Any = None, expires_in: int = 3600) -> str:
    """Return the public URL for a report image stored in the public bucket."""
    if not image_url:
        return ""

    resolved = str(image_url).strip()
    if not resolved:
        return ""

    if resolved.startswith(("data:", "blob:")):
        return resolved

    parsed = urlparse(resolved)
    if "/storage/v1/object/public/" in parsed.path.lower():
        return resolved

    object_path = _storage_object_path(resolved)
    if not object_path:
        return resolved

    bucket = (os.getenv("SUPABASE_STORAGE_BUCKET", "reports") or "reports").strip()
    base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if parsed.scheme and parsed.netloc:
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    if not base_url:
        logger.warning("Cannot resolve public report image URL without SUPABASE_URL")
        return ""

    return (
        f"{base_url}/storage/v1/object/public/"
        f"{quote(bucket, safe='')}/{quote(object_path, safe='/')}"
    )


def parse_utc_timestamp(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(MANILA_TIMEZONE)


def format_report_timestamp(value: Any, fmt: str = "%b %d, %Y  %I:%M %p") -> str:
    parsed = parse_utc_timestamp(value)
    return parsed.strftime(fmt) if parsed else "Timestamp unavailable"


def format_report_date(value: Any) -> str:
    parsed = parse_utc_timestamp(value)
    return parsed.strftime("%Y-%m-%d") if parsed else ""


def build_report_payload(
    *,
    user_id: str | None = None,
    pest_type: str,
    farmer_notes: str,
    confidence: Any,
    latitude: Any = None,
    longitude: Any = None,
    gps_accuracy: Any = "",
    location_source: str = "camera_gps",
    photo_taken_at: str = "",
    initial_recommendations: Any = None,
    farmer_name: str = "Farmer",
    created_at: str | None = None,
    submitted_at: str | None = None,
    status: str = "Under Review",
    image_url: str = "",
    barangay: str = "",
    municipality: str = "",
    province: str = "",
) -> dict[str, Any]:
    """Create a report payload compatible with the Supabase reports table."""
    if created_at is None:
        created_at = datetime.now(UTC).isoformat()
    if submitted_at is None:
        submitted_at = created_at

    if isinstance(initial_recommendations, str):
        try:
            initial_recommendations = json.loads(initial_recommendations)
        except (TypeError, ValueError):
            initial_recommendations = [initial_recommendations]
    if initial_recommendations is None:
        initial_recommendations = []

    # Convert coordinate strings to floats for database compatibility
    parsed_lat: float | None = None
    try:
        parsed_lat = float(latitude) if latitude else None
    except (ValueError, TypeError):
        parsed_lat = None
    
    parsed_lng: float | None = None
    try:
        parsed_lng = float(longitude) if longitude else None
    except (ValueError, TypeError):
        parsed_lng = None
    
    # Convert confidence to float
    try:
        confidence = float(confidence) if confidence else 0.0
    except (ValueError, TypeError):
        confidence = 0.0

    status = normalize_report_status(status, default="Under Review")

    return {
        "user_id": user_id,
        "farmer_name": farmer_name,
        "pest_type": pest_type,
        "confidence": confidence,
        "image_url": image_url,
        "farmer_notes": farmer_notes,
        "status": status,
        "created_at": created_at,
        "initial_recommendations": initial_recommendations,
        "latitude": parsed_lat,
        "longitude": parsed_lng,
        "gps_accuracy": gps_accuracy,
        "location_source": location_source,
        "photo_taken_at": photo_taken_at,
        "barangay": barangay,
        "municipality": municipality,
        "province": province,
        "submitted_at": submitted_at,
        "updated_at": submitted_at,
    }
