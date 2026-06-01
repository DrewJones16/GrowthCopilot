import os, sys
from datetime import datetime, date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from growth_copilot_mvp.aggregations import funnel_step_table, daily_installs, source_funnel_completion
from growth_copilot_mvp.detectors import detect_funnel_drops, detect_source_divergence, detect_dau_anomaly
from growth_copilot_mvp.ranker import rank, detector_weight_report
from growth_copilot_mvp.insight_clusterer import cluster_insights
from growth_copilot_mvp.trend_memory import attach_trend
from growth_copilot_mvp.causal_engine import find_causal_links, primary_hypothesis
from growth_copilot_mvp.decision_engine import make_decision, get_editorial_observation
from growth_copilot_mvp.attention import classify_clusters, attention_report, background_summary
from growth_copilot_mvp.signal_registry import (
    update_signal, check_resolutions,
    get_recently_resolved, registry_summary, outcome_summary,
    record_outcome, increment_ignored,
    detector_precision_from_outcomes,
)
from growth_copilot_mvp.trust_engine import compute_trust_adjustments, trust_summary
from growth_copilot_mvp.narrative_memory import get_narrative_hints, render_narrative_memory
from growth_copilot_mvp.demo_flow import render_demo_controls, get_demo_seed, DEMO_STEP_COUNT
from growth_copilot_mvp.signal_registry import get_all_signals
from growth_copilot_mvp.archetypes import (
    ARCHETYPES, archetype_display_options, archetype_from_display, DEFAULT_ARCHETYPE,
)

