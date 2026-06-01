"""replay_evaluator.py — stateful replay with decay simulation.

Phase 5 changes:
    - run_replay_stateful(): simulates N consecutive days using sequential seeds,
      accumulating signal state across runs (decay, persistence, suppression)
    - score_results() extended with stateful metrics
    - Both stateless (per-seed) and stateful (sequential) modes available
    - CLI and Streamlit panel updated to show both
"""
import sys, os, math, copy
from collections import defaultdict
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_copilot_mvp.synth_data import generate_events
from growth_copilot_mvp.aggregations import funnel_step_table, daily_installs, source_funnel_completion
from growth_copilot_mvp.detectors import detect_funnel_drops, detect_source_divergence, detect_dau_anomaly
from growth_copilot_mvp.ranker import rank
from growth_copilot_mvp.insight_clusterer import cluster_insights
from growth_copilot_mvp.trend_memory import attach_trend
from growth_copilot_mvp.causal_engine import find_causal_links
from growth_copilot_mvp.decision_engine import make_decision


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _mean(v): return sum(v)/len(v) if v else 0.0
def _std(v):
    if len(v) < 2: return 0.0
    m = _mean(v)
    return math.sqrt(sum((x-m)**2 for x in v)/len(v))
def _pct(v, p):
    if not v: return 0.0
    s = sorted(v); idx = (len(s)-1)*p/100
    lo, hi = int(idx), min(int(idx)+1, len(s)-1)
    return s[lo] + (s[hi]-s[lo])*(idx-lo)
def _entropy(counts):
    total = sum(counts.values())
    if not total: return 0.0
    return -sum((c/total)*math.log2(c/total) for c in counts.values() if c > 0)


# ---------------------------------------------------------------------------
# Single seed runner (stateless)
# ---------------------------------------------------------------------------

def run_seed(seed: int) -> Dict:
    events     = generate_events(days=90, daily_installs=120, seed=seed)
    funnel     = funnel_step_table(events)
    installs   = daily_installs(events)
    completion = source_funnel_completion(events)
    app_dau    = int(sum(installs.values())/len(installs))
    fc, _ = detect_funnel_drops(funnel, app_dau)
    sc, _ = detect_source_divergence(completion, app_dau)
    dc, _ = detect_dau_anomaly(installs, app_dau)
    all_c = fc + sc + dc
    for ins in all_c:
        attach_trend(ins, funnel_table=funnel, source_completion=completion,
                     daily_installs_map=installs)
    ranked    = rank(all_c)
    clustered = cluster_insights(ranked)
    causal    = find_causal_links(ranked)
    det = defaultdict(int)
    for ins in ranked: det[ins.type] += 1
    detector_types = set(ins.type for ins in ranked)
    clusters = []
    for c in clustered:
        d = make_decision(c, causal)
        clusters.append({
            "title":            c["title"],
            "severity":         c["severity"],
            "confidence_score": c["confidence"]["score"],
            "confidence_label": c["confidence"]["label"],
            "n_insights":       len(c["insights"]),
            "urgency":          d["urgency"],
        })
    return {
        "seed":               seed,
        "n_candidates":       len(ranked),
        "n_clusters":         len(clustered),
        "n_causal_links":     len(causal),
        "detector_counts":    dict(det),
        "detector_types":     list(detector_types),
        "detector_agreement": len(detector_types) >= 2,
        "clusters":           clusters,
        "fired":              len(ranked) > 0,
        "primary_title":      clustered[0]["title"] if clustered else None,
        "primary_severity":   clustered[0]["severity"] if clustered else None,
        "primary_confidence": clustered[0]["confidence"]["score"] if clustered else 0,
        "insight_conf_scores": [
            min(int(round(
                (min(math.log10(max(getattr(getattr(ins,"confidence_inputs",None),"sample_size",1),1))/math.log10(1000),1.0))*32 +
                (min(getattr(getattr(ins,"confidence_inputs",None),"effect_size",0)/0.30,1.0))*32 +
                (1.0 if getattr(getattr(ins,"confidence_inputs",None),"baseline_stability","")=="stable" else 0.35)*22 +
                (1.0 if getattr(ins,"novelty_vs_prior","")=="new" else 0.2)*14
            )), 100)
            for ins in ranked
        ],
    }


# ---------------------------------------------------------------------------
# Stateful replay — simulates accumulated signal state across days
# ---------------------------------------------------------------------------

