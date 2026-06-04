"""pages/calibration.py — System Calibration Console (separate from operational briefing)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from growth_copilot_mvp.replay_evaluator import run_replay, score_results
from growth_copilot_mvp.timeline_replay import run_timeline, timeline_summary
from growth_copilot_mvp.ranker import detector_weight_report
from growth_copilot_mvp.archetypes import ARCHETYPES, archetype_display_options, archetype_from_display, DEFAULT_ARCHETYPE
from growth_copilot_mvp.attention import (
    SURFACE_THRESHOLD, BACKGROUND_THRESHOLD, MAX_SURFACED_CLUSTERS,
    CONFIDENCE_WEIGHT, URGENCY_WEIGHT, PERSISTENCE_WEIGHT, AGREEMENT_WEIGHT,
)
from growth_copilot_mvp.signal_registry import (
    get_all_signals, get_resolved_signals, get_active_signals,
    registry_summary, outcome_summary,
    detector_precision_from_outcomes, record_outcome,
)
from growth_copilot_mvp.trust_engine import trust_summary

st.set_page_config(page_title="GrowthCopilot — Calibration", page_icon=":wrench:", layout="wide")

st.markdown("""
<style>
    .stButton > button[kind="primary"] {
        background-color: #1e293b !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)


st.title("System Calibration Console")

# Soft access warning — non-blocking, just sets expectations for non-technical visitors
with st.expander("⚙ Advanced configuration — who is this for?", expanded=False):
    st.markdown(
        "<div style='font-size:0.83rem;opacity:0.7;line-height:1.6;'>"
        "This console is intended for <strong>technical users and builders</strong> "
        "who want to inspect detector reliability, tune confidence weights, and review "
        "alert quality over time.<br><br>"
        "If you're here for the daily operational briefing — signal alerts, "
        "recommendations, and trend analysis — head back to the main page."
        "</div>",
        unsafe_allow_html=True,
    )
    st.page_link("pages/briefing.py", label="← Back to Daily Briefing")

st.markdown(
    "<div style='color:inherit;font-size:0.85rem'>"
    "For builders — not the daily operational briefing. "
    "Evaluates detector reliability, confidence calibration, and alert quality."
    "</div>",
    unsafe_allow_html=True,
)
st.write("")

# ---------------------------------------------------------------------------
# Registry overview
# ---------------------------------------------------------------------------

st.markdown("## Signal Registry")
summary = registry_summary()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tracked",  summary["total_tracked"])
c2.metric("Active",         summary["active"])
c3.metric("Surfaced",        summary.get("surfaced", summary["active"]))
c4.metric("Fading",          summary.get("fading", 0))
c5.metric("Resolved",        summary["resolved"])

all_signals = get_all_signals()
if all_signals:
    with st.expander("Signal registry detail", expanded=False):
        for sid, r in sorted(all_signals.items(), key=lambda x: x[1].get("first_seen",""), reverse=True):
            status    = r.get("status", "active")
            title     = r.get("title", sid)
            first     = r.get("first_seen", "")
            last      = r.get("last_seen", "")
            escl      = r.get("escalation_level", 0)
            recur     = r.get("recurrence_count", 0)
            narrative = r.get("narrative", "")
            conf_hist = r.get("confidence_history", [])
            avg_conf  = round(sum(c for _, c in conf_hist) / len(conf_hist), 1) if conf_hist else 0
            status_icon = {"worsening":"↘","improving":"📈","stabilizing":"→","escalated":"⚠️","recurring":"🔁","resolved":"✓","new":"🆕"}.get(status, "")
            strength = r.get("signal_strength", 0)
            strength_bar = "█" * int(strength / 5) + "░" * (20 - int(strength / 5))
            surfaced = r.get("is_surfaced", True)
            fade_note = " 🌫️ fading" if not surfaced else ""
            st.markdown(
                f"**{status_icon} {title}** &nbsp; `{status}`{fade_note} &nbsp; "
                f"First: {first} &nbsp; Last: {last} &nbsp; "
                f"Strength: {strength:.0f}/100 &nbsp; Avg conf: {avg_conf} &nbsp; Recurred: {recur}x"
            )
            if narrative:
                st.markdown(f"<div style='font-size:0.8rem;color:inherit;margin-left:1rem'>{narrative}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Detector weights
# ---------------------------------------------------------------------------

st.markdown("## Detector Weights")
st.markdown(
    "<div style='font-size:0.85rem;color:inherit;margin-bottom:0.5rem'>"
    "Current reliability weights applied during ranking. "
    "Will be replaced by empirical precision rates once outcome data accumulates."
    "</div>",
    unsafe_allow_html=True,
)
for det, info in detector_weight_report().items():
    color = "#2e7d32" if info["weight"] > 1.0 else "#f57c00" if info["weight"] < 1.0 else "#555"
    st.markdown(
        f"<div style='padding:0.4rem 0.8rem;border-left:3px solid {color};"
        f"margin-bottom:0.3rem;background:transparent;'>"
        f"<strong>`{det}`</strong> &nbsp; weight: <strong>{info['weight']}x</strong><br>"
        f"<span style='font-size:0.82rem;color:inherit;'>{info['note']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Attention architecture
# ---------------------------------------------------------------------------

st.markdown("## Attention Architecture")
st.markdown(
    "<div style='font-size:0.85rem;color:inherit;margin-bottom:0.5rem'>"
    "Three-tier system: Surfaced (briefing) → Background (tracked) → Ephemeral (discarded)."
    "</div>",
    unsafe_allow_html=True,
)
a1, a2, a3 = st.columns(3)
a1.metric("Surface threshold",    f"{SURFACE_THRESHOLD}")
a2.metric("Background threshold", f"{BACKGROUND_THRESHOLD}")
a3.metric("Max surfaced/run",     MAX_SURFACED_CLUSTERS)

st.markdown("**Surface score weights**")
st.markdown(
    f"- Confidence: **{CONFIDENCE_WEIGHT*100:.0f}%** &nbsp; "
    f"Urgency: **{URGENCY_WEIGHT*100:.0f}%** &nbsp; "
    f"Persistence: **{PERSISTENCE_WEIGHT*100:.0f}%** &nbsp; "
    f"Detector agreement: **{AGREEMENT_WEIGHT*100:.0f}%**"
)

# Show background signals from current registry
active = get_active_signals()
bg_signals = [r for r in active if not r.get("is_surfaced", True)]
if bg_signals:
    st.markdown("**Currently in background (below surface threshold):**")
    for r in bg_signals:
        st.markdown(
            f"<div style='font-size:0.82rem;color:inherit;padding:0.3rem 0.6rem;"
            f"border-left:2px solid #ccc;margin-bottom:0.2rem;'>"
            f"{r.get('title','')} — strength {r.get('signal_strength',0):.0f}/100 "
            f"— {r.get('narrative','')}"
            f"</div>",
            unsafe_allow_html=True,
        )
else:
    st.markdown("<div style='font-size:0.82rem;color:inherit;'>No background signals currently tracked.</div>",
                unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Outcome tracking
# ---------------------------------------------------------------------------

st.markdown("## Outcome Tracking")
o_sum = outcome_summary()
if o_sum.get("total_outcomes", 0) == 0:
    st.info("No outcomes recorded yet. Use the Quick feedback widget in the daily briefing.")
else:
    oc1, oc2, oc3, oc4 = st.columns(4)
    oc1.metric("Outcomes",  o_sum["total_outcomes"])
    tp = o_sum.get("signal_real_rate")
    oc2.metric("Signal real rate",   f"{tp*100:.0f}%" if tp is not None else "—")
    ru = o_sum.get("recommendation_useful_rate")
    oc3.metric("Rec. useful rate",   f"{ru*100:.0f}%" if ru is not None else "—")
    oc4.metric("Avg resolution days", o_sum.get("avg_time_to_resolution_days") or "—")
    col_a, col_b = st.columns(2)
    with col_a:
        fp = o_sum.get("false_positive_rate")
        if fp is not None: st.metric("False positive rate", f"{fp*100:.0f}%")
        ig = o_sum.get("ignored_rate")
        if ig is not None: st.metric("Ignored rate", f"{ig*100:.0f}%")
    with col_b:
        if o_sum.get("action_distribution"):
            st.markdown("**Actions taken**")
            for a, c in o_sum["action_distribution"].items():
                st.markdown(f"- {a}: **{c}**")

det_prec = detector_precision_from_outcomes()
if det_prec:
    st.markdown("### Empirical detector precision")
    for det, info in det_prec.items():
        prec  = info["precision"]
        n     = info["n_samples"]
        color = "#2e7d32" if (prec or 0) >= 0.8 else "#f57c00" if (prec or 0) >= 0.6 else "#c62828"
        note  = "" if info["reliable"] else f" ({info['min_for_reliable']-n} more needed)"
        st.markdown(f"<div style='padding:0.3rem 0.8rem;border-left:3px solid {color};margin-bottom:0.3rem;background:transparent;font-size:0.85rem;'>`{det}` — precision: <strong>{(prec or 0)*100:.0f}%</strong> (n={n}{note})</div>", unsafe_allow_html=True)

st.markdown("### Signal trust status")
all_sigs_trust = get_all_signals()
if all_sigs_trust:
    for sid, r in all_sigs_trust.items():
        ts = trust_summary(r, o_sum)
        title = r.get("title", sid)
        ignored = r.get("ignored_count", 0)
        trust_level = ts.get("trust_level", "establishing")
        color = {"high": "#2e7d32", "moderate": "#f57c00", "low": "#c62828", "establishing": "#888"}.get(trust_level, "#888")
        notes_str = " · ".join(ts.get("notes", [])) if ts.get("notes") else "No trust signals yet"
        st.markdown(f"<div style='padding:0.4rem 0.8rem;border-left:3px solid {color};margin-bottom:0.3rem;background:transparent;font-size:0.85rem;'><strong>{title}</strong> — trust: <strong style='color:{color}'>{trust_level}</strong> &nbsp; ignored: {ignored}x<br><span style='color:inherit;font-size:0.8rem;'>{notes_str}</span></div>", unsafe_allow_html=True)

st.markdown("### Log outcome manually")
all_sigs_log = get_all_signals()
if all_sigs_log:
    sig_titles = [r["title"] for r in all_sigs_log.values()]
    selected   = st.selectbox("Select signal", sig_titles, key="outcome_sig")
    if selected:
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            signal_real = st.selectbox("Signal was real?",        ["—","Yes","No","Unsure"],                         key="o_sr")
            sev_acc     = st.selectbox("Severity accurate?",      ["—","Yes","No"],                                  key="o_sa")
        with mc2:
            rec_follow  = st.selectbox("Recommendation followed?",["—","Yes","No"],                                  key="o_rf")
            rec_useful  = st.selectbox("Recommendation useful?",  ["—","Yes","Somewhat","No"],                       key="o_ru")
            action      = st.selectbox("Action taken",            ["—","none","investigating","mitigated","resolved"],key="o_at")
        with mc3:
            self_res    = st.selectbox("Self-resolved?",          ["—","Yes","No"],                                  key="o_selfres")
            impact      = st.selectbox("Business impact",         ["—","none","low","medium","high"],                key="o_impact")
            notes_field = st.text_input("Notes (optional)",                                                          key="o_notes")
        if st.button("Save outcome", type="primary", key="save_outcome"):
            if signal_real == "—" and action == "—" and rec_useful == "—":
                st.toast("Select at least one option before saving.", icon="⚠️")
                st.stop()
            kwargs = {}
            if signal_real == "Yes":         kwargs["signal_real"] = True
            elif signal_real == "No":        kwargs["signal_real"] = False
            if sev_acc == "Yes":             kwargs["severity_accurate"] = True
            elif sev_acc == "No":            kwargs["severity_accurate"] = False
            if rec_follow == "Yes":          kwargs["recommendation_followed"] = True
            elif rec_follow == "No":         kwargs["recommendation_followed"] = False
            if rec_useful in ("Yes","Somewhat"): kwargs["recommendation_useful"] = True
            elif rec_useful == "No":         kwargs["recommendation_useful"] = False
            if action != "—":               kwargs["action_taken"] = action
            if self_res == "Yes":            kwargs["self_resolved"] = True
            elif self_res == "No":           kwargs["self_resolved"] = False
            if impact != "—":               kwargs["business_impact"] = impact
            if notes_field:                  kwargs["operator_feedback"] = notes_field
            record_outcome(selected, **kwargs)
            st.toast("Outcome recorded.", icon="✓")
            st.rerun()

# ---------------------------------------------------------------------------
# Timeline replay
# ---------------------------------------------------------------------------

st.markdown("## Timeline Replay")
st.markdown(
    "<div style='font-size:0.85rem;color:inherit;margin-bottom:0.8rem;'>"
    "Simulates N consecutive days. Watch signals emerge, escalate, and resolve over time."
    "</div>", unsafe_allow_html=True,
)

tl_c1, tl_c2, tl_c3 = st.columns([1, 1, 2])
tl_days    = tl_c1.number_input("Days", min_value=7, max_value=60, value=30, step=7, key="tl_days")
tl_seed    = tl_c2.number_input("Start seed", min_value=0, value=42, step=1, key="tl_start_seed")
display_opts = archetype_display_options()
tl_arch_disp = tl_c3.selectbox("Archetype", display_opts, key="tl_arch")
tl_arch_key  = archetype_from_display(tl_arch_disp)

if st.button("Run timeline replay", type="primary", key="run_timeline_btn"):
    with st.spinner(f"Simulating {tl_days} days..."):
        tl_data = run_timeline(n_days=tl_days, start_seed=tl_seed, archetype_key=tl_arch_key)
        tl_sum  = timeline_summary(tl_data)
    st.session_state["tl_data"] = tl_data
    st.session_state["tl_sum"]  = tl_sum
    st.session_state["tl_day"]  = 0

tl_data = st.session_state.get("tl_data")
tl_sum  = st.session_state.get("tl_sum")

if tl_data and tl_sum:
    tm1, tm2, tm3, tm4 = st.columns(4)
    tm1.metric("Alert days",     f"{tl_sum['alert_days']}/{tl_sum['total_days']}")
    tm2.metric("Quiet days",     tl_sum["quiet_days"])
    tm3.metric("Escalations",    tl_sum["total_escalated"])
    tm4.metric("Avg confidence", tl_sum["conf_mean"])

    if tl_sum["primary_signals"]:
        st.markdown("**Signal distribution**")
        for title, count in sorted(tl_sum["primary_signals"].items(), key=lambda x: -x[1]):
            st.markdown(f"- {title}: **{count}** days ({count/tl_sum['total_days']*100:.0f}%)")

    if tl_sum.get("urgency_dist"):
        st.markdown("**Urgency distribution**")
        for urg, count in sorted(tl_sum["urgency_dist"].items()):
            urg_label = urg.replace("_", " ").title()
            st.markdown(f"- {urg_label}: **{count}**")

    st.markdown("### Day-by-day view")
    tl_day_idx = st.slider("Select day", 0, len(tl_data)-1, st.session_state.get("tl_day", 0), key="tl_slider")
    st.session_state["tl_day"] = tl_day_idx
    snap = tl_data[tl_day_idx]

    SCENARIO_LABELS = {"A":"Full regression","B":"Mild drop","C":"DAU spike","D":"Quiet day",
                       "E":"Recovery","F":"False positive","G":"Seasonal","H":"Rollout","I":"Attribution","J":"Conflict"}
    SEV_EMOJI  = {"CRITICAL":"🔴","WATCH":"🟡","OPPORTUNITY":"🟢"}
    URG_COLOR  = {"immediate":"#c62828","this_week":"#f57c00","monitor":"#388e3c",
                  "wait_and_observe":"#1565c0","insufficient_evidence":"#888"}

    st.markdown(
        f"<div style='padding:0.6rem 1rem;background:transparent;border-radius:6px;"
        f"border-left:4px solid #1565c0;margin-bottom:0.5rem;'>"
        f"<strong>{snap['date']}</strong> &nbsp; Seed {snap['seed']} &nbsp; "
        f"Scenario: <strong>{SCENARIO_LABELS.get(snap['scenario'], snap['scenario'])}</strong>"
        f"</div>", unsafe_allow_html=True,
    )

    if snap.get("error"):
        st.error(f"Pipeline error: {snap['error']}")
    elif not snap["fired"]:
        st.markdown(
            "<div style='padding:0.5rem 0.8rem;border-left:3px solid #388e3c;"
            "background:#f9fdf9;font-size:0.85rem;color:#2e7d32;'>"
            "✓ Quiet day — no signals above threshold</div>", unsafe_allow_html=True,
        )
    else:
        for c in snap["clusters"]:
            urg_color = URG_COLOR.get(c["urgency"], "#555")
            st.markdown(
                f"<div style='padding:0.5rem 0.8rem;background:transparent;border-radius:5px;"
                f"border-left:3px solid {urg_color};margin-bottom:0.3rem;'>"
                f"{SEV_EMOJI.get(c['severity'],'')} <strong>{c['title']}</strong> &nbsp;"
                f"<span style='color:inherit;font-size:0.8rem;'>"
                f"Confidence: {c['confidence']} ({c['conf_label']}) &nbsp; "
                f"Urgency: <span style='color:{urg_color};'>{c['urgency']}</span> &nbsp; "
                f"Direction: {c['direction']}</span></div>", unsafe_allow_html=True,
            )

    for badge_list, icon, color, label in [
        (snap.get("new_signals",[]),        "🆕", "#1565c0", "New"),
        (snap.get("escalated_signals",[]),  "⚠️", "#c62828", "Escalated"),
        (snap.get("resolved_signals",[]),   "✓",  "#388e3c", "Resolved"),
    ]:
        if badge_list:
            st.markdown(f"<div style='font-size:0.8rem;color:{color};margin-top:0.2rem;'>{icon} {label}: {', '.join(badge_list)}</div>", unsafe_allow_html=True)

    if snap.get("signal_states"):
        st.markdown("**Signal strengths**")
        for title, state in snap["signal_states"].items():
            strength = state.get("strength", 0)
            bar_w    = int(strength / 100 * 120)
            color    = "#2e7d32" if strength >= 60 else "#f57c00" if strength >= 25 else "#ccc"
            st.markdown(
                f"<div style='font-size:0.8rem;margin-bottom:0.2rem;'>"
                f"<span style='color:inherit;'>{title}</span> "
                f"<span style='color:inherit;font-size:0.75rem;'>{state['status']} · {state['days_active']}d</span><br>"
                f"<div style='height:4px;background:#eee;border-radius:2px;margin-top:2px;'>"
                f"<div style='width:{bar_w}px;max-width:120px;height:100%;background:{color};border-radius:2px;'></div></div></div>",
                unsafe_allow_html=True,
            )

st.markdown("---")

st.markdown("## Replay Evaluator")
st.markdown(
    "<div style='font-size:0.85rem;color:inherit;margin-bottom:0.8rem'>"
    "Runs N seeds through the full pipeline to score alert quality, "
    "confidence calibration, and detector reliability."
    "</div>",
    unsafe_allow_html=True,
)

col_n, col_start, col_run = st.columns([1, 1, 2])
n_seeds    = col_n.number_input("Seeds to run", min_value=5, max_value=100, value=20, step=5, key="replay_n_seeds")
start_seed = col_start.number_input("Start seed", min_value=0, value=42, step=1, key="replay_start_seed")

if col_run.button("Run evaluation", type="primary"):
    with st.spinner(f"Running {n_seeds} seeds..."):
        results = run_replay(seeds=range(start_seed, start_seed + n_seeds))
        scores  = score_results(results)
    st.session_state["eval_scores"]  = scores
    st.session_state["eval_results"] = results

scores = st.session_state.get("eval_scores")
if scores:
    total = scores["fired_count"] or 1

    st.markdown("### Alert volume")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Seeds run",    scores["total_seeds"])
    v2.metric("Alerts fired", f"{scores['fired_count']} ({scores['alert_rate']*100:.0f}%)")
    v3.metric("Silent runs",  scores["silent_count"])
    v4.metric("Avg clusters/run", scores["avg_clusters"])

    st.markdown("### Confidence calibration")
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Mean score",  scores["conf_mean"])
    cc2.metric("Std dev",     scores["conf_std"])
    cc3.metric("Entropy",     scores["conf_entropy"])
    cc4.metric("p10 / p50 / p90", f"{scores['conf_p10']} / {scores['conf_p50']} / {scores['conf_p90']}")

    st.markdown(
        f"- High ≥68: **{scores['confidence_high']}** ({scores['confidence_high']/total*100:.0f}%)"
        f"  &nbsp; Medium 42-67: **{scores['confidence_medium']}** ({scores['confidence_medium']/total*100:.0f}%)"
        f"  &nbsp; Low <42: **{scores['confidence_low']}** ({scores['confidence_low']/total*100:.0f}%)"
    )

    st.markdown("### Detector reliability")
    dr1, dr2 = st.columns(2)
    dr1.metric("Agreement rate",     f"{scores['detector_agreement_rate']*100:.0f}%")
    dr2.metric("Disagreement rate",  f"{scores['detector_disagreement_rate']*100:.0f}%")

    st.markdown("**Firing rates (avg per run)**")
    for d, r in sorted(scores["detector_avg_per_run"].items(), key=lambda x: -x[1]):
        st.markdown(f"- `{d}`: {r:.2f}x")

    co = scores.get("detector_co_occurrence", {})
    if co:
        st.markdown("**Co-occurrence (times fired together)**")
        for t1, partners in co.items():
            for t2, count in partners.items():
                if t1 < t2:
                    st.markdown(f"- `{t1}` + `{t2}`: {count}x")
