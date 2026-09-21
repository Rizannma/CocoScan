import os
import unittest

from app.map_utils import filter_map_reports, is_healthy_leaf, limit_recent_records


class MapUtilsTests(unittest.TestCase):
    def test_is_healthy_leaf(self):
        self.assertTrue(is_healthy_leaf("Healthy Coconut Leaf"))
        self.assertTrue(is_healthy_leaf("healthy"))
        self.assertTrue(is_healthy_leaf("Malusog na Dahon ng Niyog"))
        self.assertFalse(is_healthy_leaf("Rhinoceros Beetle"))
        self.assertFalse(is_healthy_leaf("Brontispa"))
        self.assertFalse(is_healthy_leaf("Unknown Pest"))

    def test_filter_map_reports_matches_location_and_pest(self):
        reports = [
            {"barangay": "San Rafael", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Rhinoceros Beetle"},
            {"barangay": "Bautista", "municipality": "Calauan", "province": "Laguna", "pest_type": "Brontispa"},
            {"barangay": "Lumbangan", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Unknown Pest"},
        ]

        filtered = filter_map_reports(reports, search_query="san pablo")

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["barangay"], "San Rafael")
        self.assertEqual(filtered[1]["barangay"], "Lumbangan")

    def test_filter_map_reports_matches_pest_filter(self):
        reports = [
            {"barangay": "San Rafael", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Rhinoceros Beetle"},
            {"barangay": "Bautista", "municipality": "Calauan", "province": "Laguna", "pest_type": "Brontispa"},
            {"barangay": "Lumbangan", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Brontispa"},
        ]

        filtered = filter_map_reports(reports, pest_filter="brontispa")
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["barangay"], "Bautista")
        self.assertEqual(filtered[1]["barangay"], "Lumbangan")

    def test_filter_map_reports_excludes_healthy_leaf(self):
        reports = [
            {"barangay": "San Rafael", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Rhinoceros Beetle"},
            {"barangay": "Bautista", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Healthy Coconut Leaf"},
            {"barangay": "Lumbangan", "municipality": "San Pablo", "province": "Laguna", "pest_type": "Brontispa"},
            {"barangay": "Del Remedio", "municipality": "San Pablo", "province": "Laguna", "pest_type": "healthy"},
        ]

        filtered = filter_map_reports(reports, search_query="san pablo")
        self.assertEqual(len(filtered), 2)
        pest_types = [r["pest_type"] for r in filtered]
        self.assertNotIn("Healthy Coconut Leaf", pest_types)
        self.assertNotIn("healthy", pest_types)
        self.assertIn("Rhinoceros Beetle", pest_types)
        self.assertIn("Brontispa", pest_types)

    def test_limit_recent_records_returns_only_five_entries(self):
        reports = [{"id": i} for i in range(1, 8)]

        limited = limit_recent_records(reports, 5)

        self.assertEqual(len(limited), 5)
        self.assertEqual([item["id"] for item in limited], [1, 2, 3, 4, 5])

    def test_map_view_template_excludes_healthy_leaf_from_legend(self):
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "map_view.html")
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("Healthy Leaf</span>", content)
        self.assertNotIn("Healthy Coconut Leaf", content)


if __name__ == "__main__":
    unittest.main()
