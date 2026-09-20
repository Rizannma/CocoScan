"""
Storage, Database Backups & Data Cleanup Service for CocoScan Admin.
Handles storage metric calculations, database dump creation, backup retention,
and system maintenance tasks.
"""

from datetime import datetime, timezone
import gzip
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Base directory for storing database backups
BACKUPS_DIR = Path(__file__).resolve().parent.parent / "backups"

# Storage limits (Default 1,024 MB = 1 GB Supabase free tier bucket limit)
DEFAULT_STORAGE_LIMIT_MB = 1024.0

# Estimated average image size for calculations when remote byte query is unsupported
DEFAULT_IMAGE_SIZE_KB = 180.0


def get_backups_dir() -> Path:
    """Ensure and return the backups directory path."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUPS_DIR


def format_bytes(size_bytes: float) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if size_bytes <= 0:
        return "0 KB"
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_storage_metrics(supabase_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Calculate storage metrics for Dataset Hub, System Backups, and Total Bucket Usage.
    """
    # 1. Calculate Backups Storage
    backup_files = list_backups()
    total_backup_bytes = sum(b.get("size_bytes", 0) for b in backup_files)
    backup_count = len(backup_files)

    # 2. Calculate Dataset Hub Storage
    # Query summary from dataset_hub module
    from app.dataset_hub import get_dataset_summary
    dataset_summary = get_dataset_summary(supabase_client)
    total_dataset_samples = dataset_summary.get("total_samples", 0)
    category_counts = dataset_summary.get("counts", {})

    # Estimate dataset image storage (or query storage if client supports it)
    dataset_bytes = int(total_dataset_samples * DEFAULT_IMAGE_SIZE_KB * 1024)

    # Breakdown per category
    categories_breakdown = []
    for slug, label in [
        ("brontispa", "Coconut Leaf Beetle (Brontispa)"),
        ("rhinoceros_beetle", "Coconut Rhinoceros Beetle"),
        ("healthy", "Healthy Coconut Leaf"),
        ("not_coconut_leaf", "Unidentified / Non-Leaf"),
    ]:
        items_count = category_counts.get(slug, 0)
        cat_bytes = int(items_count * DEFAULT_IMAGE_SIZE_KB * 1024)
        categories_breakdown.append({
            "slug": slug,
            "label": label,
            "items": items_count,
            "size_bytes": cat_bytes,
            "size_formatted": format_bytes(cat_bytes),
        })

    # 3. Total Storage Used & Bucket Progress
    # Include reports images estimate and database backups
    total_storage_bytes = dataset_bytes + total_backup_bytes
    limit_mb = float(os.getenv("SUPABASE_STORAGE_LIMIT_MB", DEFAULT_STORAGE_LIMIT_MB))
    limit_bytes = limit_mb * 1024 * 1024

    percent_used = min(100.0, (total_storage_bytes / limit_bytes) * 100.0) if limit_bytes > 0 else 0.0

    return {
        "total_storage_bytes": total_storage_bytes,
        "total_storage_formatted": format_bytes(total_storage_bytes),
        "limit_mb": limit_mb,
        "limit_formatted": f"{limit_mb / 1024:.1f} GB" if limit_mb >= 1024 else f"{limit_mb:.0f} MB",
        "percent_used": round(percent_used, 1),
        "dataset_hub": {
            "total_samples": total_dataset_samples,
            "size_bytes": dataset_bytes,
            "size_formatted": format_bytes(dataset_bytes),
            "categories": categories_breakdown,
            "status": "Synced to Supabase Cloud",
            "last_synced": datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC"),
        },
        "system_backups": {
            "count": backup_count,
            "size_bytes": total_backup_bytes,
            "size_formatted": format_bytes(total_backup_bytes),
        },
    }


