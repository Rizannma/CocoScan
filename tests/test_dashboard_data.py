import unittest

from app.dashboard_data import build_dashboard_chart_payload, normalize_pest_type, normalize_severity


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
        self.assertIn("severity_breakdown", payload)
        self.assertEqual(payload["severity_breakdown"]["categories"], ["Mild", "Moderate", "Severe"])
        self.assertEqual(len(payload["severity_breakdown"]["datasets"]), 2)
        self.assertEqual(payload["severity_breakdown"]["brontispa"]["total"], 0)
        self.assertEqual(payload["severity_breakdown"]["rhinoceros_beetle"]["total"], 0)

    def test_build_dashboard_chart_payload_uses_real_report_data(self):
        reports = [
            {"created_at": "2026-01-01T10:00:00Z", "pest_type": "Rhinoceros Beetle", "severity": "Mild"},
            {"created_at": "2026-02-01T10:00:00Z", "pest_type": "Rhinoceros Beetle", "severity": "Severe"},
            {"created_at": "2026-02-15T10:00:00Z", "pest_type": "Brontispa", "severity": "Moderate"},
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

        # Test severity breakdown
        self.assertEqual(payload["severity_breakdown"]["categories"], ["Mild", "Moderate", "Severe"])
        self.assertEqual(len(payload["severity_breakdown"]["datasets"]), 2)

        rhino_sev = payload["severity_breakdown"]["rhinoceros_beetle"]
        self.assertEqual(rhino_sev["Mild"], 1)
        self.assertEqual(rhino_sev["Moderate"], 0)
        self.assertEqual(rhino_sev["Severe"], 1)
        self.assertEqual(rhino_sev["total"], 2)

        brontispa_sev = payload["severity_breakdown"]["brontispa"]
        self.assertEqual(brontispa_sev["Mild"], 0)
        self.assertEqual(brontispa_sev["Moderate"], 1)
        self.assertEqual(brontispa_sev["Severe"], 0)
        self.assertEqual(brontispa_sev["total"], 1)