# Decay constants (mirrored from signal_registry)
_STRENGTH_INITIAL  = 60.0
_STRENGTH_FLOOR    = 25.0
_DECAY_SEEN        = {"worsening": 1.02, "stable": 0.96, "recovering": 0.90}
_DECAY_ABSENT      = 0.70
_REINFORCE_WEIGHT  = 0.30


def _sim_decay_strength(current, direction, confidence):
    decay = _DECAY_SEEN.get(direction, 0.95)
    return min(current * decay + confidence * _REINFORCE_WEIGHT, 100.0)


def run_replay_stateful(seeds=None, n: int = 20) -> List[Dict]:
    """Run sequential seeds simulating accumulated signal strength.

    Each seed represents 'day N'. Signal strengths carry over between days.
    A cluster is suppressed if its simulated strength < STRENGTH_FLOOR.
    This allows quiet days to emerge from decay without relying on the real registry.
    """
    if seeds is None:
        seeds = range(42, 42 + n)

    # Simulated signal state: {title: strength}
    signal_state: Dict[str, float] = {}
    results = []

    for seed in seeds:
        try:
            raw = run_seed(seed)
        except Exception as e:
            results.append({"seed": seed, "error": str(e), "fired": False,
                            "n_candidates": 0, "n_clusters": 0,
                            "detector_counts": {}, "clusters": [],
                            "detector_types": [], "detector_agreement": False,
                            "insight_conf_scores": [], "suppressed_by_decay": []})
            continue

        # Update strength for seen clusters
        seen_titles = {c["title"] for c in raw["clusters"]}
        suppressed  = []

        for cluster in raw["clusters"]:
            title      = cluster["title"]
            confidence = cluster["confidence_score"]
            direction  = "worsening"   # conservative assumption for simulation

            current    = signal_state.get(title, _STRENGTH_INITIAL)
            new_str    = _sim_decay_strength(current, direction, confidence)
            signal_state[title] = new_str

            if new_str < _STRENGTH_FLOOR:
                suppressed.append(title)

        # Decay absent signals
        for title in list(signal_state.keys()):
            if title not in seen_titles:
                signal_state[title] = round(signal_state[title] * _DECAY_ABSENT, 1)
                if signal_state[title] < 5.0:
                    del signal_state[title]

        # Filter clusters suppressed by decay
        active_clusters = [c for c in raw["clusters"] if c["title"] not in suppressed]
        raw["clusters"]           = active_clusters
        raw["n_clusters"]         = len(active_clusters)
        raw["fired"]              = len(active_clusters) > 0
        raw["suppressed_by_decay"] = suppressed
        raw["primary_title"]      = active_clusters[0]["title"] if active_clusters else None
        raw["primary_severity"]   = active_clusters[0]["severity"] if active_clusters else None
        raw["primary_confidence"] = active_clusters[0]["confidence_score"] if active_clusters else 0
        results.append(raw)

    return results


# ---------------------------------------------------------------------------
# Stateless replay
# ---------------------------------------------------------------------------

