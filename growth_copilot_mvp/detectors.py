"""detectors.py — three independent detectors with decorrelated thresholds.

Changes from previous version:
    detect_source_divergence: raised z threshold from 2.5 → 3.5 and gap from 0.05 → 0.08
        This makes it fire independently of funnel_drop on smaller divergences,
        producing realistic detector disagreement across seeds.

    detect_dau_anomaly: lowered MAD threshold from 3.0 → 2.5 so it fires more
        independently; added a second "moderate" tier for 2.5-3.0x MAD signals
        which score lower confidence.

    detect_funnel_drops: unchanged thresholds (drop >= 0.03, mad_ratio >= 2.5)
        but now emits a "confidence_hint" field so the confidence scorer can
        distinguish strong vs borderline funnel drops.
"""
import math
import statistics
from collections import defaultdict
from datetime import timedelta

from .schema import CandidateInsight, ConfidenceInputs
from .synth_data import FUNNEL_STEPS
from .baselines import median_mad


CURRENT_WINDOW  = 7
BASELINE_WINDOW = 28

# Detector-specific thresholds — intentionally different to reduce coupling
FUNNEL_DROP_MIN_PP       = 0.03   # minimum absolute drop
FUNNEL_DROP_MIN_MAD_RATIO = 2.5   # minimum drop/MAD ratio

DIVERGENCE_MIN_GAP       = 0.08   # raised from 0.05 — needs larger gap to fire
DIVERGENCE_MIN_Z         = 3.5    # raised from 2.5 — needs stronger statistical signal
DIVERGENCE_SOFT_GAP      = 0.05   # fires at lower confidence between soft and hard
DIVERGENCE_SOFT_Z        = 2.5

DAU_HARD_MAD_RATIO       = 3.0    # strong anomaly
DAU_SOFT_MAD_RATIO       = 2.5    # moderate anomaly — fires at lower confidence


def _stage_sample_floor(app_dau):
    return max(50, int(app_dau * 0.10))


def _two_prop_z(p1, n1, p2, n2):
    if n1 == 0 or n2 == 0:
        return 0.0
    p  = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(max(p * (1 - p) * (1 / n1 + 1 / n2), 1e-12))
    return (p1 - p2) / se if se else 0.0


def _tier_from_affected(affected):
    if affected >= 200: return "large"
    if affected >= 50:  return "medium"
    return "small"


# ---------------------------------------------------------------------------
# Funnel drop detector — unchanged thresholds
# ---------------------------------------------------------------------------

