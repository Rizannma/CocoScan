import unittest

from app.dashboard_data import build_dashboard_chart_payload, normalize_pest_type


class DashboardDataTests(unittest.TestCase):
    def test_normalize_pest_type(self):
        self.assertEqual(normalize_pest_type("brontispa"), "Brontispa")
        self.assertEqual(normalize_pest_type("Coconut Leaf Beetle"), "Brontispa")
        self.assertEqual(normalize_pest_type("BRONTISPA"), "Brontispa")
        self.assertEqual(normalize_pest_type("rhinoceros beetle"), "Rhinoceros Beetle")
        self.assertEqual(normalize_pest_type("Oryctes Rhinoceros"), "Rhinoceros Beetle")
        self.assertEqual(normalize_pest_type("Healthy Coconut Leaf"), "Healthy Coconut Leaf")
        self.assertEqual(normalize_pest_type(""), "Unknown Pest")

    def test_build_dashboard_chart_payload_returns_empty_state_for_no_reports(self):
        payload = build_dashboard_chart_payload([])

        self.assertEqual(payload["trend_labels"], ["No data"])
        self.assertEqual(len(payload["trend_datasets"]), 2)
        self.assertEqual(payload["trend_datasets"][0]["label"], "Brontispa")
        self.assertEqual(payload["trend_datasets"][1]["label"], "Rhinoceros Beetle")
        self.assertEqual(payload["distribution_labels"], ["No reports yet"])
        self.assertEqual(payload["distribution_data"], [0])

    def test_build_dashboard_chart_payload_uses_real_report_data(self):
        reports = [
            {"created_at": "2026-01-01T10:00:00Z", "pest_type": "Rhinoceros Beetle"},
            {"created_at": "2026-02-01T10:00:00Z", "pest_type": "Rhinoceros Beetle"},
            {"created_at": "2026-02-15T10:00:00Z", "pest_type": "Brontispa"},
        ]

        payload = build_dashboard_chart_payload(reports)

        self.assertEqual(payload["trend_labels"], ["Jan", "Feb"])
        self.assertEqual(payload["distribution_labels"], ["Rhinoceros Beetle", "Brontispa"])
        self.assertEqual(payload["distribution_data"], [2, 1])

        trend_labels = [ds["label"] for ds in payload["trend_datasets"]]
        self.assertIn("Brontispa", trend_labels)
        self.assertIn("Rhinoceros Beetle", trend_labels)

        brontispa_trend = next(ds for ds in payload["trend_datasets"] if ds["label"] == "Brontispa")
        rhino_trend = next(ds for ds in payload["trend_datasets"] if ds["label"] == "Rhinoceros Beetle")
        self.assertEqual(brontispa_trend["data"], [0, 1])
        self.assertEqual(rhino_trend["data"], [1, 1])

        # Trend breakdown validation
        self.assertEqual(len(payload["trend_breakdown"]), 2)
        jan_row = payload["trend_breakdown"][0]
        self.assertEqual(jan_row["period"], "Jan")
        self.assertEqual(jan_row["counts"]["Rhinoceros Beetle"], 1)
        self.assertEqual(jan_row["counts"]["Brontispa"], 0)
        self.assertEqual(jan_row["total"], 1)

        feb_row = payload["trend_breakdown"][1]
        self.assertEqual(feb_row["period"], "Feb")
        self.assertEqual(feb_row["counts"]["Rhinoceros Beetle"], 1)
        self.assertEqual(feb_row["counts"]["Brontispa"], 1)
        self.assertEqual(feb_row["total"], 2)

        self.assertEqual(payload["trend_pest_totals"]["Rhinoceros Beetle"], 2)
        self.assertEqual(payload["trend_pest_totals"]["Brontispa"], 1)
        self.assertEqual(payload["trend_grand_total"], 3)

    def test_build_dashboard_chart_payload_excludes_healthy_coconut_leaf(self):
        reports = [
            {"created_at": "2026-03-01T10:00:00Z", "pest_type": "Rhinoceros Beetle"},
            {"created_at": "2026-03-05T10:00:00Z", "pest_type": "Healthy Coconut Leaf"},
            {"created_at": "2026-03-10T10:00:00Z", "pest_type": "Brontispa"},
            {"created_at": "2026-03-15T10:00:00Z", "pest_type": "Healthy Coconut Leaf"},
        ]

        payload = build_dashboard_chart_payload(reports)

        self.assertNotIn("Healthy Coconut Leaf", payload["distribution_labels"])
        self.assertEqual(payload["distribution_labels"], ["Rhinoceros Beetle", "Brontispa"])
        self.assertEqual(payload["distribution_data"], [1, 1])

        trend_labels = [ds["label"] for ds in payload["trend_datasets"]]
        self.assertNotIn("Healthy Coconut Leaf", trend_labels)
        self.assertIn("Brontispa", trend_labels)
        self.assertIn("Rhinoceros Beetle", trend_labels)

        for row in payload["trend_breakdown"]:
            self.assertNotIn("Healthy Coconut Leaf", row["counts"])
        self.assertEqual(payload["trend_grand_total"], 2)

    def test_build_dashboard_chart_payload_all_healthy_returns_empty_state(self):
        reports = [
            {"created_at": "2026-04-01T10:00:00Z", "pest_type": "Healthy Coconut Leaf"},
            {"created_at": "2026-04-02T10:00:00Z", "pest_type": "healthy"},
        ]

        payload = build_dashboard_chart_payload(reports)

        self.assertEqual(payload["trend_labels"], ["No data"])
        self.assertEqual(payload["distribution_labels"], ["No reports yet"])
        self.assertEqual(payload["distribution_data"], [0])
        self.assertEqual(payload["trend_breakdown"], [])
        self.assertEqual(payload["trend_grand_total"], 0)


if __name__ == "__main__":
    unittest.main()
