"""trend_memory.py — deterministic trend analysis from aggregated tables.

Computes how long a signal has been active and whether it is worsening,
stable, or recovering. No storage, no LLM — pure arithmetic on the same
tables the detectors already consume.
"""
from datetime import timedelta
from collections import defaultdict
from .baselines import median_mad


TREND_WINDOW = 14  # days to look back for trend analysis
MIN_DAYS = 3       # minimum days needed to establish a trend


def _funnel_trend(funnel_table, source, step, baseline_rate):
    """Return daily rates for (source, step) over the last TREND_WINDOW days."""
    pts = []
    for (day, src, stp), v in funnel_table.items():
        if src == source and stp == step and v["exposures"] >= 10:
            pts.append((day, v["conversions"] / v["exposures"]))
    if not pts:
        return []
    pts.sort(key=lambda x: x[0])
    return pts[-TREND_WINDOW:]


def _source_divergence_trend(source_completion, source):
    """Return daily completion rates for the given source."""
    pts = []
    for (day, src), v in source_completion.items():
        if src == source and v["exposures"] >= 10:
            pts.append((day, v["conversions"] / v["exposures"]))
    if not pts:
        return []
    pts.sort(key=lambda x: x[0])
    return pts[-TREND_WINDOW:]


def _install_trend(daily_installs_map):
    """Return daily install counts over the last TREND_WINDOW days."""
    days = sorted(daily_installs_map.keys())[-TREND_WINDOW:]
    return [(d, daily_installs_map[d]) for d in days]


def _consecutive_below(pts, threshold):
    """Count consecutive trailing days where value is below threshold."""
    count = 0
    for _, v in reversed(pts):
        if v < threshold:
            count += 1
        else:
            break
    return count


def _consecutive_above(pts, threshold):
    """Count consecutive trailing days where value is above threshold."""
    count = 0
    for _, v in reversed(pts):
        if v > threshold:
            count += 1
        else:
            break
    return count


def _slope(pts):
    """Simple linear slope over the last MIN_DAYS points (normalised per day)."""
    if len(pts) < MIN_DAYS:
        return 0.0
    recent = pts[-MIN_DAYS:]
    values = [v for _, v in recent]
    n = len(values)
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


def _trend_label(slope, threshold=0.002):
    if slope < -threshold:
        return "worsening"
    if slope > threshold:
        return "recovering"
    return "stable"


def funnel_drop_trend(funnel_table, source, step, baseline_rate):
    """Analyse trend for a funnel drop insight.

    Returns a dict with:
        days_active   int   — consecutive days below baseline
        direction     str   — worsening / stable / recovering
        description   str   — human-readable trend phrase
    """
    pts = _funnel_trend(funnel_table, source, step, baseline_rate)
    if len(pts) < MIN_DAYS:
        return {"days_active": 1, "direction": "stable", "description": "First detected today"}

    days_active = _consecutive_below(pts, baseline_rate * 0.95)
    slope = _slope(pts)
    direction = _trend_label(slope)

    if days_active <= 1:
        desc = "First detected today"
    elif direction == "worsening":
        desc = f"Worsening — day {days_active} of decline"
    elif direction == "recovering":
        desc = f"Day {days_active} active, showing early recovery"
    else:
        desc = f"Ongoing — day {days_active} of decline"

    return {"days_active": days_active, "direction": direction, "description": desc}


def source_divergence_trend(source_completion, source, baseline_rate):
    """Analyse trend for a source divergence insight."""
    pts = _source_divergence_trend(source_completion, source)
    if len(pts) < MIN_DAYS:
        return {"days_active": 1, "direction": "stable", "description": "First detected today"}

    days_active = _consecutive_below(pts, baseline_rate * 0.95)
    slope = _slope(pts)
    direction = _trend_label(slope)

    if days_active <= 1:
        desc = "First detected today"
    elif direction == "worsening":
        desc = f"Worsening — day {days_active} of divergence"
    elif direction == "recovering":
        desc = f"Day {days_active} active, gap narrowing"
    else:
        desc = f"Ongoing — day {days_active} of divergence"

    return {"days_active": days_active, "direction": direction, "description": desc}


def anomaly_trend(daily_installs_map, expected):
    """Analyse trend for a DAU anomaly insight."""
    pts = _install_trend(daily_installs_map)
    if len(pts) < MIN_DAYS:
        return {"days_active": 1, "direction": "stable", "description": "First detected today"}

    days_active = _consecutive_above(pts, expected * 1.1)
    if days_active == 0:
        days_active = _consecutive_below(pts, expected * 0.9)
    slope = _slope(pts)
    direction = _trend_label(slope, threshold=1.0)

    if days_active <= 1:
        desc = "Isolated spike — first detected today"
    elif direction == "worsening":
        desc = f"Accelerating — day {days_active} of anomaly"
    elif direction == "recovering":
        desc = f"Day {days_active} active, normalising"
    else:
        desc = f"Ongoing — day {days_active} of anomaly"

    return {"days_active": days_active, "direction": direction, "description": desc}


def attach_trend(insight, funnel_table=None, source_completion=None, daily_installs_map=None):
    """Attach a trend dict to an insight based on its type.

    Mutates insight by adding a `trend` attribute.
    Returns the insight for convenience.
    """
    t = getattr(insight, "type", "")
    rm = getattr(insight, "raw_metrics", {})

    if t == "funnel_drop" and funnel_table is not None:
        source = rm.get("source", "")
        step = rm.get("step_index", 0)
        baseline = rm.get("baseline_rate", 0.5)
        trend = funnel_drop_trend(funnel_table, source, step, baseline)

    elif t == "cohort_divergence" and source_completion is not None:
        source = rm.get("worst_source", "")
        baseline = rm.get("others_rate", 0.5)
        trend = source_divergence_trend(source_completion, source, baseline)

    elif t == "anomaly" and daily_installs_map is not None:
        expected = rm.get("expected_installs", 100)
        trend = anomaly_trend(daily_installs_map, expected)

    else:
        trend = {"days_active": 1, "direction": "stable", "description": "First detected today"}

    insight.trend = trend
    return insight