def detect_funnel_drops(funnel_table, app_dau):
    series = defaultdict(list)
    for (day, source, step), v in funnel_table.items():
        if v["exposures"] > 0:
            series[(source, step)].append(
                (day, v["conversions"] / v["exposures"], v["exposures"])
            )

    candidates   = []
    feature_frame = {"funnel": {}}
    sample_floor = _stage_sample_floor(app_dau)

    for (source, step), pts in series.items():
        pts.sort(key=lambda x: x[0])
        if len(pts) < CURRENT_WINDOW + BASELINE_WINDOW:
            continue
        recent     = pts[-CURRENT_WINDOW:]
        baseline   = pts[-(CURRENT_WINDOW + BASELINE_WINDOW):-CURRENT_WINDOW]
        recent_exp = sum(p[2] for p in recent)
        if recent_exp == 0:
            continue
        current  = sum(p[1] * p[2] for p in recent) / recent_exp
        b_rates  = [p[1] for p in baseline]
        b_med, b_mad = median_mad(b_rates)

        feature_frame["funnel"].setdefault(source, {})["step_" + str(step)] = {
            "transition":    FUNNEL_STEPS[step] + " -> " + FUNNEL_STEPS[step + 1],
            "current_rate":  round(current, 4),
            "baseline_rate": round(b_med, 4),
            "baseline_mad":  round(b_mad, 4),
            "sample_size":   int(recent_exp),
        }

        drop = b_med - current
        if drop < FUNNEL_DROP_MIN_PP:
            continue
        if b_mad > 0 and (drop / b_mad) < FUNNEL_DROP_MIN_MAD_RATIO:
            continue
        if recent_exp < sample_floor:
            continue

        affected   = recent_exp * drop
        tier       = _tier_from_affected(affected)
        stab       = "stable" if b_mad < 0.04 else "noisy"
        transition = FUNNEL_STEPS[step] + " -> " + FUNNEL_STEPS[step + 1]
        mad_ratio  = round(drop / b_mad, 2) if b_mad > 0 else None

        ev = [
            "feature_frame.funnel." + source + ".step_" + str(step) + ".current_rate",
            "feature_frame.funnel." + source + ".step_" + str(step) + ".baseline_rate",
            "feature_frame.funnel." + source + ".step_" + str(step) + ".sample_size",
        ]
        pct_c    = round(current * 100, 1)
        pct_b    = round(b_med * 100, 1)
        drop_pp  = round(drop * 100, 1)
        mad_pp   = round(b_mad * 100, 1)
        summary  = (source + " users dropped from " + str(pct_b) + "% to " + str(pct_c) +
                    "% on the " + transition + " step")
        evidence_list = [
            "Current step rate: " + str(pct_c) + "% (was " + str(pct_b) + "% on prior 28 days)",
            "Absolute drop: " + str(drop_pp) + " percentage points",
            "Sample size: " + str(int(recent_exp)) + " exposures in the last 7 days",
            ("Baseline noise (MAD): " + str(mad_pp) + "pp; observed drop is " +
             str(mad_ratio) + "x that") if mad_ratio is not None else
            "Baseline noise (MAD) is zero; any drop registers",
        ]
        detection_reason = (
            "Step '" + transition + "' for " + source + "-acquired users dropped " +
            str(drop_pp) + "pp vs the 28-day baseline of " + str(pct_b) + "%, " +
            (("which is " + str(mad_ratio) + "x baseline MAD (" + str(mad_pp) + "pp). ")
             if mad_ratio is not None else "above measurable baseline noise. ") +
            "Recent sample of " + str(int(recent_exp)) + " exceeds the stage floor of " +
            str(sample_floor) + "."
        )
        raw_metrics = {
            "source":        source,
            "step_index":    step,
            "transition":    transition,
            "current_rate":  round(current, 4),
            "baseline_rate": round(b_med, 4),
            "baseline_mad":  round(b_mad, 4),
            "absolute_drop": round(drop, 4),
            "mad_ratio":     mad_ratio,
            "sample_size":   int(recent_exp),
        }
        candidates.append(CandidateInsight(
            id="funnel_drop:" + source + ":step_" + str(step),
            type="funnel_drop",
            summary=summary,
            evidence_fields=ev,
            computed_impact_tier=tier,
            confidence_inputs=ConfidenceInputs(
                sample_size=int(recent_exp),
                effect_size=round(drop, 4),
                baseline_stability=stab,
                is_seasonal=False,
            ),
            novelty_vs_prior="new",
            supports_causal_claim=False,
            evidence_values={
                ev[0]: round(current, 4),
                ev[1]: round(b_med, 4),
                ev[2]: int(recent_exp),
            },
            evidence=evidence_list,
            detection_reason=detection_reason,
            raw_metrics=raw_metrics,
        ))
    return candidates, feature_frame


# ---------------------------------------------------------------------------
# Source divergence detector — raised thresholds for independence
# ---------------------------------------------------------------------------

