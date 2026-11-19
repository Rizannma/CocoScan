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
from cryptography.fernet import Fernet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from app.backup_service import (
    format_bytes,
    get_backups_dir,
    get_storage_metrics,
    get_recent_reports_for_danger_zone,
    generate_database_backup,
    list_backups,
    list_cloud_backups,
    get_latest_backup_run,
    get_cloud_backup_download_url,
    delete_cloud_backup,
    get_backup_storage_client,
    get_backup_path,
    delete_backup,
    prune_temporary_cache,
    cleanup_old_audit_logs,
)


class StorageBackupsTests(unittest.TestCase):
    def setUp(self):
        from app.security_service import init_security_db
        init_security_db()
        self.backup_key_patch = patch.dict(
            os.environ,
            {"BACKUP_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii")},
        )
        self.backup_key_patch.start()
        self.addCleanup(self.backup_key_patch.stop)
        main.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = main.app.test_client()
        original_table = main.supabase.table

        def table_with_approved_admin(table_name):
            if table_name != "users":
                return original_table(table_name)
            query = MagicMock()
            query.select.return_value = query
            query.eq.return_value = query
            query.execute.return_value = MagicMock(data=[{
                "id": "admin-777", "email": "admin@cocoscan.org", "role": "admin",
                "status": "Approved", "first_name": "System", "last_name": "Admin",
            }])
            return query

        self.supabase_users_patch = patch.object(
            main.supabase, "table", side_effect=table_with_approved_admin
        )
        self.supabase_users_patch.start()
        self.addCleanup(self.supabase_users_patch.stop)

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0 KB")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1024 * 50), "50.0 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5), "5.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 2), "2.00 GB")

    def test_backup_client_sends_secret_key_without_bearer_header(self):
        client = MagicMock()
        client.options.headers = {
            "apiKey": "sb_secret_test",
            "Authorization": "Bearer sb_secret_test",
        }
        with (
            patch.dict(os.environ, {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_BACKUP_SERVICE_ROLE_KEY": "sb_secret_test",
            }),
            patch("supabase.create_client", return_value=client),
        ):
            result = get_backup_storage_client()

        self.assertIs(result, client)
        self.assertNotIn("Authorization", client.options.headers)

    def test_backup_client_preserves_legacy_service_role_bearer_header(self):
        client = MagicMock()
        client.options.headers = {
            "apiKey": "legacy-jwt",
            "Authorization": "Bearer legacy-jwt",
        }
        with (
            patch.dict(os.environ, {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_BACKUP_SERVICE_ROLE_KEY": "legacy-jwt",
            }),
            patch("supabase.create_client", return_value=client),
        ):
            result = get_backup_storage_client()

        self.assertIs(result, client)
        self.assertEqual(client.options.headers["Authorization"], "Bearer legacy-jwt")

    def test_backup_generation_and_listing(self):
        backups_dir = get_backups_dir()
        self.assertTrue(backups_dir.exists())

        # Generate a manual backup
        backup_info = generate_database_backup(supabase_client=None, backup_type="Manual")
        self.assertIn("filename", backup_info)
        self.assertEqual(backup_info["type"], "Manual")
        self.assertTrue(backup_info["filename"].endswith(".json.gz.enc"))
        self.assertTrue(backup_info["encrypted"])

        # Verify file exists and is gzipped json
        file_path = get_backup_path(backup_info["filename"])
        self.assertIsNotNone(file_path)
        self.assertTrue(file_path.exists())
        self.assertNotEqual(file_path.read_bytes()[:2], b"\x1f\x8b")

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

    def test_recent_reports_use_shared_date_and_status_formatting(self):
        response = MagicMock(data=[{
            "id": 27,
            "pest_type": "Rhinoceros Beetle",
            "created_at": "2026-11-02T16:00:00+00:00",
            "status": "awaiting_confirmed_schedule",
        }])
        supabase_client = MagicMock()
        supabase_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = response

        reports = get_recent_reports_for_danger_zone(supabase_client)

        self.assertEqual(reports[0]["formatted_date"], "Nov 03, 2026")
        self.assertEqual(reports[0]["status"], "Waiting for Agriculturist Confirmation")
        self.assertIn("Nov 03, 2026 (Waiting for Agriculturist Confirmation)", reports[0]["display_label"])

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
        self.assertIn("session-timeout-overlay", content)
        self.assertIn("Stay signed in", content)
        self.assertIn("You’ll be signed out in", content)
        self.assertIn("/session/keep-alive", content)
        self.assertIn("Generate Backup Now", content)
        self.assertIn("Backup schedule", content)
        self.assertIn("Cloud backup storage unavailable", content)
        self.assertIn("Danger Zone", content)
        self.assertIn("By Specific Report", content)
        self.assertIn("By Date Range / Bulk", content)
        self.assertNotIn('id="target-report-id-input"', content)
        self.assertNotIn('id="btn-trigger-danger-action"', content)
        self.assertNotIn("Or enter ID...", content)
        self.assertIn("function openBulkPreconfirmation", content)
        self.assertIn("function openBulkDeleteConfirmation", content)
        self.assertIn("openBulkDeleteConfirmation(action)", content)
        self.assertIn("Bulk Delete by Date Range", content)
        self.assertIn("delete report PCA Admin", content)
        self.assertIn("reports-master-checkbox", content)
        self.assertIn("Select All", content)
        self.assertIn("danger-reports-table", content)
        self.assertIn("toggle-report-selection-mode", content)
        self.assertIn('class="selection-count"', content)
        self.assertIn("max-width: 300px;", content)
        self.assertIn("table-layout: auto;", content)
        self.assertNotIn('id="btn-clear-selection"', content)
        self.assertNotIn("fa-check-double", content)
        self.assertNotIn("<th style=\"width: 20%;\">Pest</th>", content)
        self.assertIn(".danger-reports-table .selection-column", content)
        self.assertIn("white-space: nowrap", content)
        self.assertIn("transform: none !important", content)
        self.assertIn("quick-action-column", content)
        self.assertIn("quick-action-cell", content)
        self.assertIn(".modal-danger-header .icon-circle i", content)
        self.assertIn("font-size: 1.1rem", content)
        self.assertNotIn("font-size: 1.35rem;\n        flex-shrink: 0;", content)
        self.assertIn("btn-row-actions-menu", content)
        self.assertIn("Preview", content)
        self.assertIn("Delete", content)
        self.assertIn("previewStoredReport", content)
        self.assertIn("status-assessment", content)
        self.assertIn("status-waiting", content)
        self.assertIn("background: #eff6ff", content)
        self.assertIn("padding: 4px 8px", content)
        self.assertIn("border-radius: 4px", content)

    def test_cloud_backup_listing_and_latest_run(self):
        filename = "cocoscan_db_weekly_20261115T160000Z.dump.age"
        storage = MagicMock()
        storage.list.side_effect = [
            [{
                "name": filename,
                "metadata": {"size": "4096"},
                "created_at": "2026-11-15T16:00:00+00:00",
            }],
            [{"name": "latest.json"}],
        ]
        storage.download.return_value = json.dumps({
            "status": "success",
            "finished_at": "2026-11-15T16:02:00+00:00",
        }).encode("utf-8")
        supabase_client = MagicMock()
        supabase_client.storage.from_.return_value = storage

        backups = list_cloud_backups(supabase_client)
        latest_run = get_latest_backup_run(supabase_client)

        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]["filename"], filename)
        self.assertEqual(backups[0]["type"], "Automated")
        self.assertEqual(backups[0]["size_bytes"], 4096)
        self.assertTrue(backups[0]["encrypted"])
        self.assertEqual(latest_run["status"], "success")
        storage.download.assert_called_once_with("runs/latest.json")

    def test_cloud_backup_download_and_delete_are_scoped(self):
        filename = "cocoscan_db_weekly_20261115T160000Z.dump.age"
        storage = MagicMock()
        storage.create_signed_url.return_value = {
            "signedURL": "https://cocoscan.supabase.co/storage/v1/object/sign/"
            "cocoscan-database-backups/weekly/" + filename + "?token=temporary",
        }
        storage.remove.return_value = [{"name": filename}]
        supabase_client = MagicMock()
        supabase_client.storage.from_.return_value = storage

        with patch.dict(os.environ, {"SUPABASE_URL": "https://cocoscan.supabase.co"}):
            signed_url = get_cloud_backup_download_url(supabase_client, filename)
        with patch("app.security_service.log_audit"):
            deleted = delete_cloud_backup(
                supabase_client,
                filename,
                admin_id="admin-123",
                admin_name="PCA Admin",
            )

        self.assertTrue(signed_url.startswith("https://cocoscan.supabase.co/"))
        self.assertTrue(deleted)
        storage.create_signed_url.assert_called_once_with(f"weekly/{filename}", 300)
        storage.remove.assert_called_once_with([f"weekly/{filename}"])

    def test_admin_cloud_backup_download_and_delete_routes(self):
        filename = "cocoscan_db_weekly_20261115T160000Z.dump.age"
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        with (
            patch("app.backup_service.get_backup_path", return_value=None),
            patch("app.backup_service.get_backup_storage_client", return_value=MagicMock()),
            patch(
                "app.backup_service.get_cloud_backup_download_url",
                return_value="https://cocoscan.supabase.co/private-backup",
            ),
        ):
            download = self.client.get(f"/admin/storage-backups/download/{filename}")
        self.assertEqual(download.status_code, 302)
        self.assertEqual(download.headers["Location"], "https://cocoscan.supabase.co/private-backup")

        with (
            patch("app.backup_service.get_backup_path", return_value=None),
            patch("app.backup_service.get_backup_storage_client", return_value=MagicMock()),
            patch("app.backup_service.delete_cloud_backup", return_value=True),
        ):
            deletion = self.client.post(
                f"/admin/storage-backups/delete/{filename}",
                data={"confirmation_phrase": "delete backup PCA Admin"},
                follow_redirects=True,
            )
        self.assertEqual(deletion.status_code, 200)
        self.assertIn("deleted successfully", deletion.get_data(as_text=True))

    def test_admin_storage_page_shows_automated_run_status(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        metrics = {
            "total_storage_formatted": "0 B",
            "percent_used": 0,
            "limit_formatted": "1 GB",
            "dataset_hub": {
                "size_formatted": "0 B",
                "total_samples": 0,
                "status": "Synced to Supabase Cloud",
                "categories": [],
            },
            "system_backups": {"size_formatted": "0 B", "count": 0},
        }
        with (
            patch("app.backup_service.get_backup_storage_client", return_value=MagicMock()),
            patch("app.backup_service.get_latest_backup_run", return_value={
                "status": "success",
                "finished_at": "2026-11-15T16:02:00+00:00",
                "archive_name": "cocoscan_db_weekly_20261115T160000Z.dump.age",
                "run_url": "https://github.com/example/cocoscan/actions/runs/12345",
            }),
            patch("app.backup_service.list_backups", return_value=[]),
            patch("app.backup_service.get_storage_metrics", return_value=metrics),
            patch("app.backup_service.get_recent_reports_for_danger_zone", return_value=[]),
        ):
            response = self.client.get("/admin/storage-backups")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Latest automated run: Success", html)
        self.assertIn("cocoscan_db_weekly_20261115T160000Z.dump.age", html)
        self.assertIn("View workflow run", html)

    def test_reports_list_selection_component_rendered_with_reports(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-123"
            sess["user_role"] = "admin"
            sess["user_name"] = "PCA Admin"

        mock_reports = [
            {
                "id": 21,
                "pest_type": "Brontispa",
                "formatted_date": "Oct 05, 2026",
                "status": "Under Review",
                "display_label": "Report #21 · Brontispa · Oct 05, 2026 (Under Review)",
            },
            {
                "id": 20,
                "pest_type": "Rhinoceros Beetle",
                "formatted_date": "Sep 22, 2026",
                "status": "Assessment Issued",
                "display_label": "Report #20 · Rhinoceros Beetle · Sep 22, 2026 (Assessment Issued)",
            },
        ]

        with patch("app.backup_service.get_recent_reports_for_danger_zone", return_value=mock_reports):
            res = self.client.get("/admin/storage-backups")
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("reports-master-checkbox", html)
            self.assertIn("Select All", html)
            self.assertIn('class="selection-column"', html)
            self.assertIn("btn-row-actions-menu", html)
            self.assertIn('data-user-role="admin"', html)
            self.assertIn('class="report-row-checkbox', html)
            self.assertIn('data-report-id="21"', html)
            self.assertIn('data-report-id="20"', html)
            self.assertIn("Brontispa", html)
            self.assertIn("Rhinoceros Beetle", html)

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
        self.assertEqual(dl_res.mimetype, "application/octet-stream")
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

    def test_admin_danger_delete_multiple_reports_route_security(self):
        admin_name = "PCA Admin"
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-777"
            sess["user_role"] = "admin"
            sess["user_name"] = admin_name
            sess["user_email"] = "admin@cocoscan.org"

        with patch("app.backup_service.delete_report_cascading") as mock_delete:
            mock_delete.return_value = {
                "success": True,
                "report_id": "101",
                "deleted_images_count": 2,
                "deleted_images": ["report_media/leaf1.jpg"],
            }

            res = self.client.post(
                "/admin/storage-backups/danger/delete-report",
                data={
                    "report_ids": "101, 102, 103",
                    "confirmation_phrase": f"delete report {admin_name}",
                },
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            self.assertIn("Successfully deleted 3 reports", res.get_data(as_text=True))
            self.assertEqual(mock_delete.call_count, 3)

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
