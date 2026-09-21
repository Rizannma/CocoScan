"""
CocoScan Simplified Dataset Hub & Cloud Export Pipeline.

Features:
1. Cloud-Only Storage (Supabase): Verified & corrected images are uploaded directly
   to Supabase Storage bucket ('reports') under category paths:
   - dataset/brontispa/
   - dataset/rhinoceros_beetle/
   - dataset/healthy/
   - dataset/not_coconut_leaf/
   No dataset images or manifest files are saved to the local disk.
2. Dataset Summary & Metrics: Aggregates total samples, category breakdowns,
   and validated vs. corrected counts.
3. Export as ZIP: Assembles an in-memory ZIP archive containing categorized folders
   and root metadata files (dataset_manifest.json, dataset_metadata.csv, README.txt)
   for external offline training.
"""

import base64
import csv
import io
import json
import logging
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

logger = logging.getLogger(__name__)

CATEGORY_SLUGS: Dict[str, str] = {
    "Brontispa": "brontispa",
    "Rhinoceros Beetle": "rhinoceros_beetle",
    "Healthy Coconut Leaf": "healthy",
    "Not a Coconut Leaf Image": "not_coconut_leaf",
}

CATEGORIES: List[str] = list(CATEGORY_SLUGS.values())

SLUG_TO_LABEL: Dict[str, str] = {
    "brontispa": "Brontispa",
    "rhinoceros_beetle": "Rhinoceros Beetle",
    "healthy": "Healthy Coconut Leaf",
    "not_coconut_leaf": "Not a Coconut Leaf Image",
}

# The trained 4-class pest model output order:
PEST_CLASSES = [
    "Brontispa",          # Index 0
    "Healthy",            # Index 1
    "Not Coconut Leaf",   # Index 2
    "Rhinoceros",         # Index 3
]

# The canonical 4-class output order
CANONICAL_CLASSES = ["Brontispa", "Healthy Coconut Leaf", "Rhinoceros Beetle", "Not a Coconut Leaf Image"]
CLASS_TO_INDEX = {name: idx for idx, name in enumerate(PEST_CLASSES)}


def get_supabase_client(client: Optional[Any] = None) -> Optional[Any]:
    """Retrieve or initialize the Supabase client."""
    if client is not None:
        return client

    # Try main module supabase client first
    main_mod = sys.modules.get("main")
    if main_mod and hasattr(main_mod, "supabase") and main_mod.supabase is not None:
        return main_mod.supabase

    # Otherwise initialize from environment variables
    url = os.getenv("SUPABASE_URL", "https://utvltqgxqnpcqrphuojc.supabase.co").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()

    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception as e:
            logger.warning(f"Could not create Supabase client: {e}")
    return None


def get_storage_bucket() -> str:
    """Get the active Supabase storage bucket name."""
    return (os.getenv("SUPABASE_STORAGE_BUCKET", "reports") or "reports").strip() or "reports"


def get_public_storage_url(storage_path: str) -> str:
    """Construct the public HTTP URL for an object in Supabase storage."""
    base_url = os.getenv("SUPABASE_URL", "https://utvltqgxqnpcqrphuojc.supabase.co").rstrip("/")
    bucket = get_storage_bucket()
    clean_path = storage_path.lstrip("/")
    return f"{base_url}/storage/v1/object/public/{bucket}/{clean_path}"


def normalize_class_label(label: str) -> str:
    """Normalize user or API strings to canonical class names."""
    if not label:
        return "Not a Coconut Leaf Image"
    cleaned = label.strip().lower()
    if "brontispa" in cleaned or "leaf beetle" in cleaned:
        return "Brontispa"
    if "rhino" in cleaned or "beetle" in cleaned or "oryctes" in cleaned:
        return "Rhinoceros Beetle"
    if "healthy" in cleaned or "malusog" in cleaned:
        return "Healthy Coconut Leaf"
    if "not" in cleaned or "hindi" in cleaned or "invalid" in cleaned or "other" in cleaned or "unknown" in cleaned:
        return "Not a Coconut Leaf Image"
    for canonical in CANONICAL_CLASSES:
        if canonical.lower() == cleaned:
            return canonical
    return "Not a Coconut Leaf Image"