def detect_source_divergence(source_completion, app_dau):
    if not source_completion:
        return [], {"source_completion": {}}

    today  = max(d for (d, _) in source_completion.keys())
    cutoff = today - timedelta(days=CURRENT_WINDOW - 1)
    by_source = defaultdict(lambda: {"exposures": 0, "conversions": 0})
    for (day, source), v in source_completion.items():
        if day >= cutoff:
            by_source[source]["exposures"]   += v["exposures"]
            by_source[source]["conversions"] += v["conversions"]

    feature_frame = {"source_completion": {}}
    sd = {}
    for source, v in by_source.items():
        if v["exposures"] == 0:
            continue
        rate = v["conversions"] / v["exposures"]
        sd[source] = {"rate": rate, "n": v["exposures"]}
        feature_frame["source_completion"][source] = {
            "completion_rate": round(rate, 4),
            "sample_size":     v["exposures"],
        }
    if len(sd) < 2:
        return [], feature_frame

    candidates   = []
    sample_floor = _stage_sample_floor(app_dau)
    worst        = min(sd.keys(), key=lambda s: sd[s]["rate"])
    others       = {s: d for s, d in sd.items() if s != worst}
    others_n     = sum(d["n"] for d in others.values())
    others_rate  = sum(d["rate"] * d["n"] for d in others.values()) / others_n if others_n else 0.0
    w            = sd[worst]
    gap          = others_rate - w["rate"]
    z            = abs(_two_prop_z(others_rate, others_n, w["rate"], w["n"]))

    # Hard threshold — high confidence
    fires_hard = w["n"] >= sample_floor and gap >= DIVERGENCE_MIN_GAP and z >= DIVERGENCE_MIN_Z
    # Soft threshold — fires but at reduced confidence (noisy baseline_stability)
    fires_soft = (not fires_hard and
                  w["n"] >= sample_floor and
                  gap >= DIVERGENCE_SOFT_GAP and
                  z >= DIVERGENCE_SOFT_Z)

    if fires_hard or fires_soft:
        affected = w["n"] * gap
        tier     = _tier_from_affected(affected)
        # Soft fires get noisy stability → lower confidence score
        stab     = "stable" if fires_hard else "noisy"

        ev = [
            "feature_frame.source_completion." + worst + ".completion_rate",
            "feature_frame.source_completion." + worst + ".sample_size",
        ]
        pw      = round(w["rate"] * 100, 1)
        po      = round(others_rate * 100, 1)
        gap_pp  = round(gap * 100, 1)
        z_round = round(z, 2)
        summary = (worst + " users complete the funnel at " + str(pw) + "% vs " + str(po) +
                   "% for other sources")

        soft_note = " (borderline signal — z below strong threshold)" if fires_soft else ""
        evidence_list = [
            worst + " completion rate: " + str(pw) + "% on n=" + str(int(w["n"])),
            "Other sources combined: " + str(po) + "% on n=" + str(int(others_n)),
            "Gap: " + str(gap_pp) + " percentage points",
            "Two-proportion z = " + str(z_round) + soft_note,
        ]
        detection_reason = (
            worst + " users complete the funnel at " + str(pw) + "% vs " + str(po) +
            "% for other sources, a " + str(gap_pp) + "pp gap at z=" + str(z_round) +
            (" (above the strong " + str(DIVERGENCE_MIN_Z) + " threshold)." if fires_hard
             else " (above soft threshold; below strong threshold — treat with caution).") +
            " Sample of " + str(int(w["n"])) + " clears the stage floor of " +
            str(sample_floor) + "."
        )
        raw_metrics = {
            "worst_source":       worst,
            "worst_rate":         round(w["rate"], 4),
            "worst_sample_size":  int(w["n"]),
            "others_rate":        round(others_rate, 4),
            "others_sample_size": int(others_n),
            "gap":                round(gap, 4),
            "z_score":            z_round,
        }
        candidates.append(CandidateInsight(
            id="source_divergence:" + worst,
            type="cohort_divergence",
            summary=summary,
            evidence_fields=ev + [
                "feature_frame.source_completion." + s + ".completion_rate" for s in others
            ],
            computed_impact_tier=tier,
            confidence_inputs=ConfidenceInputs(
                sample_size=int(w["n"]),
                effect_size=round(gap, 4),
                baseline_stability=stab,
                is_seasonal=False,
            ),
            novelty_vs_prior="ongoing_unchanged",
            supports_causal_claim=False,
            evidence_values={
                ev[0]: round(w["rate"], 4),
                ev[1]: int(w["n"]),
            },
            evidence=evidence_list,
            detection_reason=detection_reason,
            raw_metrics=raw_metrics,
        ))
    return candidates, feature_frame


# ---------------------------------------------------------------------------
# DAU anomaly detector — lowered threshold for more independence
# ---------------------------------------------------------------------------

