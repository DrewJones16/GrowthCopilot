import os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                    "growth_copilot_mvp", "timeline_replay.py")
content = '''"""timeline_replay.py"""
import math
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

_STRENGTH_INITIAL = 60.0
_STRENGTH_FLOOR   = 25.0
_DECAY_SEEN       = {"worsening": 1.02, "stable": 0.96, "recovering": 0.90}
_DECAY_ABSENT     = 0.70
_REINFORCE        = 0.30

def _decay_strength(current, direction, confidence):
    decay = _DECAY_SEEN.get(direction, 0.95)
    return min(current * decay + confidence * _REINFORCE, 100.0)

def _get_direction(cluster):
    dirs = []
    for ins in cluster.get("insights", []):
        dirs.append(getattr(ins, "trend", {}).get("direction", "stable"))
    if "worsening" in dirs:  return "worsening"
    if "recovering" in dirs: return "recovering"
    return "stable"

def run_timeline(n_days=30, start_seed=42, archetype_key="consumer_social"):
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from growth_copilot_mvp.synth_data import generate_events, _pick_scenario
    from growth_copilot_mvp.aggregations import funnel_step_table, daily_installs, source_funnel_completion
    from growth_copilot_mvp.detectors import detect_funnel_drops, detect_source_divergence, detect_dau_anomaly
    from growth_copilot_mvp.ranker import rank
    from growth_copilot_mvp.insight_clusterer import cluster_insights
    from growth_copilot_mvp.trend_memory import attach_trend
    from growth_copilot_mvp.causal_engine import find_causal_links
    from growth_copilot_mvp.decision_engine import make_decision
    from growth_copilot_mvp.attention import classify_clusters
    from growth_copilot_mvp.archetypes import get_archetype

    archetype = get_archetype(archetype_key)
    signal_strengths = {}
    signal_days = {}
    signal_status = {}
    seen_titles = set()
    timeline = []
    today = date.today()

    for i in range(n_days):
        seed = start_seed + i
        day_date = today - timedelta(days=n_days - 1 - i)
        scenario_wt = archetype.get("scenario_weights", {})
        scenario = _pick_scenario(seed, scenario_wt)
        try:
            events = generate_events(days=90, seed=seed, archetype=archetype)
            funnel = funnel_step_table(events)
            installs = daily_installs(events)
            completion = source_funnel_completion(events)
            app_dau = int(sum(installs.values()) / len(installs))
            fc, _ = detect_funnel_drops(funnel, app_dau)
            sc, _ = detect_source_divergence(completion, app_dau)
            dc, _ = detect_dau_anomaly(installs, app_dau)
            all_c = fc + sc + dc
            for ins in all_c:
                attach_trend(ins, funnel_table=funnel, source_completion=completion, daily_installs_map=installs)
            ranked = rank(all_c)
            clustered = cluster_insights(ranked)
            causal = find_causal_links(ranked)
            decisions = [make_decision(c, causal) for c in clustered]
            surfaced, background = classify_clusters(clustered, decisions)
        except Exception as e:
            timeline.append({"date": day_date.isoformat(), "seed": seed, "scenario": scenario,
                "error": str(e), "fired": False, "clusters": [], "primary_title": None,
                "urgency": None, "confidence": 0, "signal_states": {}, "trust_notes": [],
                "causal_links": 0, "new_signals": [], "resolved_signals": [], "escalated_signals": []})
            continue

        fired_titles = {c["title"] for c in surfaced}
        new_signals, resolved_signals, escalated_signals = [], [], []

        for cluster in surfaced:
            title = cluster["title"]
            conf = cluster["confidence"]["score"]
            direction = _get_direction(cluster)
            if title not in signal_strengths:
                signal_strengths[title] = _STRENGTH_INITIAL
                signal_days[title] = 1
                signal_status[title] = "new"
                if title not in seen_titles:
                    new_signals.append(title)
                    seen_titles.add(title)
            else:
                signal_days[title] = signal_days.get(title, 0) + 1
                signal_strengths[title] = _decay_strength(signal_strengths[title], direction, conf)
            days = signal_days[title]
            if direction == "worsening" and days >= 5:
                signal_status[title] = "escalated"
                escalated_signals.append(title)
            elif direction == "recovering":
                signal_status[title] = "improving"
            elif direction == "stable" and days >= 3:
                signal_status[title] = "stabilizing"
            else:
                signal_status[title] = "active"

        for title in list(signal_strengths.keys()):
            if title not in fired_titles:
                signal_strengths[title] *= _DECAY_ABSENT
                if signal_strengths[title] < 5.0:
                    resolved_signals.append(title)
                    del signal_strengths[title]
                    if title in signal_days: del signal_days[title]
                    if title in signal_status: del signal_status[title]

        primary = surfaced[0] if surfaced else None
        p_dec = decisions[clustered.index(primary)] if primary and primary in clustered else None

        timeline.append({
            "date": day_date.isoformat(), "seed": seed, "scenario": scenario,
            "fired": len(surfaced) > 0,
            "clusters": [{"title": c["title"], "severity": c["severity"],
                "confidence": c["confidence"]["score"], "conf_label": c["confidence"]["label"],
                "urgency": decisions[clustered.index(c)]["urgency"] if c in clustered else "monitor",
                "direction": _get_direction(c), "n_insights": len(c["insights"])} for c in surfaced],
            "primary_title": primary["title"] if primary else None,
            "urgency": p_dec["urgency"] if p_dec else None,
            "confidence": primary["confidence"]["score"] if primary else 0,
            "signal_states": {t: {"strength": round(signal_strengths.get(t, 0), 1),
                "status": signal_status.get(t, "active"), "days_active": signal_days.get(t, 0)}
                for t in (set(signal_strengths.keys()) | fired_titles)},
            "trust_notes": [],
            "causal_links": len(causal),
            "new_signals": new_signals,
            "resolved_signals": resolved_signals,
            "escalated_signals": escalated_signals,
            "n_background": len(background),
        })
    return timeline

def timeline_summary(timeline):
    fired = [d for d in timeline if d.get("fired")]
    quiet = [d for d in timeline if not d.get("fired")]
    all_urgency = [d["urgency"] for d in fired if d.get("urgency")]
    all_conf = [d["confidence"] for d in fired if d.get("confidence")]
    all_titles = [d["primary_title"] for d in fired if d.get("primary_title")]
    title_counts = defaultdict(int)
    for t in all_titles: title_counts[t] += 1
    return {
        "total_days": len(timeline), "alert_days": len(fired), "quiet_days": len(quiet),
        "alert_rate": round(len(fired) / len(timeline), 2) if timeline else 0,
        "urgency_dist": {u: all_urgency.count(u) for u in set(all_urgency)},
        "conf_mean": round(sum(all_conf) / len(all_conf), 1) if all_conf else 0,
        "primary_signals": dict(title_counts),
        "total_new": sum(len(d.get("new_signals", [])) for d in timeline),
        "total_resolved": sum(len(d.get("resolved_signals", [])) for d in timeline),
        "total_escalated": sum(len(d.get("escalated_signals", [])) for d in timeline),
    }
'''
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Written to {path}")
print(f"Size: {len(content)} bytes")
