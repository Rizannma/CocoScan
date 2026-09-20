import io
import json
import os
import sys
import unittest
import zipfile
from unittest.mock import MagicMock, patch
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from app.dataset_hub import (
    CATEGORIES,
    CATEGORY_SLUGS,
    SLUG_TO_LABEL,
    normalize_class_label,
    get_category_slug,
    save_verified_sample,
    get_dataset_summary,
    get_recent_dataset_samples,
    generate_dataset_zip,
)


def _create_test_image():
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :, 1] = 180  # Green
    return Image.fromarray(arr, "RGB")


class DatasetHubTests(unittest.TestCase):
    def setUp(self):
        main.app.config.update(TESTING=True)
        self.client = main.app.test_client()

    def test_normalize_class_label(self):
        self.assertEqual(normalize_class_label("Brontispa"), "Brontispa")
        self.assertEqual(normalize_class_label("Coconut Leaf Beetle"), "Brontispa")
        self.assertEqual(normalize_class_label("Rhinoceros Beetle"), "Rhinoceros Beetle")
        self.assertEqual(normalize_class_label("Healthy Coconut Leaf"), "Healthy Coconut Leaf")
        self.assertEqual(normalize_class_label("Unknown Pest"), "Not a Coconut Leaf Image")
        self.assertEqual(normalize_class_label("invalid_val"), "Not a Coconut Leaf Image")

    def test_get_category_slug(self):
        self.assertEqual(get_category_slug("Brontispa"), "brontispa")
        self.assertEqual(get_category_slug("Rhinoceros Beetle"), "rhinoceros_beetle")
        self.assertEqual(get_category_slug("Healthy Coconut Leaf"), "healthy")
        self.assertEqual(get_category_slug("Not a Coconut Leaf Image"), "not_coconut_leaf")

    def test_cloud_save_verified_sample(self):
        mock_storage = MagicMock()
        mock_client = MagicMock()
        mock_client.storage.from_.return_value = mock_storage

        img = _create_test_image()
        entry = save_verified_sample(
            report_id="test-rep-cloud-1",
            image_data=img,
            verified_label="Brontispa",
            original_prediction="Rhinoceros Beetle",
            agriculturist_id="agri_user_1",
            notes="Cloud verification test",
            supabase_client=mock_client,
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry["category_slug"], "brontispa")
        self.assertEqual(entry["verified_label"], "Brontispa")
        self.assertEqual(entry["original_prediction"], "Rhinoceros Beetle")
        self.assertTrue(entry["is_correction"])
        self.assertIn("dataset_retrain/brontispa/report_test-rep-cloud-1", entry["storage_path"])
        mock_storage.upload.assert_called_once()

    def test_get_dataset_summary_and_metrics(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [
            {
                "id": 1,
                "pest_type": "Brontispa",
                "image_url": "https://example.com/img1.jpg",
                "reviewer_notes": "Confirmed by PCA",
                "status": "resolved",
                "created_at": "2026-09-18T12:00:00Z",
                "reviewed_by_id": "agri-1",
            },
            {
                "id": 2,
                "pest_type": "Rhinoceros Beetle",
                "image_url": "https://example.com/img2.jpg",
                "reviewer_notes": "Corrected from healthy",
                "status": "resolved",
                "created_at": "2026-09-18T12:05:00Z",
                "reviewed_by_id": "agri-2",
            },
        ]
        mock_client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_resp

        summary = get_dataset_summary(mock_client)
        self.assertEqual(summary["total_samples"], 2)
        self.assertEqual(summary["counts"]["brontispa"], 1)
        self.assertEqual(summary["counts"]["rhinoceros_beetle"], 1)
        self.assertEqual(summary["validated_count"], 1)
        self.assertEqual(summary["corrected_count"], 1)
        self.assertEqual(len(summary["recent_samples"]), 2)

    def test_generate_dataset_zip(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [
            {
                "id": 10,
                "pest_type": "Brontispa",
                "image_url": "",
                "reviewer_notes": "Test item",
                "status": "resolved",
                "created_at": "2026-09-18T12:00:00Z",
                "reviewed_by_id": "agri-1",
            },
        ]
        mock_client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_resp

        zip_stream, filename = generate_dataset_zip(mock_client)
        self.assertTrue(filename.startswith("cocoscan_dataset_"))
        self.assertTrue(filename.endswith(".zip"))

        # Check zip archive content
        with zipfile.ZipFile(zip_stream, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("dataset_manifest.json", namelist)
            self.assertIn("dataset_metadata.csv", namelist)
            self.assertIn("README.txt", namelist)
            self.assertIn("brontispa/.gitkeep", namelist)
            self.assertIn("rhinoceros_beetle/.gitkeep", namelist)

            manifest_bytes = zf.read("dataset_manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            self.assertEqual(manifest["total_samples"], 1)
            self.assertEqual(manifest["samples"][0]["report_id"], "10")

    def test_admin_dataset_hub_access_control(self):
        # Anonymous -> redirect to login
        resp = self.client.get("/admin/dataset-hub")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

        # Farmer -> redirect to farmer dashboard
        with self.client.session_transaction() as session:
            session["user_id"] = "farmer-1"
            session["user_role"] = "farmer"

        resp = self.client.get("/admin/dataset-hub")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/farmer/dashboard", resp.headers.get("Location", ""))

        # Admin -> 200 OK
        with self.client.session_transaction() as session:
            session["user_id"] = "admin-1"
            session["user_role"] = "admin"
            session["user_name"] = "Admin User"

        resp = self.client.get("/admin/dataset-hub")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Dataset Hub", html)
        self.assertIn("Export as ZIP", html)
        self.assertNotIn("Retrain Model", html)

    def test_admin_export_zip_route(self):
        # Admin export ZIP route test
        with self.client.session_transaction() as session:
            session["user_id"] = "admin-1"
            session["user_role"] = "admin"

        resp = self.client.get("/admin/dataset-hub/export-zip")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/zip")
        self.assertIn("attachment", resp.headers.get("Content-Disposition", ""))
        self.assertIn("cocoscan_dataset_", resp.headers.get("Content-Disposition", ""))

        # Verify stream is valid zip
        zip_bytes = io.BytesIO(resp.data)
        with zipfile.ZipFile(zip_bytes, "r") as zf:
            self.assertIn("dataset_manifest.json", zf.namelist())
            self.assertIn("dataset_metadata.csv", zf.namelist())

    def test_api_admin_dataset_hub_stats(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "admin-1"
            session["user_role"] = "admin"

        resp = self.client.get("/api/admin/dataset-hub/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)
        self.assertIn("samples", data)

    def test_agriculturist_verify_classification_endpoint(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "agri-1"
            session["user_role"] = "agri_expert"
            session["user_name"] = "Agri Expert"

        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.error = None

        class FakeQuery:
            def __init__(self, rows):
                self.rows = rows

            def select(self, *args, **kwargs):
                return self

            def update(self, *args, **kwargs):
                return self

            def eq(self, *args, **kwargs):
                return self

            def execute(self):
                return FakeResponse(self.rows)

        class FakeSupabaseClient:
            def table(self, _table_name):
                return FakeQuery([{"id": "rep-99", "pest_type": "Rhinoceros Beetle", "image_url": None}])

            @property
            def storage(self):
                mock_s = MagicMock()
                mock_from = MagicMock()
                mock_s.from_.return_value = mock_from
                return mock_s

        original_supabase = main.supabase
        main.supabase = FakeSupabaseClient()
        self.addCleanup(setattr, main, "supabase", original_supabase)

        # Post verification
        resp = self.client.post(
            "/agriculturist/verify-classification",
            data={
                "report_id": "rep-99",
                "verified_pest": "Brontispa",
                "original_prediction": "Rhinoceros Beetle",
                "is_correction": "true",
            }
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["verified_pest"], "Brontispa")


if __name__ == "__main__":
    unittest.main()