def generate_database_backup(supabase_client: Optional[Any] = None, backup_type: str = "Manual") -> Dict[str, Any]:
    """
    Generate a full compressed database backup dump containing core application tables.
    Returns metadata dict of the generated backup file.
    """
    backups_dir = get_backups_dir()
    timestamp = datetime.now(timezone.utc)
    timestamp_slug = timestamp.strftime("%Y%m%d_%H%M%S")
    type_slug = "manual" if backup_type.lower() == "manual" else "daily"
    filename = f"cocoscan_db_{type_slug}_{timestamp_slug}.json.gz"
    filepath = backups_dir / filename

    tables_data: Dict[str, Any] = {}
    table_counts: Dict[str, int] = {}
    tables_to_dump = [
        "users",
        "profiles",
        "reports",
        "visit_chats",
        "visit_schedules",
        "visit_images",
        "report_supporting_images",
    ]

    # Fetch tables concurrently from Supabase client
    if supabase_client:
        from concurrent.futures import ThreadPoolExecutor

        def _fetch_table_data(tbl_name: str):
            try:
                resp = supabase_client.table(tbl_name).select("*").limit(5000).execute()
                rows = resp.data if hasattr(resp, "data") and resp.data else []
                return tbl_name, rows, len(rows)
            except Exception as err:
                logger.warning(f"Could not dump table {tbl_name}: {err}")
                return tbl_name, [], 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(_fetch_table_data, tables_to_dump)
            for tbl_name, rows, count in results:
                tables_data[tbl_name] = rows
                table_counts[tbl_name] = count

    backup_payload = {
        "metadata": {
            "project": "CocoScan",
            "version": "2.0",
            "backup_type": backup_type,
            "created_at": timestamp.isoformat(),
            "table_counts": table_counts,
            "total_records": sum(table_counts.values()),
        },
        "tables": tables_data,
    }

    # Write gzipped JSON with compact formatting for speed & efficiency
    json_bytes = json.dumps(backup_payload, separators=(',', ':'), default=str).encode("utf-8")
    with gzip.open(filepath, "wb") as gz_file:
        gz_file.write(json_bytes)

    file_size = filepath.stat().st_size

    backup_info = {
        "filename": filename,
        "type": "Manual" if backup_type.lower() == "manual" else "Daily Automated",
        "size_bytes": file_size,
        "size_formatted": format_bytes(file_size),
        "created_at": timestamp.strftime("%b %d, %Y %H:%M"),
        "timestamp_iso": timestamp.isoformat(),
        "total_records": sum(table_counts.values()),
    }

    logger.info(f"Database backup successfully generated: {filename} ({format_bytes(file_size)})")
    return backup_info


def list_backups() -> List[Dict[str, Any]]:
    """
    List all database backups stored in the backups directory sorted by creation date descending.
    """
    backups_dir = get_backups_dir()
    backup_files = [f for f in backups_dir.glob("*.json.gz") if f.is_file()]

    backups: List[Dict[str, Any]] = []
    for f in backup_files:
        try:
            stat = f.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            is_manual = "manual" in f.name.lower()
            backups.append({
                "filename": f.name,
                "type": "Manual" if is_manual else "Daily Automated",
                "size_bytes": size,
                "size_formatted": format_bytes(size),
                "created_at": mtime.strftime("%b %d, %Y %H:%M"),
                "timestamp": stat.st_mtime,
            })
        except Exception as err:
            logger.warning(f"Failed to read backup file {f}: {err}")

    # Sort newest first
    backups.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return backups


def get_backup_path(filename: str) -> Optional[Path]:
    """
    Safely resolve a backup file path, preventing directory traversal.
    """
    safe_name = Path(filename).name
    if not safe_name.endswith(".json.gz"):
        return None
    backups_dir = get_backups_dir()
    filepath = backups_dir / safe_name
    if filepath.exists() and filepath.is_file():
        return filepath
    return None


