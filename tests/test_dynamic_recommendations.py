import unittest

from app.recommendations import (
    RECOMMENDATIONS,
    RISK_FACTORS,
    assess_risk,
    recommend_actions,
    urgency_from_risk,
)


class TestDynamicRecommendations(unittest.TestCase):
    def test_rhinoceros_beetle_recommendations_by_severity(self):
        # Mild
        mild_result = recommend_actions("Rhinoceros Beetle", severity="Mild")
        self.assertEqual(mild_result["pest"], "Rhinoceros Beetle")
        self.assertEqual(mild_result["severity"], "Mild")
        self.assertEqual(mild_result["risk"], "Low")
        self.assertEqual(mild_result["urgency"], "Low")
        self.assertTrue(len(mild_result["recommendation"]) > 0)
        self.assertTrue(any("sanitation" in r.lower() or "pheromone" in r.lower() for r in mild_result["recommendation"]))

        # Moderate
        mod_result = recommend_actions("Rhinoceros Beetle", severity="Moderate")
        self.assertEqual(mod_result["severity"], "Moderate")
        self.assertEqual(mod_result["risk"], "Medium")
        self.assertEqual(mod_result["urgency"], "Medium")
        self.assertTrue(any("muscardine" in r.lower() or "density" in r.lower() for r in mod_result["recommendation"]))

        # Severe
        sev_result = recommend_actions("Rhinoceros Beetle", severity="Severe")
        self.assertEqual(sev_result["severity"], "Severe")
        self.assertEqual(sev_result["risk"], "High")
        self.assertEqual(sev_result["urgency"], "High")
        self.assertTrue(any("immediate" in r.lower() or "technician" in r.lower() or "protective" in r.lower() for r in sev_result["recommendation"]))

    def test_brontispa_recommendations_by_severity(self):
        # Mild
        mild_result = recommend_actions("Brontispa", severity="Mild")
        self.assertEqual(mild_result["pest"], "Brontispa")
        self.assertEqual(mild_result["severity"], "Mild")
        self.assertEqual(mild_result["risk"], "Low")
        self.assertEqual(mild_result["urgency"], "Low")
        self.assertTrue(any("prune" in r.lower() or "spear" in r.lower() for r in mild_result["recommendation"]))

        # Moderate
        mod_result = recommend_actions("Brontispa", severity="Moderate")
        self.assertEqual(mod_result["severity"], "Moderate")
        self.assertEqual(mod_result["risk"], "Medium")
        self.assertEqual(mod_result["urgency"], "Medium")
        self.assertTrue(any("tetrastichus" in r.lower() or "parasitoid" in r.lower() or "earwig" in r.lower() for r in mod_result["recommendation"]))

        # Severe
        sev_result = recommend_actions("Brontispa", severity="Severe")
        self.assertEqual(sev_result["severity"], "Severe")
        self.assertEqual(sev_result["risk"], "High")
        self.assertEqual(sev_result["urgency"], "High")
        self.assertTrue(any("insecticide" in r.lower() or "quarantine" in r.lower() or "pca-approved" in r.lower() for r in sev_result["recommendation"]))

    def test_healthy_leaf_recommendations(self):
        healthy_result = recommend_actions("Healthy Coconut Leaf", severity="Mild")
        self.assertEqual(healthy_result["pest"], "Healthy Coconut Leaf")
        self.assertEqual(healthy_result["risk"], "Low")
        self.assertEqual(healthy_result["urgency"], "Low")
        self.assertTrue(len(healthy_result["recommendation"]) > 0)
        self.assertEqual(healthy_result["risk_factors"], [])

    def test_backward_compatibility_with_numeric_risk_score(self):
        # Passing an int as second parameter (legacy risk_score)
        result = recommend_actions("Rhinoceros Beetle", 85)
        self.assertEqual(result["pest"], "Rhinoceros Beetle")
        self.assertEqual(result["risk"], "High")
        self.assertTrue(len(result["recommendation"]) > 0)

    def test_assess_risk_and_urgency_helpers(self):
        self.assertEqual(assess_risk("Rhinoceros Beetle", severity="Severe"), "High")
        self.assertEqual(assess_risk("Rhinoceros Beetle", severity="Moderate"), "Medium")
        self.assertEqual(assess_risk("Rhinoceros Beetle", severity="Mild"), "Low")
        self.assertEqual(assess_risk("Healthy Coconut Leaf", severity="Severe"), "Low")
        self.assertEqual(assess_risk("Rhinoceros Beetle", risk_score=20), "Low")
        self.assertEqual(assess_risk("Rhinoceros Beetle", risk_score=50), "Medium")
        self.assertEqual(assess_risk("Rhinoceros Beetle", risk_score=80), "High")

        self.assertEqual(urgency_from_risk("High", severity="Severe"), "High")
        self.assertEqual(urgency_from_risk("Medium", severity="Moderate"), "Medium")
        self.assertEqual(urgency_from_risk("Low", severity="Mild"), "Low")


if __name__ == "__main__":
    unittest.main()
