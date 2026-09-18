import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.recommendations import (
    SAFE_INITIAL_RECOMMENDATIONS,
    RISK_FACTORS,
    assess_risk,
    recommend_actions,
    get_safe_recommendations,
    urgency_from_risk,
)


class TestDynamicRecommendations(unittest.TestCase):
    def test_rhinoceros_beetle_safe_recommendations(self):
        result = recommend_actions("Rhinoceros Beetle")
        self.assertEqual(result["pest"], "Rhinoceros Beetle")
        self.assertEqual(result["risk"], "Medium")
        self.assertEqual(result["urgency"], "Medium")
        self.assertTrue(len(result["recommendation"]) > 0)
        self.assertTrue(any("sanitation" in r.lower() or "monitor" in r.lower() for r in result["recommendation"]))

    def test_brontispa_safe_recommendations(self):
        result = recommend_actions("Brontispa")
        self.assertEqual(result["pest"], "Brontispa")
        self.assertEqual(result["risk"], "Medium")
        self.assertEqual(result["urgency"], "Medium")
        self.assertTrue(len(result["recommendation"]) > 0)
        self.assertTrue(any("spear" in r.lower() or "fronds" in r.lower() or "predator" in r.lower() for r in result["recommendation"]))

    def test_healthy_leaf_recommendations(self):
        healthy_result = recommend_actions("Healthy Coconut Leaf")
        self.assertEqual(healthy_result["pest"], "Healthy Coconut Leaf")
        self.assertEqual(healthy_result["risk"], "Low")
        self.assertEqual(healthy_result["urgency"], "Low")
        self.assertTrue(len(healthy_result["recommendation"]) > 0)

    def test_get_safe_recommendations(self):
        recos = get_safe_recommendations("Brontispa")
        self.assertIsInstance(recos, list)
        self.assertGreater(len(recos), 0)

    def test_assess_risk_and_urgency_helpers(self):
        self.assertEqual(assess_risk("Rhinoceros Beetle"), "Medium")
        self.assertEqual(assess_risk("Brontispa"), "Medium")
        self.assertEqual(assess_risk("Healthy Coconut Leaf"), "Low")
        self.assertEqual(assess_risk("Unknown"), "Low")

        self.assertEqual(urgency_from_risk("High"), "High")
        self.assertEqual(urgency_from_risk("Medium"), "Medium")
        self.assertEqual(urgency_from_risk("Low"), "Low")

    def test_get_official_recommendations(self):
        from app.recommendations import get_official_recommendations, OFFICIAL_RECOMMENDATIONS

        rhino_recs = get_official_recommendations("Rhinoceros Beetle")
        self.assertIsInstance(rhino_recs, list)
        self.assertEqual(len(rhino_recs), 4)
        self.assertTrue(any("pheromone" in r.lower() for r in rhino_recs))

        brontispa_recs = get_official_recommendations("Brontispa")
        self.assertIsInstance(brontispa_recs, list)
        self.assertEqual(len(brontispa_recs), 5)
        self.assertTrue(any("prune" in r.lower() for r in brontispa_recs))

        healthy_recs = get_official_recommendations("Healthy Coconut Leaf")
        self.assertIsInstance(healthy_recs, list)
        self.assertEqual(len(healthy_recs), 2)


if __name__ == "__main__":
    unittest.main()
