"""
Safe Initial Recommendation Engine for CocoScan.
Provides low-risk, non-invasive farm maintenance, sanitation, and monitoring actions
tailored to the preliminary pest classification result while awaiting agriculturist verification.
"""

from typing import Any, Dict, List, Optional, Union

PRECAUTIONARY_DISCLAIMER = (
    "Note: AI scan results are preliminary. Please focus on safe, non-invasive sanitation "
    "and monitoring actions while awaiting confirmation and expert guidance from your local agriculturist."
)

RISK_FACTORS: Dict[str, List[str]] = {
    "Rhinoceros Beetle": [
        "Decaying coconut logs, rotting stumps, or dead standing palms",
        "Unmanaged farm manure or breeding compost heaps",
        "Overgrown vegetation restricting crown visibility",
        "Previous rhinoceros beetle occurrence in adjacent palm stands",
    ],
    "Brontispa": [
        "Unopened, curled spear leaves with restricted aeration",
        "High shade or dense canopy microclimates in nursery/young palm areas",
        "Dry seasonal weather favoring rapid beetle reproduction",
        "Presence of unmanaged infested fronds harboring larvae",
    ],
    "Healthy Coconut Leaf": [
        "Routine seasonal pest emergence in surrounding barangays",
        "Soil nutrient depletion or prolonged moisture stress",
    ],
    "Not a Coconut Leaf Image": [
        "Low lighting, motion blur, or excessive distance from target leaf",
    ],
}

SAFE_INITIAL_RECOMMENDATIONS: Dict[str, List[str]] = {
    "Rhinoceros Beetle": [
        "Improve general farm sanitation by clearing fallen decaying coconut logs, rotting wood, and compost heaps.",
        "Inspect palm crowns and spear leaves regularly for characteristic V-shaped cuts or entry boreholes.",
        "Install non-chemical perimeter light traps or organic pheromone monitoring traps to observe beetle activity.",
        "Avoid applying unverified chemical insecticides; await formal recommendations from your agricultural officer.",
    ],
    "Brontispa": [
        "Inspect central spear leaves and unopened fronds weekly for early feeding streaks or browning edges.",
        "Maintain clean weed management and ensure adequate sunlight penetration and aeration around younger palms.",
        "Carefully collect and safely compost or dispose of fallen, dried, or curled fronds to disrupt shelter sites.",
        "Preserve native beneficial predator populations (such as earwigs); avoid broad-spectrum chemical sprays.",
    ],
    "Healthy Coconut Leaf": [
        "Maintain regular monthly orchard inspections to monitor tree crown vigor and spot any early pest arrivals.",
        "Ensure balanced soil fertilization and organic mulching to maintain natural tree resistance.",
        "Keep palm bases clear of dense weeds and decaying organic litter.",
        "Record routine tree observation dates in your farm notebook or digital log.",
    ],
    "Not a Coconut Leaf Image": [
        "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.",
        "Hold the device steady and re-scan from approximately 1 to 2 feet away.",
        "Avoid scanning non-plant objects, background scenery, or extremely blurry images.",
    ],
}

# Backward compatibility alias
RECOMMENDATIONS = SAFE_INITIAL_RECOMMENDATIONS

OFFICIAL_RECOMMENDATIONS: Dict[str, List[str]] = {
    "Rhinoceros Beetle": [
        "Improve farm sanitation and remove breeding sites",
        "Install pheromone traps and green Muscardine fungus log traps",
        "Apply biological treatment or use light traps at night",
        "Monitor weekly and consult an agricultural technician for severe cases",
    ],
    "Brontispa": [
        "Prune and safely dispose of infested leaves",
        "Maintain field sanitation and monitor infestation levels",
        "Release earwigs and Tetrastichus parasitoids for natural control",
        "Spray white Muscardine fungus",
        "Use approved pesticide early morning for severe infestations",
    ],
    "Healthy Coconut Leaf": [
        "Continue regular monitoring",
        "Maintain current sanitation practices",
    ],
    "Not a Coconut Leaf Image": [
        "Ensure the camera is focused directly on a coconut leaf, frond, or crown section under daylight.",
        "Hold the device steady and re-scan from approximately 1 to 2 feet away.",
    ],
}


def get_safe_recommendations(pest: str) -> List[str]:
    """Return safe initial recommendations for a given pest."""
    return SAFE_INITIAL_RECOMMENDATIONS.get(
        pest,
        SAFE_INITIAL_RECOMMENDATIONS.get("Healthy Coconut Leaf", [])
    )


def get_official_recommendations(pest: str) -> List[str]:
    """Return official, complete recommendations tailored to a verified pest diagnosis."""
    if not pest:
        return OFFICIAL_RECOMMENDATIONS["Healthy Coconut Leaf"]
    
    cleaned = str(pest).strip().lower()
    if "brontispa" in cleaned or "leaf beetle" in cleaned:
        return OFFICIAL_RECOMMENDATIONS["Brontispa"]
    if "rhino" in cleaned or "beetle" in cleaned or "oryctes" in cleaned:
        return OFFICIAL_RECOMMENDATIONS["Rhinoceros Beetle"]
    if "healthy" in cleaned or "malusog" in cleaned:
        return OFFICIAL_RECOMMENDATIONS["Healthy Coconut Leaf"]
    if "not" in cleaned or "hindi" in cleaned or "invalid" in cleaned or "unknown" in cleaned:
        return OFFICIAL_RECOMMENDATIONS["Not a Coconut Leaf Image"]

    return OFFICIAL_RECOMMENDATIONS.get(
        pest,
        OFFICIAL_RECOMMENDATIONS.get("Healthy Coconut Leaf", [])
    )


def assess_risk(pest: str, *args, **kwargs) -> str:
    """Assess risk level based on pest type."""
    if pest == "Healthy Coconut Leaf":
        return "Low"
    if pest in ("Rhinoceros Beetle", "Brontispa"):
        return "Medium"
    return "Low"


def urgency_from_risk(risk_level: str, *args, **kwargs) -> str:
    """Determine urgency level for initial farmer action."""
    if risk_level == "High":
        return "High"
    if risk_level == "Medium":
        return "Medium"
    return "Low"


def recommend_actions(
    pest: str,
    severity: Optional[Union[str, int]] = None,
    risk_score: Optional[int] = None,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Generate safe, non-invasive initial action recommendations based on detected pest.

    Args:
        pest: Type of pest detected ('Brontispa', 'Rhinoceros Beetle', 'Healthy Coconut Leaf', etc.)
        severity: Legacy parameter retained for backward compatibility (ignored)
        risk_score: Optional risk score integer

    Returns:
        Dictionary with safe initial recommendations, precautionary framing, and risk level.
    """
    risk_level = assess_risk(pest)
    urgency = urgency_from_risk(risk_level)

    recommendations = SAFE_INITIAL_RECOMMENDATIONS.get(
        pest,
        SAFE_INITIAL_RECOMMENDATIONS.get("Healthy Coconut Leaf", [])
    )
    risk_factors = RISK_FACTORS.get(pest, [])

    return {
        "pest": pest,
        "risk": risk_level,
        "urgency": urgency,
        "recommendation": recommendations,
        "recommendations": recommendations,
        "precautionary_note": PRECAUTIONARY_DISCLAIMER,
        "risk_factors": risk_factors,
    }