def run_replay(seeds=None, n: int = 20) -> List[Dict]:
    if seeds is None:
        seeds = range(42, 42 + n)
    results = []
    for seed in seeds:
        try:
            results.append(run_seed(seed))
        except Exception as e:
            results.append({"seed": seed, "error": str(e), "fired": False,
                            "n_candidates": 0, "n_clusters": 0,
                            "detector_counts": {}, "clusters": [],
                            "detector_types": [], "detector_agreement": False,
                            "insight_conf_scores": []})
    return results


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_results(results: List[Dict]) -> Dict:
    total  = len(results)
    fired  = [r for r in results if r.get("fired")]
    n_fire = len(fired)
    alert_rate = n_fire / total if total else 0.0

    det_totals = defaultdict(int)
    for r in results:
        for d, c in r.get("detector_counts", {}).items():
            det_totals[d] += c
    det_rates = {d: round(c/total, 2) for d, c in det_totals.items()}

    agree_rate    = sum(1 for r in fired if r.get("detector_agreement")) / n_fire if n_fire else 0
    disagree_rate = sum(
        1 for r in fired
        if "funnel_drop" in r.get("detector_types", [])
        and "cohort_divergence" not in r.get("detector_types", [])
    ) / n_fire if n_fire else 0

    co_occur = defaultdict(lambda: defaultdict(int))
    for r in fired:
        types = r.get("detector_types", [])
        for i, t1 in enumerate(types):
            for t2 in types[i+1:]:
                co_occur[t1][t2] += 1; co_occur[t2][t1] += 1

    primary_confs = [r["primary_confidence"] for r in fired if r.get("primary_confidence")]
    conf_high   = sum(1 for s in primary_confs if s >= 68)
    conf_med    = sum(1 for s in primary_confs if 42 <= s < 68)
    conf_low    = sum(1 for s in primary_confs if s < 42)
    conf_entropy = _entropy({"high": conf_high, "medium": conf_med, "low": conf_low})

    titles = [r["primary_title"] for r in fired if r.get("primary_title")]
    title_counts = defaultdict(int)
    for t in titles: title_counts[t] += 1
    title_dist = {t: round(c/len(titles), 2) for t, c in sorted(title_counts.items(), key=lambda x: -x[1])} if titles else {}

    urgency_dist = defaultdict(int)
    for r in fired:
        for c in r.get("clusters", []): urgency_dist[c["urgency"]] += 1

    causal_rate = sum(1 for r in fired if r.get("n_causal_links", 0) > 0) / n_fire if n_fire else 0

    suppressed_total = sum(len(r.get("suppressed_by_decay", [])) for r in results)

    all_insight_confs = []
    for r in fired: all_insight_confs.extend(r.get("insight_conf_scores", []))

    warnings = []
    if alert_rate >= 0.90:
        warnings.append(f"Alert rate is {alert_rate*100:.0f}% — very high. In production this would indicate over-triggering.")
    if _std(primary_confs) < 4.0 and primary_confs:
        warnings.append(f"Confidence std dev is {round(_std(primary_confs),1)} — scores are compressing. Consider widening uncertainty range.")
    if conf_entropy < 0.3:
        warnings.append(f"Confidence entropy {round(conf_entropy,3)} — nearly all alerts in same bucket.")
    if agree_rate >= 0.95:
        warnings.append(f"Detector agreement {agree_rate*100:.0f}% — suspiciously high.")
    if disagree_rate < 0.05:
        warnings.append(f"Detector disagreement {disagree_rate*100:.0f}% — detectors almost never conflict.")

    return {
        "total_seeds":            total,
        "fired_count":            n_fire,
        "silent_count":           total - n_fire,
        "alert_rate":             round(alert_rate, 3),
        "avg_candidates":         round(_mean([r["n_candidates"] for r in fired]), 1),
        "avg_clusters":           round(_mean([r["n_clusters"] for r in fired]), 1),
        "conf_mean":              round(_mean(primary_confs), 1),
        "conf_std":               round(_std(primary_confs), 1),
        "conf_p10":               round(_pct(primary_confs, 10), 1),
        "conf_p50":               round(_pct(primary_confs, 50), 1),
        "conf_p90":               round(_pct(primary_confs, 90), 1),
        "conf_entropy":           round(conf_entropy, 3),
        "confidence_high":        conf_high,
        "confidence_medium":      conf_med,
        "confidence_low":         conf_low,
        "insight_conf_mean":      round(_mean(all_insight_confs), 1),
        "insight_conf_std":       round(_std(all_insight_confs), 1),
        "detector_avg_per_run":   det_rates,
        "detector_agreement_rate":    round(agree_rate, 3),
        "detector_disagreement_rate": round(disagree_rate, 3),
        "detector_co_occurrence": {k: dict(v) for k, v in co_occur.items()},
        "primary_title_distribution": title_dist,
        "urgency_distribution":   dict(urgency_dist),
        "causal_link_rate":       round(causal_rate, 3),
        "suppressed_by_decay":    suppressed_total,
        "calibration_warnings":   warnings,
        "errors":                 sum(1 for r in results if "error" in r),
    }


# ---------------------------------------------------------------------------
# Streamlit panel
# ---------------------------------------------------------------------------