def get_category_slug(label: str) -> str:
    """Get directory slug for a given label."""
    norm = normalize_class_label(label)
    return CATEGORY_SLUGS.get(norm, "not_coconut_leaf")


def save_verified_sample(
    report_id: Union[int, str],
    image_data: Union[bytes, str, Image.Image],
    verified_label: str,
    original_prediction: Optional[str] = None,
    agriculturist_id: Optional[str] = None,
    notes: Optional[str] = None,
    supabase_client: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Save an agriculturist-verified report image directly into Supabase Storage.
    No files are written to local disk.
    """
    canonical_label = normalize_class_label(verified_label)
    category_slug = get_category_slug(canonical_label)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_report_id = str(report_id).replace("/", "_").replace("\\", "_")
    filename = f"report_{safe_report_id}_{timestamp_str}.jpg"
    storage_path = f"dataset_retrain/{category_slug}/{filename}"
    bucket = get_storage_bucket()
    client = get_supabase_client(supabase_client)

    pil_img: Optional[Image.Image] = None

    if isinstance(image_data, Image.Image):
        pil_img = image_data.convert("RGB")
    elif isinstance(image_data, bytes):
        try:
            pil_img = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to open image bytes for report #{report_id}: {e}")
            return None
    elif isinstance(image_data, str):
        # Could be base64, local file path, or URL
        if image_data.startswith("data:") or "," in image_data:
            try:
                b64_str = image_data.split(",", 1)[1] if "," in image_data else image_data
                raw = base64.b64decode(b64_str)
                pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to decode base64 for report #{report_id}: {e}")
                return None
        elif Path(image_data).exists():
            try:
                pil_img = Image.open(Path(image_data)).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to open path {image_data}: {e}")
                return None
        elif image_data.startswith("http://") or image_data.startswith("https://"):
            try:
                import httpx
                resp = httpx.get(image_data, timeout=10.0)
                if resp.status_code == 200:
                    pil_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to fetch image from URL {image_data}: {e}")
                return None
        else:
            # Check Supabase Storage path
            try:
                if client:
                    try:
                        storage = client.storage.from_(bucket)
                        raw_bytes = storage.download(image_data.lstrip("/"))
                        if raw_bytes:
                            pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                    except Exception as direct_err:
                        logger.debug(f"Direct storage download fallback for {image_data}: {direct_err}")
                if pil_img is None:
                    storage_url = get_public_storage_url(image_data)
                    import httpx
                    resp = httpx.get(storage_url, timeout=10.0)
                    if resp.status_code == 200:
                        pil_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to fetch image from Supabase storage {image_data}: {e}")
                return None

    if pil_img is None:
        logger.warning(f"No valid image could be resolved for report #{report_id}")
        return None

    # Resize/compress to standard 512x512 JPEG for dataset storage in-memory
    pil_img.thumbnail((512, 512), Image.Resampling.BILINEAR)
    img_byte_arr = io.BytesIO()
    pil_img.save(img_byte_arr, format="JPEG", quality=90)
    image_bytes = img_byte_arr.getvalue()

    # Upload directly to Supabase Storage without writing to local disk
    if client:
        try:
            storage = client.storage.from_(bucket)
            storage.upload(storage_path, image_bytes, {"content-type": "image/jpeg", "upsert": "true"})
            logger.info(f"Cloud dataset sample uploaded: {bucket}/{storage_path}")
        except Exception as upload_err:
            logger.warning(f"Supabase Storage upload failed for {storage_path}: {upload_err}")
    else:
        logger.warning(f"Supabase client unavailable; verified sample in-memory only: {storage_path}")

    public_url = get_public_storage_url(storage_path)
    is_correction = bool(original_prediction and normalize_class_label(original_prediction) != canonical_label)

    entry = {
        "id": f"sample_{safe_report_id}_{timestamp_str}",
        "report_id": safe_report_id,
        "filename": filename,
        "storage_path": storage_path,
        "public_url": public_url,
        "relative_path": storage_path,
        "category_slug": category_slug,
        "verified_label": canonical_label,
        "original_prediction": original_prediction or "Unknown",
        "is_correction": is_correction,
        "agriculturist_id": agriculturist_id if agriculturist_id else None,
        "notes": (notes or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return entry


def get_dataset_summary(supabase_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Calculate and return dataset collection statistics from Supabase reports & storage.
    """
    client = get_supabase_client(supabase_client)
    counts = {
        "brontispa": 0,
        "rhinoceros_beetle": 0,
        "healthy": 0,
        "not_coconut_leaf": 0,
    }
    validated_count = 0
    corrected_count = 0
    samples: List[Dict[str, Any]] = []

    if client:
        try:
            # Query reports with pest_type and images
            rep_resp = (
                client.table("reports")
                .select("id, pest_type, image_url, expert_recommendations, status, created_at, reviewed_by_id")
                .order("created_at", desc=True)
                .execute()
            )
            rows = getattr(rep_resp, "data", []) or []

            for row in rows:
                pest_type = row.get("pest_type") or "Not a Coconut Leaf Image"
                canonical = normalize_class_label(pest_type)
                slug = get_category_slug(canonical)
                if slug in counts:
                    counts[slug] += 1

                # Check if assessed / validated
                status = str(row.get("status") or "").lower()
                expert_rec = row.get("expert_recommendations") or []
                notes = (
                    row.get("final_remarks")
                    or row.get("reviewer_notes")
                    or (expert_rec[0] if isinstance(expert_rec, list) and len(expert_rec) > 0 else "")
                    or ""
                )

                # Determine if validated or corrected
                is_corrected = False
                if "corrected" in str(notes).lower() or "correction" in str(notes).lower():
                    is_corrected = True
                    corrected_count += 1
                else:
                    validated_count += 1

                img_url = row.get("image_url") or ""
                thumb_url = img_url
                if img_url and not (img_url.startswith("http://") or img_url.startswith("https://") or img_url.startswith("data:")):
                    thumb_url = get_public_storage_url(img_url)

                samples.append({
                    "id": f"report_{row.get('id')}",
                    "report_id": str(row.get("id")),
                    "category_slug": slug,
                    "verified_label": canonical,
                    "original_prediction": canonical,
                    "is_correction": is_corrected,
                    "image_url": thumb_url,
                    "public_url": thumb_url,
                    "storage_path": f"dataset_retrain/{slug}/report_{row.get('id')}.jpg",
                    "relative_path": f"dataset_retrain/{slug}/report_{row.get('id')}.jpg",
                    "notes": str(notes).strip() if notes else "",
                    "agriculturist_id": row.get("reviewed_by_id") or "PCA Expert",
                    "created_at": row.get("created_at") or datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            logger.warning(f"Error fetching dataset summary from Supabase: {e}")

    total_samples = sum(counts.values())

    return {
        "total_samples": total_samples,
        "validated_count": validated_count,
        "corrected_count": corrected_count,
        "counts": counts,
        "categories": {
            "brontispa": {"label": "Brontispa", "count": counts["brontispa"], "slug": "brontispa"},
            "rhinoceros_beetle": {"label": "Rhinoceros Beetle", "count": counts["rhinoceros_beetle"], "slug": "rhinoceros_beetle"},
            "healthy": {"label": "Healthy Coconut Leaf", "count": counts["healthy"], "slug": "healthy"},
            "not_coconut_leaf": {"label": "Not a Coconut Leaf Image", "count": counts["not_coconut_leaf"], "slug": "not_coconut_leaf"},
        },
        "recent_samples": samples[:50],
    }


def get_recent_dataset_samples(
    limit: int = 50, category: Optional[str] = None, supabase_client: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Retrieve recent verified samples, optionally filtered by category."""
    summary = get_dataset_summary(supabase_client)
    samples = summary.get("recent_samples", [])
    if category and category.lower() != "all":
        norm_cat = get_category_slug(category)
        samples = [item for item in samples if item.get("category_slug") == norm_cat]
    return samples[:limit]


def generate_dataset_zip(supabase_client: Optional[Any] = None) -> Tuple[io.BytesIO, str]:
    """
    Assemble and return an in-memory ZIP archive containing categorized folders
    and root metadata files (dataset_manifest.json, dataset_metadata.csv, README.txt)
    for external offline training.

    Returns:
        (BytesIO buffer containing the ZIP archive, filename string)
    """
    client = get_supabase_client(supabase_client)
    summary = get_dataset_summary(client)
    samples = summary.get("recent_samples", [])

    zip_buffer = io.BytesIO()
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"cocoscan_dataset_{timestamp_str}.zip"

    manifest_entries: List[Dict[str, Any]] = []
    csv_rows: List[List[str]] = [
        ["report_id", "category_slug", "verified_label", "original_prediction", "is_correction", "agriculturist_id", "created_at", "filename", "public_url"]
    ]

    import httpx

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        # Create empty placeholder category folders
        for slug in CATEGORIES:
            zip_file.writestr(f"{slug}/.gitkeep", b"")

        for sample in samples:
            slug = sample.get("category_slug", "not_coconut_leaf")
            rep_id = sample.get("report_id", "unknown")
            file_name = f"report_{rep_id}_{timestamp_str}.jpg"
            zip_entry_path = f"{slug}/{file_name}"
            img_url = sample.get("public_url") or sample.get("image_url")

            img_bytes: Optional[bytes] = None
            if img_url:
                try:
                    if img_url.startswith("http://") or img_url.startswith("https://"):
                        resp = httpx.get(img_url, timeout=10.0)
                        if resp.status_code == 200:
                            img_bytes = resp.content
                    elif img_url.startswith("data:"):
                        b64_str = img_url.split(",", 1)[1] if "," in img_url else img_url
                        img_bytes = base64.b64decode(b64_str)
                except Exception as dl_err:
                    logger.warning(f"Could not download image {img_url} for ZIP export: {dl_err}")

            if img_bytes:
                zip_file.writestr(zip_entry_path, img_bytes)

            manifest_entry = {
                "report_id": rep_id,
                "category": slug,
                "verified_label": sample.get("verified_label"),
                "original_prediction": sample.get("original_prediction"),
                "is_correction": sample.get("is_correction", False),
                "agriculturist_id": sample.get("agriculturist_id"),
                "created_at": sample.get("created_at"),
                "zip_path": zip_entry_path,
                "public_url": img_url,
            }
            manifest_entries.append(manifest_entry)

            csv_rows.append([
                str(rep_id),
                slug,
                str(sample.get("verified_label", "")),
                str(sample.get("original_prediction", "")),
                "true" if sample.get("is_correction") else "false",
                str(sample.get("agriculturist_id", "")),
                str(sample.get("created_at", "")),
                file_name,
                str(img_url or ""),
            ])

        # Write dataset_manifest.json
        manifest_json_str = json.dumps({
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_samples": len(manifest_entries),
            "categories": summary.get("counts", {}),
            "validated_count": summary.get("validated_count", 0),
            "corrected_count": summary.get("corrected_count", 0),
            "samples": manifest_entries,
        }, indent=2)
        zip_file.writestr("dataset_manifest.json", manifest_json_str.encode("utf-8"))

        # Write dataset_metadata.csv
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerows(csv_rows)
        zip_file.writestr("dataset_metadata.csv", csv_buffer.getvalue().encode("utf-8"))

        # Write README.txt
        readme_text = f"""CocoScan Exported Dataset Pipeline
Exported on: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
Total Samples: {len(manifest_entries)}

Categories:
- brontispa/ : Coconut Leaf Beetle (Brontispa longissima)
- rhinoceros_beetle/ : Coconut Rhinoceros Beetle (Oryctes rhinoceros)
- healthy/ : Healthy Coconut Leaf
- not_coconut_leaf/ : Unidentified or Non-Coconut Leaf Images

Files:
- dataset_manifest.json : JSON metadata for each verified sample
- dataset_metadata.csv  : CSV table for training pipeline integration (PyTorch/TensorFlow/YOLO)
"""
        zip_file.writestr("README.txt", readme_text.encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer, zip_filename
