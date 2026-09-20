"""
Automated unit and integration tests for Storage, Backups & Danger Zone admin features.
"""

from datetime import datetime, timezone
import json
import os
import sys
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from app.backup_service import (
    format_bytes,
    get_backups_dir,
    get_storage_metrics,
    generate_database_backup,
    list_backups,
    get_backup_path,
    delete_backup,
    prune_temporary_cache,
    cleanup_old_audit_logs,
)


class StorageBackupsTests(unittest.TestCase):
    def setUp(self):
        from app.security_service import init_security_db
        init_security_db()
        main.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = main.app.test_client()

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0 KB")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1024 * 50), "50.0 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5), "5.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 2), "2.00 GB")

    def test_backup_generation_and_listing(self):
        backups_dir = get_backups_dir()
        self.assertTrue(backups_dir.exists())

        # Generate a manual backup
        backup_info = generate_database_backup(supabase_client=None, backup_type="Manual")
        self.assertIn("filename", backup_info)
        self.assertEqual(backup_info["type"], "Manual")
        self.assertTrue(backup_info["filename"].endswith(".json.gz"))

        # Verify file exists and is gzipped json
        file_path = get_backup_path(backup_info["filename"])
        self.assertIsNotNone(file_path)
        self.assertTrue(file_path.exists())

        # Verify list_backups finds it
        backups = list_backups()
        self.assertTrue(len(backups) >= 1)
        found = any(b["filename"] == backup_info["filename"] for b in backups)
        self.assertTrue(found)

        # Clean up
        delete_success = delete_backup(backup_info["filename"])
        self.assertTrue(delete_success)
        self.assertFalse(file_path.exists())

    def test_get_storage_metrics(self):
        metrics = get_storage_metrics(supabase_client=None)
        self.assertIn("total_storage_formatted", metrics)
        self.assertIn("percent_used", metrics)
        self.assertIn("dataset_hub", metrics)
        self.assertIn("system_backups", metrics)
        self.assertEqual(len(metrics["dataset_hub"]["categories"]), 4)

    def test_admin_storage_backups_access_control(self):
        # Unauthenticated: should redirect to login
        res = self.client.get("/admin/storage-backups")
        self.assertIn(res.status_code, [302, 401, 403])

        # Farmer role: should be forbidden/redirected
        with self.client.session_transaction() as sess:
            sess["user_id"] = "farmer-123"
            sess["user_role"] = "farmer"
            sess["user_name"] = "Farmer John"

        res = self.client.get("/admin/storage-backups")
        self.assertIn(res.status_code, [302, 403])

        # Admin role: should allow access (200 OK)
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        res = self.client.get("/admin/storage-backups")
        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn("Storage &amp; Backups", content)
        self.assertIn("Total Storage Used", content)
        self.assertIn("Dataset Hub Storage", content)
        self.assertIn("System Backups Storage", content)
        self.assertIn("Database Backups", content)
        self.assertIn("Generate Backup Now", content)
        self.assertIn("Tiered Retention Policy", content)
        self.assertIn("Danger Zone", content)
        self.assertIn("By Specific Report", content)
        self.assertIn("By Date Range / Bulk", content)
        self.assertIn("Trigger Report Deletion...", content)
        self.assertIn("Bulk Delete by Date Range", content)
        self.assertIn("delete report PCA Admin", content)

    def test_admin_generate_download_delete_backup_routes(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        # 1. Trigger generate backup POST
        gen_res = self.client.post("/admin/storage-backups/generate", follow_redirects=True)
        self.assertEqual(gen_res.status_code, 200)

        # 2. Get newest backup
        backups = list_backups()
        self.assertTrue(len(backups) > 0)
        target_filename = backups[0]["filename"]

        # 3. Download the backup
        dl_res = self.client.get(f"/admin/storage-backups/download/{target_filename}")
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.mimetype, "application/gzip")
        self.assertTrue(len(dl_res.data) > 0)

        # 4. Delete the backup - Reject if confirmation phrase is missing or wrong
        bad_del_res = self.client.post(
            f"/admin/storage-backups/delete/{target_filename}",
            data={"confirmation_phrase": "wrong phrase"},
            follow_redirects=True,
        )
        self.assertEqual(bad_del_res.status_code, 200)
        self.assertIn("Confirmation phrase mismatch", bad_del_res.get_data(as_text=True))
        self.assertIsNotNone(get_backup_path(target_filename))

        # 5. Delete the backup - Succeed with exact phrase 'delete backup PCA Admin'
        del_res = self.client.post(
            f"/admin/storage-backups/delete/{target_filename}",
            data={"confirmation_phrase": "delete backup PCA Admin"},
            follow_redirects=True,
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertIn("deleted successfully", del_res.get_data(as_text=True))
        self.assertIsNone(get_backup_path(target_filename))

        # 6. Verify audit log entry was written
        from app.security_service import get_audit_logs
        logs_data = get_audit_logs(page=1, per_page=10, search=target_filename)
        logs_list = logs_data.get("logs", [])
        self.assertTrue(any(target_filename in str(l.get("details", "")) for l in logs_list if isinstance(l, dict)))

    def test_danger_zone_endpoints(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        # Prune cache
        prune_res = self.client.post("/admin/storage-backups/danger/prune-cache", follow_redirects=True)
        self.assertEqual(prune_res.status_code, 200)

        # Cleanup old audit logs
        cleanup_res = self.client.post(
            "/admin/storage-backups/danger/cleanup-logs",
            data={"retention_days": "90"},
            follow_redirects=True,
        )
        self.assertEqual(cleanup_res.status_code, 200)

    def test_danger_zone_report_deletion_security_and_audit(self):
        admin_name = "PCA Admin"
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-777"
            sess["user_role"] = "admin"
            sess["user_name"] = admin_name
            sess["user_email"] = "admin@cocoscan.org"

        # 1. Reject if confirmation phrase is wrong or mismatched
        bad_phrase_res = self.client.post(
            "/admin/storage-backups/danger/delete-report",
            data={
                "report_id": "999",
                "confirmation_phrase": "delete report someone_else",
            },
            follow_redirects=True,
        )
        self.assertEqual(bad_phrase_res.status_code, 200)
        self.assertIn("Confirmation phrase mismatch", bad_phrase_res.get_data(as_text=True))

        # 2. Reject if report ID is missing
        no_id_res = self.client.post(
            "/admin/storage-backups/danger/delete-report",
            data={
                "report_id": "",
                "confirmation_phrase": f"delete report {admin_name}",
            },
            follow_redirects=True,
        )
        self.assertEqual(no_id_res.status_code, 200)
        self.assertIn("Please specify a valid Report ID", no_id_res.get_data(as_text=True))

        # 3. Successful deletion when phrase matches perfectly
        with patch("app.backup_service.delete_report_cascading") as mock_delete:
            mock_delete.return_value = {
                "success": True,
                "report_id": "999",
                "deleted_images_count": 2,
                "deleted_images": ["report_media/farmer_1/leaf1.jpg", "report_media/farmer_1/leaf2.jpg"],
                "timestamp": "2026-09-20 17:00:00 UTC",
                "audit_details": f"Admin '{admin_name}' (ID: admin-777) permanently deleted Report #999 and 2 associated image file(s).",
            }

            good_res = self.client.post(
                "/admin/storage-backups/danger/delete-report",
                data={
                    "report_id": "999",
                    "confirmation_phrase": f"delete report {admin_name}",
                },
                follow_redirects=True,
            )
            self.assertEqual(good_res.status_code, 200)
            self.assertIn("permanently purged", good_res.get_data(as_text=True))
            mock_delete.assert_called_once()

    def test_delete_report_cascading_audit_log_written(self):
        from app.backup_service import delete_report_cascading
        from app.security_service import get_audit_logs

        admin_id = "admin-888"
        admin_name = "Super Admin"
        admin_email = "superadmin@cocoscan.org"

        # Execute cascading deletion
        result = delete_report_cascading(
            report_id="101",
            admin_id=admin_id,
            admin_name=admin_name,
            admin_email=admin_email,
            supabase_client=None,  # Offline/fallback mode
            ip_address="192.168.1.50",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["report_id"], "101")
        self.assertIn("audit_details", result)

        # Verify entry is recorded in the audit trail
        logs_data = get_audit_logs(page=1, per_page=10, search="101")
        total_val: Any = logs_data.get("total", 0)
        self.assertGreaterEqual(int(total_val), 1)
        logs_list = logs_data.get("logs", [])
        self.assertIsInstance(logs_list, list)
        found_entry = any("Report #101" in str(log.get("details", "")) for log in logs_list if isinstance(log, dict))
        self.assertTrue(found_entry)

    def test_bulk_delete_reports_by_date_range_and_audit(self):
        from app.backup_service import bulk_delete_reports_by_date_range
        from app.security_service import get_audit_logs

        admin_id = "admin-777"
        admin_name = "Auditor Admin"
        admin_email = "auditor@cocoscan.org"

        # Month and Year bulk deletion
        res = bulk_delete_reports_by_date_range(
            year=2024,
            month=8,
            admin_id=admin_id,
            admin_name=admin_name,
            admin_email=admin_email,
            supabase_client=None,
            ip_address="10.0.0.1",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["date_range_label"], "August 2024")
        self.assertGreater(res["deleted_reports_count"], 0)
        self.assertIn("audit_details", res)

        # Year only bulk deletion
        res_year = bulk_delete_reports_by_date_range(
            year=2023,
            month=None,
            admin_id=admin_id,
            admin_name=admin_name,
            admin_email=admin_email,
            supabase_client=None,
        )
        self.assertTrue(res_year["success"])
        self.assertEqual(res_year["date_range_label"], "Year 2023")

        # Verify audit logs captured the action
        logs_data = get_audit_logs(page=1, per_page=10, search="August 2024")
        logs_list = logs_data.get("logs", [])
        self.assertIsInstance(logs_list, list)
        found_bulk_entry = any("August 2024" in str(log.get("details", "")) for log in logs_list if isinstance(log, dict))
        self.assertTrue(found_bulk_entry)

    def test_admin_bulk_delete_reports_route_security(self):
        admin_name = "Super Admin"
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-1"
            sess["user_role"] = "admin"
            sess["user_name"] = admin_name

        # 1. Phrase mismatch should reject deletion
        bad_res = self.client.post(
            "/admin/storage-backups/danger/bulk-delete",
            data={
                "year": "2024",
                "month": "6",
                "confirmation_phrase": "incorrect phrase",
            },
            follow_redirects=True,
        )
        self.assertEqual(bad_res.status_code, 200)
        self.assertIn("Confirmation phrase mismatch", bad_res.get_data(as_text=True))

        # 2. Correct confirmation phrase executes bulk deletion
        with patch("app.backup_service.bulk_delete_reports_by_date_range") as mock_bulk:
            mock_bulk.return_value = {
                "success": True,
                "date_range_label": "June 2024",
                "deleted_reports_count": 12,
                "deleted_images_count": 24,
            }

            good_res = self.client.post(
                "/admin/storage-backups/danger/bulk-delete",
                data={
                    "year": "2024",
                    "month": "6",
                    "confirmation_phrase": f"delete report {admin_name}",
                },
                follow_redirects=True,
            )
            self.assertEqual(good_res.status_code, 200)
            self.assertIn("Bulk deletion completed for June 2024", good_res.get_data(as_text=True))
            mock_bulk.assert_called_once()

    def test_count_reports_by_date_range_service(self):
        from app.backup_service import count_reports_by_date_range

        # 1. Standalone fallback test
        res = count_reports_by_date_range(year=2024, month=7, supabase_client=None)
        self.assertTrue(res["success"])
        self.assertEqual(res["date_range_label"], "July 2024")
        self.assertIsInstance(res["count"], int)

        # 2. Invalid year / month
        bad_year = count_reports_by_date_range(year="invalid")
        self.assertFalse(bad_year["success"])

        bad_month = count_reports_by_date_range(year=2024, month=13)
        self.assertFalse(bad_month["success"])

        # 3. Year only
        year_res = count_reports_by_date_range(year=2025, month=None, supabase_client=None)
        self.assertTrue(year_res["success"])
        self.assertEqual(year_res["date_range_label"], "Year 2025")

    def test_admin_danger_count_bulk_route(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-count-test"
            sess["user_role"] = "admin"
            sess["user_name"] = "Count Admin"

        with patch("app.backup_service.count_reports_by_date_range") as mock_count:
            # When items are found
            mock_count.return_value = {
                "success": True,
                "count": 8,
                "date_range_label": "May 2024",
                "year": 2024,
                "month": 5,
            }

            res = self.client.get("/admin/storage-backups/danger/count-bulk?year=2024&month=5")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["count"], 8)
            self.assertEqual(data["date_range_label"], "May 2024")

            # When 0 items are found
            mock_count.return_value = {
                "success": True,
                "count": 0,
                "date_range_label": "January 2021",
                "year": 2021,
                "month": 1,
            }
            res_zero = self.client.get("/admin/storage-backups/danger/count-bulk?year=2021&month=1")
            self.assertEqual(res_zero.status_code, 200)
            data_zero = res_zero.get_json()
            self.assertTrue(data_zero["success"])
            self.assertEqual(data_zero["count"], 0)


if __name__ == "__main__":
    unittest.main()