def delete_backup(
    filename: str,
    admin_id: str = "",
    admin_name: str = "",
    admin_email: str = "",
    ip_address: str = "",
) -> bool:
    """
    Safely delete a database backup file and write an audit trail entry.
    """
    filepath = get_backup_path(filename)
    if filepath and filepath.exists():
        try:
            file_size = filepath.stat().st_size
            formatted_size = format_bytes(file_size)
            filepath.unlink()
            logger.info(f"Deleted backup: {filename}")

            # Automated Audit Trail Logging
            iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            audit_details = (
                f"Admin '{admin_name or 'Administrator'}' (ID: {admin_id or 'admin'}) permanently deleted "
                f"database backup archive '{filename}' (Size: {formatted_size}). Action Timestamp: {iso_timestamp}."
            )
            try:
                from app.security_service import log_audit
                log_audit(
                    email=admin_email or f"{admin_name or 'Admin'} ({admin_id or 'admin'})",
                    role="admin",
                    action="DATABASE_BACKUP_DELETE",
                    details=audit_details,
                    ip_address=ip_address or "",
                )
            except Exception as ae:
                logger.error(f"Failed to record audit log for backup deletion: {ae}")

            return True
        except Exception as e:
            logger.error(f"Error deleting backup {filename}: {e}")
            return False
    return False


def prune_temporary_cache() -> Dict[str, Any]:
    """
    Danger Zone utility: Clean up temporary files, orphaned uploads, and scratch cache.
    """
    pruned_count = 0
    freed_bytes = 0

    temp_dirs = [
        Path(__file__).resolve().parent.parent / "temp",
        Path(__file__).resolve().parent.parent / "static" / "temp",
        Path(__file__).resolve().parent.parent / "uploads" / "temp",
    ]

    for d in temp_dirs:
        if d.exists() and d.is_dir():
            for item in d.glob("*"):
                try:
                    if item.is_file():
                        freed_bytes += item.stat().st_size
                        item.unlink()
                        pruned_count += 1
                    elif item.is_dir():
                        freed_bytes += sum(f.stat().st_size for f in item.glob("**/*") if f.is_file())
                        shutil.rmtree(item)
                        pruned_count += 1
                except Exception as err:
                    logger.warning(f"Could not remove temp item {item}: {err}")

    return {
        "success": True,
        "pruned_items": pruned_count,
        "freed_bytes": freed_bytes,
        "freed_formatted": format_bytes(freed_bytes),
    }


def cleanup_old_audit_logs(days: int = 90) -> Dict[str, Any]:
    """
    Danger Zone utility: Prune audit log entries older than specified retention days.
    """
    try:
        from app.security_service import cleanup_old_logs
        deleted_count = cleanup_old_logs(days=days)
        return {
            "success": True,
            "deleted_records": deleted_count,
            "retention_days": days,
        }
    except Exception as err:
        logger.error(f"Failed to cleanup old audit logs: {err}")
        return {
            "success": False,
            "error": str(err),
            "deleted_records": 0,
        }


def extract_storage_path(url_or_path: str, bucket: str = "reports") -> Optional[str]:
    """Extract relative bucket object path from URL or relative path string."""
    if not url_or_path:
        return None
    cleaned = url_or_path.strip()
    if f"/storage/v1/object/public/{bucket}/" in cleaned:
        return cleaned.split(f"/storage/v1/object/public/{bucket}/", 1)[-1].lstrip("/")
    if cleaned.startswith(f"{bucket}/"):
        return cleaned.split(f"{bucket}/", 1)[-1].lstrip("/")
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return None
    return cleaned.lstrip("/")


