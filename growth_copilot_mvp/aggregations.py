"""Aggregate raw events into the narrow tables the detectors consume.

These are the only things detectors read. New insight types start with a new
aggregation here, not a new query against raw events.
"""
from collections import defaultdict
from .synth_data import FUNNEL_STEPS


def funnel_step_table(events):
    """{(day, source, step_idx): {exposures, conversions}} for transition i -> i+1."""
    user_events = defaultdict(set)
    user_meta = {}
    for e in events:
        user_events[e["user"]].add(e["event"])
        if e["event"] == "install":
            user_meta[e["user"]] = (e["day"], e["source"])

    agg = defaultdict(lambda: {"exposures": 0, "conversions": 0})
    for user, evset in user_events.items():
        if user not in user_meta:
            continue
        day, source = user_meta[user]
        for i in range(len(FUNNEL_STEPS) - 1):
            from_e, to_e = FUNNEL_STEPS[i], FUNNEL_STEPS[i + 1]
            if from_e in evset:
                key = (day, source, i)
                agg[key]["exposures"] += 1
                if to_e in evset:
                    agg[key]["conversions"] += 1
    return dict(agg)


def daily_installs(events):
    """{day: install_count} — stands in for top-line DAU in this prototype."""
    out = defaultdict(int)
    for e in events:
        if e["event"] == "install":
            out[e["day"]] += 1
    return dict(out)


def source_funnel_completion(events):
    """{(day, source): {exposures, conversions}} where conversion = reached habit_action."""
    user_events = defaultdict(set)
    user_meta = {}
    for e in events:
        user_events[e["user"]].add(e["event"])
        if e["event"] == "install":
            user_meta[e["user"]] = (e["day"], e["source"])

    agg = defaultdict(lambda: {"exposures": 0, "conversions": 0})
    for user, evset in user_events.items():
        if user not in user_meta:
            continue
        day, source = user_meta[user]
        agg[(day, source)]["exposures"] += 1
        if "habit_action" in evset:
            agg[(day, source)]["conversions"] += 1
    return dict(agg)
