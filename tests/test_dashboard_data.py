import unittest

from app.dashboard_data import build_dashboard_chart_payload


class DashboardDataTests(unittest.TestCase):
    def test_build_dashboard_chart_payload_returns_empty_state_for_no_reports(self):
        payload = build_dashboard_chart_payload([])

        self.assertEqual(payload["trend_labels"], ["No data"])
        self.assertEqual(payload["distribution_labels"], ["No reports yet"])
        self.assertEqual(payload["distribution_data"], [0])
        self.assertIn("severity_breakdown", payload)
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
        self.assertEqual(payload["trend_datasets"][0]["data"], [1, 1])

        # Test severity breakdown
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
