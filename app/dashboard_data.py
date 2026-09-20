from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Mapping, Sequence


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


def build_dashboard_chart_payload(reports: Sequence[Mapping[str, Any]], group_by_day: bool = False) -> dict[str, Any]:
    """Build chart-friendly trend and pest distribution data from real reports."""
    empty_payload = {
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
        "trend_breakdown": [],
        "trend_pests": ["Brontispa", "Rhinoceros Beetle"],
        "trend_pest_totals": {"Brontispa": 0, "Rhinoceros Beetle": 0},
        "trend_grand_total": 0,
    }

    if not reports:
        return empty_payload

    monthly_counts: dict[str, Counter[str]] = defaultdict(Counter)
    pest_counter: Counter[str] = Counter()

    for report in reports:
        created_at = report.get("created_at") or report.get("submitted_at") or report.get("photo_taken_at")
        dt = _parse_datetime(created_at)

        raw_pest = str(report.get("pest_type") or "Unknown Pest").strip() or "Unknown Pest"
        pest_name = normalize_pest_type(raw_pest)

        # Exclude Healthy Coconut Leaf across all pest trend and pest distribution charts
        if pest_name.lower().startswith("healthy") or "healthy" in pest_name.lower():
            continue

        if dt:
            if group_by_day:
                time_key = dt.strftime("%b %d")
            else:
                time_key = dt.strftime("%b")
            monthly_counts[time_key][pest_name] += 1

        pest_counter[pest_name] += 1

    if not monthly_counts:
        return empty_payload

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
        if pest not in all_trend_pests and "healthy" not in pest.lower():
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

    distribution_labels = [pest for pest, _ in pest_counter.most_common(5) if "healthy" not in pest.lower()]
    distribution_data = [pest_counter[pest] for pest in distribution_labels]

    if not distribution_labels:
        distribution_labels = ["No reports yet"]
        distribution_data = [0]

    trend_breakdown = []
    for month in month_labels:
        row_counts = {pest: monthly_counts[month].get(pest, 0) for pest in all_trend_pests}
        row_total = sum(row_counts.values())
        trend_breakdown.append({
            "period": month,
            "counts": row_counts,
            "total": row_total,
        })

    trend_pest_totals = {
        pest: sum(monthly_counts[m].get(pest, 0) for m in month_labels)
        for pest in all_trend_pests
    }
    trend_grand_total = sum(trend_pest_totals.values())

    return {
        "trend_labels": month_labels,
        "trend_datasets": trend_datasets,
        "distribution_labels": distribution_labels,
        "distribution_data": distribution_data,
        "trend_breakdown": trend_breakdown,
        "trend_pests": all_trend_pests,
        "trend_pest_totals": trend_pest_totals,
        "trend_grand_total": trend_grand_total,
    }