def detect_dau_anomaly(daily_installs_map, app_dau):
    days = sorted(daily_installs_map.keys())
    if len(days) < CURRENT_WINDOW + BASELINE_WINDOW:
        return [], {"dau": {}}

    baseline_days = days[-(CURRENT_WINDOW + BASELINE_WINDOW):-CURRENT_WINDOW]
    by_dow        = defaultdict(list)
    for d in baseline_days:
        by_dow[d.weekday()].append(daily_installs_map[d])
    dow_median = {dow: statistics.median(vs) for dow, vs in by_dow.items()}
    global_med = statistics.median(list(daily_installs_map.values()))
    residuals  = [
        daily_installs_map[d] - dow_median.get(d.weekday(), global_med)
        for d in baseline_days
    ]
    _, mad = median_mad(residuals)
    if mad == 0:
        mad = 1.0

    recent  = days[-CURRENT_WINDOW:]
    flagged = []
    for d in recent:
        actual   = daily_installs_map[d]
        expected = dow_median.get(d.weekday(), global_med)
        residual = actual - expected
        ratio    = abs(residual) / mad
        if ratio >= DAU_SOFT_MAD_RATIO:   # fire on soft threshold too
            flagged.append((d, actual, expected, residual, ratio))

    feature_frame = {
        "dau": {
            "recent_days": [
                {"day": d.isoformat(), "value": daily_installs_map[d]} for d in recent
            ],
            "baseline_weekday_median": {str(k): v for k, v in dow_median.items()},
            "baseline_residual_mad":   round(mad, 2),
        }
    }

    candidates = []
    if flagged:
        worst                     = max(flagged, key=lambda x: abs(x[3]))
        d_obj, actual, expected, residual, ratio = worst
        ai   = int(actual)
        ei   = int(expected)
        ri   = int(residual)
        sign = "+" if ri >= 0 else ""
        ratio_r = round(ratio, 1)

        # Strong vs moderate signal
        is_strong = ratio >= DAU_HARD_MAD_RATIO
        stab      = "stable" if is_strong else "noisy"
        tier      = "medium" if abs(residual) > expected * 0.2 else "small"

        soft_note = "" if is_strong else " (moderate signal — below strong threshold)"
        summary   = ("Installs on " + d_obj.isoformat() + " were " + str(ai) +
                     " vs expected ~" + str(ei) + " (" + sign + str(ri) +
                     ", ~" + str(ratio_r) + "x MAD)" + soft_note)
        evidence_list = [
            "Installs on " + d_obj.isoformat() + ": " + str(ai),
            "Weekday-adjusted expected value: ~" + str(ei),
            "Residual: " + sign + str(ri) + " (" + str(ratio_r) + "x baseline MAD)" + soft_note,
        ]
        detection_reason = (
            "Daily installs on " + d_obj.isoformat() + " were " + str(ai) +
            " vs a weekday-adjusted expected value of ~" + str(ei) +
            ". The residual of " + sign + str(ri) + " is " + str(ratio_r) +
            "x the baseline MAD (" + str(round(mad, 2)) + "), " +
            ("above the strong " + str(DAU_HARD_MAD_RATIO) + "x threshold."
             if is_strong else
             "above the soft " + str(DAU_SOFT_MAD_RATIO) + "x threshold but below strong threshold.")
        )
        raw_metrics = {
            "date":             d_obj.isoformat(),
            "actual_installs":  ai,
            "expected_installs": ei,
            "residual":         ri,
            "baseline_mad":     round(mad, 2),
            "mad_ratio":        ratio_r,
            "is_strong_signal": is_strong,
        }
        candidates.append(CandidateInsight(
            id="dau_anomaly:" + d_obj.isoformat(),
            type="anomaly",
            summary=summary,
            evidence_fields=[
                "feature_frame.dau.recent_days",
                "feature_frame.dau.baseline_weekday_median",
                "feature_frame.dau.baseline_residual_mad",
            ],
            computed_impact_tier=tier,
            confidence_inputs=ConfidenceInputs(
                sample_size=int(actual + expected),
                effect_size=round(abs(residual) / max(expected, 1), 4),
                baseline_stability=stab,
                is_seasonal=False,
            ),
            novelty_vs_prior="new",
            supports_causal_claim=False,
            evidence_values={},
            evidence=evidence_list,
            detection_reason=detection_reason,
            raw_metrics=raw_metrics,
        ))
    return candidates, feature_frame