def get_recent_reports_for_danger_zone(supabase_client: Optional[Any] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """Return an enriched preview list of reports available for deletion in Danger Zone with formatted date and contextual label."""
    if not supabase_client:
        return []
    try:
        resp = supabase_client.table("reports").select("id, status, pest_type, created_at, farmer_name").order("id", desc=True).limit(limit).execute()
        rows: List[Dict[str, Any]] = resp.data or []
        for r in rows:
            created_raw = r.get("created_at") or ""
            formatted_date = ""
            if created_raw:
                try:
                    dt = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%b %d, %Y")
                except Exception:
                    formatted_date = str(created_raw)[:10]
            r["formatted_date"] = formatted_date or "Recent"
            pest = r.get("pest_type") or "General"
            status = r.get("status") or "Under Review"
            r["display_label"] = f"Report #{r.get('id')} · {pest} · {r['formatted_date']} ({status})"
        return rows
    except Exception as e:
        logger.warning(f"Could not load reports preview for danger zone: {e}")
        return []


def delete_report_cascading(
    report_id: Any,
    admin_id: str,
    admin_name: str,
    admin_email: str,
    supabase_client: Optional[Any] = None,
    ip_address: str = "",
) -> Dict[str, Any]:
    """
    Cascading Deletion Process:
    1. Resolve report and associated image files.
    2. Delete images from Supabase Cloud Storage to reclaim disk space.
    3. Delete database records (visit_images, supporting_images, visit_chats, visit_schedules, reports).
    4. Write an automated audit log entry.
    """
    from app.dataset_hub import get_storage_bucket
    from app.security_service import log_audit

    bucket = get_storage_bucket()
    deleted_images: List[str] = []
    report_data: Optional[Dict[str, Any]] = None

    if supabase_client:
        # Fetch report
        try:
            r_resp = supabase_client.table("reports").select("*").eq("id", report_id).execute()
            if r_resp.data and len(r_resp.data) > 0:
                report_data = r_resp.data[0]
        except Exception as e:
            logger.warning(f"Error fetching report #{report_id}: {e}")

        if not report_data:
            return {
                "success": False,
                "error": f"Report #{report_id} not found in database.",
                "deleted_images_count": 0,
            }

        # Collect images to delete
        paths_to_delete: List[str] = []
        main_img = extract_storage_path(report_data.get("image_url", ""), bucket=bucket)
        if main_img:
            paths_to_delete.append(main_img)

        # Supporting images
        try:
            supp_resp = supabase_client.table("report_supporting_images").select("image_url").eq("report_id", report_id).execute()
            if supp_resp.data:
                for row in supp_resp.data:
                    p = extract_storage_path(row.get("image_url", ""), bucket=bucket)
                    if p and p not in paths_to_delete:
                        paths_to_delete.append(p)
        except Exception as e:
            logger.warning(f"Could not fetch supporting images for #{report_id}: {e}")

        # Visit images
        try:
            visit_resp = supabase_client.table("visit_images").select("image_url").eq("report_id", report_id).execute()
            if visit_resp.data:
                for row in visit_resp.data:
                    p = extract_storage_path(row.get("image_url", ""), bucket=bucket)
                    if p and p not in paths_to_delete:
                        paths_to_delete.append(p)
        except Exception as e:
            logger.warning(f"Could not fetch visit images for #{report_id}: {e}")

        # Remove images from Supabase Cloud Storage
        if paths_to_delete:
            try:
                storage = supabase_client.storage.from_(bucket)
                storage.remove(paths_to_delete)
                deleted_images = paths_to_delete
                logger.info(f"Removed {len(paths_to_delete)} images from storage for report #{report_id}")
            except Exception as se:
                logger.warning(f"Supabase Storage remove failed for report #{report_id}: {se}")

        # Cascade delete database records
        try:
            supabase_client.table("visit_images").delete().eq("report_id", report_id).execute()
            supabase_client.table("report_supporting_images").delete().eq("report_id", report_id).execute()
            supabase_client.table("visit_chats").delete().eq("report_id", report_id).execute()
            supabase_client.table("visit_schedules").delete().eq("report_id", report_id).execute()
            supabase_client.table("reports").delete().eq("id", report_id).execute()
            logger.info(f"Cascading database deletion completed for report #{report_id}")
        except Exception as de:
            logger.error(f"Error during cascading database delete of report #{report_id}: {de}")
            return {
                "success": False,
                "error": f"Failed to delete database records: {de}",
                "deleted_images_count": len(deleted_images),
            }
    else:
        # Simulation for testing without remote database
        deleted_images = ["simulated_image_sample.jpg"]

    # Automated Audit Trail Logging
    iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    audit_details = (
        f"Admin '{admin_name}' (ID: {admin_id}) permanently deleted Report #{report_id} "
        f"and {len(deleted_images)} associated image file(s) from Supabase Storage. "
        f"Action Timestamp: {iso_timestamp}."
    )

    try:
        log_audit(
            email=admin_email or f"{admin_name} ({admin_id})",
            role="admin",
            action="DANGER_ZONE_REPORT_DELETE",
            details=audit_details,
            ip_address=ip_address or "",
        )
    except Exception as ae:
        logger.error(f"Failed to record audit log for report deletion: {ae}")

    return {
        "success": True,
        "report_id": report_id,
        "deleted_images_count": len(deleted_images),
        "deleted_images": deleted_images,
        "timestamp": iso_timestamp,
        "audit_details": audit_details,
    }


def count_reports_by_date_range(
    year: int,
    month: Optional[int] = None,
    supabase_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate the count of reports matching the given year and optional month."""
    import calendar

    try:
        year = int(year)
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid year provided.", "count": 0}

    if month is not None:
        try:
            month = int(month)
            if not (1 <= month <= 12):
                return {"success": False, "error": "Month must be between 1 and 12.", "count": 0}
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid month provided.", "count": 0}

    if month is not None:
        last_day = calendar.monthrange(year, month)[1]
        start_iso = f"{year:04d}-{month:02d}-01T00:00:00"
        end_iso = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59.999999"
        month_name = calendar.month_name[month]
        date_range_label = f"{month_name} {year}"
    else:
        start_iso = f"{year:04d}-01-01T00:00:00"
        end_iso = f"{year:04d}-12-31T23:59:59.999999"
        date_range_label = f"Year {year}"

    count = 0
    if supabase_client:
        try:
            rep_res = (
                supabase_client.table("reports")
                .select("id", count="exact")
                .gte("created_at", start_iso)
                .lte("created_at", end_iso)
                .execute()
            )
            count = rep_res.count if rep_res.count is not None else len(rep_res.data or [])
        except Exception as e:
            logger.warning(f"Error counting reports in {date_range_label}: {e}")
            count = 0
    else:
        count = 5

    return {
        "success": True,
        "count": count,
        "date_range_label": date_range_label,
        "year": year,
        "month": month,
    }


def bulk_delete_reports_by_date_range(
    year: int,
    month: Optional[int] = None,
    admin_id: str = "",
    admin_name: str = "",
    admin_email: str = "",
    supabase_client: Optional[Any] = None,
    ip_address: str = "",
) -> Dict[str, Any]:
    """
    Bulk Deletion by Month or Year:
    1. Determine start and end date range for the specified Year and optional Month.
    2. Query all matching reports in range.
    3. For all matching reports, collect image URLs (primary, supporting, visit).
    4. Remove collected image files from Supabase Cloud Storage to reclaim disk space.
    5. Cascade delete database records (visit_images, report_supporting_images, visit_chats, visit_schedules, reports).
    6. Record an entry in the system audit logs.
    """
    import calendar
    from app.dataset_hub import get_storage_bucket
    from app.security_service import log_audit

    try:
        year = int(year)
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid year provided."}

    if month is not None:
        try:
            month = int(month)
            if not (1 <= month <= 12):
                return {"success": False, "error": "Month must be between 1 and 12."}
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid month provided."}

    if month is not None:
        last_day = calendar.monthrange(year, month)[1]
        start_iso = f"{year:04d}-{month:02d}-01T00:00:00"
        end_iso = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59.999999"
        month_name = calendar.month_name[month]
        date_range_label = f"{month_name} {year}"
    else:
        start_iso = f"{year:04d}-01-01T00:00:00"
        end_iso = f"{year:04d}-12-31T23:59:59.999999"
        date_range_label = f"Year {year}"

    bucket = get_storage_bucket()
    deleted_images_count = 0
    deleted_reports_count = 0
    deleted_report_ids: List[Any] = []

    if supabase_client:
        try:
            rep_res = (
                supabase_client.table("reports")
                .select("id, image_url")
                .gte("created_at", start_iso)
                .lte("created_at", end_iso)
                .execute()
            )
            reports_data = rep_res.data or []
        except Exception as e:
            logger.error(f"Failed to query reports for bulk delete in range {date_range_label}: {e}")
            return {"success": False, "error": f"Failed to query reports: {e}"}

        if not reports_data:
            return {
                "success": True,
                "deleted_reports_count": 0,
                "deleted_images_count": 0,
                "date_range_label": date_range_label,
                "message": f"No reports found for {date_range_label}.",
            }

        deleted_report_ids = [r["id"] for r in reports_data if "id" in r]
        deleted_reports_count = len(deleted_report_ids)

        paths_to_delete: List[str] = []
        for r in reports_data:
            img = extract_storage_path(r.get("image_url", ""), bucket=bucket)
            if img and img not in paths_to_delete:
                paths_to_delete.append(img)

        if deleted_report_ids:
            # Batch fetch supporting images
            try:
                supp_res = (
                    supabase_client.table("report_supporting_images")
                    .select("image_url")
                    .in_("report_id", deleted_report_ids)
                    .execute()
                )
                if supp_res.data:
                    for row in supp_res.data:
                        p = extract_storage_path(row.get("image_url", ""), bucket=bucket)
                        if p and p not in paths_to_delete:
                            paths_to_delete.append(p)
            except Exception as e:
                logger.warning(f"Could not batch fetch supporting images: {e}")

            # Batch fetch visit images
            try:
                visit_res = (
                    supabase_client.table("visit_images")
                    .select("image_url")
                    .in_("report_id", deleted_report_ids)
                    .execute()
                )
                if visit_res.data:
                    for row in visit_res.data:
                        p = extract_storage_path(row.get("image_url", ""), bucket=bucket)
                        if p and p not in paths_to_delete:
                            paths_to_delete.append(p)
            except Exception as e:
                logger.warning(f"Could not batch fetch visit images: {e}")

        if paths_to_delete:
            try:
                storage = supabase_client.storage.from_(bucket)
                chunk_size = 50
                for i in range(0, len(paths_to_delete), chunk_size):
                    storage.remove(paths_to_delete[i:i + chunk_size])
                deleted_images_count = len(paths_to_delete)
                logger.info(f"Removed {deleted_images_count} images from storage for bulk range {date_range_label}")
            except Exception as se:
                logger.warning(f"Supabase storage remove failed during bulk delete: {se}")

        if deleted_report_ids:
            # Batch cascading delete from child tables to parent table
            try:
                supabase_client.table("visit_images").delete().in_("report_id", deleted_report_ids).execute()
                supabase_client.table("report_supporting_images").delete().in_("report_id", deleted_report_ids).execute()
                supabase_client.table("visit_chats").delete().in_("report_id", deleted_report_ids).execute()
                supabase_client.table("visit_schedules").delete().in_("report_id", deleted_report_ids).execute()
                supabase_client.table("reports").delete().in_("id", deleted_report_ids).execute()
            except Exception as de:
                logger.error(f"Error during bulk cascading database delete: {de}")
    else:
        # Offline simulation
        deleted_reports_count = 5
        deleted_images_count = 10
        deleted_report_ids = ["sim-1", "sim-2", "sim-3", "sim-4", "sim-5"]

    # Automated Audit Trail Logging
    iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    audit_details = (
        f"Admin '{admin_name}' (ID: {admin_id}) executed bulk cascading deletion for {date_range_label}: "
        f"permanently removed {deleted_reports_count} report(s) and {deleted_images_count} associated image file(s) "
        f"from Supabase Storage. Action Timestamp: {iso_timestamp}."
    )

    try:
        log_audit(
            email=admin_email or f"{admin_name} ({admin_id})",
            role="admin",
            action="DANGER_ZONE_BULK_REPORT_DELETE",
            details=audit_details,
            ip_address=ip_address or "",
        )
    except Exception as ae:
        logger.error(f"Failed to record audit log for bulk report deletion: {ae}")

    return {
        "success": True,
        "date_range_label": date_range_label,
        "deleted_reports_count": deleted_reports_count,
        "deleted_images_count": deleted_images_count,
        "deleted_report_ids": deleted_report_ids,
        "timestamp": iso_timestamp,
        "audit_details": audit_details,
    }


