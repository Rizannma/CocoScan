import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main


class ReportDetailsApiTests(unittest.TestCase):
    def setUp(self):
        main.app.config.update(TESTING=True)
        self.client = main.app.test_client()

    def test_get_report_details_requires_auth(self):
        response = self.client.get('/api/reports/14')
        # Expect redirect or 401/403 when not logged in
        self.assertIn(response.status_code, [302, 401, 403])

    def test_get_report_details_success(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "test-agri-user"
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

            def eq(self, *args, **kwargs):
                return self

            def execute(self):
                return FakeResponse(self.rows)

        fake_report = {
            "id": 14,
            "farmer_name": "Stella Ann Mariz Montesines",
            "pest_type": "Healthy Coconut Leaf",
            "confidence": 74.4,
            "image_url": "report_media/primary_14.jpeg",
            "farmer_notes": "All looks good",
            "status": "Under Review",
            "created_at": "2026-09-18T15:41:23.408611+00:00",
            "initial_recommendations": '["Continue routine surveillance"]',
            "barangay": "Pag-asa",
            "municipality": "Liliw",
            "province": "Laguna",
            "user_id": "user-123",
            "reviewed_by_id": None,
            "expert_recommendations": None,
        }

        with patch.object(main.supabase, "table", side_effect=lambda tbl: FakeQuery([fake_report]) if tbl == "reports" else FakeQuery([])):
            response = self.client.get('/api/reports/14')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data.get("success"))
            report = data.get("report")
            self.assertEqual(report.get("id"), 14)
            self.assertEqual(report.get("farmer"), "Stella Ann Mariz Montesines")
            self.assertEqual(report.get("pest"), "Healthy Coconut Leaf")
            self.assertEqual(report.get("confidence"), "74%")
            self.assertEqual(report.get("location_text"), "Pag-asa, Liliw, Laguna")
            self.assertEqual(report.get("status"), "Under Review")

    def test_get_report_details_not_found(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "test-farmer"
            session["user_role"] = "farmer"

        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.error = None

        class FakeQuery:
            def select(self, *args, **kwargs):
                return self

            def eq(self, *args, **kwargs):
                return self

            def execute(self):
                return FakeResponse([])

        with patch.object(main.supabase, "table", return_value=FakeQuery()):
            response = self.client.get('/api/reports/99999')
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertFalse(data.get("success"))

    def test_get_report_details_with_visit_summary_and_images(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "test-agri-user"
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

            def eq(self, *args, **kwargs):
                return self

            def in_(self, *args, **kwargs):
                return self

            def order(self, *args, **kwargs):
                return self

            def execute(self):
                return FakeResponse(self.rows)

        fake_report = {
            "id": 9,
            "farmer_name": "Farmer John",
            "pest_type": "Brontispa",
            "confidence": 88.0,
            "image_url": "report_media/primary_9.jpeg",
            "farmer_notes": "Leaf browning observed",
            "status": "Resolved",
            "created_at": "2026-09-18T10:00:00.000000+00:00",
            "updated_at": "2026-09-20T14:30:00.000000+00:00",
            "visit_summary": "On-site assessment conducted. Recommended organic spray.",
            "visit_completed_at": "2026-09-20T14:30:00.000000+00:00",
            "barangay": "San Miguel",
            "municipality": "San Pablo City",
            "province": "Laguna",
            "user_id": "user-456",
            "reviewed_by_id": None,
            "expert_recommendations": '["Apply bio-control agents"]',
        }
        fake_visit_images = [
            {"report_id": 9, "image_url": "https://example.com/visit1.jpg"},
            {"report_id": 9, "image_url": "https://example.com/visit2.jpg"},
        ]

        def fake_table(tbl):
            if tbl == "reports":
                return FakeQuery([fake_report])
            elif tbl == "visit_images":
                return FakeQuery(fake_visit_images)
            return FakeQuery([])

        with patch.object(main.supabase, "table", side_effect=fake_table):
            response = self.client.get('/api/reports/9')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data.get("success"))
            report = data.get("report")
            self.assertEqual(report.get("id"), 9)
            self.assertEqual(report.get("visit_summary"), "On-site assessment conducted. Recommended organic spray.")
            self.assertEqual(report.get("visit_images"), ["https://example.com/visit1.jpg", "https://example.com/visit2.jpg"])
            self.assertEqual(report.get("status"), "Resolved")
