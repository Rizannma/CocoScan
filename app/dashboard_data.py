from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Mapping


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value

    value_str = str(value).strip()
    if not value_str:
        return None

    try:
        return datetime.fromisoformat(value_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_pest_type(pest_raw: Any) -> str:
    """Normalize pest string to canonical name ('Brontispa', 'Rhinoceros Beetle', 'Healthy Coconut Leaf', etc.)."""
    s = str(pest_raw or "").strip()
    if not s:
        return "Unknown Pest"
    lower = s.lower()
    if "brontispa" in lower or "leaf beetle" in lower:
        return "Brontispa"
    if "rhino" in lower or "rhinoceros" in lower or "oryctes" in lower:
        return "Rhinoceros Beetle"
    if "healthy" in lower:
        return "Healthy Coconut Leaf"
    return s


def normalize_severity(sev: Any, pest_type: Any = "") -> str:
    """Normalize severity string to Mild, Moderate, or Severe with consistent pest fallbacks."""
    s = str(sev or "").strip().capitalize()
    if s in ("Mild", "Moderate", "Severe"):
        return s
    pest_lower = str(pest_type or "").strip().lower()
    if "healthy" in pest_lower:
        return "Mild"
    return "Moderate"


def build_dashboard_chart_payload(reports: list[Mapping[str, Any]], group_by_day: bool = False) -> dict[str, Any]:
    """Build chart-friendly trend, distribution, and severity breakdown data from real reports."""
    empty_severity = {
        "categories": ["Mild", "Moderate", "Severe"],
        "datasets": [
            {
                "label": "Brontispa",
                "data": [0, 0, 0],
                "backgroundColor": "#164630",
                "borderColor": "#164630",
                "borderRadius": 6,
            },
            {
                "label": "Rhinoceros Beetle",
                "data": [0, 0, 0],
                "backgroundColor": "#d97706",
                "borderColor": "#d97706",
                "borderRadius": 6,
            },
        ],
        "combined": {
            "Mild": 0,
            "Moderate": 0,
            "Severe": 0,
            "total": 0,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [0, 0, 0],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
        "brontispa": {
            "Mild": 0,
            "Moderate": 0,
            "Severe": 0,
            "total": 0,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [0, 0, 0],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
        "rhinoceros_beetle": {
            "Mild": 0,
            "Moderate": 0,
            "Severe": 0,
            "total": 0,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [0, 0, 0],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
    }

    if not reports:
        return {
            "trend_labels": ["No data"],
            "trend_datasets": [
                {
                    "label": "Brontispa",
                    "data": [0],
                    "borderColor": "#164630",
                    "backgroundColor": "rgba(22, 70, 48, 0.15)",
                    "borderWidth": 2,
                    "tension": 0.2,
                    "pointRadius": 3,
                    "fill": True,
                },
                {
                    "label": "Rhinoceros Beetle",
                    "data": [0],
                    "borderColor": "#d97706",
                    "backgroundColor": "rgba(217, 119, 6, 0.15)",
                    "borderWidth": 2,
                    "tension": 0.2,
                    "pointRadius": 3,
                    "fill": True,
                },
            ],
            "distribution_labels": ["No reports yet"],
            "distribution_data": [0],
            "severity_breakdown": empty_severity,
        }

    monthly_counts: dict[str, Counter[str]] = defaultdict(Counter)
    pest_counter: Counter[str] = Counter()
    total_sev_counter: Counter[str] = Counter({"Mild": 0, "Moderate": 0, "Severe": 0})
    brontispa_sev_counter: Counter[str] = Counter({"Mild": 0, "Moderate": 0, "Severe": 0})
    rhino_sev_counter: Counter[str] = Counter({"Mild": 0, "Moderate": 0, "Severe": 0})

    for report in reports:
        created_at = report.get("created_at") or report.get("submitted_at") or report.get("photo_taken_at")
        dt = _parse_datetime(created_at)
        
        raw_pest = str(report.get("pest_type") or "Unknown Pest").strip() or "Unknown Pest"
        pest_name = normalize_pest_type(raw_pest)
        pest_lower = pest_name.lower()

        # Normalize severity consistently
        raw_sev = report.get("damage_severity") or report.get("severity")
        normalized_sev = normalize_severity(raw_sev, pest_name)

        total_sev_counter[normalized_sev] += 1

        if "brontispa" in pest_lower:
            brontispa_sev_counter[normalized_sev] += 1
        elif "rhino" in pest_lower or "beetle" in pest_lower:
            rhino_sev_counter[normalized_sev] += 1

        if dt:
            if group_by_day:
                time_key = dt.strftime("%b %d")
            else:
                time_key = dt.strftime("%b")
            monthly_counts[time_key][pest_name] += 1

        pest_counter[pest_name] += 1

    combined_total = sum(total_sev_counter.values())
    brontispa_total = sum(brontispa_sev_counter.values())
    rhino_total = sum(rhino_sev_counter.values())

    severity_breakdown = {
        "categories": ["Mild", "Moderate", "Severe"],
        "datasets": [
            {
                "label": "Brontispa",
                "data": [brontispa_sev_counter["Mild"], brontispa_sev_counter["Moderate"], brontispa_sev_counter["Severe"]],
                "backgroundColor": "#164630",
                "borderColor": "#164630",
                "borderRadius": 6,
            },
            {
                "label": "Rhinoceros Beetle",
                "data": [rhino_sev_counter["Mild"], rhino_sev_counter["Moderate"], rhino_sev_counter["Severe"]],
                "backgroundColor": "#d97706",
                "borderColor": "#d97706",
                "borderRadius": 6,
            },
        ],
        "combined": {
            "Mild": total_sev_counter["Mild"],
            "Moderate": total_sev_counter["Moderate"],
            "Severe": total_sev_counter["Severe"],
            "total": combined_total,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [total_sev_counter["Mild"], total_sev_counter["Moderate"], total_sev_counter["Severe"]],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
        "brontispa": {
            "Mild": brontispa_sev_counter["Mild"],
            "Moderate": brontispa_sev_counter["Moderate"],
            "Severe": brontispa_sev_counter["Severe"],
            "total": brontispa_total,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [brontispa_sev_counter["Mild"], brontispa_sev_counter["Moderate"], brontispa_sev_counter["Severe"]],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
        "rhinoceros_beetle": {
            "Mild": rhino_sev_counter["Mild"],
            "Moderate": rhino_sev_counter["Moderate"],
            "Severe": rhino_sev_counter["Severe"],
            "total": rhino_total,
            "labels": ["Mild", "Moderate", "Severe"],
            "data": [rhino_sev_counter["Mild"], rhino_sev_counter["Moderate"], rhino_sev_counter["Severe"]],
            "colors": ["#22c55e", "#f59e0b", "#ef4444"],
        },
    }

    if not monthly_counts:
        return {
            "trend_labels": ["No data"],
            "trend_datasets": [
                {
                    "label": "Brontispa",
                    "data": [0],
                    "borderColor": "#164630",
                    "backgroundColor": "rgba(22, 70, 48, 0.15)",
                    "borderWidth": 2,
                    "tension": 0.2,
                    "pointRadius": 3,
                    "fill": True,
                },
                {
                    "label": "Rhinoceros Beetle",
                    "data": [0],
                    "borderColor": "#d97706",
                    "backgroundColor": "rgba(217, 119, 6, 0.15)",
                    "borderWidth": 2,
                    "tension": 0.2,
                    "pointRadius": 3,
                    "fill": True,
                },
            ],
            "distribution_labels": ["No reports yet"],
            "distribution_data": [0],
            "severity_breakdown": severity_breakdown,
        }

    if group_by_day:
        def _sort_day_key(k):
            try:
                return datetime.strptime(f"2024 {k}", "%Y %b %d").timetuple().tm_yday
            except Exception:
                return 0
        month_labels = sorted(monthly_counts.keys(), key=_sort_day_key)
    else:
        def _sort_month_key(k):
            try:
                return datetime.strptime(k, "%b").month
            except Exception:
                return 0
        month_labels = sorted(monthly_counts.keys(), key=_sort_month_key)

    # Always ensure Brontispa and Rhinoceros Beetle are present in trend datasets
    all_trend_pests = ["Brontispa", "Rhinoceros Beetle"]
    for pest, _ in pest_counter.most_common():
        if pest not in all_trend_pests:
            all_trend_pests.append(pest)

    def _get_pest_color(pest_label: str, index: int):
        if pest_label == "Brontispa":
            return "#164630", "rgba(22, 70, 48, 0.15)"
        if pest_label == "Rhinoceros Beetle":
            return "#d97706", "rgba(217, 119, 6, 0.15)"
        palette = [
            ("#0f766e", "rgba(15, 118, 110, 0.15)"),
            ("#3b82f6", "rgba(59, 130, 246, 0.15)"),
            ("#8b5cf6", "rgba(139, 92, 246, 0.15)"),
            ("#ec4899", "rgba(236, 72, 153, 0.15)"),
        ]
        return palette[index % len(palette)]

    trend_datasets = []
    for idx, pest_label in enumerate(all_trend_pests):
        border_col, bg_col = _get_pest_color(pest_label, idx)
        trend_datasets.append(
            {
                "label": pest_label,
                "data": [monthly_counts[month].get(pest_label, 0) for month in month_labels],
                "borderColor": border_col,
                "backgroundColor": bg_col,
                "borderWidth": 2,
                "tension": 0.2,
                "pointRadius": 3,
                "fill": True,
            }
        )

    distribution_labels = [pest for pest, _ in pest_counter.most_common(5)]
    distribution_data = [pest_counter[pest] for pest in distribution_labels]

    if not distribution_labels:
        distribution_labels = ["No reports yet"]
        distribution_data = [0]

    return {
        "trend_labels": month_labels,
        "trend_datasets": trend_datasets,
        "distribution_labels": distribution_labels,
        "distribution_data": distribution_data,
        "severity_breakdown": severity_breakdown,
    }