st.set_page_config(
    page_title="GrowthCopilot",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styles — clean operator console aesthetic
# ---------------------------------------------------------------------------
st.markdown("""
<style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    .stMarkdown, .stText, button, input, select, textarea, p, div, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 4rem !important; max-width: 720px !important; }
    h1 { font-size: 1.35rem !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    h2 { font-size: 1.05rem !important; font-weight: 600 !important; letter-spacing: -0.01em; margin-top: 1.6rem !important; }
    h3 { font-size: 0.93rem !important; font-weight: 600 !important; }
    h4 { font-size: 0.85rem !important; font-weight: 600 !important; }
    hr { border: none !important; border-top: 1px solid rgba(128,128,128,0.1) !important; margin: 1.8rem 0 !important; }
    [data-testid="stExpander"] { border: 1px solid rgba(128,128,128,0.1) !important; border-radius: 10px !important; margin-bottom: 0.6rem !important; overflow: hidden !important; box-shadow: none !important; }
    [data-testid="stExpander"]:hover { border-color: rgba(128,128,128,0.18) !important; }
    .streamlit-expanderHeader { font-size: 0.78rem !important; font-weight: 500 !important; opacity: 0.6 !important; padding: 0.6rem 0.85rem !important; background: transparent !important; }
    .streamlit-expanderContent { padding: 0.2rem 0.85rem 0.85rem !important; }
    [data-testid="stExpanderToggleIcon"] { display: none !important; }
    [data-testid="stExpander"] details summary { padding-left: 0.85rem !important; }
    /* Remove gap/indent in expander headers */
    [data-testid="stExpander"] summary { padding-left: 0.85rem !important; }
    [data-testid="stExpander"] summary svg { display: none !important; }
    [data-testid="stExpanderToggleIcon"] { display: none !important; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em; opacity: 0.4 !important; }
    [data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 600 !important; letter-spacing: -0.02em; }
    .stButton > button { font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; font-weight: 500 !important; border-radius: 8px !important; transition: all 0.15s ease !important; }
    .stButton > button[kind="primary"] { background-color: #1e293b !important; color: white !important; border: none !important; font-weight: 600 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.1) !important; display: block !important; }
    section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1.1rem !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"][aria-expanded="false"] { width: 21rem !important; transform: translateX(0) !important; }
    [data-testid="stPageLink"] { border-radius: 6px !important; padding: 7px 9px !important; margin: 1px 0 !important; font-size: 0.83rem !important; }
    [data-testid="stPageLink"] p { font-size: 0.83rem !important; }
    .stRadio > div { gap: 0.2rem !important; }
    .stRadio label { font-size: 0.79rem !important; }
    .stSelectbox label { font-size: 0.72rem !important; opacity: 0.5 !important; }
    .stToggle label { font-size: 0.8rem !important; }
    .stCaption { font-size: 0.68rem !important; opacity: 0.38 !important; }
    @keyframes pulse-dot { 0%, 100% { box-shadow: 0 0 0 0 rgba(217,79,79,0.4); } 55% { box-shadow: 0 0 0 5px rgba(217,79,79,0); } }
    .dot-pulse { animation: pulse-dot 2.4s ease-in-out infinite; }
    [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    [data-testid="stIconMaterial"] { display: none !important; }
    .streamlit-expanderHeader { padding-left: 0.85rem !important; }

    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        .block-container { color-scheme: dark; }
    }
    /* Use currentColor for text so it adapts to dark/light automatically */
    .stMarkdown p { color: inherit !important; }
    .stMarkdown div { color: inherit !important; }

    /* Fix scroll capture on Streamlit Cloud */
    html { overflow: auto !important; }
    .main { overflow: auto !important; }

</style>
""", unsafe_allow_html=True)

if "seed" not in st.session_state:
    st.session_state.seed = 42
if "archetype_key" not in st.session_state:
    st.session_state.archetype_key = DEFAULT_ARCHETYPE
if "demo_step" not in st.session_state:
    st.session_state.demo_step = 0
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False


def run_pipeline(seed, archetype_key=DEFAULT_ARCHETYPE):
    from growth_copilot_mvp.data_connector import get_connector
    archetype    = ARCHETYPES[archetype_key]
    # Use real data if user has connected, else synthetic
    _user_events = st.session_state.get("user_events")
    if _user_events:
        from growth_copilot_mvp.data_connector import StreamlitUploadConnector
        connector = StreamlitUploadConnector(_user_events)
    else:
        connector = get_connector("synthetic", seed=seed, archetype=archetype)
    events = connector.fetch_events()
    dq     = connector.data_quality_report()
    funnel       = funnel_step_table(events)
    installs     = daily_installs(events)
    completion   = source_funnel_completion(events)
    app_dau      = int(sum(installs.values()) / len(installs))
    fc, _        = detect_funnel_drops(funnel, app_dau)
    sc, _        = detect_source_divergence(completion, app_dau)
    dc, _        = detect_dau_anomaly(installs, app_dau)
    all_c        = fc + sc + dc
    for ins in all_c:
        attach_trend(ins, funnel_table=funnel, source_completion=completion,
                     daily_installs_map=installs)
    ranked       = rank(all_c)
    causal_links = find_causal_links(ranked)
    return ranked, app_dau, len(events), causal_links, dq


def update_registry(clustered):
    records       = {}
    active_titles = [c["title"] for c in clustered]
    for cluster in clustered:
        trend_dirs  = [getattr(ins, "trend", {}).get("direction", "stable")
                       for ins in cluster["insights"]]
        direction   = ("worsening" if "worsening" in trend_dirs
                       else "recovering" if "recovering" in trend_dirs else "stable")
        days_active = max(
            (getattr(ins, "trend", {}).get("days_active", 1) for ins in cluster["insights"]),
            default=1,
        )
        record = update_signal(
            cluster_title    = cluster["title"],
            severity         = cluster["severity"],
            direction        = direction,
            confidence_score = cluster["confidence"]["score"],
            days_active      = days_active,
        )
        records[cluster["title"]] = record
    check_resolutions(active_titles)
    return records


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEV_LABEL  = {"CRITICAL": "Critical", "WATCH": "Watch", "OPPORTUNITY": "Opportunity"}
SEV_EMOJI  = {"CRITICAL": "🔴", "WATCH": "🟡", "OPPORTUNITY": "🟢"}
CONF_DOTS  = {"High": "●●●", "Medium": "●●○", "Low": "●○○"}
DIR_ARROW  = {"worsening": "↘", "recovering": "↗", "stable": "→"}
FACTOR_LBL = {
    "sample_size": "Sample size", "effect_size": "Effect size",
    "baseline_stability": "Baseline stability", "novelty": "Signal novelty",
    "detector_agreement": "Detector agreement",
}
STATUS_COLOR = {
    "new": "#1565c0", "active": "#555", "worsening": "#c62828",
    "improving": "#2e7d32", "stabilizing": "#f57c00",
    "escalated": "#c62828", "recurring": "#6a1b9a", "resolved": "#388e3c",
}
STATUS_EMOJI = {
    "new": "🆕 ", "active": "", "worsening": "↘ ", "improving": "📈 ",
    "stabilizing": "→ ", "escalated": "⚠️ ", "recurring": "🔁 ", "resolved": "✓ ",
}
URG_COLOR = {
    "immediate": "#c62828", "this_week": "#f57c00",
    "monitor": "#0369a1", "wait_and_observe": "#64748b",
    "insufficient_evidence": "#888",
}


def _conf_bar(score: float, width: int = 72) -> str:
    pct   = int(round(score * 100))
    color = "#1976d2" if score >= 0.7 else "#f57c00" if score >= 0.45 else "#9e9e9e"
    return (
        f"<div style='display:flex;align-items:center;gap:0.5rem;margin:0.15rem 0;'>"
        f"<div style='flex:1;height:6px;background:#eef0f3;border-radius:3px;overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;background:{color};border-radius:3px;"
        f"transition:width 0.3s ease;'></div></div>"
        f"<span style='font-size:0.75rem;color:inherit;min-width:2.2rem;text-align:right;'>{pct}%</span>"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def render_posture(surfaced, background, recently_resolved):
    """Compact editorial posture card."""
    dirs = []
    sevs = []
    for c in surfaced:
        sevs.append(c["severity"])
        for ins in c["insights"]:
            dirs.append(getattr(ins, "trend", {}).get("direction", "stable"))

    if not surfaced:
        label, color = "All clear", "#2e7d32"
    elif "CRITICAL" in sevs and "worsening" in dirs:
        label, color = "Needs attention", "#c62828"
    elif "CRITICAL" in sevs or "worsening" in dirs:
        label, color = "Monitoring active", "#f57c00"
    elif "recovering" in dirs:
        label, color = "Improving", "#1565c0"
    else:
        label, color = "Stable", "#2e7d32"

    parts = []
    for c in surfaced:
        cdirs = [getattr(i, "trend", {}).get("direction", "stable") for i in c["insights"]]
        d     = "worsening" if "worsening" in cdirs else "recovering" if "recovering" in cdirs else "stable"
        days  = max((getattr(i, "trend", {}).get("days_active", 1) for i in c["insights"]), default=1)
        if c["severity"] == "CRITICAL" and d == "worsening":
            parts.append(f"<strong>{c['title']}</strong> is worsening.")
        elif c["severity"] == "CRITICAL" and d == "recovering":
            parts.append(f"<strong>{c['title']}</strong> is recovering — de-escalating.")
        elif d == "recovering":
            parts.append(f"<strong>{c['title']}</strong> is improving.")
        elif d == "stable" and days >= 7:
            parts.append(f"<strong>{c['title']}</strong> persisting, {days}d — no escalation.")
        else:
            parts.append(f"<strong>{c['title']}</strong> active.")
    if background:
        parts.append(f"{len(background)} signal{'s' if len(background)!=1 else ''} tracked silently below threshold.")
    # Only show resolved signals if there are also active signals (avoid contradictory "All clear + resolved")
    if recently_resolved and surfaced:
        _res_date = recently_resolved[0].get('resolution_date')
        if not _res_date or str(_res_date) == 'None':
            _res_date = 'recently'
        parts.append(f"<strong>{recently_resolved[0]['title']}</strong> resolved {_res_date}.")

    desc = " ".join(parts) if parts else "No active signals."

    st.markdown(
        f"<div style='display:flex;align-items:flex-start;gap:0.5rem;"
        f"padding-bottom:0.9rem;margin-bottom:1rem;"
        f"border-bottom:1px solid rgba(128,128,128,0.12);'>"
        f"<div style='width:6px;height:6px;border-radius:50%;background:{color};"
        f"flex-shrink:0;margin-top:0.35rem;'></div>"
        f"<div><span style='font-size:0.82rem;font-weight:600;color:{color};'>{label}</span>"
        f"<span style='font-size:0.8rem;opacity:0.3;'> &nbsp;·&nbsp; </span>"
        f"<span style='font-size:0.8rem;opacity:0.45;'>{desc}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _pill(text, bg, color, border=None):
    b = f"border:1px solid {border};" if border else ""
    return (f"<span style='display:inline-block;background:{bg};color:{color};{b}"
            f"font-size:0.67rem;font-weight:600;padding:2px 8px;border-radius:4px;"
            f"letter-spacing:0.025em;margin-right:5px;margin-bottom:3px;"
            f"vertical-align:middle;'>{text}</span>")

def _pill_critical(t): return _pill(t, "rgba(217,79,79,0.12)",   "#d94f4f", "rgba(217,79,79,0.22)")
def _pill_warning(t):  return _pill(t, "rgba(192,112,0,0.1)",    "#c07000", "rgba(192,112,0,0.2)")
def _pill_info(t):     return _pill(t, "rgba(74,111,187,0.1)",   "#4a6fbb", "rgba(74,111,187,0.2)")
def _pill_neutral(t):  return _pill(t, "rgba(128,128,128,0.08)", "#888",    "rgba(128,128,128,0.15)")
def _pill_success(t):  return _pill(t, "rgba(22,163,74,0.1)",    "#16a34a", "rgba(22,163,74,0.2)")

def _sev_dot(sev, size=8):
    cfg = {"CRITICAL": ("#d94f4f", True), "WATCH": ("#c07000", False), "OPPORTUNITY": ("#16a34a", False)}
    color, pulse = cfg.get(sev, ("#888", False))
    cls = ' class="dot-pulse"' if pulse else ""
    return (f"<span{cls} style='display:inline-block;width:{size}px;height:{size}px;"
            f"border-radius:50%;background:{color};flex-shrink:0;'></span>")

def render_signal_meta(conf, record, days_active, momentum_dir, momentum_days):
    """Status pills + confidence meta."""
    status    = record.get("status", "active") if record else "active"
    escl      = record.get("escalation_level", 0) if record else 0
    recur     = record.get("recurrence_count", 0) if record else 0
    peak_escl = record.get("peak_escalation_level", 0) if record else 0
    arrow     = DIR_ARROW.get(momentum_dir, "→")

    pills = []
    dir_fns = {
        "worsening":  lambda: _pill_critical(f"↘ Worsening · {days_active}d"),
        "recovering": lambda: _pill_success(f"↗ Recovering · {days_active}d"),
        "stable":     lambda: _pill_neutral(f"→ Stable · {days_active}d"),
    }
    pills.append(dir_fns.get(momentum_dir, dir_fns["stable"])())
    # Only show Escalated badge if currently worsening or recently escalated (last 3 direction entries)
    if escl >= 1:
        _show_escl = momentum_dir == "worsening"
        if not _show_escl:
            _dir_hist = record.get("direction_history", []) if record else []
            _recent_dirs = [d for _, d in _dir_hist[-3:]] if _dir_hist else []
            _show_escl = "worsening" in _recent_dirs
        if _show_escl:
            if escl >= 2: pills.append(_pill_critical("Escalated"))
            else:         pills.append(_pill_warning("Escalated"))
    if recur > 0:   pills.append(_pill_info(f"×{recur + 1}"))
    conf_fns = {"High": _pill_success, "Medium": _pill_warning, "Low": _pill_critical}
    pills.append(conf_fns.get(conf["label"], _pill_neutral)(f"{conf['label']} {conf['score']}"))
    st.markdown(
        f"<div style='margin-bottom:0.5rem;line-height:1.9;'>{'  '.join(pills)}</div>",
        unsafe_allow_html=True,
    )


def render_narrative(record):
    """Compact context block — only shows when there's something meaningful."""
    if not record or record.get("is_new_today", True): return
    dir_hist  = record.get("direction_history", [])
    conf_hist = record.get("confidence_history", [])
    if len(dir_hist) < 2: return

    lines = []
    yd, td = (dir_hist[-2][1] if len(dir_hist)>=2 else None), (dir_hist[-1][1] if dir_hist else None)
    yc, tc = (conf_hist[-2][1] if len(conf_hist)>=2 else None), (conf_hist[-1][1] if conf_hist else None)
    recur  = record.get("recurrence_count", 0)
    peak   = record.get("peak_escalation_level", 0)
    status = record.get("status", "active")

    if yd and td and yd != td:
        if td == "recovering" and yd == "worsening":   lines.append("Shifted from worsening to recovering since yesterday.")
        elif td == "worsening" and yd in ("stable","recovering"): lines.append("Deteriorated overnight — was stable yesterday.")
        elif td == "stable" and yd == "worsening":     lines.append("Worsening trend has paused.")
    if recur > 0: lines.append(f"Recurred {recur+1}x total.")
    if peak >= 2: lines.append("Previously reached critical escalation.")
    elif peak == 1 and status not in ("escalated","worsening"): lines.append("Was escalated — now de-escalating.")
    if yc and tc and abs(tc-yc) >= 8:
        lines.append(f"Confidence {'strengthened' if tc>yc else 'weakened'} ({yc} → {tc}).")

    if lines:
        st.markdown(
            "<div style='font-size:0.79rem;opacity:0.5;line-height:1.5;"
            "margin:0.1rem 0 0.45rem;'>"
            + " ".join(lines) + "</div>",
            unsafe_allow_html=True,
        )


def render_why_surfaced(cluster, decision, inside_expander=False):
    from growth_copilot_mvp.attention import (
        CONFIDENCE_WEIGHT, URGENCY_WEIGHT, PERSISTENCE_WEIGHT, AGREEMENT_WEIGHT,
        URGENCY_SCORES, _persistence_score,
    )
    conf        = cluster.get("confidence", {})
    det_agree   = 1.0 if conf.get("detector_agreement") else 0.0
    urg_score   = URGENCY_SCORES.get(decision.get("urgency","monitor"), 0.20)
    insights    = cluster.get("insights", [])
    days_active = max((getattr(i,"trend",{}).get("days_active",1) for i in insights), default=1)
    total_score = cluster.get("surface_score", 0)

    pts = {
        "Confidence":        round(conf.get("score",50)/100 * CONFIDENCE_WEIGHT  * 100, 1),
        "Urgency":           round(urg_score               * URGENCY_WEIGHT      * 100, 1),
        "Persistence":       round(_persistence_score(days_active) * PERSISTENCE_WEIGHT * 100, 1),
        "Detector agreement":round(det_agree               * AGREEMENT_WEIGHT    * 100, 1),
    }
    urgency_clean = decision.get("urgency","monitor").replace("_"," ").title()
    rows_why = [
        ("Confidence",        f"{conf.get('score',50)}/100",       pts["Confidence"]),
        ("Urgency",           urgency_clean,                        pts["Urgency"]),
        ("Persistence",       f"{days_active}d active",             pts["Persistence"]),
        ("Detector agreement","2+ detectors" if det_agree else "Single detector", pts["Detector agreement"]),
    ]

    def _why_table():
        st.markdown(
            "<div style='display:grid;grid-template-columns:1fr 1fr auto;"
            "gap:0.4rem 1rem;padding-bottom:0.35rem;margin-bottom:0.3rem;"
            "border-bottom:1px solid rgba(128,128,128,0.12);'>"
            "<span style='font-size:0.6rem;font-weight:600;opacity:0.4;text-transform:uppercase;letter-spacing:0.07em;'>Factor</span>"
            "<span style='font-size:0.6rem;font-weight:600;opacity:0.4;text-transform:uppercase;letter-spacing:0.07em;'>Value</span>"
            "<span style='font-size:0.6rem;font-weight:600;opacity:0.4;text-transform:uppercase;letter-spacing:0.07em;text-align:right;'>pts</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        for lbl, val, p in rows_why:
            pc = "color:#4a6fbb;opacity:1;" if p >= 10 else "opacity:0.5;"
            st.markdown(
                f"<div style='display:grid;grid-template-columns:1fr 1fr auto;"
                f"gap:0.4rem 1rem;padding:0.28rem 0;"
                f"border-bottom:1px solid rgba(128,128,128,0.06);'>"
                f"<span style='font-size:0.8rem;font-weight:500;'>{lbl}</span>"
                f"<span style='font-size:0.8rem;opacity:0.6;'>{val}</span>"
                f"<span style='font-size:0.78rem;font-family:ui-monospace,monospace;"
                f"font-weight:600;text-align:right;{pc}'>{p}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    if inside_expander:
        st.markdown(
            f"<div style='font-size:0.6rem;font-weight:600;opacity:0.35;"
            f"text-transform:uppercase;letter-spacing:0.09em;margin:0.7rem 0 0.4rem;'>"
            f"Surface score · {total_score}/100</div>",
            unsafe_allow_html=True,
        )
        _why_table()
    else:
        with st.expander(f"Evidence · Surface score  ·  {total_score}/100", expanded=False):
            _why_table()


def render_action_card(decision):
    uc = decision["urgency_color"]
    ud = decision["urgency_display"]
    rc = decision.get("recommendation_confidence","")
    co = decision.get("intervention_cost","")
    rv = decision.get("reversibility","")
    # Tint background to match urgency color
    import re as _re
    hex_c = uc.lstrip("#")
    r_val, g_val, b_val = int(hex_c[0:2],16), int(hex_c[2:4],16), int(hex_c[4:6],16)
    tint_bg = f"rgba({r_val},{g_val},{b_val},0.05)"
    bdr     = f"rgba({r_val},{g_val},{b_val},0.25)"
    st.markdown(
        f"<div style='border-radius:8px;border:1px solid {bdr};"
        f"background:{tint_bg};padding:0.85rem 1rem;margin-bottom:0.5rem;'>"
        f"<div style='display:flex;align-items:center;gap:5px;margin-bottom:0.35rem;'>"
        f"<div style='width:5px;height:5px;border-radius:50%;background:{uc};flex-shrink:0;'></div>"
        f"<span style='font-size:0.65rem;font-weight:700;color:{uc};"
        f"text-transform:uppercase;letter-spacing:0.1em;'>{ud}</span>"
        f"</div>"
        f"<div style='font-size:0.9rem;line-height:1.55;font-weight:500;'>{decision['action']}</div>"
        f"<div style='font-size:0.65rem;opacity:0.5;margin-top:0.3rem;'>"
        f"Confidence: {rc} &nbsp;·&nbsp; Cost: {co} &nbsp;·&nbsp; {rv.replace('_',' ').title()}"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def render_consequences(cons):
    if not cons: return
    with st.expander("Why this recommendation", expanded=False):
        st.markdown(
            f"<div style='font-size:0.82rem;color:inherit;font-style:italic;"
            f"margin-bottom:0.6rem;'>{cons.get('confidence_frame','')}</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            for k, label in [("expected_value","Expected value"),("time_sensitivity","Time sensitivity"),("wait_cost","Cost of waiting")]:
                st.markdown(f"<div style='font-size:0.78rem;color:inherit;margin-bottom:0.1rem;text-transform:uppercase;letter-spacing:0.05em;'>{label}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.83rem;color:inherit;margin-bottom:0.5rem;'>{cons.get(k,'')}</div>", unsafe_allow_html=True)
        with c2:
            for k, label in [("blast_radius","Blast radius"),("inaction_risk","Risk of inaction"),("operator_burden","Operator burden")]:
                st.markdown(f"<div style='font-size:0.78rem;color:inherit;margin-bottom:0.1rem;text-transform:uppercase;letter-spacing:0.05em;'>{label}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.83rem;color:inherit;margin-bottom:0.5rem;'>{cons.get(k,'')}</div>", unsafe_allow_html=True)


def render_feedback(cluster_title: str):
    key = f"feedback_done_{cluster_title}"
    if st.session_state.get(key):
        st.markdown("<div style='font-size:0.75rem;color:#388e3c;margin-top:0.2rem;'>✓ Feedback recorded</div>", unsafe_allow_html=True)
        return
    with st.expander("Rate this signal", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.3rem;'>Was this real?</div>", unsafe_allow_html=True)
            sr = st.selectbox("sr", ["Select…","Yes","No","Unsure"], index=0,
                              label_visibility="collapsed", key=f"sr_{cluster_title}")
        with c2:
            st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.3rem;'>Action taken?</div>", unsafe_allow_html=True)
            at = st.selectbox("at", ["Select…","None","Investigating","Mitigated"], index=0,
                              label_visibility="collapsed", key=f"at_{cluster_title}")
        with c3:
            st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.3rem;'>Useful?</div>", unsafe_allow_html=True)
            ru = st.selectbox("ru", ["Select…","Yes","Somewhat","No"], index=0,
                              label_visibility="collapsed", key=f"ru_{cluster_title}")
        with c4:
            st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
            if st.button("Save", key=f"fb_{cluster_title}", use_container_width=True):
                if sr == "Select…" and at == "Select…" and ru == "Select…":
                    st.toast("Select at least one option before saving.", icon="⚠️")
                else:
                    kwargs = {}
                    if sr == "Yes":       kwargs["signal_real"] = True
                    elif sr == "No":      kwargs["signal_real"] = False
                    if at not in ("Select…",): kwargs["action_taken"] = at.lower()
                    if ru == "Yes":       kwargs["recommendation_useful"] = True
                    elif ru == "Somewhat":kwargs["recommendation_useful"] = True
                    elif ru == "No":      kwargs["recommendation_useful"] = False
                    if at == "None":      increment_ignored(cluster_title)
                    if kwargs:
                        record_outcome(cluster_title, **kwargs)
                        st.toast("Saved. Thanks for the feedback.", icon="✓")
                    st.session_state[key] = True
                    st.rerun()


def render_resolved(recently_resolved):
    if not recently_resolved: return
    st.markdown(
        "<div style='height:1px;background:rgba(128,128,128,0.1);margin:1.4rem 0 0.8rem;'></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
        "text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.5rem;'>"
        "Recently resolved</div>",
        unsafe_allow_html=True,
    )
    for r in recently_resolved:
        sev_h    = r.get("severity_history", [])
        sev_last = sev_h[-1][1] if sev_h else "WATCH"
        dot_c    = {"CRITICAL":"rgba(217,79,79,0.35)","WATCH":"rgba(192,112,0,0.35)","OPPORTUNITY":"rgba(22,163,74,0.35)"}.get(sev_last,"rgba(128,128,128,0.3)")
        notes = []
        try:
            from datetime import date
            dur = (date.fromisoformat(r.get("resolution_date","")) - date.fromisoformat(r.get("first_seen",""))).days
            if dur > 0: notes.append(f"{dur}d")
        except: pass
        if r.get("peak_escalation_level",0) >= 1: notes.append("escalated")
        if r.get("recurrence_count",0) > 0: notes.append(f"×{r['recurrence_count']}")
        meta = " · ".join(notes)
        _res_d = r.get("resolution_date")
        _res_d_str = str(_res_d) if _res_d and str(_res_d) != "None" else "recently"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.5rem;"
            f"padding:0.3rem 0;opacity:0.45;'>"
            f"<div style='width:6px;height:6px;border-radius:50%;flex-shrink:0;background:{dot_c};'></div>"
            f"<span style='font-size:0.79rem;font-weight:500;'>{r.get('title','')}</span>"
            f"<span style='font-size:0.7rem;margin-left:auto;white-space:nowrap;'>"
            f"Resolved {_res_d_str}{' · '+meta if meta else ''}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # Brand
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;color:inherit;letter-spacing:-0.01em;"
        "margin-bottom:0.1rem;'>GrowthCopilot</div>"
        "<div style='font-size:0.72rem;color:inherit;margin-bottom:1rem;'>"
        "Operational intelligence</div>",
        unsafe_allow_html=True,
    )

    # Navigation group
    st.markdown("<div style='height:1px;background:rgba(128,128,128,0.1);margin:0.8rem 0;'></div>", unsafe_allow_html=True)


    # Always define arch (used in header even when scenario selector is hidden)
    arch = ARCHETYPES[st.session_state.get("archetype_key", "consumer_social")]
    # Scenario group — only for demo/synthetic mode
    if not st.session_state.get("user_events"):
    # Scenario group
        st.markdown(
            "<div style='font-size:0.68rem;font-weight:600;color:inherit;text-transform:uppercase;"
            "letter-spacing:0.08em;margin-bottom:0.4rem;'>Scenario</div>",
            unsafe_allow_html=True,
        )
        display_options  = archetype_display_options()
        current_display  = f"{ARCHETYPES[st.session_state.archetype_key]['emoji']} {ARCHETYPES[st.session_state.archetype_key]['name']}"
        selected_display = st.selectbox("Company type", display_options,
                                        index=display_options.index(current_display),
                                        key="archetype_selector", label_visibility="collapsed")
        new_key = archetype_from_display(selected_display)
        if new_key != st.session_state.archetype_key:
            st.session_state.archetype_key = new_key
            st.session_state.seed = 8
            st.rerun()

        st.markdown(
            f"<div style='font-size:0.75rem;color:inherit;margin-top:0.3rem;line-height:1.4;'>"
            f"{arch['description']}</div>"
            f"<div style='font-size:0.72rem;color:inherit;margin-top:0.3rem;'>"
            f"Key metric: {arch['key_metric']}</div>"
            f"<div style='font-size:0.72rem;color:inherit;margin-top:0.15rem;"
            f"overflow-wrap:break-word;word-break:break-word;'>"
            f"Sources: {', '.join(arch['sources'])}</div>",
            unsafe_allow_html=True,
        )



        render_demo_controls(st.sidebar)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

col_title, col_date = st.columns([3, 2])
with col_title:
    st.markdown(
        f"<div style='font-size:1.3rem;font-weight:700;letter-spacing:-0.02em;color:inherit;'>"
        f"GrowthCopilot</div>"
        f"<div style='font-size:0.78rem;color:inherit;margin-top:0.1rem;'>Daily Briefing</div>",
        unsafe_allow_html=True,
    )
with col_date:
    st.markdown(
        f"<div style='text-align:right;font-size:0.78rem;color:inherit;padding-top:0.3rem;'>"
        f"{date.today().strftime('%A, %b %d')}<br>"
        f"{arch['emoji']} {arch['name']}</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

if 'seed' not in st.session_state:
    st.session_state['seed'] = 8
if 'archetype_key' not in st.session_state:
    st.session_state['archetype_key'] = 'consumer_social'

# Namespace registry by archetype so history doesn't bleed across company types
import growth_copilot_mvp.signal_registry as _sr_mod
_sr_mod._CURRENT_ARCHETYPE = st.session_state.get('archetype_key', 'consumer_social')

_active_seed = st.session_state.seed
if st.session_state.get('demo_mode'):
    _active_seed = get_demo_seed(st.session_state.get('demo_step', 0))
ranked, app_dau, n_events, causal_links, _dq = run_pipeline(
    _active_seed, st.session_state.archetype_key
)
clustered     = cluster_insights(ranked)
all_decisions = [make_decision(c, causal_links) for c in clustered]

surfaced_clusters, background_clusters = classify_clusters(clustered, all_decisions)
attn_report        = attention_report(surfaced_clusters, background_clusters)
reg_records        = update_registry(surfaced_clusters + background_clusters)

_o_sum    = outcome_summary()
_det_prec = detector_precision_from_outcomes()
_trust_adj, _trust_log = [], []
for _c, _d in zip(clustered, all_decisions):
    _adj, _notes = compute_trust_adjustments(_c, _d, reg_records.get(_c["title"]), _o_sum, _det_prec)
    _trust_adj.append(_adj)
    _trust_log.append(_notes)
all_decisions = _trust_adj

primary_cluster    = surfaced_clusters[0] if surfaced_clusters else None
secondary_clusters = surfaced_clusters[1:]
top_hypothesis     = primary_hypothesis(causal_links)
reg_summary        = registry_summary()
recently_resolved  = get_recently_resolved(3)

# ---------------------------------------------------------------------------
# Quiet day
# ---------------------------------------------------------------------------

if not ranked or not surfaced_clusters:
    render_posture([], background_clusters, recently_resolved)
    bg_note = ""
    if background_clusters:
        bg_text = background_summary(background_clusters)
        bg_note = (f"<div style='font-size:0.72rem;opacity:0.22;margin-top:1.2rem;'>"
                   f"{bg_text}</div>")
    st.markdown(
        f"<div style='padding:3.5rem 0 2.5rem;'>"
        f"<div style='font-size:1.6rem;font-weight:700;letter-spacing:-0.04em;'>"
        f"All clear.</div>"
        f"<div style='font-size:0.82rem;opacity:0.3;margin-top:0.7rem;max-width:380px;"
        f"line-height:1.65;'>"
        f"No signal crossed the confidence threshold today. "
        f"The system stays silent when the evidence doesn't warrant action."
        f"</div>{bg_note}</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Primary signal
# ---------------------------------------------------------------------------

elif primary_cluster:
    sev       = primary_cluster["severity"]
    conf      = primary_cluster["confidence"]

    trends        = [getattr(i,"trend",{}) for i in primary_cluster["insights"]]
    worst_trend   = max(trends, key=lambda t: t.get("days_active",0), default={})
    days_active   = worst_trend.get("days_active", 1)
    momentum_dir  = worst_trend.get("direction", "stable")
    p_record      = reg_records.get(primary_cluster["title"], {})
    dir_history   = p_record.get("direction_history", [])
    momentum_days = sum(1 for _, d in reversed(dir_history) if d == momentum_dir) or 1
    decision      = all_decisions[clustered.index(primary_cluster)]
    cons          = decision.get("consequences", {})

    # First-run welcome overlay
    # Show overlay only on true first visit — not after regenerate
    _is_first_visit = (
        not st.session_state.get("first_run_dismissed") and
        not st.session_state.get("user_events") and
        st.session_state.get("seed", 8) == 8 and
        not st.session_state.get("demo_mode") and
        st.session_state.get("_regen_count", 0) == 0
    )
    if _is_first_visit:
        st.markdown(
            "<div style='border-radius:10px;border:1px solid rgba(128,128,128,0.15);"
            "padding:1.4rem 1.5rem;margin-bottom:1.2rem;background:rgba(128,128,128,0.03);'>"
            "<div style='font-size:1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.5rem;'>"
            "Welcome to GrowthCopilot</div>"
            "<div style='font-size:0.83rem;opacity:0.6;line-height:1.65;margin-bottom:1rem;max-width:540px;'>"
            "You're looking at a simulated product intelligence briefing. "
            "The system has detected a signal in synthetic data and is recommending action — "
            "exactly as it would with your real analytics."
            "</div>"
            "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.7rem;margin-bottom:0.2rem;'>"
            "<div style='padding:0.75rem 0.9rem;border-radius:8px;border:1px solid rgba(128,128,128,0.15);'>"
            "<div style='font-size:0.68rem;font-weight:600;opacity:0.45;text-transform:uppercase;"
            "letter-spacing:0.08em;margin-bottom:0.25rem;'>See the full story</div>"
            "<div style='font-size:0.79rem;opacity:0.6;line-height:1.5;'>"
            "Enable <strong>Follow the story</strong> in the sidebar to walk through "
            "a 28-day escalation arc step by step.</div></div>"
            "<div style='padding:0.75rem 0.9rem;border-radius:8px;border:1px solid rgba(128,128,128,0.15);'>"
            "<div style='font-size:0.68rem;font-weight:600;opacity:0.45;text-transform:uppercase;"
            "letter-spacing:0.08em;margin-bottom:0.25rem;'>Try your own data</div>"
            "<div style='font-size:0.79rem;opacity:0.6;line-height:1.5;'>"
            "Click <strong>Connect Your Data</strong> in the sidebar to upload "
            "a CSV from Mixpanel or Amplitude.</div></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Got it, show me the briefing", type="primary", key="dismiss_first_run"):
            st.session_state["first_run_dismissed"] = True
            st.rerun()

    # Data source banner
    if st.session_state.get("user_events"):
        src = st.session_state.get("user_data_source", "CSV")
        n   = len(st.session_state["user_events"])
        st.markdown(
            f"<div style='font-size:0.71rem;margin-bottom:0.8rem;"
            f"padding:0.35rem 0.7rem;border-radius:6px;"
            f"border:1px solid rgba(22,163,74,0.2);background:rgba(22,163,74,0.04);'>"
            f"<span style='color:#16a34a;font-weight:600;'>Your data</span>"
            f" &nbsp;·&nbsp; {src} &nbsp;·&nbsp; {n:,} events"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='font-size:0.71rem;opacity:0.35;margin-bottom:0.3rem;'>"
            "Demo data &nbsp;·&nbsp; Synthetic events &nbsp;·&nbsp; Results are illustrative"
            "</div>",
            unsafe_allow_html=True,
        )
        st.page_link("pages/connect.py", label="Connect your data →")
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    render_posture(surfaced_clusters, background_clusters, recently_resolved)


    # Signal header
    # Adjust displayed severity based on current direction
    # A recovering CRITICAL signal should show as WATCH to avoid contradiction
    _display_sev = sev
    if sev == "CRITICAL" and momentum_dir == "recovering":
        _display_sev = "WATCH"
    elif sev == "CRITICAL" and momentum_dir == "stable" and days_active > 7:
        _display_sev = "WATCH"
    sev_t = SEV_LABEL.get(_display_sev, _display_sev)
    sev_c = {"CRITICAL":"#d94f4f","WATCH":"#c07000","OPPORTUNITY":"#16a34a"}.get(_display_sev,"#888")
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:5px;margin-bottom:0.12rem;'>"
        f"<div style='width:5px;height:5px;border-radius:50%;background:{sev_c};flex-shrink:0;'></div>"
        f"<span style='font-size:0.65rem;font-weight:700;color:{sev_c};"
        f"text-transform:uppercase;letter-spacing:0.1em;opacity:0.7;'>{sev_t}</span>"
        f"</div>"
        f"<div style='font-size:1.25rem;font-weight:700;letter-spacing:-0.025em;"
        f"line-height:1.2;margin-bottom:0.3rem;'>{primary_cluster['title']}</div>",
        unsafe_allow_html=True,
    )
    # ── Editorial observation — ONE sharp analyst sentence ──────────────────
    _obs = get_editorial_observation(primary_cluster, decision, causal_links, p_record)
    if _obs:
        st.markdown(
            f"<div style='font-size:0.88rem;line-height:1.65;font-weight:400;"
            f"margin:0.15rem 0 0.75rem;opacity:0.8;max-width:580px;'>{_obs}</div>",
            unsafe_allow_html=True,
        )

    render_signal_meta(conf, p_record, days_active, momentum_dir, momentum_days)

    # ── Narrative context (change since yesterday — only if meaningful) ──────
    render_narrative(p_record)

    # ── Operational memory (only if history exists) ──────────────────────────
    _all_sigs = get_all_signals()
    _hints    = get_narrative_hints(primary_cluster, p_record, _all_sigs)
    render_narrative_memory(_hints)

    # What matters
    st.markdown(
        "<div style='font-size:0.6rem;font-weight:600;opacity:0.35;"
        "text-transform:uppercase;letter-spacing:0.09em;margin:0.7rem 0 0.3rem;'>"
        "What matters</div>",
        unsafe_allow_html=True,
    )
    for idx, ins in enumerate(primary_cluster["insights"]):
        arrow  = DIR_ARROW.get(getattr(ins,"trend",{}).get("direction","stable"),"")
        rm     = getattr(ins, "raw_metrics", {})
        if idx == 0 and rm:
            # Try to extract a headline number for big stat callout
            headline_val  = None
            headline_sub  = None
            if rm.get("current_rate") is not None and rm.get("baseline_rate") is not None:
                cur = rm["current_rate"] * 100
                base= rm["baseline_rate"] * 100
                headline_val = f"{cur:.1f}%"
                headline_sub = f"vs {base:.1f}% baseline"
            elif rm.get("actual_installs") is not None:
                headline_val = f"{rm['actual_installs']:,}"
                headline_sub = f"installs vs ~{rm.get('expected_installs',0):,} expected"
            elif rm.get("worst_rate") is not None:
                headline_val = f"{rm['worst_rate']*100:.1f}%"
                headline_sub = f"vs {rm.get('others_rate',0)*100:.1f}% other sources"

            if headline_val:
                # Derive a short metric label from signal context
                if rm.get("actual_installs") is not None:
                    _metric_label = "Daily installs"
                elif rm.get("worst_rate") is not None:
                    _metric_label = primary_cluster["title"] + " rate"
                else:
                    _metric_label = primary_cluster["title"]
                st.markdown(
                    f"<div style='padding:0.3rem 0 0.6rem 0;'>"
                    f"<div style='font-size:0.65rem;font-weight:600;opacity:0.38;"
                    f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.35rem;'>"
                    f"{_metric_label}</div>"
                    f"<div style='font-size:2.8rem;font-weight:700;"
                    f"letter-spacing:-0.04em;line-height:1;'>{headline_val}</div>"
                    f"<div style='font-size:0.74rem;opacity:0.4;margin-top:0.3rem;'>"
                    f"{headline_sub}</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='font-size:0.87rem;color:inherit;padding:0.3rem 0;"
                    f"border-left:2px solid #e2e8f0;padding-left:0.7rem;margin-bottom:0.25rem;'>"
                    f"{ins.summary} <span style='color:#94a3b8;'>{arrow}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"<div style='font-size:0.83rem;color:inherit;padding:0.2rem 0;"
                f"border-left:2px solid #f1f5f9;padding-left:0.6rem;margin-bottom:0.2rem;'>"
                f"{ins.summary} <span style='color:#cbd5e1;'>{arrow}</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin:0.5rem 0;'></div>", unsafe_allow_html=True)

    # Combined signal detail expander — evidence first, surface score below
    with st.expander("Signal detail", expanded=False):
        factors = conf.get("factors", {})
        badges_html = "".join(
            f"<span style='display:inline-block;background:rgba(128,128,128,0.08);"
            f"border:1px solid rgba(128,128,128,0.12);border-radius:4px;"
            f"padding:2px 7px;margin:0 4px 4px 0;font-size:0.67rem;font-weight:600;'>"
            f"<span style='opacity:0.45;font-weight:400;'>{FACTOR_LBL.get(k,k).split()[0]} </span>"
            f"<span style='color:{'#4a6fbb' if v>=0.7 else '#c07000' if v>=0.45 else '#d94f4f'};'>"
            f"{int(v*100)}%</span></span>"
            for k, v in factors.items()
        )
        st.markdown(f"<div style='margin-bottom:0.8rem;line-height:1.9;'>{badges_html}</div>",
                    unsafe_allow_html=True)
        items = list(factors.items())
        left_items  = items[:len(items)//2 + len(items)%2]
        right_items = items[len(items)//2 + len(items)%2:]
        gc1, gc2 = st.columns(2)
        for col, col_items in [(gc1, left_items), (gc2, right_items)]:
            with col:
                for k, v in col_items:
                    st.markdown(
                        f"<div style='margin-bottom:0.5rem;'>"
                        f"<div style='font-size:0.68rem;font-weight:500;opacity:0.5;"
                        f"text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.2rem;'>"
                        f"{FACTOR_LBL.get(k,k)}</div>{_conf_bar(v)}</div>",
                        unsafe_allow_html=True,
                    )
        if conf.get("detector_agreement"):
            st.markdown(
                "<div style='font-size:0.73rem;margin-top:0.4rem;padding:3px 8px;"
                "border-radius:4px;display:inline-block;background:rgba(22,163,74,0.1);"
                "color:#16a34a;border:1px solid rgba(22,163,74,0.2);opacity:0.85;'>"
                "✓ Multiple detectors agree</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size:0.73rem;margin-top:0.4rem;padding:3px 8px;"
                "border-radius:4px;display:inline-block;background:rgba(234,179,8,0.08);"
                "color:#b45309;border:1px solid rgba(234,179,8,0.22);'>"
                "⚠ Single detector — treat with caution.</div>",
                unsafe_allow_html=True,
            )
        # Surface score breakdown, separated by a thin rule
        st.markdown(
            "<div style='height:1px;background:rgba(128,128,128,0.1);margin:0.8rem 0 0.4rem;'></div>",
            unsafe_allow_html=True,
        )
        render_why_surfaced(primary_cluster, decision, inside_expander=True)

    if top_hypothesis:
        with st.expander("Likely cause", expanded=True):
            st.markdown(
                f"<div style='font-size:0.82rem;opacity:0.72;line-height:1.55;'>"
                f"{top_hypothesis}</div>",
                unsafe_allow_html=True,
            )

    # Action card
    render_action_card(decision)
    render_consequences(cons)

    # Trust notes
    _ts = trust_summary(p_record, _o_sum)
    if _ts.get("notes"):
        notes_str = " &nbsp;·&nbsp; ".join(_ts["notes"])
        st.markdown(
            f"<div style='font-size:0.72rem;opacity:0.38;margin:0.3rem 0 0.5rem;'>"
            f"◆ {notes_str}</div>",
            unsafe_allow_html=True,
        )

    render_feedback(primary_cluster["title"])


    # Decision details (collapsed)
    with st.expander("Details", expanded=False):
        def _drow(lbl, val):
            st.markdown(
                f"<div style='margin-bottom:0.5rem;'>"
                f"<div style='font-size:0.6rem;font-weight:600;opacity:0.32;"
                f"text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.1rem;'>{lbl}</div>"
                f"<div style='font-size:0.82rem;opacity:0.72;line-height:1.45;'>{val}</div>"
                f"</div>", unsafe_allow_html=True)
        if decision.get("owner"):             _drow("Owner", decision["owner"])
        if decision.get("success_metric"):    _drow("Success metric", decision["success_metric"])
        if decision.get("false_positive_risk"): _drow("If we're wrong", decision["false_positive_risk"])
        blockers = [b for b in decision.get("blockers", []) if b and str(b).strip()]
        if blockers:
            st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.32;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.2rem;'>Blockers</div>", unsafe_allow_html=True)
            for b in blockers:
                st.markdown(f"<div style='font-size:0.8rem;opacity:0.62;padding:0.1rem 0 0.1rem 0.55rem;border-left:1px solid rgba(128,128,128,0.18);margin-bottom:0.12rem;'>{b}</div>", unsafe_allow_html=True)

    if len(causal_links) > 1:
        with st.expander("Related signals", expanded=False):
            for link in causal_links[1:]:
                st.markdown(
                    f"<div style='font-size:0.8rem;opacity:0.68;line-height:1.55;padding:0.2rem 0;'>"
                    f"<span style='font-size:0.62rem;font-weight:600;opacity:0.5;"
                    f"text-transform:uppercase;letter-spacing:0.06em;display:block;"
                    f"margin-bottom:0.1rem;'>{link.get('strength','').title()}</span>"
                    f"{link['hypothesis']}</div>",
                    unsafe_allow_html=True,
                )

    # Secondary signals
    if secondary_clusters:
        st.markdown("---")
        for cluster in secondary_clusters:
            s_e   = SEV_EMOJI.get(cluster["severity"],"")
            s_t   = SEV_LABEL.get(cluster["severity"], cluster["severity"])
            c     = cluster["confidence"]
            s_rec = reg_records.get(cluster["title"],{})
            sec_trends = [getattr(i,"trend",{}) for i in cluster["insights"]]
            sec_worst  = max(sec_trends, key=lambda t: t.get("days_active",0), default={})
            sec_arrow  = DIR_ARROW.get(sec_worst.get("direction","stable"),"")
            sec_dec    = all_decisions[clustered.index(cluster)]
            narrative  = s_rec.get("narrative","")
            recur      = s_rec.get("recurrence_count",0)
            s_color    = STATUS_COLOR.get(s_rec.get("status","active"),"#555")

            st.markdown(
                f"<div style='padding:0.6rem 0.8rem;border-radius:6px;background:rgba(128,128,128,0.05);border:1px solid rgba(128,128,128,0.1);"
                f"border-left:2px solid {URG_COLOR.get(sec_dec['urgency'],'#ccc')};"
                f"margin-bottom:0.4rem;'>"
                f"<div style='display:flex;align-items:center;gap:5px;font-size:0.7rem;font-weight:600;"
                f"opacity:0.6;text-transform:uppercase;letter-spacing:0.08em;'>"
                f"{_sev_dot(cluster['severity'])}{s_t}</div>"
                f"<div style='font-size:0.88rem;font-weight:600;color:inherit;margin:0.1rem 0;'>{cluster['title']}</div>"
                f"<div style='font-size:0.78rem;color:{s_color};'>{narrative}"
                f"{'  ·  Recurred '+str(recur)+'x' if recur>0 else ''}</div>"
                f"<div style='font-size:0.78rem;color:inherit;margin-top:0.2rem;'>"
                f"{'  '.join(ins.summary+' '+sec_arrow for ins in cluster['insights'])}</div>"
                f"<div style='font-size:0.8rem;color:{sec_dec['urgency_color']};font-weight:600;"
                f"margin-top:0.3rem;'>{sec_dec['urgency_display']}: "
                f"<span style='font-weight:400;color:inherit;'>{sec_dec['action']}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    render_resolved(recently_resolved)

    # Pipeline details (very collapsed — for developers only)
    if not st.session_state.get("user_events") and st.session_state.get("demo_mode"):
        with st.expander("System diagnostics", expanded=False):
            _surf = attn_report.get("surface_scores",{}).get(primary_cluster["title"],0)
            _rr   = f"{(_o_sum.get('signal_real_rate') or 0)*100:.0f}%" if _o_sum.get("total_outcomes",0)>0 else "—"
            _tr   = "; ".join(n for ns in _trust_log for n in ns) if any(_trust_log) else "none"
            _cells = [
                ("seed",f"{_active_seed}"),("dau",f"~{app_dau}"),("events",f"{n_events:,}"),
                ("candidates",str(len(ranked))),("causal",str(len(causal_links))),("surface",str(_surf)),
                ("active",str(reg_summary["active"])),("resolved",str(reg_summary["resolved"])),
                ("recurring",str(reg_summary["recurring"])),
                ("outcomes",str(_o_sum.get("total_outcomes",0))),("real rate",_rr),
                ("trust",_tr[:40]+("…" if len(_tr)>40 else "")),
            ]
            rows_html = "".join(
                f"<div style='display:flex;flex-direction:column;'>"
                f"<span style='font-size:0.58rem;font-weight:600;opacity:0.35;"
                f"text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.1rem;'>{k}</span>"
                f"<span style='font-size:0.75rem;font-weight:500;'>{v}</span></div>"
                for k,v in _cells
            )
            st.markdown(
                f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
                f"gap:0.7rem 1rem;font-family:ui-monospace,monospace;'>{rows_html}</div>",
                unsafe_allow_html=True,
            )


    # ---------------------------------------------------------------------------
    # Footer
    # ---------------------------------------------------------------------------

    st.markdown(
    "<div style='height:1px;background:rgba(128,128,128,0.1);margin:2rem 0 1rem;'></div>",
    unsafe_allow_html=True,
    )


col_btn, col_note = st.columns([1, 3])
with col_btn:
    _dm = st.session_state.get("demo_mode", False)
    _cur_step = st.session_state.get("demo_step", 0)
    from growth_copilot_mvp.demo_flow import DEMO_STEP_COUNT as _dsc
    _at_end = _dm and _cur_step >= _dsc - 1
    _btn_label = "Start over ↺" if _at_end else ("Next step →" if _dm else "Regenerate")
    if st.button(_btn_label, type="primary", use_container_width=True):
        if _dm:
            from growth_copilot_mvp.demo_flow import get_demo_seed as _gds
            if _at_end:
                # Loop back to start
                st.session_state["demo_step"] = 0
                st.session_state["seed"] = _gds(0)
            else:
                _ns = _cur_step + 1
                st.session_state["demo_step"] = _ns
                st.session_state["seed"] = _gds(_ns)
        else:
            st.session_state.seed += 1
            st.session_state["_regen_count"] = st.session_state.get("_regen_count", 0) + 1
        st.rerun()
with col_note:
    _dm2 = st.session_state.get("demo_mode", False)
    if _dm2:
        from growth_copilot_mvp.demo_flow import get_demo_seed as _gds2, get_demo_label as _gdl2
        _meta = f"demo · {_gdl2(st.session_state.get('demo_step',0))}"
    else:
        if st.session_state.get("user_events"):
            src = st.session_state.get("user_data_source", "your data")
            n   = len(st.session_state["user_events"])
            _meta = f"{src} · {n:,} events"
        else:
            _meta = ""  # hide debug info from regular users
    st.markdown(
    f"<div style='font-family:ui-monospace,monospace;"
    f"font-size:0.67rem;opacity:0.32;padding-top:0.65rem;'>{_meta}</div>",
    unsafe_allow_html=True,
) else "Regenerate")
    if st.button(_btn_label, type="primary", use_container_width=True):
        if _dm:
            from growth_copilot_mvp.demo_flow import get_demo_seed as _gds
            if _at_end:
                # Loop back to start
                st.session_state["demo_step"] = 0
                st.session_state["seed"] = _gds(0)
            else:
                _ns = _cur_step + 1
                st.session_state["demo_step"] = _ns
                st.session_state["seed"] = _gds(_ns)
        else:
            st.session_state.seed += 1
            st.session_state["_regen_count"] = st.session_state.get("_regen_count", 0) + 1
        st.rerun()
with col_note:
    _dm2 = st.session_state.get("demo_mode", False)
    if _dm2:
        from growth_copilot_mvp.demo_flow import get_demo_seed as _gds2, get_demo_label as _gdl2
        _meta = f"demo · {_gdl2(st.session_state.get('demo_step',0))}"
    else:
        if st.session_state.get("user_events"):
            src = st.session_state.get("user_data_source", "your data")
            n   = len(st.session_state["user_events"])
            _meta = f"{src} · {n:,} events"
        else:
            _meta = ""  # hide debug info from regular users
    st.markdown(
    f"<div style='font-family:ui-monospace,monospace;"
    f"font-size:0.67rem;opacity:0.32;padding-top:0.65rem;'>{_meta}</div>",
    unsafe_allow_html=True,
)
    unsafe_allow_html=True,
)
)
