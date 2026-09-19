import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from app.recommendations import recommend_actions, SAFE_INITIAL_RECOMMENDATIONS, PRECAUTIONARY_DISCLAIMER


class AgriReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        main.app.config.update(TESTING=True)
        self.client = main.app.test_client()

    def test_precautionary_recommendations_safe_actions(self):
        # Verify initial recommendations for Rhinoceros Beetle
        reco_rhino = recommend_actions("Rhinoceros Beetle")
        self.assertIn("recommendations", reco_rhino)
        self.assertGreaterEqual(len(reco_rhino["recommendations"]), 3)
        self.assertIn("sanitation", reco_rhino["recommendations"][0].lower())
        self.assertIn("precautionary_note", reco_rhino)
        self.assertIn("safe, non-invasive", reco_rhino["precautionary_note"].lower())

        # Verify initial recommendations for Brontispa
        reco_brontispa = recommend_actions("Brontispa")
        self.assertIn("recommendations", reco_brontispa)
        self.assertGreaterEqual(len(reco_brontispa["recommendations"]), 3)
        self.assertIn("spear leaves", reco_brontispa["recommendations"][0].lower())

    def test_agriculturist_submit_assessment_and_verification_validate(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "agri-expert-101"
            session["user_role"] = "agri_expert"
            session["user_name"] = "Maria Clara"

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
            def table(self, table_name):
                if table_name == "reports":
                    return FakeQuery([{"id": 42, "pest_type": "Brontispa", "image_url": "https://example.com/leaf.jpg", "farmer_notes": "Spear leaves damaged."}])
                if table_name == "users":
                    return FakeQuery([{"first_name": "Maria", "last_name": "Clara"}])
                if table_name == "profiles":
                    return FakeQuery([{"position_title": "Senior PCA Officer", "agency_office": "PCA Region IV-A"}])
                return FakeQuery([])

            @property
            def storage(self):
                mock_s = MagicMock()
                mock_from = MagicMock()
                mock_s.from_.return_value = mock_from
                return mock_s

        original_supabase = main.supabase
        main.supabase = FakeSupabaseClient()
        self.addCleanup(setattr, main, "supabase", original_supabase)

        # Submit assessment confirming AI prediction as correct
        resp = self.client.post(
            "/agriculturist/submit-assessment",
            json={
                "report_id": 42,
                "assessment_notes": "Confirmed Brontispa infestation. Clean spear fronds and apply pheromone traps.",
                "verified_pest": "Brontispa",
                "is_correction": False,
            }
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["reviewer_name"], "Maria Clara")
        self.assertEqual(data["reviewer_position"], "Senior PCA Officer")
        self.assertEqual(data["reviewer_office"], "PCA Region IV-A")
        self.assertEqual(data["verified_pest"], "Brontispa")

    def test_agriculturist_submit_assessment_with_correction(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "agri-expert-102"
            session["user_role"] = "agri_expert"
            session["user_name"] = "Juan Dela Cruz"

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
            def table(self, table_name):
                if table_name == "reports":
                    return FakeQuery([{"id": 88, "pest_type": "Healthy Coconut Leaf", "image_url": "https://example.com/rhino.jpg"}])
                if table_name == "users":
                    return FakeQuery([{"first_name": "Juan", "last_name": "Dela Cruz"}])
                if table_name == "profiles":
                    return FakeQuery([{"position_title": "Agriculturist II", "agency_office": "PCA San Pablo City"}])
                return FakeQuery([])

            @property
            def storage(self):
                mock_s = MagicMock()
                mock_from = MagicMock()
                mock_s.from_.return_value = mock_from
                return mock_s

        original_supabase = main.supabase
        main.supabase = FakeSupabaseClient()
        self.addCleanup(setattr, main, "supabase", original_supabase)

        # Submit assessment correcting AI prediction to Rhinoceros Beetle
        resp = self.client.post(
            "/agriculturist/submit-assessment",
            json={
                "report_id": 88,
                "assessment_notes": "Corrected: Evidence of boreholes indicates Rhinoceros Beetle, not healthy.",
                "verified_pest": "Rhinoceros Beetle",
                "is_correction": True,
            }
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["reviewer_name"], "Juan Dela Cruz")
        self.assertEqual(data["verified_pest"], "Rhinoceros Beetle")
        self.assertIn("official_recommendations", data)
        self.assertGreater(len(data["official_recommendations"]), 0)

    def test_report_modal_template_contains_verification_and_notice_elements(self):
        # Verify that report_modal.html contains the necessary element IDs and classes
        with open("templates/components/report_modal.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Pending vs Verified result indicators
        self.assertIn('id="report-pest-eyebrow"', html)
        self.assertIn('id="pest-eyebrow-pending"', html)
        self.assertIn('id="pest-eyebrow-verified"', html)
        self.assertIn('id="report-pending-validation-notice"', html)
        self.assertIn('id="report-verifier-name"', html)

        # Safe Precautionary Actions notice
        self.assertIn('safe-actions-notice-banner', html)
        self.assertIn('id="report-safe-actions-notice"', html)

        # Expert Assessment & Verification controls
        self.assertIn('id="btn-tab-validate-correct"', html)
        self.assertIn('id="btn-tab-correct-result"', html)
        self.assertIn('Mark as Verified', html)
        self.assertIn('Re-verify Result', html)
        self.assertIn('id="agri-verified-pest-select"', html)
        self.assertIn('id="agri-correction-select-wrap" style="display:none;', html)

    def test_cloud_dataset_routing_during_assessment(self):
        from app.dataset_hub import save_verified_sample

        mock_storage = MagicMock()
        mock_client = MagicMock()
        mock_client.storage.from_.return_value = mock_storage

        # Create dummy in-memory image
        img = Image.new("RGB", (100, 100), color=(0, 128, 0))
        entry = save_verified_sample(
            report_id=999,
            image_data=img,
            verified_label="Brontispa",
            original_prediction="Healthy Coconut Leaf",
            agriculturist_id="agri-1",
            notes="Verified as Brontispa",
            supabase_client=mock_client,
        )

        self.assertIsNotNone(entry)
        self.assertTrue(entry["storage_path"].startswith("dataset_retrain/brontispa/"))
        self.assertTrue(entry["is_correction"])
        mock_storage.upload.assert_called_once()


if __name__ == "__main__":
    unittest.main()