def render_eval_panel(n_seeds: int = 20) -> None:
    import streamlit as st

    with st.expander("Replay evaluation", expanded=False):
        st.markdown(
            f"<div style='font-size:0.85rem;color:#888;margin-bottom:0.5rem'>"
            f"Runs {n_seeds} seeds through the pipeline. "
            f"<strong>Stateful mode</strong> simulates signal decay across consecutive days."
            f"</div>",
            unsafe_allow_html=True,
        )
        mode = st.radio("Mode", ["Stateful (with decay)", "Stateless (per-seed)"],
                        horizontal=True, key="eval_mode")
        if st.button("Run evaluation", key="run_eval"):
            with st.spinner(f"Running {n_seeds} seeds..."):
                if "Stateful" in mode:
                    results = run_replay_stateful(n=n_seeds)
                else:
                    results = run_replay(n=n_seeds)
                scores = score_results(results)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Seeds run",    scores["total_seeds"])
            c2.metric("Alerts fired", f"{scores['fired_count']} ({scores['alert_rate']*100:.0f}%)")
            c3.metric("Silent runs",  scores["silent_count"])
            c4.metric("Suppressed by decay", scores.get("suppressed_by_decay", 0))

            total = scores["fired_count"] or 1
            st.markdown("**Confidence calibration**")
            st.markdown(
                f"- Distribution: High **{scores['confidence_high']}** "
                f"/ Medium **{scores['confidence_medium']}** "
                f"/ Low **{scores['confidence_low']}**\n"
                f"- Mean: **{scores['conf_mean']}** &nbsp; Std: **{scores['conf_std']}** "
                f"&nbsp; Entropy: **{scores['conf_entropy']}**\n"
                f"- p10={scores['conf_p10']} / p50={scores['conf_p50']} / p90={scores['conf_p90']}"
            )
            st.markdown("**Detector reliability**")
            st.markdown(
                f"- Agreement: **{scores['detector_agreement_rate']*100:.0f}%** &nbsp; "
                f"Disagreement: **{scores['detector_disagreement_rate']*100:.0f}%**"
            )
            for d, r in sorted(scores["detector_avg_per_run"].items(), key=lambda x: -x[1]):
                st.markdown(f"- `{d}`: {r:.2f}x/run")
            co = scores.get("detector_co_occurrence", {})
            if co:
                st.markdown("**Co-occurrence**")
                for t1, partners in co.items():
                    for t2, count in partners.items():
                        if t1 < t2: st.markdown(f"- `{t1}` + `{t2}`: **{count}** runs")
            st.markdown("**Signal consistency**")
            for title, pct in scores["primary_title_distribution"].items():
                st.markdown(f"- {title}: **{pct*100:.0f}%**")
            st.markdown(f"- Causal links: **{scores['causal_link_rate']*100:.0f}%** of alert runs")
            st.markdown("**Urgency distribution**")
            for urg, count in sorted(scores["urgency_distribution"].items()):
                st.markdown(f"- {urg}: **{count}**")
            warnings = scores.get("calibration_warnings", [])
            if warnings:
                st.markdown("**Calibration warnings**")
                for w in warnings: st.warning(w)
            else:
                st.success("No calibration warnings.")
            if scores["errors"] > 0:
                st.error(f"{scores['errors']} seed(s) errored.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seeds",    type=int, default=20)
    p.add_argument("--start",   type=int, default=42)
    p.add_argument("--stateful", action="store_true")
    args = p.parse_args()

    seeds = range(args.start, args.start + args.seeds)
    print(f"Running {'stateful' if args.stateful else 'stateless'} replay: {args.seeds} seeds...")
    results = run_replay_stateful(seeds=seeds) if args.stateful else run_replay(seeds=seeds)
    scores  = score_results(results)
    sep = "-" * 60
    print(sep)
    print("REPLAY EVALUATION REPORT")
    print(sep)
    print(f"Mode:         {'stateful (decay)' if args.stateful else 'stateless'}")
    print(f"Alert rate:   {scores['alert_rate']*100:.0f}% ({scores['fired_count']}/{scores['total_seeds']})")
    print(f"Suppressed:   {scores.get('suppressed_by_decay', 0)} clusters by decay")
    print(f"Conf mean/std/entropy: {scores['conf_mean']} / {scores['conf_std']} / {scores['conf_entropy']}")
    print(f"High/Med/Low: {scores['confidence_high']} / {scores['confidence_medium']} / {scores['confidence_low']}")
    print(f"Agree/Disagree: {scores['detector_agreement_rate']*100:.0f}% / {scores['detector_disagreement_rate']*100:.0f}%")
    for d, r in sorted(scores["detector_avg_per_run"].items(), key=lambda x: -x[1]):
        print(f"  {d}: {r:.2f}x/run")
    print("Primary titles:", scores["primary_title_distribution"])
    print("Urgency:", scores["urgency_distribution"])
    for w in scores.get("calibration_warnings", []): print(f"  ⚠ {w}")
    print(sep)