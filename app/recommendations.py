"""
Recommendation engine for pest management actions based on pest type, severity level, and risk assessment.
"""

from typing import Any, Dict, List, Optional, Union

RISK_FACTORS: Dict[str, List[str]] = {
    "Rhinoceros Beetle": [
        "Poor farm sanitation",
        "Decaying logs and organic debris",
        "Unmanaged breeding compost heaps",
        "Warm night temperatures",
        "Strong wind dispersal",
        "Previous farm infestation",
    ],
    "Brontispa": [
        "Nursery and young palm areas",
        "Dense canopy vegetation",
        "Humid, shaded microclimates",
        "Poor spear leaf aeration",
        "Previous farm infestation",
    ],
    "Healthy Coconut Leaf": []
}

RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "Rhinoceros Beetle": {
        "Mild": [
            "Improve farm sanitation and clear fallen coconut logs or rotting stumps",
            "Install perimeter pheromone traps (e.g., Oryctalure) to track beetle activity",
            "Inspect fronds weekly for early V-shaped cuts or boreholes in the crown",
            "Maintain clean palm crowns and eliminate nearby decaying organic matter",
        ],
        "Moderate": [
            "Deploy green Muscardine fungus (Metarhizium anisopliae) in breeding logs and compost heaps",
            "Increase pheromone trap density across affected palm blocks to trap adult beetles",
            "Apply biological or botanical deterrents (e.g., neem extract or naphthalene balls) in leaf axils",
            "Prune and safely destroy heavily bored fronds to prevent secondary crown rots",
            "Conduct bi-weekly surveillance across adjacent coconut stands",
        ],
        "Severe": [
            "Perform immediate targeted intervention and destroy all identified breeding sites",
            "Apply PCA-recommended protective crown treatments or biological controls directly to the canopy",
            "Set up intensive light traps combined with mass pheromone trapping across the farm",
            "Isolate severely damaged palms for intensive rehabilitation or controlled sanitation removal",
            "Consult a local PCA officer or agricultural technician for cluster-level pest emergency protocols",
        ],
    },
    "Brontispa": {
        "Mild": [
            "Prune and safely dispose of lightly infested or curling spear leaves",
            "Maintain good field sanitation and ensure proper spacing for sunlight penetration",
            "Conduct weekly inspections of young spear leaves for early feeding streaks",
            "Conserve native generalist predators such as earwigs in the field",
        ],
        "Moderate": [
            "Release biological control agents such as larval parasitoids (Tetrastichus brontispae) and predatory earwigs (Chelisoches morio)",
            "Spray entomopathogenic fungi (white Muscardine fungus / Beauveria bassiana) directly onto affected crowns",
            "Prune and safely dispose of heavily curled spear leaves to break the beetle life cycle",
            "Apply targeted organic botanical sprays (e.g., neem extract) during early morning hours",
            "Monitor pest population density and seedling health bi-weekly",
        ],
        "Severe": [
            "Apply PCA-approved insecticide sprays early in the morning before high sunlight",
            "Quarantine severely affected nursery blocks to prevent beetle migration to mature palms",
            "Carry out comprehensive crown cleaning and remove all dried or infested central fronds",
            "Mass-release parasitoid wasps (Tetrastichus brontispae) following chemical spray withdrawal",
            "Engage local agricultural extension workers for nursery rehabilitation and cluster containment",
        ],
    },
    "Healthy Coconut Leaf": {
        "Mild": [
            "Continue regular monthly monitoring and maintain good farm sanitation",
            "Ensure balanced soil nutrition and adequate irrigation for palm vigor",
        ],
        "Moderate": [
            "Continue routine surveillance and maintain clean palm bases",
            "Implement preventive cultural management practices",
        ],
        "Severe": [
            "Continue standard maintenance practices and routine monitoring",
            "Maintain optimal fertilization and sanitation protocols",
        ],
    },
}


def assess_risk(pest: str, severity: str = "Moderate", risk_score: Optional[int] = None) -> str:
    """Assess risk level based on pest type, severity, and optional risk score."""
    if risk_score is not None:
        if risk_score <= 30:
            return "Low"
        if risk_score <= 60:
            return "Medium"
        return "High"

    if pest == "Healthy Coconut Leaf":
        return "Low"

    normalized_severity = severity.strip().capitalize()
    if normalized_severity == "Severe":
        return "High"
    if normalized_severity == "Moderate":
        return "Medium"
    return "Low"


def urgency_from_risk(risk_level: str, severity: Optional[str] = None) -> str:
    """Determine urgency level from risk level and severity."""
    normalized_severity = severity.strip().capitalize() if severity else ""
    if risk_level == "High" or normalized_severity == "Severe":
        return "High"
    if risk_level == "Medium" or normalized_severity == "Moderate":
        return "Medium"
    return "Low"


def recommend_actions(
    pest: str,
    severity: Union[str, int] = "Moderate",
    risk_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate action recommendations dynamically tailored to pest type and severity level.

    Args:
        pest: Type of pest detected (e.g., 'Brontispa', 'Rhinoceros Beetle', 'Healthy Coconut Leaf')
        severity: Severity level ('Mild', 'Moderate', 'Severe') or integer risk score for backward compatibility
        risk_score: Optional explicit risk score (0-100)

    Returns:
        Dictionary with tailored recommendations, severity, risk level, urgency, and risk factors.
    """
    # Backward compatibility: if severity is passed as an int (legacy risk_score argument)
    if isinstance(severity, (int, float)):
        risk_score = severity
        normalized_severity = "Moderate"
    else:
        normalized_severity = severity.strip().capitalize()

    if normalized_severity not in ("Mild", "Moderate", "Severe"):
        normalized_severity = "Moderate"

    risk_level = assess_risk(pest, severity=normalized_severity, risk_score=risk_score)
    urgency = urgency_from_risk(risk_level, severity=normalized_severity)

    # Lookup dynamic recommendations tailored to pest and severity
    pest_recos = RECOMMENDATIONS.get(pest, {})
    if isinstance(pest_recos, dict):
        recommendations = pest_recos.get(normalized_severity, [])
        if not recommendations and pest_recos:
            recommendations = next(iter(pest_recos.values()), [])
    elif isinstance(pest_recos, list):
        recommendations = pest_recos
    else:
        recommendations = []

    risk_factors = RISK_FACTORS.get(pest, [])

    return {
        "pest": pest,
        "severity": normalized_severity,
        "risk": risk_level,
        "urgency": urgency,
        "recommendation": recommendations,
        "risk_factors": risk_factors,
    }
